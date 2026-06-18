#!/usr/bin/env python3
"""validate_decoration.py -- thin CLI harness over decoration_rules.

Walks a volume/chapter/section (scoped via _targeting), classifies each .tex as
chapter_index | section_note | other, runs block rules (on math environments)
and file rules (whole-file), and prints a grouped report.

Exit codes: 0 = no errors, 2 = error-severity issues found (with --fail-on-errors), 1 = fatal.
Reuses _targeting for discovery so the tree is walked one way across all validators.
"""
from __future__ import annotations
import argparse, json, os, sys
from collections import Counter
from pathlib import Path
import re

import decoration_rules as dr
import _targeting as tg

EXCLUDED = {"bibliography", *tg.IGNORED_DIR_NAMES}

def classify(path: Path) -> str:
    if path.name == "index.tex" and tg.is_chapter_root(path.parent):
        return "chapter_index"
    if path.name == "index.tex" and re.fullmatch(r"volume-[ivx]+", path.parent.parent.name):
        return "chapter_index"
    if "notes" in {p.lower() for p in path.parts}:
        return "section_note"
    return "other"

def iter_tex(roots: list[Path]):
    for root in roots:
        if root.is_file() and root.suffix == ".tex":
            yield root; continue
        for dp, dns, fns in os.walk(root):
            dp_path = Path(dp)
            dns[:] = [
                d for d in dns
                if d not in EXCLUDED
                and not d.startswith(".")
                and not tg.is_ignored_path(dp_path / d, root)
            ]
            for f in fns:
                path = Path(dp) / f
                if f.endswith(".tex") and not tg.is_ignored_path(path, root):
                    yield path

def walk_roots_for(target: tg.Target, root: Path) -> list[Path]:
    if target.scope == "section":
        return [p for p in (target.notes_dir, target.proofs_dir) if p]
    if target.scope == "chapter" and target.chapter:
        return [target.chapter]
    if target.scope == "volume" and target.volume:
        return [target.volume]
    volumes = tg.volume_roots(root)
    return volumes or [root]

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run LRA decoration rules over a volume/chapter/section.")
    ap.add_argument("--root", required=True)
    ap.add_argument("--volume"); ap.add_argument("--chapter"); ap.add_argument("--section")
    ap.add_argument("--require-box", action="store_true",
                    help="require every formal environment to use its semantic math box")
    ap.add_argument("--no-require-box", action="store_true",
                    help="deprecated no-op: semantic math boxes are selective by default")
    ap.add_argument("--breadcrumb-max-leading-exposition", type=int, default=0)
    ap.add_argument("--toolkit-max-leading-exposition", type=int, default=1)
    ap.add_argument("--canonical-dir", help="dir with predicates.yaml/structures.yaml; enables formal_reading concept triggers")
    ap.add_argument("--no-formal-reading", action="store_true", help="disable the formal_reading_required rule")
    ap.add_argument("--json", default=None, help="write machine report to this path")
    ap.add_argument("--fail-on-errors", action="store_true")
    args = ap.parse_args(argv)

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"fatal: root not found: {root}", file=sys.stderr); return 1
    try:
        target = tg.resolve_target(root, args.volume, args.chapter, args.section)
    except ValueError as e:
        print(f"fatal: {e}", file=sys.stderr); return 1

    surface_forms = []
    if args.canonical_dir:
        import formal_reading
        surface_forms, gap = formal_reading.load_concept_surface_forms(args.canonical_dir)
        print(f"formal-reading triggers: {len(surface_forms)} concept forms "
              f"(derived {gap['derived_from_name']}, stoplisted {gap['stoplisted_single_word']}, "
              f"structures.yaml {'present' if gap['structures_yaml_present'] else 'absent'})\n")

    ctx = dr.Context(
        require_box=args.require_box,
        breadcrumb_max_leading_exposition=args.breadcrumb_max_leading_exposition,
        toolkit_max_leading_exposition=args.toolkit_max_leading_exposition,
        formal_reading=not args.no_formal_reading,
        concept_surface_forms=surface_forms,
    )

    records = []
    files = 0
    for tex in sorted(set(iter_tex(walk_roots_for(target, root)))):
        files += 1
        kind = classify(tex)
        text = dr.strip_latex_comments(tex.read_text(encoding="utf-8", errors="replace"))
        info = dr.FileInfo(str(tex), kind)
        issues = list(dr.run_file_rules(text, info, ctx))
        for b in dr.extract_blocks(text):
            issues.extend(dr.run_rules(b, ctx))
        try: rel = str(tex.relative_to(root))
        except ValueError: rel = str(tex)
        for i in issues:
            records.append({"file": rel.replace("\\","/"), "kind": kind, "line": i.line,
                            "severity": i.severity, "code": i.code, "message": i.message})

    sev = Counter(r["severity"] for r in records)
    by_file: dict[str, list] = {}
    for r in records: by_file.setdefault(r["file"], []).append(r)

    print(f"decoration check: {files} files, {len(records)} issue(s) "
          f"[{sev.get('error',0)} error, {sev.get('warning',0)} warning, {sev.get('review',0)} review]\n")
    for f in sorted(by_file):
        print(f"  {f}  ({by_file[f][0]['kind']})")
        for r in sorted(by_file[f], key=lambda r: (r["line"], r["code"])):
            print(f"    L{r['line']:<4} {r['severity']:<7} {r['code']}: {r['message']}")
        print()
    if not records:
        print("  clean.\n")

    if args.json:
        Path(args.json).write_text(json.dumps(
            {"root": str(root), "scope": target.scope, "files": files, "records": records},
            indent=2) + "\n", encoding="utf-8")
        print(f"json report: {args.json}")

    errors = sev.get("error", 0)
    if args.fail_on_errors and errors:
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
