from __future__ import annotations

from pathlib import Path

from core.finding import Finding, finding
from core.tex import INPUT_RE, line_at, read_text, strip_latex_comments
from core.file_inventory import validator_files


def validate(volume_root: Path, files=None) -> list[Finding]:
    findings: list[Finding] = []
    for tex in validator_files(volume_root, files):
        _validate_file(volume_root, tex, findings)
    return findings


def _validate_file(volume_root: Path, path: Path, findings: list[Finding]) -> None:
    text = strip_latex_comments(read_text(path))
    for match in INPUT_RE.finditer(text):
        target = match.group(1).strip()
        if not target or target.startswith(("http://", "https://")):
            continue
        if not _resolves_input(volume_root, path, target):
            findings.append(
                finding(
                    "missing_input_target",
                    f"Input target does not resolve to a .tex file: {target}.",
                    path,
                    volume_root,
                    line_at(text, match.start()),
                )
            )


def _resolves_input(volume_root: Path, source: Path, target: str) -> bool:
    target_path = Path(target.replace("\\", "/"))
    suffixes: list[str | None]
    if target_path.suffix == ".tex":
        suffixes = [None]
    else:
        suffixes = [".tex"]

    bases: list[Path]
    if target_path.is_absolute():
        bases = [Path()]
    else:
        bases = [
            source.parent,
            volume_root,
            volume_root.parent,
        ]

    for base in bases:
        candidate = base / target_path
        for suffix in suffixes:
            resolved = candidate if suffix is None else candidate.with_suffix(suffix)
            if resolved.is_file():
                return True
    return False
