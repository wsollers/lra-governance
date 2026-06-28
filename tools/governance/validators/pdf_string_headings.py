from __future__ import annotations

import re
from pathlib import Path

from core.file_inventory import validator_files
from core.finding import Finding, finding
from core.tex import read_text, strip_latex_comments


HEADING_RE = re.compile(
    r"\\(?P<command>chapter|section|subsection|subsubsection)\*?(?:\[[^\]]*\])?\{(?P<title>[^\n]*)"
)
TEXORPDFSTRING_RE = re.compile(r"\\texorpdfstring\{.*\}\{(?P<pdf>[^{}]*)\}")
UNSAFE_PDF_TOKENS = ("$", "^", "_", "\\")


def validate(volume_root: Path, files=None) -> list[Finding]:
    findings: list[Finding] = []
    for tex in validator_files(volume_root, files):
        _validate_file(volume_root, tex, findings)
    return findings


def _validate_file(volume_root: Path, path: Path, findings: list[Finding]) -> None:
    text = strip_latex_comments(read_text(path))
    for match in HEADING_RE.finditer(text):
        title = match.group("title")
        line = text.count("\n", 0, match.start()) + 1
        command = match.group("command")
        pdf_match = TEXORPDFSTRING_RE.search(title)
        if pdf_match:
            pdf_title = pdf_match.group("pdf")
            if any(token in pdf_title for token in UNSAFE_PDF_TOKENS):
                findings.append(
                    finding(
                        "heading_pdf_string_not_plain_text",
                        f"\\{command} \\texorpdfstring alternate must be plain bookmark text without TeX math tokens.",
                        path,
                        volume_root,
                        line,
                    )
                )
            continue
        if "$" in title or r"\(" in title or r"\)" in title:
            findings.append(
                finding(
                    "heading_math_requires_pdf_string",
                    f"\\{command} title contains math; wrap the title with \\texorpdfstring{{...}}{{plain PDF bookmark text}}.",
                    path,
                    volume_root,
                    line,
                )
            )
