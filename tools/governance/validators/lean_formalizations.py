from __future__ import annotations

import re
from pathlib import Path

from core.finding import Finding, finding
from core.tex import read_text, strip_latex_comments


FORMAL_BEGIN_RE = re.compile(
    r"\\begin\{(?P<env>definition|axiom|theorem|lemma|proposition|corollary)\}"
    r"(?:\[[^\]]*\])?",
    re.IGNORECASE,
)
LABEL_RE = re.compile(r"\\label\{(?P<label>(?:def|ax|thm|lem|prop|cor):[^{}]+)\}")
SECTION_RE = re.compile(r"\\(?:chapter|section|subsection|subsubsection)\*?\{")
LEAN_FORMALIZES_NAME_RE = re.compile(r"\\LeanFormalizes\b")
LEAN_FORMALIZES_RE = re.compile(
    r"\\LeanFormalizes"
    r"\{(?P<label>(?:def|ax|thm|lem|prop|cor):[^{}]+)\}"
    r"\{(?P<repo>[A-Za-z0-9_.-]+)\}"
    r"\{(?P<module>[A-Za-z][A-Za-z0-9_'.]*(?:\.[A-Za-z][A-Za-z0-9_'.]*)*)\}"
    r"\{(?P<decl>[A-Za-z_][A-Za-z0-9_'.]*)\}"
    r"\{(?P<status>checked|statement|pending|incomplete)\}",
    re.IGNORECASE,
)


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    for path in files:
        if path.suffix != ".tex":
            continue
        text = strip_latex_comments(read_text(path))
        _validate_file(volume_root, path, text, findings)
    return findings


def _validate_file(volume_root: Path, path: Path, text: str, findings: list[Finding]) -> None:
    spans = _formal_trailing_windows(text)
    attached = set()
    for attached_label, start, end in spans:
        for match in LEAN_FORMALIZES_NAME_RE.finditer(text, start, end):
            attached.add(match.start())
            full = LEAN_FORMALIZES_RE.match(text, match.start())
            if not full:
                findings.append(
                    finding(
                        "lean_formalizes_malformed",
                        r"\LeanFormalizes must have {label}{repo}{module}{declaration}{status}; status is checked, statement, pending, or incomplete.",
                        path,
                        volume_root,
                        _line_at(text, match.start()),
                        "error",
                    )
                )
                continue
            target_label = full.group("label").strip()
            if target_label != attached_label:
                findings.append(
                    finding(
                        "lean_formalizes_label_mismatch",
                        r"\LeanFormalizes label must match the immediately preceding formal artifact label.",
                        path,
                        volume_root,
                        _line_at(text, match.start()),
                        "error",
                    )
                )
    for match in LEAN_FORMALIZES_NAME_RE.finditer(text):
        if match.start() in attached:
            continue
        findings.append(
            finding(
                "lean_formalizes_unattached",
                r"\LeanFormalizes must appear immediately after a formal artifact and before the next formal artifact or section.",
                path,
                volume_root,
                _line_at(text, match.start()),
                "error",
            )
        )


def _formal_trailing_windows(text: str) -> list[tuple[str, int, int]]:
    windows: list[tuple[str, int, int]] = []
    for begin in FORMAL_BEGIN_RE.finditer(text):
        env = begin.group("env")
        end_match = re.search(rf"\\end\{{{re.escape(env)}\}}", text[begin.end() :], re.IGNORECASE)
        if not end_match:
            continue
        block_end = begin.end() + end_match.end()
        block = text[begin.start() : block_end]
        label = LABEL_RE.search(block)
        if not label:
            continue
        next_formal = FORMAL_BEGIN_RE.search(text, block_end)
        next_section = SECTION_RE.search(text, block_end)
        candidates = [match.start() for match in (next_formal, next_section) if match]
        windows.append((label.group("label"), block_end, min(candidates) if candidates else len(text)))
    return windows


def _line_at(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1
