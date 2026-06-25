#!/usr/bin/env python3
r"""
cross_volume_move.py - mechanical cross-volume chapter harvest for the LRA re-org.

Moves a GROUP of chapters from a SOURCE volume into a DESTINATION volume's book,
across repos, doing only the mechanical, non-judgemental work:

  1. MOVE     each chapter dir  volume-X/<ch>  ->  volume-Y/<book>/<ch>  (cross-repo).
  2. REWRITE  inside every moved chapter, swap each group prefix
              volume-X/<ch_i>  ->  volume-Y/<book>/<ch_i>  (boundary-aware, byte-
              preserving). Carries the volume-token change AND the book insertion,
              and fixes intra-group cross-references in one pass.
  3. YAML     set each chapter.yaml's `volume:` (-> volume-Y) and `book:` (-> <book>);
              its `path:` is fixed by step 2.
  4. DEST     (re)generate volume-Y/<book>/index.tex (chapters in plan order,
              \clearpage-separated) and insert ONE \input{volume-Y/<book>/index}
              into volume-Y's volume index (end of routing region, style-preserving).
  5. SOURCE   remove the moved chapters' inputs from volume-X's volume index
              (style-preserving: keeps the source's \clearpage convention).
  6. REPORT   residual `volume-X/<other>` path tokens inside the moved chapters
              (= genuine cross-volume references to re-point in the next gated step).

DRY-RUN BY DEFAULT. Writes nothing without --apply. Idempotent. Scoped to mechanical
relocation + path rewriting only; cross-reference/label re-pointing is the separate,
gated pass that follows (expect ref-warnings after this runs - that is by design).

Gate after: verify_book_move on BOTH volumes, then build both.

Usage:
  python cross_volume_move.py --source-repo "F:\repos\lra-volume-v" ^
      --dest-repo "F:\repos\lra-volume-i" --plan harvest-geometry.json            # dry-run
  python cross_volume_move.py --source-repo ... --dest-repo ... --plan ... --apply  # do it
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
    hits = [
        p for p in volume_dir.rglob(chapter)
        if p.is_dir() and p.name == chapter and (p / "chapter.yaml").is_file()
    ]
    if len(hits) > 1:
        raise SystemExit(f"AMBIGUOUS: multiple chapter dirs named '{chapter}': {hits}")
    return hits[0] if hits else None


def rewrite_prefix_in_tree(root: Path, old: str, new: str, apply: bool) -> list[tuple[Path, int]]:
    pat = re.compile(re.escape(old) + r"(?=[/}\s]|$)")
    touched = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in (".tex", ".yaml", ".yml"):
            continue
        try:
            text = p.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            continue
        new_text, n = pat.subn(new, text)
        if n:
            touched.append((p, n))
            if apply:
                p.write_bytes(new_text.encode("utf-8"))
    return touched


def count_residual(root: Path, source_volume: str, chapters: list[str]) -> list[tuple[Path, int]]:
    """Count source_volume/<seg> occurrences where <seg> is NOT a moved chapter."""
    pat = re.compile(re.escape(source_volume) + r"/([A-Za-z0-9_-]+)")
    chs = set(chapters)
    found = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in (".tex", ".yaml", ".yml"):
            continue
        try:
            text = p.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            continue
        n = sum(1 for m in pat.finditer(text) if m.group(1) not in chs)
        if n:
            found.append((p, n))
    return found


def set_yaml_volume_book(chapter_dir: Path, volume: str, book: str, apply: bool) -> str:
    cy = chapter_dir / "chapter.yaml"
    if not cy.is_file():
        return "no chapter.yaml (?)"
    text = cy.read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    notes = []
    vi = next((i for i, l in enumerate(lines) if l.startswith("volume:")), None)
    if vi is not None:
        if lines[vi].strip() != f"volume: {volume}":
            lines[vi] = f"volume: {volume}"; notes.append("volume updated")
    else:
        lines.insert(0, f"volume: {volume}"); notes.append("volume inserted")
    bi = next((i for i, l in enumerate(lines) if l.startswith("book:")), None)
    if bi is not None:
        if lines[bi].strip() != f"book: {book}":
            lines[bi] = f"book: {book}"; notes.append("book updated")
    else:
        pi = next((i for i, l in enumerate(lines) if l.startswith("path:")), None)
        at = (pi + 1) if pi is not None else len(lines)
        lines.insert(at, f"book: {book}"); notes.append("book inserted")
    if apply:
        cy.write_bytes(nl.join(lines).encode("utf-8"))
    return ", ".join(notes) if notes else "yaml already set"


def gen_book_index(dest_volume_dir: Path, dest_volume: str, book: str, chapters: list[str], apply: bool):
    """(Re)generate the book router. If the router already exists, MERGE: keep its
    existing chapters in order and append the new ones at the end (never clobber)."""
    target = dest_volume_dir / book / "index.tex"
    existing: list[str] = []
    if target.is_file():
        txt = target.read_bytes().decode("utf-8")
        for line in txt.split("\n"):
            t = routing_target(line)
            if t is not None:
                seg = t.split("/")[-2]
                if seg != "index" and seg not in existing:
                    existing.append(seg)
    merged = list(existing)
    added: list[str] = []
    for ch in chapters:
        if ch not in merged:
            merged.append(ch); added.append(ch)
    lines = [
        f"% Book: {book}",
        "% Book router --- no \\part; chapters render under the volume's existing \\part.",
    ]
    for i, ch in enumerate(merged):
        lines.append(f"\\input{{{dest_volume}/{book}/{ch}/index}}")
        if i != len(merged) - 1:
            lines.append("\\clearpage")
    body = "\n".join(lines) + "\n"
    if apply:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body.encode("utf-8"))
    return body, existing, added


def routing_target(line: str):
    m = INPUT_RE.search(strip_comment(line))
    if not m:
        return None
    t = m.group(1)
    return t if t.split("/")[-1] == "index" else None


def edit_volume_index(volume_dir: Path, transform, apply: bool):
    idx = volume_dir / "index.tex"
    text = idx.read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    routing_idx = [i for i, l in enumerate(lines) if routing_target(l) is not None]
    if not routing_idx:
        return None
    start, end = routing_idx[0], routing_idx[-1]
    had_clearpage = any(l.strip() == "\\clearpage" for l in lines[start : end + 1])
    targets = [routing_target(l) for l in lines[start : end + 1] if routing_target(l) is not None]
    new_targets = transform(list(targets))
    if new_targets == targets:
        return None
    block = []
    for j, t in enumerate(new_targets):
        block.append(f"\\input{{{t}}}")
        if had_clearpage and j != len(new_targets) - 1:
            block.append("\\clearpage")
    new_lines = lines[:start] + block + lines[end + 1 :]
    old_region = nl.join(lines[start : end + 1])
    new_region = nl.join(block)
    if apply:
        idx.write_bytes(nl.join(new_lines).encode("utf-8"))
    return old_region, new_region


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Mechanical cross-volume chapter harvest (dry-run by default).")
    ap.add_argument("--source-repo", required=True)
    ap.add_argument("--dest-repo", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)

    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    source_volume = plan["source_volume"]
    dest_volume = plan["dest_volume"]
    dest_book = plan["dest_book"]
    chapters = plan["chapters"]
    apply = args.apply

    source_repo = Path(args.source_repo).resolve()
    dest_repo = Path(args.dest_repo).resolve()
    source_volume_dir = (source_repo / source_volume).resolve()
    dest_volume_dir = (dest_repo / dest_volume).resolve()

    mode = "APPLY" if apply else "DRY-RUN"
    print(f"== cross_volume_move [{mode}] : {source_volume}/* -> {dest_volume}/{dest_book}/ ==\n")

    prefix_map = {f"{source_volume}/{ch}": f"{dest_volume}/{dest_book}/{ch}" for ch in chapters}

    moved = skipped = 0
    moved_trees = []
    for ch in chapters:
        src = find_chapter_dir(source_volume_dir, ch)
        dst = dest_volume_dir / dest_book / ch
        if src is None:
            if dst.is_dir():
                print(f"  = {ch}: already at {dest_volume}/{dest_book}/{ch} (skip move)")
                moved_trees.append(dst); skipped += 1
                continue
            print(f"  ! MISSING chapter '{ch}' - not found under {source_volume_dir} nor at dest")
            continue
        print(f"  > {ch}: {source_volume}/{ch}  ->  {dest_volume}/{dest_book}/{ch}")
        if apply:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
        moved_trees.append(dst if apply else src)
        moved += 1

    print("\n  -- path rewrites (group prefixes) + yaml --")
    for tree in moved_trees:
        total = 0; files = set()
        for old, new in prefix_map.items():
            for p, n in rewrite_prefix_in_tree(tree, old, new, apply):
                total += n; files.add(p)
        print(f"  {tree.name}: {total} rewrite(s) across {len(files)} file(s)")
        print(f"      yaml  {set_yaml_volume_book(tree, dest_volume, dest_book, apply)}")

    print("\n  -- dest book router --")
    _body, existing, added = gen_book_index(dest_volume_dir, dest_volume, dest_book, chapters, apply)
    if existing:
        verb = "merged into" if apply else "would merge into"
        addtxt = ", ".join(added) if added else "none (all already present)"
        print(f"  {verb} {dest_volume}/{dest_book}/index.tex  "
              f"({len(existing)} existing + {len(added)} new = {len(existing) + len(added)}; added: {addtxt})")
    else:
        verb = "wrote" if apply else "would write"
        print(f"  {verb} {dest_volume}/{dest_book}/index.tex  ({len(added)} chapter(s))")

    print("\n  -- dest volume index --")
    book_target = f"{dest_volume}/{dest_book}/index"
    res = edit_volume_index(dest_volume_dir, lambda ts: ts if book_target in ts else ts + [book_target], apply)
    if res is None:
        print(f"  {dest_volume} index already routes {dest_book} (no change)")
    else:
        old_region, new_region = res
        print("  REPLACE routing region:")
        for l in old_region.split("\n"):
            print(f"    - {l}")
        print("  WITH:")
        for l in new_region.split("\n"):
            print(f"    + {l}")

    print("\n  -- source volume index --")
    remove = set(chapters)
    res = edit_volume_index(source_volume_dir, lambda ts: [t for t in ts if t.split("/")[-2] not in remove], apply)
    if res is None:
        print(f"  {source_volume} index already free of moved chapters (no change)")
    else:
        old_region, new_region = res
        print("  REPLACE routing region:")
        for l in old_region.split("\n"):
            print(f"    - {l}")
        print("  WITH:")
        for l in new_region.split("\n"):
            print(f"    + {l}")

    print("\n  -- residual cross-volume references (re-point next) --")
    base = dest_volume_dir if apply else source_volume_dir
    any_residual = False
    for tree in moved_trees:
        for p, n in count_residual(tree, source_volume, chapters):
            any_residual = True
            try:
                rel = p.relative_to(base).as_posix()
            except ValueError:
                rel = p.as_posix()
            print(f"  {n:>3}x  {source_volume}/...  in  {rel}")
    if not any_residual:
        print(f"  none - no residual '{source_volume}/<other>' tokens in the moved chapters")

    print(f"\nRESULT [{mode}]: {moved} moved, {skipped} already-placed.")
    if not apply:
        print("Re-run with --apply to perform these changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
