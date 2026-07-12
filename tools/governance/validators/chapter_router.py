from __future__ import annotations

import re
from pathlib import Path

from core.finding import Finding, finding
from core.tex import strip_latex_comment
from core.volume import routed_chapter_roots, latex_input_path


CHAPTER_LINE_RE = re.compile(r"\\chapter(?!\*)(?:\[[^\]]*\])?\{.*\}$")
LABEL_LINE_RE = re.compile(r"\\label\{(?:ch|chap):[a-z0-9-]+\}$")
BREADCRUMB_LINE_RE = re.compile(r"\\breadcrumb\{.*\}\{.*\}\{.*\}\{.*\}$")
LRAMETA_BEGIN_RE = re.compile(r"\\lrameta\{$")
LRA_BREADCRUMB_LINE_RE = re.compile(r"\\LraBreadcrumb$")


def _significant_lines(text: str):
    for line_no, raw in enumerate(text.splitlines(), 1):
        stripped = strip_latex_comment(raw).strip()
        if stripped:
            yield line_no, stripped


def _router_layers(lines: list[tuple[int, str]]) -> list[tuple[int, str]]:
    layers: list[tuple[int, str]] = []
    index = 0
    while index < len(lines):
        line_no, line = lines[index]
        if BREADCRUMB_LINE_RE.fullmatch(line):
            layers.append((line_no, "breadcrumb"))
            index += 1
            continue
        if LRAMETA_BEGIN_RE.fullmatch(line):
            start_line = line_no
            index += 1
            while index < len(lines) and lines[index][1] != "}":
                index += 1
            if index < len(lines) and lines[index][1] == "}":
                index += 1
            if index < len(lines) and LRA_BREADCRUMB_LINE_RE.fullmatch(lines[index][1]):
                layers.append((start_line, "breadcrumb"))
                index += 1
            else:
                layers.append((start_line, "invalid_lrameta_breadcrumb"))
            continue
        layers.append((line_no, line))
        index += 1
    return layers


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    for chapter in routed_chapter_roots(volume_root):
        index = chapter / "index.tex"
        if not index.exists():
            continue
        root = latex_input_path(index).removesuffix("/index")
        required_prefix = [
            ("chapter", CHAPTER_LINE_RE, "non-starred \\chapter{...}"),
            ("label", LABEL_LINE_RE, "\\label{chap:...} or \\label{ch:...}"),
            ("breadcrumb", re.compile(r"^breadcrumb$"), "\\breadcrumb{...}{...}{...}{...} or \\lrameta{...} followed by \\LraBreadcrumb"),
            ("notes_input", re.compile(rf"\\input\{{{re.escape(root)}/notes/index\}}$"), f"\\input{{{root}/notes/index}}"),
            ("exclude_begin", re.compile(r"\\LRAExcludeFromPrintEditionBegin$"), "\\LRAExcludeFromPrintEditionBegin"),
            ("proofs_heading", re.compile(r"\\section\*\{Proofs\}$"), "\\section*{Proofs}"),
            ("proofs_input", re.compile(rf"\\input\{{{re.escape(root)}/proofs/index\}}$"), f"\\input{{{root}/proofs/index}}"),
        ]
        optional_capstone = [
            ("capstone_heading", re.compile(r"\\section\*\{Capstone\}$"), "\\section*{Capstone}"),
            ("capstone_input", re.compile(rf"\\input\{{{re.escape(root)}/proofs/exercises/index\}}$"), f"\\input{{{root}/proofs/exercises/index}}"),
        ]
        exclude_end = [
            ("exclude_end", re.compile(r"\\LRAExcludeFromPrintEditionEnd$"), "\\LRAExcludeFromPrintEditionEnd"),
        ]
        lines = list(_significant_lines(index.read_text(encoding="utf-8", errors="replace")))
        layers = _router_layers(lines)
        expected_without_capstone = required_prefix + exclude_end
        expected_with_capstone = required_prefix + optional_capstone + exclude_end
        if len(layers) == len(expected_with_capstone):
            expected = expected_with_capstone
        elif len(layers) == len(expected_without_capstone):
            expected = expected_without_capstone
        else:
            detail = "; ".join(pattern for _, _, pattern in expected_with_capstone) + " (capstone lines optional)"
            line = layers[min(len(layers), len(expected_with_capstone))][0] if len(layers) > len(expected_with_capstone) else 0
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
        for (line_no, line), (name, pattern, expected_text) in zip(layers, expected):
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
