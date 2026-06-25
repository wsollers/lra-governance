#!/usr/bin/env python3
r"""
verify_book_move.py - standalone, read-only verifier for the LRA book-tier re-org.

Independently reproduces the two invariants the LaTeX build and the volume
validator care about, WITHOUT importing the governance core (so it is a genuine
second opinion, not the same code grading its own homework):

  1. RESOLUTION : every \input/\include reachable from the volume index resolves
                  to a file that exists on disk. A stale path left behind by a
                  move (an \input still pointing at the old location) fails here,
                  exactly as the LaTeX build would.
  2. NO ORPHANS : every chapter directory on disk (one holding both notes/ and
                  proofs/) is reached by that \input chain. A chapter moved but
                  not re-routed is an orphan and fails here.

Optional, when --book and --chapter are given (pilot assertions):
  - the moved chapter has the canonical five files at its new home,
  - its chapter.yaml carries the right `path:` and `book:`,
  - the book router exists AND is reached from the volume index,
  - (with --old-rel) the old location is gone and its path string is nowhere live.
  - the hand-authored router files (book index + chapter routers + chapter.yaml)
    are ASCII-only, which the volume validator enforces as an error in .tex.

Mutates nothing. Exit 0 = all checks pass, 1 = at least one fails.

Example (the riemann-integration pilot):

  python verify_book_move.py ^
      --repo "F:\repos\lra-volume-iii" --volume volume-iii ^
      --book book-integration --chapter riemann-integration ^
      --old-rel analysis/riemann-integration
"""
from __future__ import annotations

import argparse
import sys
import re
from pathlib import Path

# \input{...} or \include{...}; the brace form this corpus uses.
INPUT_RE = re.compile(r"\\(?:input|include)\s*\{([^}]+)\}")


def strip_comment(line: str) -> str:
    """Drop everything from the first unescaped % (a LaTeX comment) to EOL."""
    out, i, n = [], 0, len(line)
    while i < n:
        c = line[i]
        if c == "\\" and i + 1 < n:        # escaped char (incl. \%) - keep the pair
            out.append(line[i : i + 2])
            i += 2
            continue
        if c == "%":                        # start of comment
            break
        out.append(c)
        i += 1
    return "".join(out)


def find_inputs(text: str) -> list[str]:
    found: list[str] = []
    for raw in text.splitlines():
        for m in INPUT_RE.finditer(strip_comment(raw)):
            found.append(m.group(1).strip())
    return found


def resolve(target: str, source: Path, roots: list[Path]) -> Path | None:
    r"""Resolve an \input target the way the build does: try the source's own
    directory first (relative inputs), then each volume/repo root; with and
    without a .tex suffix."""
    names = [target] + ([] if target.endswith(".tex") else [target + ".tex"])
    for root in [source.parent, *roots]:
        for name in names:
            cand = root / name
            if cand.is_file():
                return cand.resolve()
    return None


def walk(start: Path, roots: list[Path]) -> tuple[set[Path], list[tuple[Path, str]]]:
    r"""Follow the \input chain from `start`. Returns (reached files, unresolved
    (source, target) pairs)."""
    visited: set[Path] = set()
    reached: set[Path] = set()
    missing: list[tuple[Path, str]] = []
    stack = [start.resolve()]
    while stack:
        f = stack.pop()
        if f in visited:
            continue
        visited.add(f)
        reached.add(f)
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            missing.append((f, f"<unreadable: {e}>"))
            continue
        for tgt in find_inputs(text):
            r = resolve(tgt, f, roots)
            if r is None:
                missing.append((f, tgt))
            else:
                stack.append(r)
    return reached, missing


def find_chapter_dirs(volume_dir: Path) -> list[Path]:
    """A chapter is any directory holding both a notes/ and a proofs/ subdir."""
    return [
        p
        for p in volume_dir.rglob("*")
        if p.is_dir() and (p / "notes").is_dir() and (p / "proofs").is_dir()
    ]


def scan_old_path(volume_dir: Path, old_rel: str):
    """Find every line mentioning the old path string; split live vs commented."""
    active, commented = [], []
    for p in volume_dir.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in (".tex", ".yaml", ".yml"):
            continue
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for i, raw in enumerate(lines, 1):
            if old_rel in raw:
                (active if old_rel in strip_comment(raw) else commented).append(
                    (p, i, raw.strip())
                )
    return active, commented


def check_ascii(paths: list[Path]):
    """Find non-ASCII characters in the given files. Returns a list of
    (path, lineno, col, char, codepoint). Deliberately scoped to the handful of
    router/metadata files a move authors - NOT body content, which is moved
    verbatim and may legitimately contain Unicode."""
    findings = []
    for p in paths:
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for col, ch in enumerate(line, 1):
                if ord(ch) > 0x7F:
                    findings.append((p, i, col, ch, ord(ch)))
    return findings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Verify a book-tier chapter move (read-only).")
    ap.add_argument("--repo", required=True, help="volume repo root (the dir that contains the volume content dir)")
    ap.add_argument("--volume", required=True, help="volume content dir name, e.g. volume-iii")
    ap.add_argument("--book", help="new book dir, e.g. book-integration (enables pilot assertions)")
    ap.add_argument("--chapter", help="moved chapter subject, e.g. riemann-integration")
    ap.add_argument("--old-rel", help="old chapter path relative to the volume dir, e.g. analysis/riemann-integration")
    args = ap.parse_args(argv)

    repo = Path(args.repo).resolve()
    volume_dir = (repo / args.volume).resolve()
    roots = [repo, volume_dir]
    index = volume_dir / "index.tex"

    print(f"== verifying {volume_dir} ==\n")
    if not index.is_file():
        print(f"FAIL  volume index missing: {index}")
        return 1

    failures = 0

    # 1. resolution -------------------------------------------------------------
    reached, missing = walk(index, roots)
    if missing:
        failures += 1
        print(f"FAIL  {len(missing)} unresolved \\input(s) - the build would break here:")
        for src, tgt in missing:
            print(f"        in {src}")
            print(f"          -> {tgt}")
    else:
        print(f"PASS  every \\input reachable from the volume index resolves "
              f"({len(reached)} files reached)")

    # 2. orphans ----------------------------------------------------------------
    chapter_dirs = find_chapter_dirs(volume_dir)
    orphans = [c for c in chapter_dirs if (c / "index.tex").resolve() not in reached]
    if orphans:
        failures += 1
        print(f"FAIL  {len(orphans)} chapter(s) on disk not reached by the \\input chain (orphaned):")
        for c in orphans:
            print(f"        {c}")
    else:
        print(f"PASS  all {len(chapter_dirs)} chapter dirs on disk are routed (no orphans)")

    # 3. old-path purge ---------------------------------------------------------
    if args.old_rel:
        active, commented = scan_old_path(volume_dir, args.old_rel)
        if active:
            failures += 1
            print(f'FAIL  {len(active)} live reference(s) to old path "{args.old_rel}":')
            for p, i, txt in active:
                print(f"        {p}:{i}: {txt}")
        else:
            print(f'PASS  no live references to old path "{args.old_rel}"')
        if commented:
            print(f'WARN  {len(commented)} commented-out reference(s) to "{args.old_rel}" '
                  f"(harmless, but worth tidying):")
            for p, i, txt in commented:
                print(f"        {p}:{i}: {txt}")

    # 4. pilot assertions -------------------------------------------------------
    if args.book and args.chapter:
        chap = volume_dir / args.book / args.chapter
        canonical = [
            chap / "index.tex",
            chap / "chapter.yaml",
            chap / "notes" / "index.tex",
            chap / "proofs" / "index.tex",
            chap / "proofs" / "exercises" / "index.tex",
        ]
        miss = [f for f in canonical if not f.is_file()]
        if miss:
            failures += 1
            print("FAIL  new chapter home missing canonical files:")
            for f in miss:
                print(f"        {f}")
        else:
            print(f"PASS  new chapter home has all canonical files: {chap}")

        book_index = volume_dir / args.book / "index.tex"
        if not book_index.is_file():
            failures += 1
            print(f"FAIL  book router missing: {book_index}")
        elif book_index.resolve() not in reached:
            failures += 1
            print(f"FAIL  book router exists but is not reached from the volume index: {book_index}")
        else:
            print(f"PASS  book router exists and is routed: {book_index}")

        cy = chap / "chapter.yaml"
        if cy.is_file():
            txt = cy.read_text(encoding="utf-8", errors="replace")
            want_path = f"{args.volume}/{args.book}/{args.chapter}"
            ok_path = f"path: {want_path}" in txt
            ok_book = f"book: {args.book}" in txt
            if ok_path and ok_book:
                print("PASS  chapter.yaml path + book correct")
            else:
                failures += 1
                print("FAIL  chapter.yaml fields off:")
                if not ok_path:
                    print(f"        expected  path: {want_path}")
                if not ok_book:
                    print(f"        expected  book: {args.book}")

        if args.old_rel:
            old_dir = volume_dir / args.old_rel
            if old_dir.exists():
                failures += 1
                print(f"FAIL  old chapter dir still present: {old_dir}")
            else:
                print(f"PASS  old chapter dir is gone: {old_dir}")

        # ASCII guard, scoped to the files this move hand-authors. The validator
        # flags non-ASCII in .tex as an error; catch it here, pre-build. Body
        # content is intentionally excluded - it is moved verbatim, not authored.
        routers = [
            book_index,
            chap / "index.tex",
            chap / "notes" / "index.tex",
            chap / "proofs" / "index.tex",
            chap / "proofs" / "exercises" / "index.tex",
            chap / "chapter.yaml",
        ]
        ascii_hits = check_ascii(routers)
        if ascii_hits:
            failures += 1
            print(f"FAIL  {len(ascii_hits)} non-ASCII char(s) in hand-authored router files:")
            for p, ln, col, ch, cp in ascii_hits:
                print(f"        {p}:{ln}:{col}: {ch!r} (U+{cp:04X})  -> use an ASCII equivalent (e.g. --- for em-dash)")
        else:
            print("PASS  hand-authored router files are ASCII-clean")

    print()
    if failures:
        print(f"RESULT: {failures} check(s) FAILED")
        return 1
    print("RESULT: all checks passed - safe to build")
    return 0


if __name__ == "__main__":
    sys.exit(main())
