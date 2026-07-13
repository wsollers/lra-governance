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
SOURCE_VARIANT_NAME_RE = re.compile(r"\\SourceVariantOf\b")
SOURCE_VARIANT_RE = re.compile(
    r"\\SourceVariantOf"
    r"\{(?P<target>(?:def|ax|thm|lem|prop|cor):[^{}]+)\}"
    r"\{(?P<author>[^{}]+)\}"
    r"\{(?P<book>[^{}]+)\}"
    r"\{(?P<kind>source_variant_of|reduces_to)\}",
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
    for _label, start, end in spans:
        for match in SOURCE_VARIANT_NAME_RE.finditer(text, start, end):
            attached.add(match.start())
            full = SOURCE_VARIANT_RE.match(text, match.start())
            if not full:
                findings.append(
                    finding(
                        "source_variant_malformed",
                        r"\SourceVariantOf must have {target}{author}{book}{kind}; kind is source_variant_of or reduces_to.",
                        path,
                        volume_root,
                        _line_at(text, match.start()),
                        "error",
                    )
                )
                continue
            if not full.group("author").strip() or not full.group("book").strip():
                findings.append(
                    finding(
                        "source_variant_missing_source_metadata",
                        r"\SourceVariantOf requires nonempty author and book/source arguments.",
                        path,
                        volume_root,
                        _line_at(text, match.start()),
                        "error",
                    )
                )
    for match in SOURCE_VARIANT_NAME_RE.finditer(text):
        if match.start() in attached:
            continue
        findings.append(
            finding(
                "source_variant_unattached",
                r"\SourceVariantOf must appear immediately after a formal artifact and before the next formal artifact or section.",
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
