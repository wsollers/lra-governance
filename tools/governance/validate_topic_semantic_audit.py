#!/usr/bin/env python3
"""Validate one reversible topic semantic-audit manifest."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None

REVIEW_FILES = {
    "package.yaml",
    "artifact.yaml",
    "corrected.tex",
    "source.patch",
    "validation.yaml",
    "source-map.yaml",
    "registry-needs.yaml",
    "formalization-links.yaml",
    "proof-vault-links.yaml",
}
AUDIT_FILES = {"logic-validation.yaml", "execution-validation.yaml"}
TERMINAL = {"validated", "failed", "blocked"}


@dataclass
class Result:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.errors


def load_mapping(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a mapping")
    return data


def schema_validate(data: dict[str, Any], schema_path: Path, result: Result) -> None:
    if jsonschema is None:
        result.warnings.append("jsonschema is not installed; schema validation was skipped")
        return
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(data), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.path) or "<root>"
        result.errors.append(f"schema:{location}: {error.message}")


def semantic_checks(data: dict[str, Any], manifest_path: Path, strict: bool, result: Result) -> None:
    artifacts = data.get("artifacts") or []
    summary = data.get("summary") or {}

    labels: set[str] = set()
    orders: list[int] = []
    counts = {"validated": 0, "failed": 0, "blocked": 0}
    root = manifest_path.parent

    for index, entry in enumerate(artifacts, start=1):
        if not isinstance(entry, dict):
            continue
        label = str(entry.get("label") or "")
        order = entry.get("order")
        status = entry.get("status")
        review_directory = Path(str(entry.get("review_directory") or ""))

        if label in labels:
            result.errors.append(f"artifacts[{index}].label: duplicate label {label}")
        labels.add(label)
        if isinstance(order, int):
            orders.append(order)

        expected_slug = label.replace(":", "-")
        if review_directory.name != expected_slug:
            result.errors.append(
                f"artifacts[{index}].review_directory: expected basename {expected_slug!r}"
            )

        folder = review_directory if review_directory.is_absolute() else root.parent.parent.parent / review_directory
        if not folder.exists():
            result.errors.append(f"artifacts[{index}].review_directory: missing directory {folder}")
            continue

        missing_review = sorted(name for name in REVIEW_FILES if not (folder / name).exists())
        if status in {"reviewed", "validated", "failed"} and missing_review:
            result.errors.append(
                f"artifacts[{index}]: missing review files: {', '.join(missing_review)}"
            )

        if status in TERMINAL:
            counts[status] += 1
            missing_audit = sorted(name for name in AUDIT_FILES if not (folder / name).exists())
            if strict and missing_audit:
                result.errors.append(
                    f"artifacts[{index}]: terminal entry missing audit files: {', '.join(missing_audit)}"
                )

        if status == "validated":
            for field_name in ("review_commit", "temporary_apply_commit", "revert_commit"):
                if not entry.get(field_name):
                    result.errors.append(f"artifacts[{index}].{field_name}: required for validated entry")
            if not entry.get("source_restored"):
                result.errors.append(f"artifacts[{index}].source_restored: validated source must be restored")
            if entry.get("deterministic_result") not in {"pass", "pass_with_warnings"}:
                result.errors.append(f"artifacts[{index}].deterministic_result: validated entry did not pass")
            if entry.get("logic_result") not in {"pass", "pass_with_warnings"}:
                result.errors.append(f"artifacts[{index}].logic_result: validated entry did not pass")

        if entry.get("temporary_apply_commit") and not entry.get("revert_commit") and status in TERMINAL:
            result.errors.append(f"artifacts[{index}]: temporary source commit lacks matching revert")

    if sorted(orders) != list(range(1, len(artifacts) + 1)):
        result.errors.append("artifacts.order: values must be unique and consecutive from 1")

    expected = {
        "inventory_count": len(artifacts),
        "validated_count": counts["validated"],
        "failed_count": counts["failed"],
        "blocked_count": counts["blocked"],
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            result.errors.append(f"summary.{key}: expected {value}, found {summary.get(key)!r}")

    all_terminal = len(artifacts) == sum(counts.values())
    if all_terminal:
        if not summary.get("source_restored"):
            result.errors.append("summary.source_restored: completed topic must restore source")
        if strict and not summary.get("final_validation_commit"):
            result.errors.append("summary.final_validation_commit: required for strict completed audit")
    elif summary.get("final_validation_commit"):
        result.warnings.append("summary.final_validation_commit is set before all entries are terminal")


def format_report(result: Result) -> str:
    lines = ["# Topic Semantic Audit Validation", "", f"Result: {'PASS' if result.clean else 'FAIL'}", ""]
    lines += ["## Errors", ""]
    lines += [f"- {item}" for item in result.errors] or ["_None._"]
    lines += ["", "## Warnings", ""]
    lines += [f"- {item}" for item in result.warnings] or ["_None._"]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--governance-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()

    result = Result()
    try:
        data = load_mapping(args.manifest)
    except Exception as exc:
        result.errors.append(str(exc))
        data = {}

    schema_path = args.governance_root / "constitution" / "schema" / "topic-semantic-audit.schema.json"
    if not schema_path.exists():
        result.errors.append(f"missing schema: {schema_path}")
    else:
        schema_validate(data, schema_path, result)

    if data:
        semantic_checks(data, args.manifest, args.strict, result)

    if args.format == "json":
        print(json.dumps({"clean": result.clean, "errors": result.errors, "warnings": result.warnings}, indent=2))
    else:
        print(format_report(result), end="")
    return 0 if result.clean else 1


if __name__ == "__main__":
    sys.exit(main())
