#!/usr/bin/env python3
"""Set or check LaTeX Workshop root comments in LRA volume TeX files."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path


ROOT_COMMENT_RE = re.compile(r"^%\s*!TEX\s+root\s*=.*$", re.IGNORECASE)
INPUT_RE = re.compile(r"\\input\{([^}]+)\}")


def tracked_tex_files(root: Path) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "*.tex"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return sorted(path for path in root.rglob("*.tex") if ".git" not in path.parts and "build" not in path.parts)
    return [root / line.strip() for line in result.stdout.splitlines() if line.strip()]


def root_inputs(volume_root: Path) -> dict[Path, Path]:
    mapping: dict[Path, Path] = {}
    for tex_root in sorted(volume_root.glob("volume-*.tex")):
        text = tex_root.read_text(encoding="utf-8", errors="replace")
        if "\\documentclass" not in text:
            continue
        for match in INPUT_RE.finditer(text):
            target = (volume_root / match.group(1)).with_suffix(".tex")
            if target.name == "index.tex" and target.parent.name.startswith("book-"):
                mapping[target.parent.resolve()] = tex_root.resolve()
    return mapping


def root_for_file(path: Path, mapping: dict[Path, Path]) -> Path | None:
    resolved = path.resolve()
    candidates = [
        (book_root, tex_root)
        for book_root, tex_root in mapping.items()
        if resolved == book_root / "index.tex" or book_root in resolved.parents
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda item: len(item[0].parts), reverse=True)
    return candidates[0][1]


def should_skip_tex(path: Path) -> bool:
    if "_to_delete" in path.parts:
        return True
    if path.name in {"source.tex", "corrected.tex"} and (
        (path.parent / "artifact.yaml").exists() or (path.parent / "generation-request.json").exists()
    ):
        return True
    return False


def relative_comment(path: Path, tex_root: Path) -> str:
    try:
        rel = Path(os.path.relpath(tex_root, path.parent))
    except ValueError:
        rel = tex_root
    return f"% !TEX root = {rel.as_posix()}"


def current_root_comment(path: Path) -> str | None:
    try:
        first_line = path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    except IndexError:
        return None
    if ROOT_COMMENT_RE.match(first_line):
        return first_line
    return None


def expected_root_comment(path: Path, tex_root: Path) -> str:
    return relative_comment(path, tex_root)


def updated_text(path: Path, tex_root: Path) -> tuple[str, bool]:
    text = path.read_text(encoding="utf-8", errors="replace")
    comment = expected_root_comment(path, tex_root)
    lines = text.splitlines()
    newline = "\n" if text.endswith("\n") else ""
    if lines and ROOT_COMMENT_RE.match(lines[0]):
        if lines[0] == comment:
            return text, False
        lines[0] = comment
        return "\n".join(lines) + newline, True
    return comment + "\n" + text, True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."), help="target lra-volume-* repo root")
    parser.add_argument("--check", action="store_true", help="fail if active TeX files have missing or stale root comments")
    parser.add_argument("--write", action="store_true", help="write changes; default is dry-run")
    args = parser.parse_args(argv)
    if args.check and args.write:
        raise SystemExit("--check and --write are mutually exclusive")

    volume_root = args.root.expanduser().resolve()
    mapping = root_inputs(volume_root)
    if not mapping:
        raise SystemExit(f"no book roots discovered in {volume_root}")

    missing = 0
    stale = 0
    changed = 0
    skipped = 0
    for path in tracked_tex_files(volume_root):
        resolved = path.resolve()
        if resolved.parent == volume_root and resolved.name.startswith("volume-"):
            skipped += 1
            continue
        if should_skip_tex(path):
            skipped += 1
            continue
        tex_root = root_for_file(path, mapping)
        if tex_root is None:
            skipped += 1
            continue
        actual = current_root_comment(path)
        expected = expected_root_comment(path, tex_root)
        if args.check:
            if actual is None:
                missing += 1
                print(f"missing: {path.relative_to(volume_root)} expected {expected}")
            elif actual != expected:
                stale += 1
                print(f"stale: {path.relative_to(volume_root)} expected {expected} found {actual}")
            continue
        new_text, needs_write = updated_text(path, tex_root)
        if not needs_write:
            continue
        changed += 1
        action = "updated" if args.write else "would_update"
        print(f"{action}: {path.relative_to(volume_root)}")
        if args.write:
            path.write_text(new_text, encoding="utf-8", newline="\n")

    if args.check:
        print(f"missing={missing} stale={stale} skipped={skipped}")
        return 1 if missing or stale else 0
    print(f"changed={changed} skipped={skipped} write={args.write}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
