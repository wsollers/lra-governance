#!/usr/bin/env python3
r"""Migrate hand-rolled chrome tcolorboxes to their canonical macros.

  breadcrumb tcolorbox  ->  \breadcrumb{subject}{prior}{current}{next}
                            (lra-common/common/breadcrumb-macros.tex)
  toolkit    tcolorbox  ->  \begin{toolkitbox}{title}...\end{toolkitbox}
                            (lra-common/common/structural-presentations.tex)

Only tcolorboxes with `colback=breadcrumb` (breadcrumb) or a Toolkit title are
touched; every other tcolorbox is left alone. Breadcrumb conversions that cannot be
parsed confidently are SKIPPED and reported, never guessed. Dry-run by default;
pass --apply to write. Line endings preserved.
"""
from __future__ import annotations
import argparse, re
from pathlib import Path

TCB    = re.compile(r"\\begin\{tcolorbox\}\[(?P<opts>[^\]]*)\](?P<body>.*?)\\end\{tcolorbox\}", re.DOTALL)
TEXTBF = re.compile(r"\\textbf\{(.*?)\}")
ARROW  = re.compile(r"\$\\;\\to\\;\$")
CENTER = re.compile(r"\\begin\{center\}(.*?)\\end\{center\}", re.DOTALL)

def _clean(s: str) -> str:
    s = s.replace(r"\small", "").replace(r"\centering", "")
    return re.sub(r"\s+", " ", s).strip()

def _strip_textbf(s: str) -> str:
    return _clean(TEXTBF.sub(r"\1", s))

def extract_title(opts: str):
    """Brace-balanced value of title={...}; handles nesting like {\\small\\textbf{X}}."""
    m = re.search(r"title=\{", opts)
    if not m:
        return None
    i = m.end() - 1
    depth = 0
    for j in range(i, len(opts)):
        if opts[j] == "{":
            depth += 1
        elif opts[j] == "}":
            depth -= 1
            if depth == 0:
                return opts[i + 1:j]
    return None

def convert_breadcrumb(opts: str, body: str):
    """Return \breadcrumb{...} or None if it can't be parsed confidently."""
    title_raw = extract_title(opts)
    if title_raw is None:
        return None
    subject = _strip_textbf(title_raw)
    mc = CENTER.search(body)
    chain = mc.group(1) if mc else body
    parts = [p for p in (ARROW.split(chain)) if _clean(p)]
    cur_i = next((i for i, p in enumerate(parts) if "\\textbf" in p), None)
    if cur_i is None:
        return None
    current = _clean(TEXTBF.search(parts[cur_i]).group(1))
    prior = _strip_textbf(" ".join(parts[:cur_i])) if cur_i > 0 else ""
    nxt   = _strip_textbf(" ".join(parts[cur_i + 1:])) if cur_i < len(parts) - 1 else ""
    if not subject or not current:
        return None
    return f"\\breadcrumb{{{subject}}}{{{prior}}}{{{current}}}{{{nxt}}}"

def process(text: str, report: list, path):
    def repl(m):
        opts, body = m.group("opts"), m.group("body")
        if "colback=breadcrumb" in opts:
            out = convert_breadcrumb(opts, body)
            if out is None:
                report.append(("SKIP-breadcrumb", str(path)))
                return m.group(0)
            report.append(("breadcrumb", str(path)))
            return out
        title_raw = extract_title(opts)
        if title_raw and "toolkit" in title_raw.lower():
            title = _strip_textbf(title_raw)
            report.append(("toolkit", str(path)))
            return f"\\begin{{toolkitbox}}{{{title}}}{body}\\end{{toolkitbox}}"
        return m.group(0)
    return TCB.sub(repl, text)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = sorted(Path(a.root).rglob("*.tex"))
    report, changed = [], 0
    for f in files:
        text = open(f, encoding="utf-8", newline="").read()
        before = len(report)
        new = process(text, report, f)
        if new != text:
            changed += 1
            for kind, p in report[before:]:
                if p == str(f):
                    print(f"{'APPLY' if a.apply else 'WOULD'} {kind:18} {f}")
            if a.apply:
                open(f, "w", encoding="utf-8", newline="").write(new)
    skips = sum(1 for k, _ in report if k.startswith("SKIP"))
    print(f"\n{'Applied' if a.apply else 'Dry-run'}: {changed} file(s) changed; "
          f"{sum(1 for k,_ in report if k=='breadcrumb')} breadcrumb, "
          f"{sum(1 for k,_ in report if k=='toolkit')} toolkit; {skips} skipped; scanned {len(files)} .tex.")
    if skips:
        print("SKIPPED (parse-unsure, left untouched -- handle manually):")
        for k, p in report:
            if k.startswith("SKIP"): print("   ", p)

if __name__ == "__main__":
    main()
