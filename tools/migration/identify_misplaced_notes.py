#!/usr/bin/env python3
"""Identify misplaced NOTES files (flat notes/*.tex that belong in notes/{topic}/).

Thin wrapper over identify_misplaced_files.find_misplaced() filtered to the
'flat_notes' kind, so notes and proofs share one detector (no duplicate logic).
Target topic is derived from the filename (notes-{topic}.tex); a file is 'movable'
only when that topic already exists, else 'needs-human' (we do not invent topics).
Read-only. archive/ is excluded by the underlying detector.
"""
from __future__ import annotations
import argparse, json
from dataclasses import asdict
from pathlib import Path
import identify_misplaced_files as idm

def find_notes(root: Path, topic_filter=None):
    return [i for i in idm.find_misplaced(root, topic_filter) if i.kind == "flat_notes"]

def main():
    ap = argparse.ArgumentParser(description="Identify misplaced notes files.")
    ap.add_argument("--root", required=True)
    ap.add_argument("--topic")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    a = ap.parse_args()
    items = find_notes(Path(a.root).resolve(), a.topic)
    if a.format == "json":
        print(json.dumps([asdict(i) for i in items], indent=2)); return
    by = {}
    for i in items:
        by.setdefault(i.status, []).append(i)
    print(f"root: {a.root}")
    for st in ("movable", "needs-human"):
        if st not in by: continue
        print(f"\n{st.upper()} ({len(by[st])}):")
        for i in by[st]:
            arrow = f"  ->  {i.target}" if i.target else "  ->  (topic not found; needs human)"
            print(f"  [{i.chapter}] {i.current}{arrow}" + (f"   ({i.signal})" if i.signal else ""))
    print(f"\nsummary: { {k: len(v) for k, v in by.items()} }")

if __name__ == "__main__":
    raise SystemExit(main())
