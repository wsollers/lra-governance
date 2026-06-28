from __future__ import annotations

import re
from pathlib import Path

from core.file_inventory import validator_files
from core.finding import Finding, finding
from core.tex import read_text, strip_latex_comments


CAPTIONOF_RE = re.compile(r"\\captionof\{figure\}")
FIG_LABEL_RE = re.compile(r"\\label\{fig:[^{}]+\}")
CAPTION_RE = re.compile(r"\\caption(?:\[[^\]]*\])?\{")
LOCAL_CONTAINER_RE = re.compile(r"\\begin\{(?:figure|minipage)\}")


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    for tex in validator_files(volume_root, files):
        _validate_file(volume_root, tex, findings)
    return findings


def _validate_file(volume_root: Path, path: Path, findings: list[Finding]) -> None:
    text = strip_latex_comments(read_text(path))
    for match in CAPTIONOF_RE.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        findings.append(
            finding(
                "captionof_figure_not_allowed",
                "Use a non-floating minipage with \\captionsetup{type=figure,hypcap=false} and \\caption instead of \\captionof{figure}.",
                path,
                volume_root,
                line,
            )
        )

    for match in FIG_LABEL_RE.finditer(text):
        prefix = text[: match.start()]
        last_caption = _last_match_start(CAPTION_RE, prefix)
        last_label = _last_match_start(FIG_LABEL_RE, prefix)
        last_container = _last_match_start(LOCAL_CONTAINER_RE, prefix)
        if last_caption >= 0 and last_caption > last_label and last_caption > last_container:
            continue
        line = text.count("\n", 0, match.start()) + 1
        findings.append(
            finding(
                "figure_label_without_local_caption",
                "Figure labels must immediately belong to a local \\caption in the same figure/minipage block.",
                path,
                volume_root,
                line,
            )
        )


def _last_match_start(pattern: re.Pattern[str], text: str) -> int:
    last = -1
    for match in pattern.finditer(text):
        last = match.start()
    return last
