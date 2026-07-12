from __future__ import annotations

from pathlib import Path

from core.file_inventory import validator_files
from core.finding import Finding, finding
from core.tex import read_text


REPLACEMENTS = {
    "\u2014": "---",
    "\u2013": "--",
    "\u201c": "``",
    "\u201d": "''",
    "\u2019": "'",
    "\u2193": r"$\downarrow$",
    "\u2191": r"$\uparrow$",
    "\u2192": r"$\to$",
    "\u2190": r"$\leftarrow$",
    "\u00b0": r"^\circ",
}


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    for tex in validator_files(volume_root, files):
        _validate_file(volume_root, tex, findings)
    return findings


def _validate_file(volume_root: Path, path: Path, findings: list[Finding]) -> None:
    text = read_text(path)
    for line_number, line in enumerate(text.splitlines(), start=1):
        seen_on_line: set[str] = set()
        for char in line:
            if ord(char) <= 0x7F or char in seen_on_line:
                continue
            seen_on_line.add(char)
            codepoint = f"U+{ord(char):04X}"
            replacement = REPLACEMENTS.get(char)
            if replacement:
                message = f"Non-ASCII TeX character {char!r} ({codepoint}); use {replacement!r}."
            else:
                message = f"Non-ASCII TeX character {char!r} ({codepoint}); use an ASCII LaTeX command or macro."
            findings.append(finding("non_ascii_tex_character", message, path, volume_root, line_number))
