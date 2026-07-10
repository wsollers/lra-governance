from __future__ import annotations

import re
from pathlib import Path

from core.finding import Finding, finding
from core.tex import read_text, strip_latex_comments
from core.file_inventory import validator_files


FORMAL_RE = re.compile(
    r"\\begin\{(?P<env>definition|axiom|theorem|lemma|proposition|corollary)\}"
    r"(?:\[[^\]]*\])?",
    re.IGNORECASE,
)


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    for tex in validator_files(volume_root, files):
        _validate_file(volume_root, tex, findings)
    return findings


def _validate_file(volume_root: Path, path: Path, findings: list[Finding]) -> None:
    text = strip_latex_comments(read_text(path))
    blocks = list(_formal_blocks(text))
    for index, (begin, end_pos) in enumerate(blocks):
        next_pos = blocks[index + 1][0].start() if index + 1 < len(blocks) else len(text)
        decoration = text[end_pos:next_pos]
        if "interpretation" in decoration.lower():
            continue
        line = text.count("\n", 0, begin.start()) + 1
        findings.append(
            finding(
                "missing_interpretation",
                "Interpretation remark is missing.",
                path,
                volume_root,
                line,
            )
        )


def _formal_blocks(text: str):
    for begin in FORMAL_RE.finditer(text):
        env = begin.group("env")
        end = re.search(rf"\\end\{{{re.escape(env)}\}}", text[begin.end():], re.IGNORECASE)
        if end:
            yield begin, begin.end() + end.end()
