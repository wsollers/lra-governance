#!/usr/bin/env python3
r"""Repair deterministic LaTeX breakage produced by migration/generation passes.

This is a narrow safety pass for generated artifacts. It is not a formatter.

Repairs:
  - malformed generated proof return links such as
    \hyperref[prop:x]{Return to Theorem (\texorpdfstring{\hyperref[prf:x).}
  - malformed theorem-like stub optional titles that start a \texorpdfstring
    / \hyperref expression but never close it,
  - stale router inputs to deleted proofs/notes/index files after relocation,
  - files with one extra top-level \end{enumerate} and orphan top-level \item
    lines by inserting the missing opening \begin{enumerate}.

Dry-run by default; pass --apply to write. Idempotent.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

INPUT_RE = re.compile(r"\\(?:input|include)\{([^}]+)\}")
RETURN_BAD_RE = re.compile(
    r"^\\hyperref\[(?P<label>[^\]]+)\]\{Return to (?P<kind>Theorem|Proposition|Lemma|Corollary)"
    r"\s*\(\\texorpdfstring\{\\hyperref\[[^\]\)]*(?:\]|\))\.\}\s*$"
)
BAD_OPTIONAL_RE = re.compile(
    r"^\\begin\{(?P<env>theorem|proposition|lemma|corollary)\*\}"
    r"\[\\texorpdfstring\{\\hyperref\[[^\]]+\]\s*$"
)
PROOF_LABEL_RE = re.compile(r"\\label\{prf:([a-z0-9-]+)\}")


def read(path: Path) -> str:
    return open(path, encoding="utf-8", newline="").read()


def write(path: Path, text: str, apply: bool) -> None:
    if apply:
        open(path, "w", encoding="utf-8", newline="").write(text)


def nl_of(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def title_from_root(root: str) -> str:
    return root.replace("-", " ").title()


def repair_return_links(text: str) -> tuple[str, int]:
    nl = nl_of(text)
    changed = 0
    out: list[str] = []
    for line in text.split(nl):
        m = RETURN_BAD_RE.match(line.strip())
        if m:
            changed += 1
            out.append(rf"\hyperref[{m.group('label')}]{{Return to {m.group('kind')}}}")
        else:
            out.append(line)
    return nl.join(out), changed


def repair_bad_stub_titles(text: str) -> tuple[str, int]:
    nl = nl_of(text)
    lines = text.split(nl)
    root_match = PROOF_LABEL_RE.search(text)
    fallback = title_from_root(root_match.group(1)) if root_match else "Generated Proof Stub"
    changed = 0
    out: list[str] = []
    i = 0
    while i < len(lines):
        m = BAD_OPTIONAL_RE.match(lines[i].strip())
        if not m:
            out.append(lines[i])
            i += 1
            continue
        if i + 1 < len(lines) and lines[i + 1].lstrip().startswith("{"):
            # Valid generated form split across two lines:
            # \begin{theorem*}[\texorpdfstring{\hyperref[prf:x]
            # {Display Title}}{Display Title}]
            out.append(lines[i])
            i += 1
            continue
        # The following line is usually either a real title fragment or a TODO
        # placeholder. In both cases, prefer a syntactically safe title.
        out.append(rf"\begin{{{m.group('env')}*}}[{fallback}]")
        changed += 1
        i += 1
    return nl.join(out), changed


def target_exists(index_file: Path, target: str) -> bool:
    target = target.replace("\\", "/").removesuffix(".tex")
    root = index_file
    parts = list(index_file.resolve().parts)
    vol_idx = next((i for i, part in enumerate(parts) if re.fullmatch(r"volume-[ivx]+", part)), None)
    if vol_idx is not None:
        root = Path(*parts[:vol_idx])
    candidate = root / (target + ".tex")
    return candidate.exists()


def repair_stale_proofs_notes_inputs(path: Path, text: str) -> tuple[str, int]:
    nl = nl_of(text)
    changed = 0
    out: list[str] = []
    for line in text.split(nl):
        m = INPUT_RE.search(line)
        if not m:
            out.append(line)
            continue
        target = m.group(1).replace("\\", "/").removesuffix(".tex")
        if not target.endswith("/proofs/notes/index") or target_exists(path, target):
            out.append(line)
            continue
        replacement = target.removesuffix("/notes/index") + "/index"
        if target_exists(path, replacement):
            out.append(line.replace(m.group(1), replacement))
        else:
            # Usually this is proofs/index.tex trying to route the deleted
            # legacy notes index. If no canonical replacement exists, drop it.
            pass
        changed += 1
    return nl.join(out), changed


def repair_missing_outer_enumerate(text: str) -> tuple[str, int]:
    begins = len(re.findall(r"\\begin\{enumerate\}", text))
    ends = len(re.findall(r"\\end\{enumerate\}", text))
    if ends <= begins:
        return text, 0
    nl = nl_of(text)
    lines = text.split(nl)
    depth = 0
    for idx, line in enumerate(lines):
        depth += line.count(r"\begin{enumerate}")
        if depth == 0 and re.match(r"^\s*\\item\b", line):
            lines.insert(idx, r"\begin{enumerate}")
            return nl.join(lines), 1
        depth -= line.count(r"\end{enumerate}")
    return text, 0


def process_file(path: Path) -> tuple[str, list[str]]:
    text = read(path)
    actions: list[str] = []
    new, n = repair_return_links(text)
    if n:
        actions.append(f"return-links:{n}")
    text = new
    new, n = repair_bad_stub_titles(text)
    if n:
        actions.append(f"stub-titles:{n}")
    text = new
    if path.name == "index.tex":
        new, n = repair_stale_proofs_notes_inputs(path, text)
        if n:
            actions.append(f"stale-proof-routes:{n}")
        text = new
    new, n = repair_missing_outer_enumerate(text)
    if n:
        actions.append("missing-enumerate:1")
    return new, actions


def repair_breadcrumb_preamble(root: Path, apply: bool) -> int:
    """Ensure a volume repo's shared preamble loads breadcrumb macros."""
    candidates = []
    if re.fullmatch(r"volume-[ivx]+", root.name):
        candidates.append(root.parent / "common" / "volume-preamble.tex")
    candidates.append(root / "common" / "volume-preamble.tex")

    changed = 0
    for preamble in candidates:
        macro = preamble.parent / "breadcrumb-macros.tex"
        if not preamble.exists() or not macro.exists():
            continue
        text = read(preamble)
        if "common/breadcrumb-macros" in text:
            continue
        nl = nl_of(text)
        needle = r"\input{common/boxes}"
        if needle in text:
            new = text.replace(needle, needle + nl + r"\input{common/breadcrumb-macros}", 1)
        else:
            new = text + ("" if text.endswith(("\n", "\r")) else nl) + r"\input{common/breadcrumb-macros}" + nl
        print(f"{'REPAIR' if apply else 'WOULD REPAIR'} {preamble}  (breadcrumb-preamble:1)")
        write(preamble, new, apply)
        changed += 1
    return changed


def main() -> int:
    ap = argparse.ArgumentParser(description="Repair generated LaTeX migration artifacts.")
    ap.add_argument("--root", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    changed = repair_breadcrumb_preamble(root, args.apply)
    for path in sorted(root.rglob("*.tex")):
        if ".git" in path.parts:
            continue
        old = read(path)
        new, actions = process_file(path)
        if not actions or new == old:
            continue
        changed += 1
        rel = path.relative_to(root)
        print(f"{'REPAIR' if args.apply else 'WOULD REPAIR'} {rel}  ({', '.join(actions)})")
        write(path, new, args.apply)

    print(f"\n{'APPLIED' if args.apply else 'DRY-RUN'}: repaired {changed} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
