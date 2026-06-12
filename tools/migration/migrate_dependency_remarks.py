#!/usr/bin/env python3
r"""Migrate parseable legacy dependency remarks to the dependencies environment.

This tool is intentionally conservative. It converts only:

    \begin{remark*}[Dependencies]
    ... at least one \hyperref[...] ...
    \end{remark*}

to:

    \begin{dependencies}
    ...
    \end{dependencies}

It does not invent dependency targets, does not rewrite prose-only blocks, and
does not normalize itemization. Canonical dependency rendering can happen after
the graph has been corrected.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


DEPENDENCY_REMARK_RE = re.compile(
    r"\\begin\{remark\*\}\[Dependencies\](?P<body>[\s\S]*?)\\end\{remark\*\}",
    re.IGNORECASE,
)
HYPERREF_RE = re.compile(r"\\hyperref\[[^\]]+\]")
COMMENT_RE = re.compile(r"(?<!\\)%.*$")


@dataclass
class FileReport:
    path: str
    converted: int = 0
    skipped_prose_only: int = 0


def strip_comments(text: str) -> str:
    return "\n".join(COMMENT_RE.sub("", line) for line in text.splitlines())


def migrate_text(text: str) -> tuple[str, int, int]:
    converted = 0
    skipped = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal converted, skipped
        body = match.group("body")
        if not HYPERREF_RE.search(strip_comments(body)):
            skipped += 1
            return match.group(0)
        converted += 1
        return "\\begin{dependencies}" + body + "\\end{dependencies}"

    return DEPENDENCY_REMARK_RE.sub(repl, text), converted, skipped


def iter_tex(root: Path) -> list[Path]:
    ignored = {"archive", "archives", "build", "common", "constitution", "docs", "migration-reports", ".git", ".github"}
    if root.is_file():
        return [root] if root.suffix == ".tex" else []
    files: list[Path] = []
    for path in root.rglob("*.tex"):
        try:
            parts = path.relative_to(root).parts
        except ValueError:
            parts = path.parts
        if any(part in ignored for part in parts):
            continue
        files.append(path)
    return sorted(files)


def run(root: Path, write: bool) -> list[FileReport]:
    reports: list[FileReport] = []
    for path in iter_tex(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        new_text, converted, skipped = migrate_text(text)
        if converted or skipped:
            reports.append(FileReport(str(path), converted, skipped))
        if write and converted and new_text != text:
            path.write_text(new_text, encoding="utf-8")
    return reports


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate parseable remark*[Dependencies] blocks.")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    reports = run(args.root.resolve(), args.write)
    total_converted = sum(item.converted for item in reports)
    total_skipped = sum(item.skipped_prose_only for item in reports)
    payload = {
        "root": str(args.root.resolve()),
        "write": args.write,
        "converted": total_converted,
        "skipped_prose_only": total_skipped,
        "files": [asdict(item) for item in reports],
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"dependency remark migration: converted={total_converted}, skipped_prose_only={total_skipped}, write={args.write}")
    if args.json:
        print(f"json report: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
