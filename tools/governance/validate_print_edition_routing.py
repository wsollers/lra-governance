#!/usr/bin/env python3
r"""Validate print-edition routing gate placement.

Policy:
  - chapter index.tex wraps proof and capstone routes in
    \LRAExcludeFromPrintEditionBegin / \LRAExcludeFromPrintEditionEnd;
  - files below proofs/ use ordinary \input{...};
  - retired print-aware routing macros are rejected everywhere.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

from rules.routing import print_edition_inputs


EXCLUDED_DIRS = {
    ".git",
    ".history",
    ".venv",
    "__pycache__",
    "archive",
    "build",
    "common",
    "dist",
    "lean",
    "node_modules",
    "out",
    "output",
    "outputs",
    "proof-techniques",
    "reports",
    "venv",
}
EXCLUDED_RELATIVE_DIRS = {
    "volume-ii/integers/notes/mendelson-construction",
    "volume-ii/integers/notes/tao-construction",
    "volume-ii/integers/proofs/mendelson-construction",
    "volume-ii/integers/proofs/tao-construction",
    "volume-iii/analysis/real-analysis",
}


def is_excluded_path(path: Path) -> bool:
    full = path.resolve().as_posix()
    return any(full.endswith(f"/{rel}") or f"/{rel}/" in full for rel in EXCLUDED_RELATIVE_DIRS)


class FileInfo:
    def __init__(self, path: Path, kind: str):
        self.path = str(path)
        self.kind = kind


def classify(path: Path) -> str:
    if path.name == "index.tex" and (path.parent / "notes").is_dir() and (path.parent / "proofs").is_dir():
        return "chapter_index"
    return "other"


def iter_tex(root: Path):
    if root.is_file() and root.suffix == ".tex":
        yield root
        return
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        dirnames[:] = [
            name
            for name in dirnames
            if name not in EXCLUDED_DIRS and not name.startswith(".") and not is_excluded_path(current / name)
        ]
        for filename in filenames:
            if filename.endswith(".tex"):
                yield Path(dirpath) / filename


def validate_path(path: Path, root: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    info = FileInfo(path, classify(path))
    records = []
    for finding in print_edition_inputs.check(text, info, None):
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            rel = path.as_posix()
        records.append(
            {
                "file": rel,
                "kind": info.kind,
                "line": finding.line,
                "severity": finding.severity,
                "code": finding.code,
                "message": finding.message,
            }
        )
    return records


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate LRA print-edition proof routing gates.")
    parser.add_argument("paths", nargs="+", help="Volume, chapter, repo, or .tex paths to scan.")
    parser.add_argument("--json", help="Write machine-readable report.")
    parser.add_argument("--fail-on-errors", action="store_true")
    args = parser.parse_args(argv)

    roots = [Path(path).resolve() for path in args.paths]
    missing = [root for root in roots if not root.exists()]
    if missing:
        for root in missing:
            print(f"fatal: path not found: {root}", file=sys.stderr)
        return 1

    records = []
    files = 0
    for root in roots:
        for tex in sorted(iter_tex(root)):
            files += 1
            records.extend(validate_path(tex, root if root.is_dir() else root.parent))

    sev = Counter(record["severity"] for record in records)
    print(
        f"print-edition routing check: {files} files, {len(records)} issue(s) "
        f"[{sev.get('error', 0)} error, {sev.get('warning', 0)} warning]"
    )
    by_file: dict[str, list[dict]] = {}
    for record in records:
        by_file.setdefault(record["file"], []).append(record)
    for file in sorted(by_file):
        print(f"\n  {file} ({by_file[file][0]['kind']})")
        for record in sorted(by_file[file], key=lambda item: (item["line"], item["code"])):
            print(f"    L{record['line']:<4} {record['severity']:<7} {record['code']}: {record['message']}")
    if not records:
        print("\n  clean.")

    if args.json:
        Path(args.json).write_text(
            json.dumps({"files": files, "records": records}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"\njson report: {args.json}")

    if args.fail_on_errors and sev.get("error", 0):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
