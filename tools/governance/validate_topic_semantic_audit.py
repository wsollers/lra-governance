#!/usr/bin/env python3
"""Validate one reversible topic semantic-audit manifest and its audit records."""

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
AUDIT_FILE = "audit-validation.yaml"
TERMINAL = {"validated", "failed", "blocked"}
PASS_RESULTS = {"pass", "pass_with_warnings"}


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


def schema_validate(
    data: dict[str, Any],
    schema_path: Path,
    prefix: str,
    result: Result,
) -> None:
    if jsonschema is None:
        result.warnings.append(
            f"{prefix}: jsonschema is not installed; schema validation was skipped"
        )
        return
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(data), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.path) or "<root>"
        result.errors.append(f"{prefix}:{location}: {error.message}")


def expected_overall_for_status(status: str) -> set[str]:
    if status == "validated":
        return PASS_RESULTS
    if status == "blocked":
        return {"blocked"}
    if status == "failed":
        return {"fail", "infrastructure_error"}
    return {"not_run", "pass", "pass_with_warnings", "fail", "blocked", "infrastructure_error"}


def validate_audit_record(
    entry: dict[str, Any],
    audit_path: Path,
    audit_schema_path: Path,
    index: int,
    result: Result,
) -> None:
    try:
        audit = load_mapping(audit_path)
    except Exception as exc:
        result.errors.append(f"artifacts[{index}].audit_validation_file: {exc}")
        return

    schema_validate(audit, audit_schema_path, f"audit[{entry.get('label')}]"," 
        " result)

    artifact = audit.get("artifact") or {}
    crosswalk = {
        "label": entry.get("label"),
        "kind": entry.get("kind"),
        "source_file": entry.get("source_file"),
        "review_directory": entry.get("review_directory"),
    }
    for key, expected in crosswalk.items():
        if artifact.get(key) != expected:
            result.errors.append(
                f"artifacts[{index}].audit_validation_file: artifact.{key} "
                f"expected {expected!r}, found {artifact.get(key)!r}"
            )

    review = audit.get("review_package") or {}
    temporary = audit.get("temporary_application") or {}
    deterministic = audit.get("deterministic_validation") or {}
    logic = audit.get("logic_validation") or {}
    reversion = audit.get("reversion") or {}
    overall = audit.get("overall") or {}

    commit_pairs = {
        "review_commit": review.get("review_commit"),
        "temporary_apply_commit": temporary.get("commit"),
        "revert_commit": reversion.get("commit"),
    }
    for field_name, actual in commit_pairs.items():
        if entry.get(field_name) != actual:
            result.errors.append(
                f"artifacts[{index}].{field_name}: manifest {entry.get(field_name)!r} "
                f"does not match audit record {actual!r}"
            )

    if entry.get("deterministic_result") != deterministic.get("result"):
        result.errors.append(
            f"artifacts[{index}].deterministic_result: manifest and audit record differ"
        )
    if entry.get("logic_result") != logic.get("result"):
        result.errors.append(
            f"artifacts[{index}].logic_result: manifest and audit record differ"
        )
    if bool(entry.get("source_restored")) != bool(reversion.get("source_restored")):
        result.errors.append(
            f"artifacts[{index}].source_restored: manifest and audit record differ"
        )

    status = str(entry.get("status") or "")
    if overall.get("result") not in expected_overall_for_status(status):
        result.errors.append(
            f"artifacts[{index}].status: {status!r} is inconsistent with "
            f"audit overall result {overall.get('result')!r}"
        )

    applied = bool(temporary.get("applied"))
    if applied and not temporary.get("commit"):
        result.errors.append(
            f"artifacts[{index}].temporary_apply_commit: applied audit lacks commit"
        )
    if applied and not reversion.get("required"):
        result.errors.append(
            f"artifacts[{index}].reversion.required: temporary application requires revert"
        )
    if applied and not reversion.get("commit"):
        result.errors.append(
            f"artifacts[{index}].revert_commit: temporary application lacks revert commit"
        )
    if reversion.get("source_restored"):
        for file_index, item in enumerate(reversion.get("verified_files") or [], start=1):
            if not item.get("matches"):
                result.errors.append(
                    f"artifacts[{index}].reversion.verified_files[{file_index}]: "
                    "source_restored is true but file hash does not match"
                )


def semantic_checks(
    data: dict[str, Any],
    repo_root: Path,
    governance_root: Path,
    strict: bool,
    result: Result,
) -> None:
    artifacts = data.get("artifacts") or []
    summary = data.get("summary") or {}
    topic = data.get("topic") or {}

    labels: set[str] = set()
    orders: list[int] = []
    counts = {"validated": 0, "failed": 0, "blocked": 0}
    audit_schema_path = (
        governance_root
        / "constitution"
        / "schema"
        / "artifact-audit-validation.schema.json"
    )
    if not audit_schema_path.exists():
        result.errors.append(f"missing schema: {audit_schema_path}")

    source_paths: set[str] = set()
    for source in (data.get("source_baseline") or {}).get("source_files") or []:
        path = str((source or {}).get("path") or "")
        if path in source_paths:
            result.errors.append(f"source_baseline.source_files: duplicate path {path}")
        source_paths.add(path)

    for index, entry in enumerate(artifacts, start=1):
        if not isinstance(entry, dict):
            continue
        label = str(entry.get("label") or "")
        order = entry.get("order")
        status = str(entry.get("status") or "")
        review_directory = Path(str(entry.get("review_directory") or ""))
        audit_validation_file = Path(str(entry.get("audit_validation_file") or ""))

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
        expected_audit = review_directory / AUDIT_FILE
        if audit_validation_file != expected_audit:
            result.errors.append(
                f"artifacts[{index}].audit_validation_file: expected "
                f"{expected_audit.as_posix()!r}"
            )

        folder = review_directory if review_directory.is_absolute() else repo_root / review_directory
        audit_path = (
            audit_validation_file
            if audit_validation_file.is_absolute()
            else repo_root / audit_validation_file
        )

        if status == "queued":
            if folder.exists():
                result.warnings.append(
                    f"artifacts[{index}]: queued entry already has review directory {folder}"
                )
            continue

        if not folder.exists():
            result.errors.append(
                f"artifacts[{index}].review_directory: missing directory {folder}"
            )
            continue

        missing_review = sorted(name for name in REVIEW_FILES if not (folder / name).exists())
        if status in {"reviewed", "validated", "failed"} and missing_review:
            result.errors.append(
                f"artifacts[{index}]: missing review files: {', '.join(missing_review)}"
            )

        if status in TERMINAL:
            counts[status] += 1
            if not audit_path.exists():
                if strict:
                    result.errors.append(
                        f"artifacts[{index}].audit_validation_file: missing {audit_path}"
                    )
            elif audit_schema_path.exists():
                validate_audit_record(
                    entry,
                    audit_path,
                    audit_schema_path,
                    index,
                    result,
                )

        if status == "validated":
            for field_name in (
                "review_commit",
                "temporary_apply_commit",
                "revert_commit",
            ):
                if not entry.get(field_name):
                    result.errors.append(
                        f"artifacts[{index}].{field_name}: required for validated entry"
                    )
            if not entry.get("source_restored"):
                result.errors.append(
                    f"artifacts[{index}].source_restored: validated source must be restored"
                )
            if entry.get("deterministic_result") not in PASS_RESULTS:
                result.errors.append(
                    f"artifacts[{index}].deterministic_result: validated entry did not pass"
                )
            if entry.get("logic_result") not in PASS_RESULTS:
                result.errors.append(
                    f"artifacts[{index}].logic_result: validated entry did not pass"
                )

        if (
            entry.get("temporary_apply_commit")
            and not entry.get("revert_commit")
            and status in TERMINAL
        ):
            result.errors.append(
                f"artifacts[{index}]: temporary source commit lacks matching revert"
            )

    if sorted(orders) != list(range(1, len(artifacts) + 1)):
        result.errors.append(
            "artifacts.order: values must be unique and consecutive from 1"
        )

    expected = {
        "inventory_count": len(artifacts),
        "validated_count": counts["validated"],
        "failed_count": counts["failed"],
        "blocked_count": counts["blocked"],
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            result.errors.append(
                f"summary.{key}: expected {value}, found {summary.get(key)!r}"
            )

    all_terminal = len(artifacts) == sum(counts.values())
    if strict and not topic.get("inventory_commit"):
        result.errors.append("topic.inventory_commit: required in strict mode")
    if all_terminal:
        if not summary.get("source_restored"):
            result.errors.append(
                "summary.source_restored: completed topic must restore source"
            )
    elif summary.get("source_restored"):
        result.warnings.append(
            "summary.source_restored is true before all entries are terminal"
        )


def format_report(result: Result) -> str:
    lines = [
        "# Topic Semantic Audit Validation",
        "",
        f"Result: {'PASS' if result.clean else 'FAIL'}",
        "",
        "## Errors",
        "",
    ]
    lines += [f"- {item}" for item in result.errors] or ["_None._"]
    lines += ["", "## Warnings", ""]
    lines += [f"- {item}" for item in result.warnings] or ["_None._"]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--governance-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()

    result = Result()
    try:
        data = load_mapping(args.manifest)
    except Exception as exc:
        result.errors.append(str(exc))
        data = {}

    schema_path = (
        args.governance_root
        / "constitution"
        / "schema"
        / "topic-semantic-audit.schema.json"
    )
    if not schema_path.exists():
        result.errors.append(f"missing schema: {schema_path}")
    else:
        schema_validate(data, schema_path, "topic", result)

    if data:
        semantic_checks(
            data,
            args.repo_root.resolve(),
            args.governance_root.resolve(),
            args.strict,
            result,
        )

    if args.format == "json":
        print(
            json.dumps(
                {
                    "clean": result.clean,
                    "errors": result.errors,
                    "warnings": result.warnings,
                },
                indent=2,
            )
        )
    else:
        print(format_report(result), end="")
    return 0 if result.clean else 1


if __name__ == "__main__":
    sys.exit(main())
