from __future__ import annotations

import re
from pathlib import Path

from core.finding import Finding, finding
from core.tex import line_at, read_text, strip_latex_comments


FORMAL_BEGIN_RE = re.compile(
    r"\\begin\{(?P<env>definition|axiom|theorem|lemma|proposition|corollary)\*?\}"
    r"(?P<title>\[[^\]]+\])?",
    re.IGNORECASE,
)


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    for path in files:
        if path.suffix != ".tex":
            continue
        text = strip_latex_comments(read_text(path))
        for match in FORMAL_BEGIN_RE.finditer(text):
            title = match.group("title")
            if title and title[1:-1].strip():
                continue
            findings.append(
                finding(
                    "formal_environment_missing_name",
                    "Definition, axiom, and theorem-like environments must have a bracketed display name.",
                    path,
                    volume_root,
                    line_at(text, match.start()),
                    "error",
                )
            )
    return findings
