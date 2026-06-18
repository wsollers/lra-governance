#!/usr/bin/env python3
"""Move early dependencies blocks after formal decoration remarks.

This is a mechanical fixer for `decoration_order` findings where an existing
`\begin{dependencies}` block appears before `Standard quantified statement` in
a formal statement's decoration region. It does not invent dependencies and
does not edit mathematical statement bodies.
"""
from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path


FORMAL_RE = re.compile(
    r"\\begin\{(?P<env>definition|axiom|theorem|lemma|proposition|corollary)\}"
    r"(?:\[[^\]]*\])?",
    re.IGNORECASE,
)
SECTION_RE = re.compile(r"\\(?:chapter|section|subsection|subsubsection)\*?\{")
LABEL_RE = re.compile(r"\\label\{([^}]+)\}")
DEPENDENCIES_RE = re.compile(r"\n*\\begin\{dependencies\}[\s\S]*?\\end\{dependencies\}\n*", re.IGNORECASE)
STANDARD_RE = re.compile(r"\\begin\{remark\*\}\[Standard quantified statement\]", re.IGNORECASE)

IGNORED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "archive",
    "archives",
    "bibliography",
    "build",
    "dist",
    "node_modules",
}


@dataclass(frozen=True)
class Fix:
    path: Path
    label: str
    line: int


def iter_tex(root: Path):
    if root.is_file():
        if root.suffix == ".tex":
            yield root
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in IGNORED_DIRS and not name.startswith(".")]
        for filename in filenames:
            if filename.endswith(".tex"):
                yield Path(dirpath) / filename


def formal_blocks(text: str):
    for begin in FORMAL_RE.finditer(text):
        env = begin.group("env")
        end = re.search(rf"\\end\{{{re.escape(env)}\}}", text[begin.end() :], re.IGNORECASE)
        if end:
            yield begin, begin.end() + end.end()


def next_boundary(text: str, start: int) -> int:
    formal = FORMAL_RE.search(text, start)
    section = SECTION_RE.search(text, start)
    candidates = [match.start() for match in (formal, section) if match]
    return min(candidates) if candidates else len(text)


def line_at(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def fix_text(path: Path, text: str, max_fixes: int | None) -> tuple[str, list[Fix]]:
    pieces: list[str] = []
    cursor = 0
    fixes: list[Fix] = []

    for begin, formal_end in formal_blocks(text):
        if max_fixes is not None and len(fixes) >= max_fixes:
            break
        boundary = next_boundary(text, formal_end)
        decoration = text[formal_end:boundary]
        labels = LABEL_RE.findall(text[begin.start() : formal_end])
        if not labels:
            continue

        standard = STANDARD_RE.search(decoration)
        dependency = DEPENDENCIES_RE.search(decoration)
        if not standard or not dependency or dependency.start() > standard.start():
            continue

        dependencies_block = dependency.group(0).strip()
        without_dependency = decoration[: dependency.start()] + decoration[dependency.end() :]
        replacement_decoration = without_dependency.rstrip() + "\n\n" + dependencies_block + "\n"

        pieces.append(text[cursor:formal_end])
        pieces.append(replacement_decoration)
        cursor = boundary
        fixes.append(Fix(path=path, label=labels[0], line=line_at(text, begin.start())))

    if not fixes:
        return text, []

    pieces.append(text[cursor:])
    return "".join(pieces), fixes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--write", action="store_true", help="Rewrite files in place.")
    parser.add_argument("--max-fixes", type=int, default=None, help="Maximum number of blocks to fix.")
    args = parser.parse_args()

    all_fixes: list[Fix] = []
    remaining = args.max_fixes
    for tex in sorted(iter_tex(args.root)):
        if remaining is not None and remaining <= 0:
            break
        text = tex.read_text(encoding="utf-8")
        new_text, fixes = fix_text(tex, text, remaining)
        if not fixes:
            continue
        all_fixes.extend(fixes)
        if args.write:
            tex.write_text(new_text, encoding="utf-8")
        if remaining is not None:
            remaining -= len(fixes)

    action = "rewrote" if args.write else "would rewrite"
    print(f"{action} {len(all_fixes)} block(s)")
    for fix in all_fixes:
        print(f"{fix.path}:{fix.line} {fix.label}")


if __name__ == "__main__":
    main()
