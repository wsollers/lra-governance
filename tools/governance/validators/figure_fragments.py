from __future__ import annotations

import re
from pathlib import Path

from core.finding import Finding, finding
from core.file_inventory import validator_files
from core.tex import line_at, read_text, strip_latex_comments


DOCUMENT_TAGS = (
    r"\documentclass",
    r"\begin{document}",
    r"\end{document}",
    r"\usepackage",
)
BEGIN_FIGURE_RE = re.compile(r"\\begin\{figure\}(?:\[([^\]]*)\])?")
CAPTION_RE = re.compile(r"\\caption(?:\[[^\]]*\])?\{")
LABEL_RE = re.compile(r"\\label\{[^{}]+\}")


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    for fragment in validator_files(volume_root.parent, files):
        parts = fragment.parts
        if len(parts) < 3 or parts[-3:-1] != ("tex", "figures"):
            continue
        _validate_fragment(volume_root, fragment, findings)
    return findings


def _validate_fragment(volume_root: Path, path: Path, findings: list[Finding]) -> None:
    text = strip_latex_comments(read_text(path))

    for tag in DOCUMENT_TAGS:
        index = text.find(tag)
        if index >= 0:
            findings.append(
                finding(
                    "figure_fragment_document_tag",
                    f"Figure fragments under tex/figures must not contain {tag}; keep document scaffolding in tex/figures/_src.",
                    path,
                    volume_root,
                    line_at(text, index),
                )
            )

    if not CAPTION_RE.search(text):
        findings.append(
            finding(
                "figure_fragment_missing_caption",
                "Figure fragments under tex/figures must contain a local \\caption{...}.",
                path,
                volume_root,
            )
        )

    if not LABEL_RE.search(text):
        findings.append(
            finding(
                "figure_fragment_missing_label",
                "Figure fragments under tex/figures must contain a local \\label{...}.",
                path,
                volume_root,
            )
        )

    figure_matches = list(BEGIN_FIGURE_RE.finditer(text))
    if not figure_matches:
        findings.append(
            finding(
                "figure_fragment_missing_figure_environment",
                "Figure fragments under tex/figures must contain a non-floating figure environment.",
                path,
                volume_root,
            )
        )
        return

    for match in figure_matches:
        placement = match.group(1)
        if placement == "H":
            continue
        found = f"[{placement}]" if placement is not None else "no placement"
        findings.append(
            finding(
                "figure_fragment_must_be_nonfloating",
                f"Figure fragments under tex/figures must use \\begin{{figure}}[H]; found {found}.",
                path,
                volume_root,
                line_at(text, match.start()),
            )
        )
