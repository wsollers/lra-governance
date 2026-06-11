#!/usr/bin/env python3
"""Blank the 'Proof structure' remark in proof STUBS (both bodies still TODO).

Mirrors engine rule decoration_rules.proof_stub_structure_blank: while a proof is a
stub (Professional + Detailed bodies are TODO), the remark*[Proof structure] block
must be blank. Removes premature planned-proof prose from such stubs.

Scope: prf-*.tex. Authored proofs (no TODO body) are left untouched. Idempotent.
Dry-run by default; pass --apply to write. Line endings are preserved.
"""
from __future__ import annotations
import argparse, re
from pathlib import Path

PROOF_BODY = re.compile(r"\\begin\{proof\}(.*?)\\end\{proof\}", re.DOTALL)
STRUCT     = re.compile(r"(\\begin\{remark\*\}\[Proof structure\])(.*?)(\\end\{remark\*\})", re.DOTALL)
TODO       = re.compile(r"\bTODO\b", re.IGNORECASE)

def strip_comments_ws(s: str) -> str:
    return "".join(re.sub(r"(?<!\\)%.*$", "", ln) for ln in s.splitlines()).strip()

def is_stub(text: str) -> bool:
    bodies = [b for b in PROOF_BODY.findall(text)
              if "Professional Standard Proof" in b or "Detailed Learning Proof" in b]
    return bool(bodies) and all(TODO.search(b) for b in bodies)

def process(text: str):
    if not is_stub(text):
        return text, 0
    nl = "\r\n" if "\r\n" in text else "\n"
    n = 0
    def repl(m):
        nonlocal n
        if strip_comments_ws(m.group(2)) == "":
            return m.group(0)            # already blank -> idempotent
        n += 1
        return m.group(1) + nl + m.group(3)
    return STRUCT.sub(repl, text), n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = sorted(Path(a.root).rglob("prf-*.tex"))
    nf = nb = 0
    for f in files:
        text = open(f, encoding="utf-8", newline="").read()
        new, n = process(text)
        if n:
            nf += 1; nb += n
            print(f"{'BLANKED' if a.apply else 'WOULD BLANK'} {n}  {f}")
            if a.apply:
                open(f, "w", encoding="utf-8", newline="").write(new)
    print(f"\n{'Applied' if a.apply else 'Dry-run'}: {nb} Proof-structure block(s) blanked in {nf} stub file(s); scanned {len(files)} prf-*.tex.")

if __name__ == "__main__":
    main()
