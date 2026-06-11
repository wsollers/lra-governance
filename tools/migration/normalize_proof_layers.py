#!/usr/bin/env python3
r"""Normalize proof layer headings in volume proof files.

The canonical proof-layer shape is:

    \begin{proof}[Professional Standard Proof]
    \LRAProofBodyStart
    ...
    \end{proof}

and similarly for the Detailed Learning Proof layer. This script is
idempotent: it adds the body-start macro only when absent and converts the
legacy bold-heading forms without touching authored proof prose.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

UNTITLED_LAYER_RE = re.compile(
    r"\\begin\{proof\}(?P<ws>\s*)"
    r"\\textbf\{(?P<title>Professional Standard Proof|Detailed Learning Proof)\.\}~\\\\(?P<after>[ \t]*\r?\n)",
    re.MULTILINE,
)
STANDALONE_DETAILED_RE = re.compile(
    r"(?P<indent>[ \t]*)\\textbf\{Detailed Learning Proof\.\}~\\\\(?P<after>[ \t]*\r?\n)",
    re.MULTILINE,
)
STANDALONE_PROFESSIONAL_BEFORE_PROOF_RE = re.compile(
    r"(?P<indent>[ \t]*)\\textbf\{Professional Standard Proof\.\}~\\\\(?P<after>[ \t]*\r?\n)"
    r"(?P<comments>(?:[ \t]*%[^\r\n]*(?:\r?\n))*)"
    r"[ \t]*\\begin\{proof\}(?P<proof_after>[ \t]*\r?\n)"
    r"(?:[ \t]*\[Proof \(Professional Standard\)\][ \t]*(?:\r?\n))?"
)
TITLED_PROOF_RE = re.compile(
    r"\\begin\{proof\}\[(?P<title>Professional Standard Proof|Detailed Learning Proof)\]"
    r"(?P<after>[ \t]*\r?\n)(?![ \t]*\\LRAProofBodyStart(?:\r?\n|$))"
)
NESTED_DETAILED_PSEUDO_PROOF_RE = re.compile(
    r"(?P<head>\\begin\{proof\}\[Detailed Learning Proof\][ \t]*\r?\n"
    r"\\LRAProofBodyStart[ \t]*\r?\n)"
    r"(?:[ \t]*% MIGRATION TODO:[^\r\n]*(?:\r?\n))?"
    r"(?:[ \t]*TODO: Expand the professional proof into a detailed learning proof\.[ \t]*(?:\r?\n)+)?"
    r"[ \t]*\\begin\{proof\}\[Proof \(Detailed Learning\)\][ \t]*(?:\r?\n)"
)
PSEUDO_PROOF_TITLE_LINE_RE = re.compile(
    r"^[ \t]*\[Proof \((?:Professional Standard|Detailed Learning)\)\][ \t]*(?:\r?\n)",
    re.MULTILINE,
)
DETAILED_BEGIN = r"\begin{proof}[Detailed Learning Proof]"
DETAILED_CLOSE_DELIM_RE = re.compile(
    r"\n(?=\\begin\{remark\*\}\[(?:Proof structure|Dependencies)\]|\\begin\{dependencies\}|\\NoLocalDependencies|\\clearpage)"
)


def normalize_text(text: str) -> tuple[str, int]:
    changed = 0

    def standalone_professional_repl(match: re.Match[str]) -> str:
        nonlocal changed
        changed += 1
        nl = match.group("proof_after")
        return (
            match.group("indent")
            + r"\begin{proof}[Professional Standard Proof]"
            + nl
            + match.group("indent")
            + r"\LRAProofBodyStart"
            + nl
            + match.group("comments")
        )

    text = STANDALONE_PROFESSIONAL_BEFORE_PROOF_RE.sub(standalone_professional_repl, text)

    def untitled_layer_repl(match: re.Match[str]) -> str:
        nonlocal changed
        changed += 1
        return (
            rf"\begin{{proof}}[{match.group('title')}]"
            + match.group("after")
            + r"\LRAProofBodyStart"
            + match.group("after")
        )

    text = UNTITLED_LAYER_RE.sub(untitled_layer_repl, text)

    def detailed_repl(match: re.Match[str]) -> str:
        nonlocal changed
        changed += 1
        nl = match.group("after")
        return (
            match.group("indent")
            + r"\begin{proof}[Detailed Learning Proof]"
            + nl
            + match.group("indent")
            + r"\LRAProofBodyStart"
            + nl
        )

    text = STANDALONE_DETAILED_RE.sub(detailed_repl, text)
    text, nested_count = NESTED_DETAILED_PSEUDO_PROOF_RE.subn(r"\g<head>", text)
    changed += nested_count
    text, pseudo_count = PSEUDO_PROOF_TITLE_LINE_RE.subn("", text)
    changed += pseudo_count
    text, close_count = close_standalone_detailed_layers(text)
    changed += close_count

    def body_start_repl(match: re.Match[str]) -> str:
        nonlocal changed
        changed += 1
        return (
            rf"\begin{{proof}}[{match.group('title')}]"
            + match.group("after")
            + r"\LRAProofBodyStart"
            + match.group("after")
        )

    text = TITLED_PROOF_RE.sub(body_start_repl, text)
    return text, changed


def close_standalone_detailed_layers(text: str) -> tuple[str, int]:
    out = []
    pos = 0
    changed = 0
    while True:
        start = text.find(DETAILED_BEGIN, pos)
        if start < 0:
            out.append(text[pos:])
            break
        out.append(text[pos:start])
        delim = DETAILED_CLOSE_DELIM_RE.search(text, start)
        if not delim:
            segment = text[start:]
            if r"\end{proof}" in segment:
                out.append(segment)
            else:
                out.append(segment.rstrip())
                out.append("\n\\end{proof}\n")
                changed += 1
            break
        existing_end = text.find(r"\end{proof}", start, delim.start())
        if existing_end >= 0:
            out.append(text[start:delim.start()])
        else:
            out.append(text[start:delim.start()].rstrip())
            out.append("\n\\end{proof}\n")
            changed += 1
        pos = delim.start()
    return "".join(out), changed


def iter_proof_files(root: Path):
    for path in root.rglob("*.tex"):
        parts = {part.lower() for part in path.parts}
        if "proofs" not in parts:
            continue
        if any(part.startswith("_") for part in path.parts):
            continue
        yield path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Volume root or repository root.")
    parser.add_argument("--apply", action="store_true", help="Write changes.")
    parser.add_argument("--quiet", action="store_true", help="Print only the summary.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    files = touched = replacements = 0
    for path in iter_proof_files(root):
        files += 1
        text = path.read_text(encoding="utf-8", errors="ignore")
        new_text, count = normalize_text(text)
        if not count or new_text == text:
            continue
        touched += 1
        replacements += count
        if not args.quiet:
            print(f"{'WRITE' if args.apply else 'WOULD'} {path} ({count})")
        if args.apply:
            path.write_text(new_text, encoding="utf-8", newline="")
    print(f"{'APPLIED' if args.apply else 'DRY-RUN'}: files={files}, touched={touched}, replacements={replacements}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
