from __future__ import annotations

import re
from pathlib import Path

from core.finding import Finding, finding
from core.tex import strip_latex_comment
from core.volume import chapter_roots, latex_input_path


CHAPTER_LINE_RE = re.compile(r"\\chapter(?!\*)(?:\[[^\]]*\])?\{.*\}$")
LABEL_LINE_RE = re.compile(r"\\label\{(?:ch|chap):[a-z0-9-]+\}$")
BREADCRUMB_LINE_RE = re.compile(r"\\breadcrumb\{.*\}\{.*\}\{.*\}\{.*\}$")


def _significant_lines(text: str):
    for line_no, raw in enumerate(text.splitlines(), 1):
        stripped = strip_latex_comment(raw).strip()
        if stripped:
            yield line_no, stripped


def validate(volume_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for chapter in chapter_roots(volume_root):
        index = chapter / "index.tex"
        if not index.exists():
            continue
        root = latex_input_path(index).removesuffix("/index")
        expected = [
            ("chapter", CHAPTER_LINE_RE, "non-starred \\chapter{...}"),
            ("label", LABEL_LINE_RE, "\\label{chap:...} or \\label{ch:...}"),
            ("breadcrumb", BREADCRUMB_LINE_RE, "\\breadcrumb{...}{...}{...}{...}"),
            ("notes_input", re.compile(rf"\\input\{{{re.escape(root)}/notes/index\}}$"), f"\\input{{{root}/notes/index}}"),
            ("exclude_begin", re.compile(r"\\LRAExcludeFromPrintEditionBegin$"), "\\LRAExcludeFromPrintEditionBegin"),
            ("proofs_heading", re.compile(r"\\section\*\{Proofs\}$"), "\\section*{Proofs}"),
            ("proofs_input", re.compile(rf"\\input\{{{re.escape(root)}/proofs/index\}}$"), f"\\input{{{root}/proofs/index}}"),
            ("capstone_heading", re.compile(r"\\section\*\{Capstone\}$"), "\\section*{Capstone}"),
            ("capstone_input", re.compile(rf"\\input\{{{re.escape(root)}/proofs/exercises/index\}}$"), f"\\input{{{root}/proofs/exercises/index}}"),
            ("exclude_end", re.compile(r"\\LRAExcludeFromPrintEditionEnd$"), "\\LRAExcludeFromPrintEditionEnd"),
        ]
        lines = list(_significant_lines(index.read_text(encoding="utf-8", errors="replace")))
        if len(lines) != len(expected):
            detail = "; ".join(pattern for _, _, pattern in expected)
            line = lines[min(len(lines), len(expected))][0] if len(lines) > len(expected) else 0
            findings.append(
                finding(
                    "chapter_router_shape",
                    f"Chapter router must contain exactly this skeleton, with no extra rendered content: {detail}.",
                    index,
                    volume_root,
                    line,
                    "warning",
                )
            )
            continue
        for (line_no, line), (name, pattern, expected_text) in zip(lines, expected):
            if not pattern.fullmatch(line):
                findings.append(
                    finding(
                        "chapter_router_shape",
                        f"Chapter router layer {name} should be {expected_text}.",
                        index,
                        volume_root,
                        line_no,
                        "warning",
                    )
                )
    return findings
