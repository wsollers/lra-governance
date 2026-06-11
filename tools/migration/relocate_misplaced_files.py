#!/usr/bin/env python3
"""Relocate misplaced .tex files into the canonical layout and fix routers.

Chains after identify_misplaced_files.py (imports find_misplaced + helpers). For
each MOVABLE item it: creates the target topic dir + index.tex (and wires that
index into the parent router) when new, moves/renames the file, adds the new
\\input to the target topic index, removes the old \\input from the source index,
and finally deletes an emptied legacy proofs/notes/ dir (de-routing it).

Relocation fixes LOCATION + ROUTING only -- it does not convert legacy proof
bodies to the modern layered format. 'needs-human' items are reported, not moved.

Dry-run by default; --apply to write. Line endings preserved. Never overwrites.
"""
from __future__ import annotations
import argparse, re
from pathlib import Path
import identify_misplaced_files as idm

def nl_of(text, default="\n"):
    return "\r\n" if "\r\n" in text else default

def read(path: Path):
    return open(path, encoding="utf-8", newline="").read()

def write(path: Path, text: str, apply: bool):
    if apply:
        path.parent.mkdir(parents=True, exist_ok=True)
        open(path, "w", encoding="utf-8", newline="").write(text)

def index_targets(text):
    return {m.group(1).replace("\\", "/").removesuffix(".tex") for m in idm.INPUT_RE.finditer(text)}

def add_input(index_path: Path, target: str, apply: bool, nl_hint="\n"):
    """Append \\input{target} to index_path (create with banner if missing). Idempotent."""
    if index_path.exists():
        text = read(index_path)
        if target in index_targets(text):
            return None
        nl = nl_of(text, nl_hint)
        glue = "" if (not text or text.endswith(("\n", "\r"))) else nl
        write(index_path, text + glue + f"\\input{{{target}}}" + nl, apply)
        return f"WIRE   {index_path.name} <- \\input{{{target}}}"
    nl = nl_hint
    banner = (f"% ========================================================={nl}"
              f"% Proofs: {index_path.parent.name}{nl}"
              f"% ========================================================={nl}{nl}")
    write(index_path, banner + f"\\input{{{target}}}" + nl, apply)
    return f"CREATE {index_path.parent.name}/index.tex (+ \\input{{{target}}})"

def remove_input(index_path: Path, target: str, stem: str, apply: bool):
    """Remove the \\input line(s) referencing the FULL target from index_path."""
    if not index_path.exists():
        return None
    text = read(index_path); nl = nl_of(text)
    kept, removed = [], 0
    for ln in text.split(nl):
        m = idm.INPUT_RE.search(ln)
        if m:
            t = m.group(1).replace("\\", "/").removesuffix(".tex")
            if t == target:
                removed += 1
                continue
        kept.append(ln)
    if removed:
        write(index_path, nl.join(kept), apply)
        return f"UNWIRE {index_path.name} -> dropped \\input for {stem}"
    return None

def legacy_index_input_order(chap: Path):
    """Map proof stem -> position in proofs/notes/index.tex (for stable ordering)."""
    idx = chap / "proofs" / "notes" / "index.tex"
    if not idx.exists():
        return {}
    order = {}
    for n, m in enumerate(idm.INPUT_RE.finditer(read(idx))):
        order[Path(m.group(1)).name] = n
    return order

def main():
    ap = argparse.ArgumentParser(description="Relocate misplaced files + fix routers.")
    ap.add_argument("--root", required=True)
    ap.add_argument("--topic", help="Restrict to one target {topic}.")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    items = idm.find_misplaced(root, a.topic)

    # report non-movable
    for i in items:
        if i.status == "needs-human":
            print(f"  SKIP (needs-human): {i.kind}: {i.current} (could not resolve target topic)")

    # group movable proof relocations by chapter, ordered by legacy index position
    by_chap = {}
    for i in items:
        if i.status == "movable" and i.kind in ("legacy_proofs_notes", "proof_topic_mismatch", "nonconforming_proof_name"):
            by_chap.setdefault(i.chapter_root_abs, []).append(i)

    moved = 0
    touched_chapters = set()
    for chap_abs, group in by_chap.items():
        chap = Path(chap_abs); vrel = idm.volume_rel(chap)
        touched_chapters.add(chap_abs)
        order = legacy_index_input_order(chap)
        group.sort(key=lambda i: order.get(Path(i.current).stem, 10**6))
        proofs_index = chap / "proofs" / "index.tex"
        nl_hint = nl_of(read(proofs_index)) if proofs_index.exists() else "\n"
        for i in group:
            src = chap / i.current
            dst = chap / i.target
            old_topic = idm.topic_after("proofs", src, chap) or "notes"
            new_topic = i.topic
            old_target = f"{vrel}/{Path(i.current).as_posix()}".removesuffix(".tex")
            new_target = f"{vrel}/{Path(i.target).as_posix()}".removesuffix(".tex")
            topic_index = chap / "proofs" / new_topic / "index.tex"
            topic_index_target = f"{vrel}/proofs/{new_topic}/index"
            print(f"\n[{i.kind}] {i.current}  ->  {i.target}   ({i.signal})")
            if dst.exists():
                print("  REFUSE: target exists; skipping"); continue
            # 1) create/wire target topic index (+ route into proofs/index.tex if new)
            new_index = not topic_index.exists()
            act = add_input(topic_index, new_target, a.apply, nl_hint)
            if act: print(f"  {act}")
            if new_index:
                act2 = add_input(proofs_index, topic_index_target, a.apply, nl_hint)
                if act2: print(f"  {act2}")
            # 2) move/rename the file
            print(f"  {'MOVE ' if a.apply else 'WOULD MOVE'} {i.current} -> {i.target}")
            if a.apply:
                dst.parent.mkdir(parents=True, exist_ok=True)
                open(dst, "w", encoding="utf-8", newline="").write(read(src))
                src.unlink()
            # 3) unwire from old topic index
            act3 = remove_input(chap / "proofs" / old_topic / "index.tex",
                                old_target, Path(i.current).name, a.apply)
            if act3: print(f"  {act3}")
            moved += 1

    # cleanup emptied legacy proofs/notes dirs (de-route + delete)
    for chap_abs in {i.chapter_root_abs for i in items}:
        chap = Path(chap_abs); vrel = idm.volume_rel(chap)
        pn = chap / "proofs" / "notes"
        if not pn.is_dir():
            continue
        remaining = [p for p in pn.glob("*.tex") if p.name != "index.tex"]
        if remaining:
            continue
        idx = pn / "index.tex"
        has_inputs = idx.exists() and any(idm.INPUT_RE.finditer(read(idx)))
        if has_inputs:
            continue
        print(f"\n[cleanup] empty legacy {vrel}/proofs/notes")
        act = remove_input(chap / "proofs" / "index.tex", f"{vrel}/proofs/notes/index", "index", a.apply)
        if act: print(f"  UNWIRE proofs/index.tex -> dropped proofs/notes/index")
        print(f"  {'DELETE' if a.apply else 'WOULD DELETE'} proofs/notes/ (index.tex + dir)")
        if a.apply:
            if idx.exists(): idx.unlink()
            try: pn.rmdir()
            except OSError as e: print(f"  (dir not empty: {e})")

    print(f"\n{'APPLIED' if a.apply else 'DRY-RUN'}: moved={moved}, chapters touched={len(touched_chapters)}")

if __name__ == "__main__":
    raise SystemExit(main())
