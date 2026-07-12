from __future__ import annotations

import json
from pathlib import Path

from core.finding import Finding, finding
from core.tex import INPUT_RE, read_text, strip_latex_comments


DEDICATION_INPUT = "common/dedication"


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    registry = _registry_for(volume_root)
    if registry is None:
        return findings

    _validate_common_file(volume_root, findings)
    roots = [volume_root.parent / f"{volume_root.name}.tex"]
    for book in registry.get("books", []):
        root_name = book.get("tex_root")
        if isinstance(root_name, str):
            roots.append(volume_root.parent / root_name)
    for root in roots:
        _validate_root(volume_root, root, findings)
    return findings


def _registry_for(volume_root: Path) -> dict | None:
    path = Path(__file__).resolve().parents[3] / "docs" / "architecture" / "book-registry.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    roman = volume_root.name.removeprefix("volume-")
    for volume in data.get("volumes", []):
        if volume.get("roman") == roman:
            return volume
    return None


def _validate_common_file(volume_root: Path, findings: list[Finding]) -> None:
    workspace = volume_root.parent.parent
    common_file = workspace / "lra-common" / "common" / "dedication.tex"
    if not common_file.is_file():
        return
    text = strip_latex_comments(read_text(common_file)).strip()
    if not text:
        findings.append(
            finding(
                "empty_common_dedication_page",
                "common/dedication.tex must not be empty.",
                common_file,
                volume_root,
            )
        )


def _validate_root(volume_root: Path, root: Path, findings: list[Finding]) -> None:
    if not root.is_file():
        return
    text = strip_latex_comments(read_text(root))
    targets = [match.group(1).replace("\\", "/").removesuffix(".tex") for match in INPUT_RE.finditer(text)]
    count = targets.count(DEDICATION_INPUT)
    if count != 1:
        findings.append(
            finding(
                "dedication_input_count",
                f"{root.name} must input {DEDICATION_INPUT} exactly once; found {count}.",
                root,
                volume_root,
            )
        )
        return
    dedication_pos = text.find(r"\input{common/dedication}")
    frontmatter_pos = text.find(r"\LRAFrontMatterPage")
    toc_pos = text.find(r"\tableofcontents")
    if frontmatter_pos < 0:
        return
    if dedication_pos < frontmatter_pos:
        findings.append(
            finding(
                "dedication_before_frontmatter",
                f"{root.name} must place {DEDICATION_INPUT} after \\LRAFrontMatterPage.",
                root,
                volume_root,
                _line_for_pos(text, dedication_pos),
            )
        )
    if toc_pos >= 0 and dedication_pos > toc_pos:
        findings.append(
            finding(
                "dedication_after_toc",
                f"{root.name} must place {DEDICATION_INPUT} before \\tableofcontents.",
                root,
                volume_root,
                _line_for_pos(text, dedication_pos),
            )
        )


def _line_for_pos(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1
