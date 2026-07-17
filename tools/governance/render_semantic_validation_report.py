#!/usr/bin/env python3
"""Render Markdown review reports for routed semantic validation targets."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

from semantic_artifact_inventory import VOLUME_NAMES, artifact_package_for, routed_formals
from validate_semantic_logic import extract_llm_artifact_and_tex, load_mapping, load_serialized_mapping
from validate_semantic_scope import find_llm_payload, indexed_llm_payloads, label_slug


REPORT_SCHEMA = "lra.semantic-validation-markdown-report/1.0"

REMARK_RE = re.compile(
    r"\\begin\{remark\*\}\[(?P<title>[^\]]+)\](?P<body>.*?)\\end\{remark\*\}",
    re.DOTALL,
)
DEPENDENCIES_RE = re.compile(r"\\begin\{dependencies\}(?P<body>.*?)\\end\{dependencies\}", re.DOTALL)
FORMAL_ENV_RE = re.compile(
    r"\\begin\{(?P<env>definition|axiom|theorem|lemma|proposition|corollary)\}"
    r"(?:\[[^\]]+\])?.*?\\end\{(?P=env)\}",
    re.DOTALL | re.IGNORECASE,
)
HYPERREF_RE = re.compile(r"\\hyperref\[(?P<label>[^\]]+)\]\{(?P<title>[^{}]+)\}")


SOURCE_FIELD_TITLES = {
    "standard_quantified": "Standard quantified statement",
    "predicate_reading": "Predicate reading",
    "negated_quantified": "Negated quantified statement",
    "negation_predicate": "Negation predicate reading",
    "failure_modes": "Failure modes",
    "interpretation": "Interpretation",
    "dependencies": "Dependencies",
}


def load_data(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain a mapping")
    return data


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        value = yaml.safe_dump(value, sort_keys=False, allow_unicode=True)
    return re.sub(r"\s+", " ", value).strip()


def fenced(value: Any, info: str = "text") -> str:
    if value in (None, ""):
        return "_missing_\n"
    text = value if isinstance(value, str) else yaml.safe_dump(value, sort_keys=False, allow_unicode=True)
    return f"```{info}\n{text.rstrip()}\n```\n"


def md_escape(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def compact_status(value: str) -> str:
    return value.replace("_", " ")


def extract_source_sections(source_text: str) -> dict[str, str]:
    remarks = {match.group("title").strip().lower(): match.group("body").strip() for match in REMARK_RE.finditer(source_text)}
    sections: dict[str, str] = {}
    for key, title in SOURCE_FIELD_TITLES.items():
        if key == "dependencies":
            deps = DEPENDENCIES_RE.search(source_text)
            if deps:
                sections[key] = deps.group("body").strip()
            continue
        value = remarks.get(title.lower())
        if value:
            sections[key] = value
    return sections


def extract_original_environment(source_text: str) -> str:
    match = FORMAL_ENV_RE.search(source_text)
    return match.group(0).strip() if match else source_text.strip()


def dependency_labels(dependency_tex: str | None) -> list[str]:
    if not dependency_tex:
        return []
    return [f"{match.group('label')} ({match.group('title')})" for match in HYPERREF_RE.finditer(dependency_tex)]


def artifact_summary(data: dict[str, Any] | None) -> dict[str, Any]:
    if not data:
        return {}
    logical = data.get("logical_forms") if isinstance(data.get("logical_forms"), dict) else {}
    negation = logical.get("negation") if isinstance(logical.get("negation"), dict) else {}
    failure = data.get("failure_analysis") if isinstance(data.get("failure_analysis"), dict) else {}
    relationships = data.get("relationships") if isinstance(data.get("relationships"), dict) else {}
    return {
        "canonical_latex": (data.get("statement") or {}).get("canonical_latex") if isinstance(data.get("statement"), dict) else None,
        "standard_quantified": (logical.get("standard_quantified") or {}).get("latex") if isinstance(logical.get("standard_quantified"), dict) else None,
        "predicate_reading": (logical.get("predicate_reading") or {}).get("latex") if isinstance(logical.get("predicate_reading"), dict) else None,
        "negation_mechanical": (negation.get("mechanical") or {}).get("latex") if isinstance(negation.get("mechanical"), dict) else None,
        "negation_approved": (negation.get("approved_normal_form") or {}).get("latex")
        if isinstance(negation.get("approved_normal_form"), dict)
        else None,
        "failure_analysis": failure,
        "dependency_edges": relationships.get("dependency_edges") if isinstance(relationships, dict) else None,
    }


def compare_row(name: str, source_value: Any, artifact_value: Any, llm_value: Any) -> str:
    source_norm = normalize_text(source_value)
    artifact_norm = normalize_text(artifact_value)
    llm_norm = normalize_text(llm_value)
    if not source_norm and not artifact_norm and not llm_norm:
        status = "missing"
    elif source_norm and (source_norm == artifact_norm or source_norm == llm_norm):
        status = "exact match"
    elif artifact_norm and llm_norm and artifact_norm == llm_norm:
        status = "artifact/llm match"
    else:
        status = "review"
    return (
        f"| {md_escape(name)} | {md_escape(source_value or 'missing')} | "
        f"{md_escape(artifact_value or 'missing')} | {md_escape(llm_value or 'missing')} | {status} |"
    )


def validation_status_for(scope_items: dict[str, dict[str, Any]], label: str) -> dict[str, Any]:
    item = scope_items.get(label)
    if not item:
        return {"status": "not in supplied scope validation"}
    return {
        "status": item.get("status"),
        "result": (item.get("result") or {}).get("result"),
        "llm_result": ((item.get("llm_result") or {}).get("result") or {}).get("result"),
        "materialized": item.get("materialized"),
    }


def load_artifact(repo_root: Path, package: dict[str, Any]) -> dict[str, Any] | None:
    path = repo_root / package["artifact"]
    if not path.exists():
        return None
    return load_mapping(path)


def load_llm_artifact(path: Path | None) -> tuple[dict[str, Any] | None, str | None, str | None]:
    if path is None or not path.exists():
        return None, None, None
    try:
        artifact, corrected_tex = extract_llm_artifact_and_tex(load_serialized_mapping(path))
        return artifact, corrected_tex, None
    except Exception as exc:
        return None, None, str(exc)


def render_item(
    *,
    repo_root: Path,
    candidate: Any,
    scope_items: dict[str, dict[str, Any]],
    llm_data_dir: Path | None,
    explicit_payloads: dict[str, Path],
) -> tuple[str, dict[str, Any]]:
    package = artifact_package_for(candidate, repo_root)
    package_dir = repo_root / package["directory"]
    source_sections = extract_source_sections(candidate.text)
    artifact_data = load_artifact(repo_root, package)
    artifact_fields = artifact_summary(artifact_data)
    llm_path = find_llm_payload(candidate.label, package_dir, llm_data_dir, explicit_payloads)
    llm_artifact, llm_corrected_tex, llm_error = load_llm_artifact(llm_path)
    llm_fields = artifact_summary(llm_artifact)
    validation = validation_status_for(scope_items, candidate.label)

    source_dependency_labels = dependency_labels(source_sections.get("dependencies"))
    artifact_dependency_edges = artifact_fields.get("dependency_edges")
    llm_dependency_edges = llm_fields.get("dependency_edges")

    rows = [
        "| Field | Source decoration | Existing artifact | LLM payload | Status |",
        "| --- | --- | --- | --- | --- |",
        compare_row(
            "standard quantified",
            source_sections.get("standard_quantified"),
            artifact_fields.get("standard_quantified"),
            llm_fields.get("standard_quantified"),
        ),
        compare_row(
            "predicate reading",
            source_sections.get("predicate_reading"),
            artifact_fields.get("predicate_reading"),
            llm_fields.get("predicate_reading"),
        ),
        compare_row(
            "negation",
            source_sections.get("negated_quantified"),
            artifact_fields.get("negation_mechanical") or artifact_fields.get("negation_approved"),
            llm_fields.get("negation_mechanical") or llm_fields.get("negation_approved"),
        ),
        compare_row(
            "failure modes",
            source_sections.get("failure_modes"),
            artifact_fields.get("failure_analysis"),
            llm_fields.get("failure_analysis"),
        ),
        compare_row(
            "dependencies",
            ", ".join(source_dependency_labels) if source_dependency_labels else source_sections.get("dependencies"),
            artifact_dependency_edges,
            llm_dependency_edges,
        ),
    ]

    rel_source = candidate.source_file.relative_to(repo_root).as_posix()
    lines = [
        f"# {candidate.label}",
        "",
        f"- Kind: `{candidate.kind}`",
        f"- Title: `{candidate.title or ''}`",
        f"- Source: `{rel_source}:{candidate.line_start}`",
        f"- Book root: `{candidate.book_root.relative_to(repo_root).as_posix()}`",
        f"- Section: `{candidate.section or ''}`",
        f"- Package: `{package['directory']}`",
        f"- Package exists: `{package['exists']}`",
        f"- LLM payload: `{llm_path if llm_path else 'missing'}`",
        f"- Validation status: `{compact_status(str(validation.get('status')))}"
        f"{' / ' + str(validation.get('result')) if validation.get('result') else ''}`",
        "",
        "## Original Environment",
        "",
        fenced(extract_original_environment(candidate.text), "tex"),
        "## Original Routed Text",
        "",
        fenced(candidate.text, "tex"),
        "## Source Decoration Data",
        "",
    ]
    for key, title in SOURCE_FIELD_TITLES.items():
        lines.extend([f"### {title}", "", fenced(source_sections.get(key), "tex" if key != "interpretation" else "text")])
    lines.extend(
        [
            "## Artifact Comparison",
            "",
            *rows,
            "",
            "## Existing Artifact Summary",
            "",
            fenced(artifact_fields or None, "yaml"),
            "## LLM Payload Summary",
            "",
        ]
    )
    if llm_error:
        lines.extend([f"_LLM payload could not be read: `{llm_error}`_", ""])
    else:
        lines.append(fenced(llm_fields or None, "yaml"))
    if llm_corrected_tex:
        lines.extend(["## LLM Corrected TeX", "", fenced(llm_corrected_tex, "tex")])

    summary = {
        "label": candidate.label,
        "kind": candidate.kind,
        "section": candidate.section,
        "package_exists": package["exists"],
        "llm_payload": str(llm_path) if llm_path else None,
        "llm_payload_error": llm_error,
        "validation": validation,
    }
    return "\n".join(lines).rstrip() + "\n", summary


def render_reports(args: argparse.Namespace) -> dict[str, Any]:
    repo_root, volume_source, _roots, candidates = routed_formals(args)
    scope = load_data(args.scope_validation)
    scope_items = {item.get("label"): item for item in scope.get("items", []) if isinstance(item, dict) and item.get("label")}
    explicit_payloads = indexed_llm_payloads(args.llm_data)

    records: list[dict[str, Any]] = []
    for candidate in candidates:
        text, summary = render_item(
            repo_root=repo_root,
            candidate=candidate,
            scope_items=scope_items,
            llm_data_dir=args.llm_data_dir,
            explicit_payloads=explicit_payloads,
        )
        report_path = args.output_dir / f"{label_slug(candidate.label)}.md"
        write_text(report_path, text)
        summary["report"] = report_path
        records.append(summary)

    index_lines = [
        "# Volume III Bounding Semantic Validation Report",
        "",
        f"- Schema: `{REPORT_SCHEMA}`",
        f"- Repo: `{repo_root}`",
        f"- Volume source: `{volume_source.relative_to(repo_root).as_posix()}`",
        f"- Filters: book=`{args.book or ''}`, chapter=`{args.chapter or ''}`, section=`{args.section or ''}`, label=`{args.label or ''}`",
        f"- Formal environments: `{len(records)}`",
        f"- Scope validation: `{args.scope_validation or 'not supplied'}`",
        f"- LLM data dir: `{args.llm_data_dir or 'not supplied'}`",
        "",
        "| Label | Kind | Section | Package | LLM | Validation | Report |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for record in records:
        report_rel = Path(record["report"]).relative_to(args.output_index.parent).as_posix()
        validation = record["validation"]
        validation_text = validation.get("result") or validation.get("status") or "unknown"
        index_lines.append(
            f"| `{record['label']}` | {record['kind']} | {record.get('section') or ''} | "
            f"{'yes' if record['package_exists'] else 'pending'} | "
            f"{'yes' if record.get('llm_payload') else 'pending'} | "
            f"{validation_text} | [{Path(record['report']).name}]({report_rel}) |"
        )
    write_text(args.output_index, "\n".join(index_lines).rstrip() + "\n")

    return {
        "schema_version": REPORT_SCHEMA,
        "repo_root": str(repo_root),
        "volume": args.volume,
        "volume_source": volume_source.relative_to(repo_root).as_posix(),
        "formal_candidates": len(records),
        "output_index": str(args.output_index),
        "output_dir": str(args.output_dir),
        "records": [
            {
                **record,
                "report": str(record["report"]),
            }
            for record in records
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Markdown reports for semantic validation targets.")
    parser.add_argument("--repos-root", type=Path)
    parser.add_argument("--volume-root", type=Path)
    parser.add_argument("--volume", choices=tuple(VOLUME_NAMES), required=True)
    parser.add_argument("--book")
    parser.add_argument("--chapter")
    parser.add_argument("--section")
    parser.add_argument("--label")
    parser.add_argument("--target", type=Path)
    parser.add_argument("--scope-validation", type=Path)
    parser.add_argument("--llm-data-dir", type=Path)
    parser.add_argument("--llm-data", type=Path, action="append")
    parser.add_argument("--output-index", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path)
    parser.add_argument("--format", choices=("yaml", "json"), default="yaml")
    args = parser.parse_args()

    try:
        payload = render_reports(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    if args.summary_output:
        write_text(args.summary_output, text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
