from __future__ import annotations

from pathlib import Path

from core.finding import Finding, finding
from core.tex import read_text, strip_latex_comment
from core.file_inventory import files_to_validate


def validate(volume_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for tex in files_to_validate([volume_root]):
        _validate_file(volume_root, tex, findings)
    return findings


def _validate_file(volume_root: Path, path: Path, findings: list[Finding]) -> None:
    for line_no, raw in enumerate(read_text(path).splitlines(), 1):
        stripped = strip_latex_comment(raw).strip()
        if r"\clearpage" in stripped and stripped != r"\clearpage":
            findings.append(
                finding(
                    "illegal_clearpage_position",
                    r"\clearpage must be a standalone structural command, not embedded in prose or math.",
                    path,
                    volume_root,
                    line_no,
                )
            )
