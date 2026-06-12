r"""Print-edition routing checks.

Chapter routers own the print-edition boundary. Proof and capstone routes are
ordinary ``\input`` lines inside one ``\LRAExcludeFromPrintEditionBegin`` /
``\LRAExcludeFromPrintEditionEnd`` block. Files below ``proofs/`` use ordinary
``\input`` as plain router files.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass
class Finding:
    code: str
    message: str
    severity: str = "error"
    line: int = 0


RAW_INPUT_RE = re.compile(r"\\(?:input|include)\{([^}]+)\}")
LEGACY_INPUT_RE = re.compile(r"\\(?P<macro>LRAProofsInput|LRAExercisesInput|LRACapstoneInput)\{(?P<target>[^}]+)\}")
EXCLUDE_BEGIN_RE = re.compile(r"\\LRAExcludeFromPrintEditionBegin\b")
EXCLUDE_END_RE = re.compile(r"\\LRAExcludeFromPrintEditionEnd\b")


def _line(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def _normalize(target: str) -> str:
    return target.replace("\\", "/").removesuffix(".tex")


def _target_kind(target: str) -> str | None:
    normalized = _normalize(target)
    if normalized.endswith("/proofs/exercises/index"):
        return "exercises_index"
    if normalized.endswith("/proofs/index"):
        return "proofs_index"
    if "/proofs/exercises/capstone-" in normalized:
        return "capstone"
    if "/proofs/exercises/" in normalized:
        return "exercises"
    if "/proofs/" in normalized:
        return "proofs"
    if normalized.endswith("/exercises/index") or "/exercises/" in normalized:
        return "exercises"
    return None


def _posix_path(info) -> str:
    return getattr(info, "path", "").replace("\\", "/")


def _is_chapter_index(info) -> bool:
    return getattr(info, "kind", "") == "chapter_index"


def _in_excluded_span(spans: list[tuple[int, int]], pos: int) -> bool:
    return any(start <= pos <= end for start, end in spans)


def _exclude_spans(text: str) -> tuple[list[tuple[int, int]], list[Finding]]:
    findings: list[Finding] = []
    begins = list(EXCLUDE_BEGIN_RE.finditer(text))
    ends = list(EXCLUDE_END_RE.finditer(text))
    if len(begins) != len(ends):
        findings.append(
            Finding(
                "print_edition_exclusion_unbalanced",
                "Print-edition exclusion blocks must have matching begin and end markers.",
                "error",
                _line(text, (begins + ends)[0].start()) if begins or ends else 0,
            )
        )
        return [], findings
    spans: list[tuple[int, int]] = []
    for begin, end in zip(begins, ends):
        if end.start() < begin.end():
            findings.append(
                Finding(
                    "print_edition_exclusion_misordered",
                    "\\LRAExcludeFromPrintEditionEnd appears before its begin marker.",
                    "error",
                    _line(text, end.start()),
                )
            )
            continue
        spans.append((begin.start(), end.end()))
    return spans, findings


def check(text: str, info, ctx) -> Iterable[Finding]:
    is_chapter_index = _is_chapter_index(info)
    spans, span_findings = _exclude_spans(text)

    for item in span_findings:
        yield item

    for match in LEGACY_INPUT_RE.finditer(text):
        macro = match.group("macro")
        yield Finding(
            "legacy_print_edition_input_macro",
            f"\\{macro} is retired; use ordinary \\input{{...}} and place chapter proof/capstone routes inside the print-edition exclusion block.",
            "error",
            _line(text, match.start()),
        )

    if not is_chapter_index:
        for match in EXCLUDE_BEGIN_RE.finditer(text):
            yield Finding(
                "print_edition_exclusion_not_chapter_index",
                "Print-edition exclusion blocks belong only in the chapter index router.",
                "error",
                _line(text, match.start()),
            )
        for match in EXCLUDE_END_RE.finditer(text):
            yield Finding(
                "print_edition_exclusion_not_chapter_index",
                "Print-edition exclusion blocks belong only in the chapter index router.",
                "error",
                _line(text, match.start()),
            )
        return

    raw_matches = list(RAW_INPUT_RE.finditer(text))
    has_print_sensitive_route = any(_target_kind(match.group(1)) is not None for match in raw_matches)
    if not spans and not has_print_sensitive_route:
        return

    if len(spans) != 1:
        yield Finding(
            "print_edition_exclusion_block_count",
            "Chapter index must contain exactly one print-edition exclusion block wrapping proofs and capstone routes.",
            "error",
            _line(text, spans[0][0]) if spans else 0,
        )

    for match in raw_matches:
        target = match.group(1)
        kind = _target_kind(target)
        if kind is not None:
            if not _in_excluded_span(spans, match.start()):
                yield Finding(
                    "print_edition_chapter_input_outside_exclusion",
                    f"Chapter index routes {target} outside the print-edition exclusion block.",
                    "error",
                    _line(text, match.start()),
                )
