#!/usr/bin/env python3
"""Render GPT-facing semantic AST comparison packets.

The report keeps original TeX visible and places it beside standard quantified
TeX, hand-parser and Lark-parser witnesses, artifact ASTs, and negation ASTs.
It is deliberately diagnostic: it does not decide which side is right.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from semantic_artifact_inventory import artifact_package_for, routed_formals


def fenced(value: Any, info: str = "text") -> str:
    if value in (None, ""):
        return "_missing_\n"
    if not isinstance(value, str):
        value = yaml.safe_dump(value, sort_keys=False, allow_unicode=True)
    return f"```{info}\n{value.rstrip()}\n```\n"


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: YAML root must be a mapping")
    return data


def load_scope(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def scope_items(scope: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("label")): item for item in scope.get("items", []) if isinstance(item, dict)}


def result_codes(item: dict[str, Any] | None) -> list[str]:
    if not item:
        return []
    result = item.get("result") or {}
    return sorted({str(finding.get("code")) for finding in result.get("findings", []) if finding.get("code")})


def result_status(item: dict[str, Any] | None) -> str:
    if not item:
        return "not validated"
    result = item.get("result") or {}
    return str(result.get("result") or item.get("status") or "unknown")


def parser_table(block: dict[str, Any]) -> str:
    witnesses = block.get("parser_witnesses") if isinstance(block, dict) else None
    if not isinstance(witnesses, dict):
        return "_missing parser witnesses_\n"
    hand = witnesses.get("hand_parser") if isinstance(witnesses.get("hand_parser"), dict) else {}
    lark = witnesses.get("lark_parser") if isinstance(witnesses.get("lark_parser"), dict) else {}
    lines = [
        f"- Hand parser available: `{hand.get('available')}`",
        f"- Lark parser available: `{lark.get('available')}`",
        f"- Parsers agree: `{witnesses.get('parsers_agree')}`",
    ]
    return "\n".join(lines) + "\n"


def render_label(repo_root: Path, candidate: Any, scope_by_label: dict[str, dict[str, Any]]) -> str:
    package = artifact_package_for(candidate, repo_root)
    artifact_path = repo_root / package["artifact"]
    corrected_path = repo_root / package["corrected_tex"]
    item = scope_by_label.get(candidate.label)
    data = load_yaml(artifact_path) if artifact_path.exists() else {}
    statement = data.get("statement") if isinstance(data.get("statement"), dict) else {}
    forms = data.get("logical_forms") if isinstance(data.get("logical_forms"), dict) else {}
    standard = forms.get("standard_quantified") if isinstance(forms.get("standard_quantified"), dict) else {}
    predicate = forms.get("predicate_reading") if isinstance(forms.get("predicate_reading"), dict) else {}
    negation = forms.get("negation") if isinstance(forms.get("negation"), dict) else {}
    mechanical = negation.get("mechanical") if isinstance(negation.get("mechanical"), dict) else {}
    approved = negation.get("approved_normal_form") if isinstance(negation.get("approved_normal_form"), dict) else {}

    lines = [
        f"## {candidate.label}",
        "",
        f"- Kind: `{candidate.kind}`",
        f"- Title: `{candidate.title or ''}`",
        f"- Validation: `{result_status(item)}`",
        f"- Finding codes: `{', '.join(result_codes(item)) or 'none'}`",
        f"- Source: `{candidate.source_file.relative_to(repo_root).as_posix()}:{candidate.line_start}`",
        f"- Artifact: `{package['artifact']}`",
        "",
        "### Original Routed TeX",
        "",
        fenced(candidate.text, "tex"),
        "### Canonical Statement TeX",
        "",
        fenced(statement.get("canonical_latex"), "tex"),
        "### Standard Quantified TeX",
        "",
        fenced(standard.get("latex"), "tex"),
        "### Predicate Reading TeX",
        "",
        fenced(predicate.get("latex"), "tex"),
        "### Parser Witness Status",
        "",
        "**Standard quantified**",
        "",
        parser_table(standard),
        "**Predicate reading**",
        "",
        parser_table(predicate),
        "### Artifact AST",
        "",
        fenced(statement.get("semantic_ast"), "yaml"),
        "### Standard Quantified AST",
        "",
        fenced(standard.get("ast"), "yaml"),
        "### Hand Parser AST",
        "",
        fenced(((standard.get("parser_witnesses") or {}).get("hand_parser") or {}).get("ast"), "yaml"),
        "### Lark Parser AST",
        "",
        fenced(((standard.get("parser_witnesses") or {}).get("lark_parser") or {}).get("ast"), "yaml"),
        "### Mechanical Negation",
        "",
        fenced(mechanical.get("latex"), "tex"),
        fenced(mechanical.get("ast"), "yaml"),
        "### Approved/Normalized Negation",
        "",
        fenced(approved.get("latex"), "tex"),
        fenced(approved.get("ast"), "yaml"),
    ]
    if corrected_path.exists():
        lines.extend(["### Materialized Corrected TeX", "", fenced(corrected_path.read_text(encoding="utf-8"), "tex")])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repos-root", type=Path, default=Path.cwd().parent)
    parser.add_argument("--volume-root", type=Path)
    parser.add_argument("--volume", required=True)
    parser.add_argument("--book")
    parser.add_argument("--chapter")
    parser.add_argument("--section")
    parser.add_argument("--target", type=Path)
    parser.add_argument("--label", action="append", dest="labels")
    parser.add_argument("--scope-report", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.label = None

    repo_root, _volume_source, _roots, candidates = routed_formals(args)
    selected = candidates
    if args.labels:
        keep = set(args.labels)
        selected = [candidate for candidate in selected if candidate.label in keep]
    scope = scope_items(load_scope(args.scope_report))
    lines = [
        "# Semantic AST Comparison Packet",
        "",
        "This packet preserves the original TeX and compares it with generated support forms, parser witnesses, artifact ASTs, and mechanical negations.",
        "",
    ]
    for candidate in selected:
        package = artifact_package_for(candidate, repo_root)
        if not (repo_root / package["artifact"]).exists():
            continue
        lines.append(render_label(repo_root, candidate, scope))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
