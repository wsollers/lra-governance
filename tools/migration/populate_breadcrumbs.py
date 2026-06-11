#!/usr/bin/env python3
r"""Populate canonical \breadcrumb{} macros across the whole work (deterministic).

The breadcrumb chain is GLOBAL: chapters are concatenated across volumes in the
order the volume indexes are given, and prior/next resolve across that global chain
-- so a chapter at a volume boundary points into the adjoining volume. The overall
first chapter's prior is "Start Studying" and the overall last chapter's next is
"Torus Renders" (outer sentinels).

  Order  = chapter \input order within each volume index, volumes in arg order.
  Titles = each chapter.yaml `display_title`.
  Render = canonical render_breadcrumb (constitution/auditor/generators/
           breadcrumb_deterministic.py) -- single source of truth.

Re-runnable: insert a chapter (add its \input to a volume index) and re-run. For
each chapter index.tex: REPLACE an existing \breadcrumb{...} (fixes stale ones),
else INSERT after \chapter{...} (and its \label{} if present). Dry-run by default;
--apply to write. Line endings preserved.

Usage (volumes in reading order; repeat --volume-index):
  populate_breadcrumbs.py --volume-index ...\\lra-volume-i\\volume-i\\index.tex \
                          --volume-index ...\\lra-volume-ii\\volume-ii\\index.tex
"""
from __future__ import annotations
import argparse, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "constitution" / "auditor" / "generators"))
from breadcrumb_deterministic import render_breadcrumb

START_SENTINEL = {"subject": "__start__", "display_title": "Start Studying"}
END_SENTINEL   = {"subject": "__end__",   "display_title": "Torus Renders"}

CHAPTER_INPUT = re.compile(r"\\input\{[^{}]*?/([^/{}]+)/index\}")
BREADCRUMB_RE = re.compile(r"\\breadcrumb(?:\{[^{}]*\}){4}")
CHAPTER_RE    = re.compile(r"\\chapter\*?\{[^{}]*\}")

def yaml_field(text, key):
    m = re.search(rf"^{key}:\s*(.+?)\s*$", text, re.MULTILINE)
    if not m:
        return None
    val = m.group(1).strip()
    # Strip one layer of matching YAML quotes so display_title: "Foo" -> Foo
    # (the regex captures quotes verbatim). Empty after stripping -> None, so the
    # caller falls back to the subject slug instead of emitting a literal {''}.
    if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
        val = val[1:-1].strip()
    return val or None

def collect_chapters(volume_index: Path):
    vol_root = volume_index.parent
    out = []
    for subj in CHAPTER_INPUT.findall(volume_index.read_text(encoding="utf-8", errors="ignore")):
        cy = vol_root / subj / "chapter.yaml"
        disp = (yaml_field(cy.read_text(encoding="utf-8", errors="ignore"), "display_title")
                if cy.exists() else None) or subj
        out.append({"subject": subj, "display_title": disp, "index_path": vol_root / subj / "index.tex"})
    return out

def apply_to_index(text, bc):
    nl = "\r\n" if "\r\n" in text else "\n"
    ex = BREADCRUMB_RE.search(text)
    if ex:
        if ex.group(0) == bc: return text, "unchanged", None
        return text[:ex.start()] + bc + text[ex.end():], "replaced", ex.group(0)
    m = CHAPTER_RE.search(text)
    if not m: return text, "no-chapter", None
    end = m.end()
    ml = re.match(r"\s*\\label\{[^{}]*\}", text[end:])
    if ml: end += ml.end()
    return text[:end] + nl + nl + bc + text[end:], "inserted", None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volume-index", action="append", required=True, type=Path,
                    help="Volume index .tex (repeat, in reading order).")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    chapters = []
    for vi in a.volume_index:
        chapters += collect_chapters(vi)
    registry = ([START_SENTINEL]
                + [{"subject": c["subject"], "display_title": c["display_title"]} for c in chapters]
                + [END_SENTINEL])

    print(f"Global chain ({len(chapters)} chapters), bracketed by "
          f"'{START_SENTINEL['display_title']}' ... '{END_SENTINEL['display_title']}':")
    changed = 0
    for c in chapters:
        bc = render_breadcrumb(c["subject"], c["display_title"], registry, is_stub=False)
        idx = c["index_path"]
        if not idx.exists():
            print(f"  SKIP (no index.tex): {c['subject']}"); continue
        text = open(idx, encoding="utf-8", newline="").read()
        new, action, old = apply_to_index(text, bc)
        tag = {"inserted": "INSERT", "replaced": "REPLACE", "unchanged": "ok", "no-chapter": "NO-CHAPTER"}[action]
        print(f"  [{tag:9}] {bc}")
        if action == "replaced": print(f"             (was: {old})")
        if new != text:
            changed += 1
            if a.apply: open(idx, "w", encoding="utf-8", newline="").write(new)
    print(f"\n{'Applied' if a.apply else 'Dry-run'}: {changed} index file(s) would change.")

if __name__ == "__main__":
    main()
