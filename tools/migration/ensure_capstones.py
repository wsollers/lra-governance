#!/usr/bin/env python3
r"""Ensure every chapter has a canonical capstone in the proper place + routed.

Canonical location: proofs/exercises/capstone-{subject}.tex, routed LAST in
proofs/exercises/index.tex, which is routed from proofs/index.tex
(constitution/schema/file-schema.yaml). The stub matches the engine's
capstone_structure rule: \newpage, \phantomsection, \label{cap:{subject}},
exactly one problem tcolorbox, the word "Problem", and a Dependency ceiling remark.

Per chapter it: scaffolds proofs/exercises/ if absent; renames a mis-named
capstone into the canonical name; creates a compliant STUB if none exists (never
overwriting an existing capstone); and ensures the capstone is the last \input in
proofs/exercises/index.tex (wiring that index into proofs/index.tex). With
--upgrade-empty it also replaces a CONTENT-LESS placeholder capstone (one with no
tcolorbox) with the compliant stub. A legacy chapter-root capstone.tex (or
chapter-root exercises/) is REPORTED, not touched.

One script (the capstone is one fixed file per chapter -- no list to triage).
Dry-run by default; --apply to write. Line endings preserved. archive/ excluded.
"""
from __future__ import annotations
import argparse, re
from pathlib import Path

INPUT_RE = re.compile(r"\\(?:input|include|LRAProofsInput|LRAExercisesInput|LRACapstoneInput)\{([^}]+)\}")

def camel(subject: str) -> str:
    return "".join(p.capitalize() for p in re.split(r"[-_]", subject))

def volume_rel(chap: Path) -> str:
    parts = chap.resolve().parts
    for i, p in enumerate(parts):
        if re.fullmatch(r"volume-[ivx]+", p):
            return "/".join(parts[i:])
    return chap.name

def subject_of(chap: Path) -> str:
    cy = chap / "chapter.yaml"
    if cy.exists():
        m = re.search(r"^subject:\s*(\S+)\s*$", cy.read_text(encoding="utf-8", errors="ignore"), re.MULTILINE)
        if m:
            return m.group(1)
    return chap.name

def find_chapters(root: Path):
    root = root.resolve()
    if (root / "notes").is_dir() and (root / "proofs").is_dir() and "archive" not in root.parts:
        return [root]
    out = []
    for proofs in root.rglob("proofs"):
        chap = proofs.parent
        if proofs.is_dir() and (chap / "notes").is_dir() and "archive" not in chap.parts:
            out.append(chap.resolve())
    return sorted(set(out))

def stub(subject: str, title: str) -> str:
    guard = f"LRA{camel(subject)}CapstoneRendered"
    return (
        f"\\ifcsname {guard}\\endcsname\n\\else\n"
        f"\\expandafter\\gdef\\csname {guard}\\endcsname{{}}\n\n"
        "\\newpage\n\\phantomsection\n"
        f"\\label{{cap:{subject}}}\n\n"
        "\\begin{tcolorbox}[\n"
        "  colback=gray!6,\n  colframe=gray!40,\n  arc=2pt,\n"
        "  left=8pt, right=8pt, top=6pt, bottom=6pt,\n"
        "  title={\\small\\textbf{Capstone Problem}},\n"
        "  fonttitle=\\small\\bfseries\n]\n"
        "\\textbf{Problem.}\n"
        f"TODO: state one synthesizing problem for {title}, using only concepts at or\n"
        "before this chapter in the registry.\n"
        "\\end{tcolorbox}\n\n"
        "\\begin{remark*}[Dependency ceiling]\n"
        "The capstone may use only results routed at or before this chapter.\n"
        "\\end{remark*}\n\n"
        "\\clearpage\n\\fi\n"
    )

def read(p: Path):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def write(p: Path, text: str) -> None:
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(text)

def nl_of(text, d="\n"):
    return "\r\n" if "\r\n" in text else d

def route_capstone_last(index_path: Path, cap_target: str, apply: bool, nl="\n"):
    r"""Ensure \input{cap_target} is present and is the LAST \input. Returns action or None."""
    if index_path.exists():
        text = read(index_path); nl = nl_of(text, nl)
        lines = text.split(nl)
        cap_line = f"\\input{{{cap_target}}}"
        norm = lambda s: (INPUT_RE.search(s).group(1).replace("\\", "/").removesuffix(".tex")
                          if INPUT_RE.search(s) else None)
        has = any(norm(l) == cap_target for l in lines)
        last_input_idx = max((i for i, l in enumerate(lines) if INPUT_RE.search(l)), default=-1)
        already_last = has and last_input_idx >= 0 and norm(lines[last_input_idx]) == cap_target
        if already_last:
            return None
        lines = [l for l in lines if norm(l) != cap_target]            # drop any existing
        last_input_idx = max((i for i, l in enumerate(lines) if INPUT_RE.search(l)), default=-1)
        if last_input_idx >= 0:
            lines.insert(last_input_idx + 1, cap_line)
        else:
            if lines and lines[-1].strip() != "":
                lines.append("")
            lines.append(cap_line)
        new = nl.join(lines)
        if apply:
            write(index_path, new)
        return ("MOVE capstone -> last" if has else "ROUTE capstone (last)")
    new = f"% Exercise proofs router{nl}\\input{{{cap_target}}}{nl}"
    if apply:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        write(index_path, new)
    return "CREATE proofs/exercises/index.tex (+ capstone)"

def ensure_proofs_routes_exercises(proofs_index: Path, ex_target: str, apply: bool):
    if not proofs_index.exists():
        return None
    text = read(proofs_index); nl = nl_of(text)
    targets = {m.group(1).replace("\\", "/").removesuffix(".tex") for m in INPUT_RE.finditer(text)}
    if ex_target in targets:
        return None
    glue = "" if (not text or text.endswith(("\n", "\r"))) else nl
    new = text + glue + f"\\input{{{ex_target}}}" + nl
    if apply:
        write(proofs_index, new)
    return "WIRE proofs/index.tex -> proofs/exercises/index"

def main():
    ap = argparse.ArgumentParser(description="Ensure canonical capstone presence + routing.")
    ap.add_argument("--root", required=True)
    ap.add_argument("--upgrade-empty", action="store_true",
                    help="Replace an existing CONTENT-LESS placeholder capstone (no tcolorbox) with the compliant stub.")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    acted = 0
    for chap in find_chapters(root):
        subject = subject_of(chap)
        vrel = volume_rel(chap)
        ex_dir = chap / "proofs" / "exercises"
        canonical = ex_dir / f"capstone-{subject}.tex"
        ex_index = ex_dir / "index.tex"
        proofs_index = chap / "proofs" / "index.tex"
        cap_target = f"{vrel}/proofs/exercises/capstone-{subject}"
        ex_target = f"{vrel}/proofs/exercises/index"
        actions = []
        # 1) capstone file: rename a mis-named one, else create stub if missing
        if not canonical.exists():
            misnamed = [p for p in ex_dir.glob("capstone*.tex")] if ex_dir.is_dir() else []
            if len(misnamed) == 1:
                actions.append(f"RENAME {misnamed[0].name} -> capstone-{subject}.tex")
                if a.apply:
                    canonical.parent.mkdir(parents=True, exist_ok=True)
                    write(canonical, read(misnamed[0]))
                    misnamed[0].unlink()
            else:
                title = subject.replace("-", " ").title()
                actions.append("CREATE capstone stub")
                if a.apply:
                    canonical.parent.mkdir(parents=True, exist_ok=True)
                    write(canonical, stub(subject, title))
        elif a.upgrade_empty:
            body = re.sub(r"(?<!\\)%.*", "", read(canonical))
            if "\\begin{tcolorbox}" not in body:
                title = subject.replace("-", " ").title()
                actions.append("UPGRADE empty capstone -> compliant stub")
                if a.apply:
                    write(canonical, stub(subject, title))
        # 2) route capstone last (creates ex_index if absent)
        act = route_capstone_last(ex_index, cap_target, a.apply)
        if act:
            actions.append(act)
        # 3) wire exercises index into proofs/index.tex
        act2 = ensure_proofs_routes_exercises(proofs_index, ex_target, a.apply)
        if act2:
            actions.append(act2)
        # 4) report legacy artifacts (no action)
        legacy = []
        if (chap / "capstone.tex").exists():
            legacy.append("chapter-root capstone.tex (legacy; rich content -- migrate manually?)")
        if (chap / "exercises").is_dir():
            legacy.append("chapter-root exercises/ (legacy; belongs under proofs/exercises/)")
        if actions or legacy:
            print(f"\n[{vrel}]  subject={subject}")
            for x in actions:
                print(f"  {'APPLY' if a.apply else 'PLAN '}: {x}")
            for x in legacy:
                print(f"  FLAG : {x}")
            if actions:
                acted += 1
    print(f"\n{'APPLIED' if a.apply else 'DRY-RUN'}: {acted} chapter(s) needed capstone action.")

if __name__ == "__main__":
    raise SystemExit(main())
