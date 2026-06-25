#!/usr/bin/env python3
r"""
book_partition.py - mechanical book-tier partition for an LRA volume.

Given a plan (which chapters belong to which book, in order), this performs the
purely mechanical re-org and nothing judgemental:

  1. MOVE      each chapter dir into its book dir (volume/<book>/<chapter>/).
  2. REWRITE   every \input/path inside the moved chapter, swapping the old
               path prefix (volume/<old>/<chapter>) for the new one
               (volume/<book>/<chapter>). Boundary-aware, so 'functions' never
               matches inside 'function-sequences'. Byte-preserving (line
               endings untouched).
  3. YAML      set chapter.yaml's `book:` field (its `path:` is fixed by step 2).
  4. ROUTERS   (re)generate each book's index.tex - a no-\part router listing
               its chapters in plan order, \clearpage-separated, so chapters
               still render under the volume's existing \part. Then reconcile the
               volume index: collapse the analysis chapter list into one \input
               per book, in plan order, preserving front matter, \part, the
               bounding \clearpages, and every downstream (evict-list) chapter.

DRY-RUN BY DEFAULT. Writes nothing without --apply. Idempotent: a chapter already
at its target is left alone; re-running after --apply is a no-op.

This tool is deliberately scoped to mechanical relocation + path rewriting. It
does NOT touch cross-references or labels (those are the careful, separate
re-pointing pass). After it runs, gate with verify_book_move.py + validate_volume
+ the build.

Usage:
  python book_partition.py --repo "F:\repos\lra-volume-iii" --plan book-partition-iii.json            # dry-run
  python book_partition.py --repo "F:\repos\lra-volume-iii" --plan book-partition-iii.json --apply     # do it
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

INPUT_RE = re.compile(r"\\(?:input|include)\s*\{([^}]+)\}")


def strip_comment(line: str) -> str:
    out, i, n = [], 0, len(line)
    while i < n:
        c = line[i]
        if c == "\\" and i + 1 < n:
            out.append(line[i : i + 2]); i += 2; continue
        if c == "%":
            break
        out.append(c); i += 1
    return "".join(out)


def find_chapter_dir(volume_dir: Path, chapter: str) -> Path | None:
    """A chapter dir is the one named <chapter> that carries a chapter.yaml
    (distinguishes it from a same-named notes/proofs topic dir)."""
    hits = [
        p for p in volume_dir.rglob(chapter)
        if p.is_dir() and p.name == chapter and (p / "chapter.yaml").is_file()
    ]
    if len(hits) > 1:
        raise SystemExit(f"AMBIGUOUS: multiple chapter dirs named '{chapter}': {hits}")
    return hits[0] if hits else None


def rewrite_prefix_in_tree(root: Path, old: str, new: str, apply: bool) -> list[tuple[Path, int]]:
    """Replace path prefix `old` with `new` in every .tex/.yaml under root.
    Boundary-aware (next char must be / } whitespace or EOL). Byte-preserving."""
    pat = re.compile(re.escape(old) + r"(?=[/}\s]|$)")
    touched = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in (".tex", ".yaml", ".yml"):
            continue
        data = p.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        new_text, n = pat.subn(new, text)
        if n:
            touched.append((p, n))
            if apply:
                p.write_bytes(new_text.encode("utf-8"))
    return touched


def set_yaml_book(chapter_dir: Path, book: str, apply: bool) -> str:
    """Ensure chapter.yaml has `book: <book>`. Returns a status string."""
    cy = chapter_dir / "chapter.yaml"
    if not cy.is_file():
        return "no chapter.yaml (?)"
    data = cy.read_bytes()
    text = data.decode("utf-8")
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    book_idx = next((i for i, l in enumerate(lines) if l.startswith("book:")), None)
    if book_idx is not None:
        if lines[book_idx].strip() == f"book: {book}":
            return "book: already set"
        lines[book_idx] = f"book: {book}"
        status = "book: updated"
    else:
        path_idx = next((i for i, l in enumerate(lines) if l.startswith("path:")), None)
        insert_at = (path_idx + 1) if path_idx is not None else len(lines)
        lines.insert(insert_at, f"book: {book}")
        status = "book: inserted"
    if apply:
        cy.write_bytes(nl.join(lines).encode("utf-8"))
    return status


def gen_book_index(volume_dir: Path, volume: str, book: str, chapters: list[str], apply: bool) -> str:
    r"""Write the book router: no \part, chapters \clearpage-separated."""
    lines = [
        f"% Book: {book}",
        "% Book router --- no \\part; chapters render under the volume's existing \\part.",
    ]
    for i, ch in enumerate(chapters):
        lines.append(f"\\input{{{volume}/{book}/{ch}/index}}")
        if i != len(chapters) - 1:
            lines.append("\\clearpage")
    body = "\n".join(lines) + "\n"
    target = volume_dir / book / "index.tex"
    if apply:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body.encode("utf-8"))
    return body


def reconcile_volume_index(volume_dir: Path, volume: str, book_of_chapter: dict[str, str],
                           book_order: list[str], apply: bool) -> tuple[str, str] | None:
    r"""Rewrite the volume index routing region so each book's chapters collapse
    to a single \input{volume/<book>/index} at that book's first appearance,
    while NON-plan inputs (chapters that stay put this pass) are preserved in
    place and order. Routing inputs are those ending in '/index'; front matter
    and trailing lines are untouched. Returns (old, new) or None."""
    idx = volume_dir / "index.tex"
    text = idx.read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    plan_books = set(book_order)

    def routing_target(line: str):
        m = INPUT_RE.search(strip_comment(line))
        if not m:
            return None
        target = m.group(1)
        return target if target.split("/")[-1] == "index" else None

    routing_idx = [i for i, l in enumerate(lines) if routing_target(l) is not None]
    if not routing_idx:
        return None
    start, end = routing_idx[0], routing_idx[-1]

    emitted: set[str] = set()
    targets: list[str] = []
    for i in range(start, end + 1):
        t = routing_target(lines[i])
        if t is None:
            continue
        seg = t.split("/")[-2] if "/" in t else ""
        if seg in book_of_chapter:            # a plan chapter -> its book (once)
            book = book_of_chapter[seg]
            if book not in emitted:
                emitted.add(book)
                targets.append(f"{volume}/{book}/index")
        elif seg in plan_books:               # an already-collapsed book input
            if seg not in emitted:
                emitted.add(seg)
                targets.append(f"{volume}/{seg}/index")
        else:                                 # non-plan input -> preserve in place
            targets.append(t)

    block: list[str] = []
    for j, tgt in enumerate(targets):
        block.append(f"\\input{{{tgt}}}")
        if j != len(targets) - 1:
            block.append("\\clearpage")

    old_region = nl.join(lines[start : end + 1])
    new_region = nl.join(block)
    if old_region == new_region:
        return None

    new_lines = lines[:start] + block + lines[end + 1 :]
    if apply:
        idx.write_bytes(nl.join(new_lines).encode("utf-8"))
    return old_region, new_region


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Mechanical book-tier partition (dry-run by default).")
    ap.add_argument("--repo", required=True, help="volume repo root (contains the volume content dir)")
    ap.add_argument("--plan", required=True, help="path to the partition plan JSON")
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    args = ap.parse_args(argv)

    repo = Path(args.repo).resolve()
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    volume = plan["volume"]
    volume_dir = (repo / volume).resolve()
    books = plan["books"]
    apply = args.apply

    mode = "APPLY" if apply else "DRY-RUN"
    print(f"== book_partition [{mode}] : {volume_dir} ==\n")

    book_of_chapter = {ch: b["name"] for b in books for ch in b["chapters"]}
    book_order = [b["name"] for b in books]

    moved = skipped = 0
    for book in books:
        bname = book["name"]
        for ch in book["chapters"]:
            src = find_chapter_dir(volume_dir, ch)
            if src is None:
                print(f"  ! MISSING chapter '{ch}' - not found under {volume_dir}")
                continue
            old_prefix = src.relative_to(repo).as_posix()
            dst = volume_dir / bname / ch
            new_prefix = dst.relative_to(repo).as_posix()

            if src.resolve() == dst.resolve():
                print(f"  = {ch}: already at {new_prefix} (skip move)")
                skipped += 1
                # still ensure yaml book field + book index will list it
                print(f"      yaml  {set_yaml_book(src, bname, apply)}")
                continue

            print(f"  > {ch}: {old_prefix}  ->  {new_prefix}")
            if apply:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
            rewrite_root = dst if apply else src
            touched = rewrite_prefix_in_tree(rewrite_root, old_prefix, new_prefix, apply)
            total = sum(n for _, n in touched)
            print(f"      rewrite  {total} path occurrence(s) across {len(touched)} file(s)")
            print(f"      yaml  {set_yaml_book(dst if apply else src, bname, apply)}")
            moved += 1

    print("\n  -- book routers --")
    for book in books:
        body = gen_book_index(volume_dir, volume, book["name"], book["chapters"], apply)
        verb = "wrote" if apply else "would write"
        print(f"  {verb} {volume}/{book['name']}/index.tex  ({len(book['chapters'])} chapter(s))")

    print("\n  -- volume index --")
    res = reconcile_volume_index(volume_dir, volume, book_of_chapter, book_order, apply)
    if res is None:
        print("  volume index already reconciled (no change)")
    else:
        old_region, new_region = res
        print("  REPLACE routing region:")
        for l in old_region.split("\n"):
            print(f"    - {l}")
        print("  WITH:")
        for l in new_region.split("\n"):
            print(f"    + {l}")

    print(f"\nRESULT [{mode}]: {moved} moved, {skipped} already-placed.")
    if not apply:
        print("Re-run with --apply to perform these changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
