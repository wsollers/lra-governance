#!/usr/bin/env python3
"""Audit checked Lean theorems for matching TeX LeanFormalizes tags."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

try:
    from search_internal_object_index import record_score, tokenize
except ModuleNotFoundError:  # pragma: no cover - exercised by package imports
    from tools.governance.search_internal_object_index import record_score, tokenize


def load_payload(path: Path) -> dict[str, Any]:
    if path.suffix.lower() in {".yaml", ".yml"}:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("objects"), list):
        raise ValueError(f"{path} is not an internal object index payload")
    return data


def write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() in {".yaml", ".yml"}:
        text = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    else:
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")


def terminal_declaration(record: dict[str, Any]) -> str:
    return str(record.get("declaration") or record.get("name") or "").split(".")[-1]


def lean_identity(record: dict[str, Any]) -> tuple[str, str]:
    return str(record.get("module") or ""), terminal_declaration(record)


def link_identity(link: dict[str, Any]) -> tuple[str, str]:
    return str(link.get("module") or ""), str(link.get("declaration") or "").split(".")[-1]


def production_lean(record: dict[str, Any]) -> bool:
    return str(record.get("path") or "").replace("\\", "/").startswith("LRA/")


def compact_lean(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "object_id": record.get("object_id"),
        "kind": record.get("kind"),
        "name": record.get("name"),
        "module": record.get("module"),
        "declaration": terminal_declaration(record),
        "path": record.get("path"),
        "line": record.get("line"),
    }


def compact_tex(record: dict[str, Any], link: dict[str, Any]) -> dict[str, Any]:
    return {
        "object_id": record.get("object_id"),
        "kind": record.get("kind"),
        "name": record.get("name"),
        "label": record.get("label"),
        "path": record.get("path"),
        "line": record.get("line"),
        "link_status": link.get("status"),
    }


def normalize_key(text: str) -> str:
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def lean_query(record: dict[str, Any]) -> str:
    metadata = record.get("metadata", {})
    parts = [
        str(metadata.get("leading_comment_name") or ""),
        str(metadata.get("leading_comment") or ""),
        str(record.get("name") or ""),
        terminal_declaration(record),
        str(record.get("statement") or ""),
        str(record.get("module") or ""),
    ]
    return " ".join(part for part in parts if part).strip()


def candidate_ref(record: dict[str, Any], score: float) -> dict[str, Any]:
    return {
        "score": round(score, 4),
        "object_id": record.get("object_id"),
        "kind": record.get("kind"),
        "name": record.get("name"),
        "label": record.get("label"),
        "path": record.get("path"),
        "line": record.get("line"),
    }


def tex_search_blob(record: dict[str, Any]) -> str:
    return " ".join(
        str(record.get(field) or "")
        for field in ("name", "label", "statement", "search_text", "path")
    )


def important_tokens(text: str) -> set[str]:
    return {
        token
        for token in tokenize(text)
        if len(token) >= 4 and token not in {"theorem", "lemma", "definition", "proposition", "corollary"}
    }


def lean_to_tex_candidates(
    lean: dict[str, Any],
    tex_records: list[tuple[dict[str, Any], set[str]]],
    *,
    limit: int = 5,
) -> tuple[str, list[dict[str, Any]]]:
    query = lean_query(lean)
    if not query:
        return "none", []
    scored = []
    lean_title = normalize_key(str(lean.get("metadata", {}).get("leading_comment_name") or lean.get("name") or ""))
    lean_decl = normalize_key(terminal_declaration(lean))
    query_tokens = important_tokens(query)
    for tex, tex_tokens in tex_records:
        if tex.get("metadata", {}).get("starred"):
            continue
        if "/proofs/" in str(tex.get("path") or ""):
            continue
        if query_tokens and not (query_tokens & tex_tokens):
            continue
        score = record_score(tex, query, ("name", "label", "statement", "search_text", "path"))
        tex_title = normalize_key(str(tex.get("name") or ""))
        tex_label = normalize_key(str(tex.get("label") or ""))
        if lean_title and lean_title == tex_title:
            score += 120.0
        if lean_decl and (lean_decl == tex_title or lean_decl in tex_label):
            score += 80.0
        if score > 0:
            scored.append((score, tex))
    scored.sort(key=lambda item: (-item[0], str(item[1].get("path") or ""), int(item[1].get("line") or 0)))
    candidates = [candidate_ref(tex, score) for score, tex in scored[:limit]]
    if not candidates:
        return "none", []
    top = float(candidates[0]["score"])
    second = float(candidates[1]["score"]) if len(candidates) > 1 else 0.0
    if top >= 120.0 and top - second >= 20.0:
        return "reliable", candidates
    if top >= 70.0:
        return "review", candidates
    return "none", candidates


def build_audit(
    index_payload: dict[str, Any],
    *,
    include_lemmas: bool = False,
    production_only: bool = True,
    include_candidate_lookup: bool = False,
    example_limit: int = 20,
) -> dict[str, Any]:
    kinds = {"theorem"}
    if include_lemmas:
        kinds.add("lemma")

    lean_records = [
        item
        for item in index_payload.get("objects", [])
        if item.get("source_family") == "lean"
        and item.get("kind") in kinds
        and item.get("metadata", {}).get("verification_status") == "checked"
        and (not production_only or production_lean(item))
    ]
    tex_records = [item for item in index_payload.get("objects", []) if item.get("source_family") == "tex"]
    tex_records_with_tokens = [(item, important_tokens(tex_search_blob(item))) for item in tex_records]

    tex_links_by_lean: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for tex in tex_records:
        for link in tex.get("metadata", {}).get("lean_formalizes") or []:
            tex_links_by_lean.setdefault(link_identity(link), []).append(compact_tex(tex, link))

    tagged = []
    missing = []
    status_counts: Counter[str] = Counter()
    candidate_counts: Counter[str] = Counter()
    missing_with_candidates = []
    for lean in lean_records:
        identity = lean_identity(lean)
        links = tex_links_by_lean.get(identity, [])
        if links:
            tagged.append({"lean": compact_lean(lean), "tex_links": links})
            for link in links:
                status_counts[str(link.get("link_status") or "(missing)")] += 1
        else:
            missing_ref = compact_lean(lean)
            if include_candidate_lookup:
                classification, candidates = lean_to_tex_candidates(lean, tex_records_with_tokens)
                missing_ref["candidate_lookup"] = {
                    "classification": classification,
                    "query": lean_query(lean),
                    "candidates": candidates,
                }
                candidate_counts[classification] += 1
                if classification != "none":
                    missing_with_candidates.append(missing_ref)
            missing.append(missing_ref)

    by_module: Counter[str] = Counter()
    for item in missing:
        module = str(item.get("module") or "(missing)")
        parts = module.split(".")
        by_module[".".join(parts[:3]) if len(parts) >= 3 else module] += 1

    return {
        "schema_version": "lra.checked-lean-tex-tag-audit/1.0",
        "inputs": index_payload.get("inputs", {}),
        "policy": {
            "lean_kinds": sorted(kinds),
            "lean_verification_status": "checked",
            "production_only": production_only,
            "matching": "exact Lean module plus terminal declaration against TeX LeanFormalizes link",
        },
        "counts": {
            "checked_lean_theorems": len(lean_records),
            "checked_lean_theorems_with_tex_tag": len(tagged),
            "checked_lean_theorems_missing_tex_tag": len(missing),
            "tex_link_statuses_for_tagged_lean": dict(sorted(status_counts.items())),
            "missing_candidate_lookup": dict(sorted(candidate_counts.items())),
        },
        "missing_by_module_prefix": dict(sorted(by_module.items())),
        "examples": {
            "tagged": tagged[:example_limit],
            "missing": missing[:example_limit],
            "missing_with_candidates": missing_with_candidates[:example_limit],
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True, help="Internal object index JSON/YAML.")
    parser.add_argument("--output", type=Path, required=True, help="Audit output YAML/JSON.")
    parser.add_argument("--include-lemmas", action="store_true", help="Include checked Lean lemmas as well as theorems.")
    parser.add_argument("--include-nonproduction-lean", action="store_true")
    parser.add_argument("--include-candidate-lookup", action="store_true", help="Search TeX records for likely matches to missing checked Lean declarations.")
    parser.add_argument("--example-limit", type=int, default=20)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    audit = build_audit(
        load_payload(args.index),
        include_lemmas=args.include_lemmas,
        production_only=not args.include_nonproduction_lean,
        include_candidate_lookup=args.include_candidate_lookup,
        example_limit=args.example_limit,
    )
    write_payload(args.output, audit)
    counts = audit["counts"]
    print(
        "checked Lean theorem tag audit: "
        f"checked={counts['checked_lean_theorems']} "
        f"tagged={counts['checked_lean_theorems_with_tex_tag']} "
        f"missing={counts['checked_lean_theorems_missing_tex_tag']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
