from __future__ import annotations

from pathlib import Path

from core.finding import Finding, finding
from core.tex import read_text
from core.volume import chapter_roots, is_ignored
from rules.routing import print_edition_inputs


class FileInfo:
    def __init__(self, path: Path, kind: str):
        self.path = str(path)
        self.kind = kind


def validate(volume_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for chapter in chapter_roots(volume_root):
        for tex in sorted(chapter.rglob("*.tex")):
            if is_ignored(tex, volume_root):
                continue
            kind = "chapter_index" if tex == chapter / "index.tex" else "other"
            info = FileInfo(tex, kind)
            text = read_text(tex)
            for item in print_edition_inputs.check(text, info, None):
                findings.append(
                    finding(item.code, item.message, tex, volume_root, item.line, item.severity)
                )
    return findings
