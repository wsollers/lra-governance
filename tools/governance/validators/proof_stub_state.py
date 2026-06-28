from __future__ import annotations

from pathlib import Path

from core.finding import Finding, finding
from core.tex import read_text
from core.file_inventory import validator_files
from rules.proofs import proof_stub_state as proof_stub_rule


class _Info:
    def __init__(self, path: str):
        self.path = path


def validate(volume_root: Path, files=None) -> list[Finding]:
    findings: list[Finding] = []
    for tex in validator_files(volume_root, files):
        rel = tex.resolve().relative_to(volume_root.resolve()).as_posix()
        if "/proofs/" not in f"/{rel}" or "/proofs/exercises/" in f"/{rel}":
            continue
        text = read_text(tex)
        for item in proof_stub_rule.check(text, _Info(rel), None) or []:
            findings.append(
                finding(item.code, item.message, tex, volume_root, item.line, item.severity)
            )
    return findings
