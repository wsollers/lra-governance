#!/usr/bin/env python3
"""Autofix missing predicate-reading dependencies reported by semantic AST validation.

This is intentionally a post-run source fixer.  It does not decide which
dependencies are mathematically required; it consumes validator reports that
already contain `dependency_verification.suggested_dependency_additions` and
patches only those labels into the corresponding TeX dependency blocks.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "lra.semantic-dependency-autofix/1.0"
LABEL_RE = re.compile(r"\\label\{(?P<label>[^{}]+)\}")
HYPERREF_RE = re.compile(r"\\hyperref\[(?P<label>[^\]]+)\]")
DEPENDENCIES_RE = re.compile(
    r"\\begin\{dependencies\}(?P<body>.*?)\\end\{dependencies\}",
    re.S,
)
ITEMIZE_END_RE = re.compile(r"(?P<indent>[ \t]*)\\end\{itemize\}")
FORMAL_BEGIN_OR_BOX_RE = re.compile(
    r"\\begin\{(?:definition|axiom|theorem|lemma|proposition|corollary)(?:box)?\}",
    re.IGNORECASE,
)


@dataclass
class FixRequest:
    label: str
    source_file: str
    additions: list[str]


@dataclass
class PatchRecord:
    label: str
    source_file: str
    additions: list[str] = field(default_factory=list)
    skipped_existing: list[str] = field(default_factory=list)
    status: str = "pending"
    reason: str | None = None

    def as_json(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "label": self.label,
            "source_file": self.source_file,
            "status": self.status,
            "additions": self.additions,
            "skipped_existing": self.skipped_existing,
        }
        if self.reason:
            payload["reason"] = self.reason
        return payload


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def report_files(paths: Iterable[Path]) -> list[Path]:
    found: list[Path] = []
    for path in paths:
        if path.is_dir():
            found.extend(sorted(path.rglob("*.json")))
        elif path.suffix.lower() == ".json":
            found.append(path)
    return sorted({path.resolve() for path in found})


def requests_from_report(path: Path) -> list[FixRequest]:
    try:
        data = load_json(path)
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(data, dict):
        return []
    requests: list[FixRequest] = []
    for report in data.get("reports", []):
        if not isinstance(report, dict):
            continue
        verification = report.get("dependency_verification")
        if not isinstance(verification, dict):
            continue
        additions = verification.get("suggested_dependency_additions") or []
        additions = [item for item in additions if isinstance(item, str)]
        if not additions:
            continue
        label = report.get("label")
        source_file = report.get("source_file")
        if isinstance(label, str) and isinstance(source_file, str):
            requests.append(FixRequest(label=label, source_file=source_file, additions=sorted(set(additions))))
    return requests


def collect_requests(paths: Iterable[Path]) -> list[FixRequest]:
    merged: dict[tuple[str, str], set[str]] = {}
    for path in report_files(paths):
        for request in requests_from_report(path):
            key = (request.label, request.source_file)
            merged.setdefault(key, set()).update(request.additions)
    return [
        FixRequest(label=label, source_file=source_file, additions=sorted(additions))
        for (label, source_file), additions in sorted(merged.items())
    ]


def display_name_for_label(label: str) -> str:
    name = label.split(":", 1)[-1]
    overrides = {
        "real-upper-bound": "Upper Bound",
        "real-lower-bound": "Lower Bound",
        "ordered-set": "Ordered Set",
        "least-upper-bound-property": "Least Upper Bound Property",
    }
    if name in overrides:
        return overrides[name]
    return " ".join(part.capitalize() for part in name.split("-") if part)


def formal_block_span(text: str, label: str) -> tuple[int, int] | None:
    label_match = re.search(r"\\label\{" + re.escape(label) + r"\}", text)
    if not label_match:
        return None
    starts = [match.start() for match in FORMAL_BEGIN_OR_BOX_RE.finditer(text)]
    start = 0
    for candidate in starts:
        if candidate <= label_match.start():
            start = candidate
        else:
            break
    end = len(text)
    for candidate in starts:
        if candidate > label_match.start():
            end = candidate
            break
    return start, end


def labels_in_dependency_block(block_text: str) -> set[str]:
    dep_match = DEPENDENCIES_RE.search(block_text)
    if not dep_match:
        return set()
    return set(HYPERREF_RE.findall(dep_match.group(0)))


def dependency_item(label: str, *, itemize: bool) -> str:
    item = rf"\hyperref[{label}]{{{display_name_for_label(label)}}}"
    if itemize:
        return f"  \\item {item}"
    return item


def insert_into_existing_dependencies(block_text: str, additions: list[str]) -> str:
    dep_match = DEPENDENCIES_RE.search(block_text)
    if not dep_match:
        raise ValueError("block has no dependencies environment")
    dep_text = dep_match.group(0)
    has_itemize = "\\begin{itemize}" in dep_text
    lines = [dependency_item(label, itemize=has_itemize) for label in additions]
    if has_itemize:
        end_match = ITEMIZE_END_RE.search(dep_text)
        if not end_match:
            raise ValueError("dependencies itemize has no end marker")
        insert_at = end_match.start()
        replacement = dep_text[:insert_at] + "\n".join(lines) + "\n" + dep_text[insert_at:]
    else:
        insert_at = dep_text.rfind(r"\end{dependencies}")
        replacement = dep_text[:insert_at].rstrip() + "\n" + "\n".join(lines) + "\n" + dep_text[insert_at:]
    return block_text[: dep_match.start()] + replacement + block_text[dep_match.end() :]


def append_new_dependencies(block_text: str, additions: list[str]) -> str:
    lines = [
        r"\begin{dependencies}",
        r"\begin{itemize}",
        *[dependency_item(label, itemize=True) for label in additions],
        r"\end{itemize}",
        r"\end{dependencies}",
    ]
    return block_text.rstrip() + "\n\n" + "\n".join(lines) + "\n"


def patch_block_text(block_text: str, additions: list[str]) -> tuple[str, list[str], list[str]]:
    existing = labels_in_dependency_block(block_text)
    to_add = [label for label in additions if label not in existing]
    skipped = [label for label in additions if label in existing]
    if not to_add:
        return block_text, [], skipped
    if DEPENDENCIES_RE.search(block_text):
        return insert_into_existing_dependencies(block_text, to_add), to_add, skipped
    return append_new_dependencies(block_text, to_add), to_add, skipped


def apply_request(repo_root: Path, request: FixRequest, *, dry_run: bool = False) -> PatchRecord:
    record = PatchRecord(label=request.label, source_file=request.source_file)
    path = (repo_root / request.source_file).resolve()
    try:
        path.relative_to(repo_root.resolve())
    except ValueError:
        record.status = "skipped"
        record.reason = "source file is outside repo root"
        return record
    if not path.exists():
        record.status = "skipped"
        record.reason = "source file does not exist"
        return record
    text = path.read_text(encoding="utf-8")
    span = formal_block_span(text, request.label)
    if not span:
        record.status = "skipped"
        record.reason = "label not found in source file"
        return record
    start, end = span
    block_text = text[start:end]
    try:
        patched_block, added, skipped = patch_block_text(block_text, request.additions)
    except ValueError as exc:
        record.status = "skipped"
        record.reason = str(exc)
        return record
    record.additions = added
    record.skipped_existing = skipped
    if not added:
        record.status = "unchanged"
        record.reason = "all suggested dependencies were already present"
        return record
    record.status = "would_patch" if dry_run else "patched"
    if not dry_run:
        path.write_text(text[:start] + patched_block + text[end:], encoding="utf-8")
    return record


def autofix(repo_root: Path, report_paths: Iterable[Path], *, dry_run: bool = False) -> dict[str, Any]:
    requests = collect_requests(report_paths)
    records = [apply_request(repo_root.resolve(), request, dry_run=dry_run) for request in requests]
    return {
        "schema_version": SCHEMA_VERSION,
        "repo_root": str(repo_root.resolve()),
        "dry_run": dry_run,
        "request_count": len(requests),
        "patched_count": sum(1 for record in records if record.status == "patched"),
        "would_patch_count": sum(1 for record in records if record.status == "would_patch"),
        "unchanged_count": sum(1 for record in records if record.status == "unchanged"),
        "skipped_count": sum(1 for record in records if record.status == "skipped"),
        "records": [record.as_json() for record in records],
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--report",
        type=Path,
        action="append",
        required=True,
        help="Validator JSON report file or directory to scan recursively.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    summary = autofix(args.repo_root, args.report, dry_run=args.dry_run)
    payload = json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 1 if summary["skipped_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
