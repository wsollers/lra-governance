#!/usr/bin/env python3
"""Validate note prose is inside approved block environments.

This checker is intentionally path-scoped. Older notes may predate the block
discipline, so generation prompts should pass the files or directories they
just touched.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from _targeting import discovery_lines, note_validation_paths, resolve_target


BEGIN_ENV_RE = re.compile(r"^\s*\\begin\{([^{}]+)\}")
END_ENV_RE = re.compile(r"^\s*\\end\{([^{}]+)\}")
PLAIN_BLOCK_RE = re.compile(r"\\begin\{(remark|example)\}(?!\*)")
DISALLOWED_BLOCK_RE = re.compile(r"\\begin\{(examplebox|workedexamples)\}")

ALLOWED_TOP_LEVEL_COMMANDS = (
    "\\chapter",
    "\\section",
    "\\subsection",
    "\\subsubsection",
    "\\paragraph",
    "\\input",
    "\\include",
    "\\label",
    "\\clearpage",
    "\\newpage",
    "\\FloatBarrier",
)


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    path: str
    line: int
    severity: str = "error"


def iter_tex_files(paths: list[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_dir():
            yield from sorted(
                p
                for p in path.rglob("*.tex")
                if not any(part.startswith(".") for part in p.parts)
            )
        elif path.suffix == ".tex":
            yield path


def strip_comment(line: str) -> str:
    escaped = False
    out: list[str] = []
    for ch in line:
        if ch == "\\":
            escaped = not escaped
            out.append(ch)
            continue
        if ch == "%" and not escaped:
            break
        escaped = False
        out.append(ch)
    return "".join(out)


def is_allowed_top_level_line(line: str) -> bool:
    stripped = strip_comment(line).strip()
    if not stripped:
        return True
    if stripped.startswith("%"):
        return True
    if stripped.startswith(ALLOWED_TOP_LEVEL_COMMANDS):
        return True
    return False


def validate_file(path: Path, root: Path) -> list[Finding]:
    findings: list[Finding] = []
    stack: list[str] = []
    rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else path.as_posix()

    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = strip_comment(raw_line)

        if PLAIN_BLOCK_RE.search(line):
            findings.append(
                Finding(
                    code="plain_block_environment",
                    message="Use the starred house block environment here.",
                    path=rel,
                    line=line_no,
                )
            )

        if DISALLOWED_BLOCK_RE.search(line):
            findings.append(
                Finding(
                    code="non_house_block_environment",
                    message="Use a current house block environment instead of this block.",
                    path=rel,
                    line=line_no,
                )
            )

        begin = BEGIN_ENV_RE.match(line)
        if begin:
            stack.append(begin.group(1))

        if not stack and not is_allowed_top_level_line(raw_line):
            findings.append(
                Finding(
                    code="top_level_prose",
                    message="Prose in notes must be inside a formal, exposition, remark*, example*, or dependency block.",
                    path=rel,
                    line=line_no,
                )
            )

        end = END_ENV_RE.match(line)
        if end and stack:
            stack.pop()

    if stack:
        findings.append(
            Finding(
                code="unclosed_environment",
                message=f"Unclosed environment(s): {', '.join(stack)}.",
                path=rel,
                line=1,
            )
        )

    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate note files use approved prose blocks and no top-level prose."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Specific .tex files or directories to validate.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Repository root used for relative paths.",
    )
    parser.add_argument("--volume", help="Validate notes under a discovered volume, such as volume-ii.")
    parser.add_argument("--chapter", help="Validate notes under a discovered chapter, such as whole-numbers.")
    parser.add_argument(
        "--section",
        help="Validate one discovered notes topic, such as extending-addition. Use --chapter if ambiguous.",
    )
    parser.add_argument(
        "--list-targets",
        action="store_true",
        help="List discovered volumes, chapters, and sections, then exit.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON findings.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    if args.list_targets:
        print("\n".join(discovery_lines(root)))
        return 0

    try:
        target = resolve_target(root, args.volume, args.chapter, args.section)
    except ValueError as exc:
        print(f"ERROR target_resolution - {exc}", file=sys.stderr)
        return 2

    if args.paths:
        paths = [p if p.is_absolute() else root / p for p in args.paths]
        target_scope = "paths"
    else:
        paths = note_validation_paths(target)
        target_scope = target.scope

    findings: list[Finding] = []
    files = list(dict.fromkeys(iter_tex_files(paths)))
    for path in files:
        findings.extend(validate_file(path.resolve(), root))

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        print("Note block validation summary")
        print(f"root: {root}")
        print(f"target_scope: {target_scope}")
        if target.volume:
            print(f"volume: {target.volume.name}")
        if target.chapter:
            print(f"chapter: {target.chapter.name}")
        if target.section:
            print(f"section: {target.section}")
        print(f"file_count: {len(files)}")
        print(f"error_count: {len(findings)}")
        print(f"status: {'FAIL' if findings else 'PASS'}")
        for finding in findings:
            print(
                f"ERROR {finding.code} {finding.path}:{finding.line} - {finding.message}"
            )

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
