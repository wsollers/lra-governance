#!/usr/bin/env python3
r"""Find and remove 'Status: Planned' stub markers from LaTeX sources.

'Status: Planned' is a retired stub-status slot -- e.g. \section*{Status: Planned}
in a chapter index, a "% Status: Planned" comment, or a bare line. This removes
those WHOLE marker lines (and a redundant blank left behind). An inline occurrence
embedded in other content (e.g. \textbf{Status: Planned.} inside a capstone box) is
FLAGGED, not removed, to avoid leaving dangling prose -- handle those by hand.

It does NOT touch other status slots (e.g. a 'Chapter Status' box) or the
Roadmap/Chapter-structure chrome (that is remove_legacy_chrome.py's job).

Dry-run by default; --apply to write. Line endings preserved. archive/ and .git
excluded. Idempotent.
"""
from __future__ import annotations
import argparse, re
from pathlib import Path

MARKER = r"Status:\s*Planned\.?"
LINE_PATTERNS = [
    re.compile(r"^\s*\\(?:sub)*section\*?\s*\{\s*" + MARKER + r"\s*\}\s*$", re.IGNORECASE),  # \section*{Status: Planned}
    re.compile(r"^\s*%+\s*" + MARKER + r"\s*$", re.IGNORECASE),                               # % Status: Planned
    re.compile(r"^\s*" + MARKER + r"\s*$", re.IGNORECASE),                                    # bare line
]
INLINE = re.compile(r"Status:\s*Planned", re.IGNORECASE)
EXCLUDE_DIRS = {"archive", ".git"}

def nl_of(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"

def is_marker_line(line: str) -> bool:
    return any(p.match(line) for p in LINE_PATTERNS)

def process(text: str):
    nl = nl_of(text)
    lines = text.split(nl)
    out, removed, flagged = [], [], []
    i = 0
    while i < len(lines):
        line = lines[i]
        if is_marker_line(line):
            removed.append((i + 1, line.strip()))
            # if the marker sat between blank lines, drop one trailing blank too
            if out and out[-1].strip() == "" and i + 1 < len(lines) and lines[i + 1].strip() == "":
                i += 1
            i += 1
            continue
        if INLINE.search(line):
            flagged.append((i + 1, line.strip()))
        out.append(line)
        i += 1
    return nl.join(out), removed, flagged

def iter_tex(root: Path):
    for p in root.rglob("*.tex"):
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        yield p

def main():
    ap = argparse.ArgumentParser(description="Remove 'Status: Planned' stub markers.")
    ap.add_argument("--root", required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    files_changed = lines_removed = 0
    for p in sorted(iter_tex(root)):
        text = open(p, encoding="utf-8", newline="").read()
        new, removed, flagged = process(text)
        if not removed and not flagged:
            continue
        rel = p.relative_to(root).as_posix()
        print(f"\n[{rel}]")
        for ln, content in removed:
            print(f"  {'APPLY' if a.apply else 'PLAN '} remove L{ln}: {content}")
        for ln, content in flagged:
            print(f"  FLAG (inline, not removed) L{ln}: {content}")
        if removed:
            files_changed += 1
            lines_removed += len(removed)
            if a.apply and new != text:
                open(p, "w", encoding="utf-8", newline="").write(new)
    print(f"\n{'APPLIED' if a.apply else 'DRY-RUN'}: {lines_removed} marker line(s) in {files_changed} file(s).")

if __name__ == "__main__":
    raise SystemExit(main())
