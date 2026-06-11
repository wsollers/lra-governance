#!/usr/bin/env python3
r"""Remove flagged retired roadmap / role sections (purge ruling).

Mirrors the engine's structural_roadmap_purge target: a section whose heading is
a retired roadmap or role heading. Excises from that heading --
including an immediately preceding decorative comment banner -- up to (but not
including) the next sectioning boundary: \section, \subsection, \chapter, \input,
\part, a `% ====` comment banner, or EOF.

Only that span is removed; surrounding content is untouched. Dry-run by default;
pass --apply to write. Line endings preserved.
"""
from __future__ import annotations
import argparse, re
from pathlib import Path

HEADING = re.compile(r"^\s*\\section\*\{\s*Structural\s+(?:Roadmap|Role)\s*\}", re.MULTILINE)
# a boundary line that ends the roadmap span
BOUNDARY = re.compile(r"^\s*(?:\\(?:section|subsection|subsubsection|chapter|part|input|include)\b|%\s*=+\s*$)")
BANNER   = re.compile(r"^\s*%\s*=+\s*$")

def find_spans(lines):
    spans=[]
    i=0
    while i < len(lines):
        if HEADING.match(lines[i]):
            start=i
            # absorb an immediately preceding comment banner block (%==, % Title, %==)
            j=i-1
            blk=[]
            while j>=0 and lines[j].lstrip().startswith("%"):
                blk.append(j); j-=1
            if blk and any(BANNER.match(lines[k]) for k in blk):
                start=min(blk)
            # find end: first boundary line AFTER the heading
            k=i+1
            while k < len(lines) and not BOUNDARY.match(lines[k]):
                k+=1
            spans.append((start,k))   # [start, k) removed; k is the boundary (kept)
            i=k
        else:
            i+=1
    return spans

def process(text):
    nl="\r\n" if "\r\n" in text else "\n"
    lines=text.split(nl)
    spans=find_spans(lines)
    if not spans:
        return text, []
    drop=set()
    for s,e in spans:
        drop.update(range(s,e))
    kept=[ln for idx,ln in enumerate(lines) if idx not in drop]
    # collapse the blank gap left behind: trim trailing blank lines created at each cut
    new=nl.join(kept)
    new=re.sub(rf"(?:{re.escape(nl)}){{3,}}", nl+nl, new)  # >=3 newlines -> 1 blank line
    return new, spans

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--apply", action="store_true")
    a=ap.parse_args()
    files=sorted(Path(a.root).rglob("*.tex"))
    nfiles=nspans=0
    for f in files:
        text=open(f,encoding="utf-8",newline="").read()
        new,spans=process(text)
        if spans:
            nfiles+=1; nspans+=len(spans)
            for s,e in spans:
                print(f"{'REMOVE' if a.apply else 'WOULD REMOVE'} lines {s+1}-{e} ({e-s} lines)  {f}")
            if a.apply:
                open(f,"w",encoding="utf-8",newline="").write(new)
    print(f"\n{'Applied' if a.apply else 'Dry-run'}: {nspans} roadmap section(s) in {nfiles} file(s); scanned {len(files)} .tex.")

if __name__=="__main__":
    main()
