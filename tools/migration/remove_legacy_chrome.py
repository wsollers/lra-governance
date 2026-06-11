#!/usr/bin/env python3
r"""Strip legacy navigation chrome for a leaner structure.

Removes three legacy forms wherever they appear in .tex files:
  1. Journey box  -- a \begin{tcolorbox}...\end{tcolorbox} whose title contains
                     "Where You Are" / "Journey" (the old hand-rolled breadcrumb).
  2. Roadmap      -- \section*{... Roadmap ...} (plain or retired roadmap).
  3. Retired role headings.
Each removal absorbs an immediately preceding comment banner and (for the journey
box) a trailing \vspace{...}. The canonical \breadcrumb{} macro in the chapter
index is the replacement -- it is NOT touched (it is a macro, not a tcolorbox).

Dry-run by default; --apply to write. Line endings preserved.
"""
from __future__ import annotations
import argparse, re
from pathlib import Path

BEGIN_TCB = re.compile(r"\\begin\{tcolorbox\}")
END_TCB   = re.compile(r"\\end\{tcolorbox\}")
ROADMAP_HEADING = re.compile(r"^\s*\\section\*\{[^{}]*(?:Roadmap|Structural\s+Role)[^{}]*\}", re.IGNORECASE)
BOUNDARY = re.compile(r"^\s*(?:\\(?:section|subsection|subsubsection|chapter|part|input|include)\b|%\s*=+\s*$)")
BANNER   = re.compile(r"^\s*%\s*=+\s*$")
VSPACE   = re.compile(r"^\s*\\vspace\{[^{}]*\}\s*$")
JOURNEY  = re.compile(r"Where You Are|Journey", re.IGNORECASE)

def _absorb_banner(lines, start):
    """Move start up over an immediately preceding comment banner block."""
    j = start - 1
    blk = []
    while j >= 0 and lines[j].lstrip().startswith("%"):
        blk.append(j); j -= 1
    if blk and any(BANNER.match(lines[k]) for k in blk):
        return min(blk)
    return start

def find_removals(lines):
    ranges = []
    i = 0
    n = len(lines)
    while i < n:
        # --- journey tcolorbox ---
        if BEGIN_TCB.search(lines[i]):
            k = i
            while k < n and "]" not in lines[k]:
                k += 1
            opts = "\n".join(lines[i:k+1])
            if JOURNEY.search(opts):
                e = k
                while e < n and not END_TCB.search(lines[e]):
                    e += 1
                end_excl = e + 1
                if end_excl < n and VSPACE.match(lines[end_excl]):
                    end_excl += 1
                ranges.append((_absorb_banner(lines, i), end_excl))
                i = end_excl
                continue
        # --- roadmap / structural role section ---
        if ROADMAP_HEADING.match(lines[i]):
            k = i + 1
            while k < n and not BOUNDARY.match(lines[k]):
                k += 1
            ranges.append((_absorb_banner(lines, i), k))
            i = k
            continue
        i += 1
    return ranges

def process(text):
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    ranges = find_removals(lines)
    if not ranges:
        return text, []
    drop = set()
    for s, e in ranges:
        drop.update(range(s, e))
    kept = [ln for idx, ln in enumerate(lines) if idx not in drop]
    new = nl.join(kept)
    new = re.sub(rf"(?:{re.escape(nl)}){{3,}}", nl + nl, new)
    return new, ranges

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = sorted(Path(a.root).rglob("*.tex"))
    nf = nr = 0
    for f in files:
        text = open(f, encoding="utf-8", newline="").read()
        new, ranges = process(text)
        if ranges:
            nf += 1; nr += len(ranges)
            for s, e in ranges:
                print(f"{'REMOVE' if a.apply else 'WOULD REMOVE'} lines {s+1}-{e} ({e-s} lines)  {f}")
            if a.apply:
                open(f, "w", encoding="utf-8", newline="").write(new)
    print(f"\n{'Applied' if a.apply else 'Dry-run'}: {nr} legacy block(s) in {nf} file(s); scanned {len(files)} .tex.")

if __name__ == "__main__":
    main()
