#!/usr/bin/env python3
r"""
hold_move.py - park a GROUP of chapters into the flat lra-hold repo.

A thin sibling of cross_volume_move.py for moves whose destination is the holding
repo (a parking lot, NOT a volume): no book router, no destination volume index.

  1. MOVE    each chapter dir  volume-X/<ch>  ->  lra-hold/<ch>   (flat, cross-repo).
  2. REWRITE inside every moved chapter, swap each group prefix
             volume-X/<ch_i>  ->  <ch_i>  (drop the volume token -> flat, hold-root
             relative; boundary-aware, byte-preserving; fixes intra-group refs too).
  3. STAMP   each chapter.yaml with `held_from: volume-X/<ch>` (provenance); its
             `path:` is flattened by step 2.
  4. SOURCE  remove the moved chapters' inputs from volume-X's volume index
             (style-preserving).
  5. REPORT  residual `volume-X/<other>` tokens (informational only - lra-hold does
             not build, so these are dormant until/if a chapter is revived).

DRY-RUN BY DEFAULT. Idempotent. Gate after: verify_book_move on the SOURCE volume,
build the source. (lra-hold is not built or validated.)

Usage:
  python hold_move.py --source-repo "F:\repos\lra-volume-v" ^
      --hold-repo "F:\repos\lra-hold" --plan hold-manifolds.json            # dry-run
  python hold_move.py --source-repo ... --hold-repo ... --plan ... --apply    # do it
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


def set_yaml_held(chapter_dir: Path, held_from: str, apply: bool) -> str:
    cy = chapter_dir / "chapter.yaml"
    if not cy.is_file():
        return "no chapter.yaml (?)"
    text = cy.read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    hi = next((i for i, l in enumerate(lines) if l.startswith("held_from:")), None)
    if hi is not None:
        if lines[hi].strip() == f"held_from: {held_from}":
            return "held_from already set"
        lines[hi] = f"held_from: {held_from}"
        status = "held_from updated"
    else:
        pi = next((i for i, l in enumerate(lines) if l.startswith("path:")), None)
        at = (pi + 1) if pi is not None else len([l for l in lines if l.strip()])
        lines.insert(at, f"held_from: {held_from}")
        status = "held_from stamped"
    if apply:
        cy.write_bytes(nl.join(lines).encode("utf-8"))
    return status


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
    ap = argparse.ArgumentParser(description="Park chapters into flat lra-hold (dry-run by default).")
    ap.add_argument("--source-repo", required=True)
    ap.add_argument("--hold-repo", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)

    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    source_volume = plan["source_volume"]
    chapters = plan["chapters"]
    apply = args.apply

    source_repo = Path(args.source_repo).resolve()
    hold_repo = Path(args.hold_repo).resolve()
    source_volume_dir = (source_repo / source_volume).resolve()

    mode = "APPLY" if apply else "DRY-RUN"
    print(f"== hold_move [{mode}] : {source_volume}/* -> lra-hold/ (flat) ==\n")

    prefix_map = {f"{source_volume}/{ch}": ch for ch in chapters}

    moved = skipped = 0
    pairs = []  # (chapter, tree)
    for ch in chapters:
        src = find_chapter_dir(source_volume_dir, ch)
        dst = hold_repo / ch
        if src is None:
            if dst.is_dir():
                print(f"  = {ch}: already at lra-hold/{ch} (skip move)")
                pairs.append((ch, dst)); skipped += 1
                continue
            print(f"  ! MISSING chapter '{ch}' - not found under {source_volume_dir} nor at hold")
            continue
        print(f"  > {ch}: {source_volume}/{ch}  ->  lra-hold/{ch}")
        if apply:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
        pairs.append((ch, dst if apply else src))
        moved += 1

    print("\n  -- path rewrites (drop volume token) + provenance --")
    for ch, tree in pairs:
        total = 0; files = set()
        for old, new in prefix_map.items():
            for p, n in rewrite_prefix_in_tree(tree, old, new, apply):
                total += n; files.add(p)
        print(f"  {ch}: {total} rewrite(s) across {len(files)} file(s)")
        print(f"      yaml  {set_yaml_held(tree, f'{source_volume}/{ch}', apply)}")

    print("\n  -- source volume index --")
    remove = set(chapters)
    res = edit_volume_index(source_volume_dir, lambda ts: [t for t in ts if t.split("/")[-2] not in remove], apply)
    if res is None:
        print(f"  {source_volume} index already free of held chapters (no change)")
    else:
        old_region, new_region = res
        print("  REPLACE routing region:")
        for l in old_region.split("\n"):
            print(f"    - {l}")
        print("  WITH:")
        for l in new_region.split("\n"):
            print(f"    + {l}")

    print("\n  -- residual cross-volume references (informational; lra-hold does not build) --")
    base = hold_repo if apply else source_volume_dir
    any_residual = False
    for ch, tree in pairs:
        for p, n in count_residual(tree, source_volume, chapters):
            any_residual = True
            try:
                rel = p.relative_to(base).as_posix()
            except ValueError:
                rel = p.as_posix()
            print(f"  {n:>3}x  {source_volume}/...  in  {rel}")
    if not any_residual:
        print(f"  none - no residual '{source_volume}/<other>' tokens in the parked chapters")

    print(f"\nRESULT [{mode}]: {moved} parked, {skipped} already-held.")
    if not apply:
        print("Re-run with --apply to perform these changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
