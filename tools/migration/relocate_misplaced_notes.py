#!/usr/bin/env python3
"""Relocate misplaced NOTES files into notes/{topic}/ and fix routers.

Chains after identify_misplaced_notes.py. For each MOVABLE flat notes file it:
  - moves the file into notes/{topic}/ (filename preserved -- notes are NOT
    renamed, unlike proofs),
  - adds its \\input to notes/{topic}/index.tex (creating that index + wiring it
    into notes/index.tex if absent),
  - removes the old direct \\input from notes/index.tex,
  - verifies the topic-pair (warns if proofs/{topic}/ is missing).
Only moves into topics that ALREADY exist; 'needs-human' files are reported.

Reuses helpers from relocate_misplaced_files (add_input/remove_input/read/nl_of)
and the detector from identify_misplaced_files -- no duplicated logic.
Dry-run by default; --apply to write. Never overwrites.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import identify_misplaced_files as idm
import relocate_misplaced_files as rel
from identify_misplaced_notes import find_notes

def main():
    ap = argparse.ArgumentParser(description="Relocate misplaced notes files + fix routers.")
    ap.add_argument("--root", required=True)
    ap.add_argument("--topic")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    items = find_notes(root, a.topic)
    for i in items:
        if i.status == "needs-human":
            print(f"  SKIP (needs-human): {i.current}  (target topic '{Path(i.current).stem.removeprefix('notes-')}' does not exist)")
    moved = 0
    for i in (x for x in items if x.status == "movable"):
        chap = Path(i.chapter_root_abs); vrel = idm.volume_rel(chap); topic = i.topic
        src = chap / i.current; dst = chap / i.target; stem = Path(i.current).stem
        notes_index = chap / "notes" / "index.tex"
        topic_index = chap / "notes" / topic / "index.tex"
        nl = rel.nl_of(rel.read(notes_index)) if notes_index.exists() else "\n"
        new_target = f"{vrel}/notes/{topic}/{stem}"
        old_target = f"{vrel}/notes/{stem}"
        topic_index_target = f"{vrel}/notes/{topic}/index"
        print(f"\n[flat_notes] {i.current}  ->  {i.target}   ({i.signal})")
        if dst.exists():
            print("  REFUSE: target exists; skipping"); continue
        # 1) wire into target topic index (create + route into notes/index.tex if new)
        new_index = not topic_index.exists()
        act = rel.add_input(topic_index, new_target, a.apply, nl)
        if act: print(f"  {act}")
        if new_index:
            act2 = rel.add_input(notes_index, topic_index_target, a.apply, nl)
            if act2: print(f"  {act2}")
        # 2) move file (no rename)
        print(f"  {'MOVE ' if a.apply else 'WOULD MOVE'} {i.current} -> {i.target}")
        if a.apply:
            dst.parent.mkdir(parents=True, exist_ok=True)
            open(dst, "w", encoding="utf-8", newline="").write(rel.read(src))
            src.unlink()
        # 3) drop old direct route from notes/index.tex
        act3 = rel.remove_input(notes_index, old_target, Path(i.current).name, a.apply)
        if act3: print(f"  {act3}")
        # 4) topic-pair sanity
        if not (chap / "proofs" / topic).is_dir():
            print(f"  WARN: proofs/{topic}/ missing -- topic pair incomplete (create a proofs topic).")
        moved += 1
    print(f"\n{'APPLIED' if a.apply else 'DRY-RUN'}: notes moved={moved}")

if __name__ == "__main__":
    raise SystemExit(main())
