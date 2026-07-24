#!/usr/bin/env python3
"""Create semantic validation generation-request artifacts for routed formals."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

from semantic_artifact_ast_support import augment_artifact, display_body
from semantic_artifact_inventory import VOLUME_NAMES, artifact_package_for, routed_formals


REQUEST_SCHEMA = "lra.semantic-validation-artifact-request/1.0"
SUMMARY_SCHEMA = "lra.semantic-validation-artifact-creation/1.0"
ARTIFACT_SCHEMA = "lra.semantic-artifact/1.0"

FORMALIZATION_RECORD_RE = re.compile(
    r"\\begin\{formalizationrecord\}.*?\\Formalizes\{(?P<label>[^}]+)\}"
    r".*?\\textbf\{Lean module:\}\s*\\texttt\{(?P<module>[^}]+)\}\.\\par"
    r".*?\\LeanDeclaration\{(?P<declaration>[^}]+)\}"
    r".*?\\textbf\{Status:\}\s*(?P<status>.*?)\\par"
    r".*?\\begin\{leancode\}(?P<code>.*?)\\end\{leancode\}"
    r".*?\\end\{formalizationrecord\}",
    re.S,
)
FORMALIZATION_SOURCE_RE = re.compile(r"\\FormalizationSource\{(?P<source>[^}]*)\}")


def _clean_latex_text(value: str) -> str:
    return " ".join(value.replace("\\texttt{lra-lean}", "lra-lean").replace(".", " ").split())


def extract_formalization_records(source_text: str, label: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for match in FORMALIZATION_RECORD_RE.finditer(source_text):
        if match.group("label") != label:
            continue
        block = match.group(0)
        source_match = FORMALIZATION_SOURCE_RE.search(block)
        status_text = _clean_latex_text(match.group("status"))
        status = "checked" if "checked" in status_text.lower() else status_text
        records.append(
            {
                "artifact_label": label,
                "system": "Lean 4",
                "repository": "lra-lean",
                "module": match.group("module"),
                "declaration": match.group("declaration").replace(r"\_", "_"),
                "status": status,
                "environment": {
                    "mathlib_policy": "prohibited",
                },
                "source_reference": source_match.group("source") if source_match else "",
                "source_path": "",
                "code": match.group("code").strip(),
            }
        )
    return records


def build_generation_request(candidate: Any, repo_root: Path) -> dict[str, Any]:
    package = artifact_package_for(candidate, repo_root)
    source = candidate.as_json(repo_root, include_source_text=False)
    try:
        full_source_text = candidate.source_file.read_text(encoding="utf-8")
    except Exception:
        full_source_text = candidate.text
    formalizations = extract_formalization_records(full_source_text, candidate.label)
    return {
        "schema_version": REQUEST_SCHEMA,
        "label": candidate.label,
        "kind": candidate.kind,
        "title": candidate.title,
        "source": source,
        "suggested_package": package,
        "llm_packet": {
            "task": {
                "mode": "generate_semantic_artifact",
                "requested_action": "create_artifact_package",
            },
            "source": {
                "repository_root": str(repo_root),
                "file": candidate.source_file.relative_to(repo_root).as_posix(),
                "label": candidate.label,
                "environment_kind": candidate.kind,
                "source_line_start": candidate.line_start,
                "source_line_end": candidate.line_end,
                "current_tex": candidate.text,
                "formalizations": formalizations,
            },
        },
    }


def request_from_inventory_item(item: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    source_text = item.get("source_text")
    if source_text is None:
        raise ValueError(
            "inventory item does not include source_text; rerun semantic_artifact_inventory.py "
            "with --include-source-text or pass a routed scope directly"
        )
    formalizations = extract_formalization_records(source_text, item["label"])
    return {
        "schema_version": REQUEST_SCHEMA,
        "label": item["label"],
        "kind": item["kind"],
        "title": item.get("title"),
        "source": {key: value for key, value in item.items() if key != "source_text"},
        "suggested_package": item["artifact_package"],
        "llm_packet": {
            "task": {
                "mode": "generate_semantic_artifact",
                "requested_action": "create_artifact_package",
            },
            "source": {
                "repository_root": str(repo_root),
                "file": item["source_file"],
                "label": item["label"],
                "environment_kind": item["kind"],
                "source_line_start": item["source_line_start"],
                "source_line_end": item["source_line_end"],
                "current_tex": source_text,
                "formalizations": formalizations,
            },
        },
    }


def prompt_text(request: dict[str, Any]) -> str:
    label = request["label"]
    package = request["suggested_package"]["directory"]
    return (
        f"# Semantic Artifact Generation Request\n\n"
        f"Generate the reviewed semantic artifact package for `{label}`.\n\n"
        f"- Target package: `{package}`\n"
        f"- Use `generation-request.json` for metadata and `source.tex` for the exact routed source block.\n"
        f"- Produce the governed semantic package files, including `artifact.yaml` and `corrected.tex`.\n"
        f"- Do not edit volume source directly as part of request generation.\n"
    )


def existing_semantic_package(repo_root: Path, request: dict[str, Any]) -> bool:
    package = request["suggested_package"]
    return (repo_root / package["artifact"]).exists() and (repo_root / package["corrected_tex"]).exists()


def git_commit(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def local_draft_artifact(request: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    source = request["llm_packet"]["source"]
    source_tex = str(source["current_tex"])
    standard_latex = display_body(source_tex)
    source_hash = "sha256:" + hashlib.sha256(source_tex.encode("utf-8")).hexdigest()
    volume = request.get("source", {}).get("book_root", "").split("-", 2)[1] if "-" in request.get("source", {}).get("book_root", "") else None
    artifact = {
        "schema_version": ARTIFACT_SCHEMA,
        "identity": {
            "label": request["label"],
            "kind": request["kind"],
            "title": request.get("title"),
            "canonical_name": request.get("title") or request["label"],
            "status": "local_draft",
            "atomicity": {
                "status": "requires_review",
                "concepts_detected": [],
                "owning_concept": request.get("title") or request["label"],
                "split_reason": None,
            },
        },
        "location": {
            "repository": repo_root.name,
            "commit": git_commit(repo_root),
            "volume": volume,
            "book": request.get("source", {}).get("book"),
            "chapter": request.get("source", {}).get("chapter"),
            "topic": request.get("source", {}).get("section"),
            "source_file": source["file"],
            "source_line_start": source["source_line_start"],
            "source_line_end": source["source_line_end"],
            "source_hash": source_hash,
        },
        "classification": {
            "mathematical_domain": request.get("source", {}).get("chapter"),
            "artifact_form": request["kind"],
            "logical_shape": "local parser draft",
            "logical_framework": "mathematical_vernacular",
            "language_level": "mixed",
        },
        "context": [],
        "parameters": [],
        "assumptions": [],
        "statement": {
            "canonical_prose": request.get("title") or request["label"],
            "canonical_latex": source_tex,
        },
        "logical_forms": {
            "standard_quantified": {
                "latex": standard_latex,
            },
            "predicate_reading": None,
            "negation": {
                "mechanical": None,
                "approved_normal_form": None,
                "normalization_requires": [],
            },
            "contrapositive": None,
            "equivalent_forms": [],
        },
        "semantics": {
            "codex_local_reference": True,
            "local_draft": True,
        },
        "failure_analysis": {
            "applicability_failures": [],
            "statement_failures": [
                {
                    "id": "statement-failure",
                    "description": "Draft failure semantics require semantic review.",
                }
            ],
        },
        "relationships": {
            "dependency_edges": [],
            "ontology_edges": [],
            "provenance_edges": [],
            "proof_edges": [],
        },
        "notation": {},
        "exposition": {
            "summary": "Codex-local draft semantic validation payload generated from routed source.",
        },
        "verification": {
            "canonical_proof": None,
            "formalizations": source.get("formalizations") or [],
            "external_library_crosswalks": [],
            "proof_vault_records": [],
        },
        "provenance": {
            "origin": {
                "kind": "normalized_source_statement",
                "source_status": "single_primary_statement",
                "primary_source_statement": {
                    "role": "primary",
                    "source_id": None,
                    "label": request["label"],
                    "citation": None,
                    "page_range": None,
                    "evidence": "routed source environment",
                    "notes": "Codex-local draft; requires semantic review.",
                },
                "component_sources": [],
                "derivation_rule": None,
                "requires_review": True,
            },
            "explicit_from_source": ["formal environment and attached support blocks"],
            "normalized_from_source": ["ASTs are generated by local governed parsers when available"],
            "inferred_from_registry": [],
            "generated_by_analysis": ["Codex local materialize-local mode"],
            "unresolved": [],
        },
        "governance": {
            "governance_repository": "lra-governance",
            "governance_commit": git_commit(Path(__file__).resolve().parents[2]),
            "registry_commit": git_commit(Path(__file__).resolve().parents[2]),
            "schema_commit": git_commit(Path(__file__).resolve().parents[2]),
        },
    }
    return augment_artifact(artifact, source_tex)


def create_requests(
    generation_requests: list[dict[str, Any]],
    repo_root: Path,
    *,
    mode: str = "prompt",
    dry_run: bool = False,
    overwrite: bool = False,
    materialize_local: bool = False,
    limit: int | None = None,
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "schema_version": SUMMARY_SCHEMA,
        "mode": mode,
        "dry_run": dry_run,
        "materialize_local": materialize_local,
        "created": [],
        "skipped_existing_request": [],
        "already_packaged": [],
        "materialized": [],
    }
    selected = generation_requests[:limit] if limit is not None else generation_requests
    for request in selected:
        package_dir = repo_root / request["suggested_package"]["directory"]
        request_path = package_dir / "generation-request.json"
        prompt_path = package_dir / "prompt.md"
        source_path = package_dir / "source.tex"
        artifact_path = package_dir / "artifact.yaml"
        corrected_path = package_dir / "corrected.tex"
        record = {
            "label": request["label"],
            "directory": package_dir.relative_to(repo_root).as_posix(),
            "generation_request": request_path.relative_to(repo_root).as_posix(),
            "prompt": prompt_path.relative_to(repo_root).as_posix(),
            "source_tex": source_path.relative_to(repo_root).as_posix(),
        }
        if existing_semantic_package(repo_root, request):
            summary["already_packaged"].append(record)
            continue
        if request_path.exists() and not overwrite:
            summary["skipped_existing_request"].append(record)
            continue
        if not dry_run:
            package_dir.mkdir(parents=True, exist_ok=True)
            request_payload = dict(request)
            request_payload["creation_mode"] = mode
            request_path.write_text(json.dumps(request_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            source_path.write_text(request["llm_packet"]["source"]["current_tex"], encoding="utf-8")
            if mode == "prompt":
                prompt_path.write_text(prompt_text(request), encoding="utf-8")
            if materialize_local:
                corrected_path.write_text(request["llm_packet"]["source"]["current_tex"], encoding="utf-8")
                artifact = local_draft_artifact(request, repo_root)
                artifact_path.write_text(yaml.safe_dump(artifact, sort_keys=False, allow_unicode=True), encoding="utf-8")
                summary["materialized"].append(record)
        summary["created"].append(record)

    summary["requested_count"] = len(generation_requests)
    summary["selected_count"] = len(selected)
    summary["created_count"] = len(summary["created"])
    summary["skipped_existing_request_count"] = len(summary["skipped_existing_request"])
    summary["already_packaged_count"] = len(summary["already_packaged"])
    summary["materialized_count"] = len(summary["materialized"])
    return summary


def load_inventory_requests(path: Path) -> tuple[Path, list[dict[str, Any]]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("inventory must be a mapping")
    repo_root = Path(data["repo_root"]).resolve()
    requests = [
        request_from_inventory_item(item, repo_root)
        for item in data.get("items", [])
        if not item.get("artifact_package", {}).get("exists")
    ]
    return repo_root, requests


def scoped_requests(args: argparse.Namespace) -> tuple[Path, list[dict[str, Any]]]:
    repo_root, _volume_source, _roots, candidates = routed_formals(args)
    requests = []
    for candidate in candidates:
        package = artifact_package_for(candidate, repo_root)
        if not package["exists"]:
            requests.append(build_generation_request(candidate, repo_root))
    return repo_root, requests


def main() -> int:
    parser = argparse.ArgumentParser(description="Create generation-request artifacts for missing semantic packages.")
    parser.add_argument("--inventory", type=Path, help="Inventory JSON/YAML produced with --include-source-text.")
    parser.add_argument("--repos-root", type=Path)
    parser.add_argument("--volume-root", type=Path)
    parser.add_argument("--volume", choices=tuple(VOLUME_NAMES))
    parser.add_argument("--book")
    parser.add_argument("--chapter")
    parser.add_argument("--section")
    parser.add_argument("--label")
    parser.add_argument("--target", type=Path)
    parser.add_argument("--mode", choices=("prompt", "packet"), default="prompt")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--materialize-local",
        action="store_true",
        help="Also write draft artifact.yaml and corrected.tex from routed source using local parsers only.",
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=("yaml", "json"), default="yaml")
    args = parser.parse_args()

    try:
        if args.inventory:
            repo_root, requests = load_inventory_requests(args.inventory)
        else:
            repo_root, requests = scoped_requests(args)
        payload = create_requests(
            requests,
            repo_root,
            mode=args.mode,
            dry_run=args.dry_run,
            overwrite=args.overwrite,
            materialize_local=args.materialize_local,
            limit=args.limit,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
