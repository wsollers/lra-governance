from __future__ import annotations

from pathlib import Path

from core.formal_blocks import formal_blocks_for_file
from core.finding import Finding, finding
from core.file_inventory import validator_files


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    for tex in validator_files(volume_root, files):
        _validate_file(volume_root, tex, findings)
    return findings


def _validate_file(volume_root: Path, path: Path, findings: list[Finding]) -> None:
    for block in formal_blocks_for_file(path):
        if "interpretation" in block.decoration.lower():
            continue
        findings.append(
            finding(
                "missing_interpretation",
                "Interpretation remark is missing.",
                path,
                volume_root,
                block.line,
            )
        )
