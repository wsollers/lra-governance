from __future__ import annotations

import re
from pathlib import Path

from core.finding import Finding, finding
from core.file_inventory import reachable_files
from core.tex import input_targets, read_text, strip_latex_comment
from core.volume import chapter_roots, latex_input_path


TCOLORBOX_RE = re.compile(r"\\begin\{tcolorbox\}")
INPUT_ORDER_RE = re.compile(r"\\(?:input|include)\{([^}]+)\}")


def validate(volume_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for chapter in chapter_roots(volume_root):
        included = reachable_files(chapter)
        capstone = chapter / "proofs" / "exercises" / f"capstone-{chapter.name}.tex"
        if capstone.exists() and capstone.resolve() in included:
            _validate_capstone_file(volume_root, chapter, capstone, findings)
        exercise_index = chapter / "proofs" / "exercises" / "index.tex"
        if exercise_index.exists() and exercise_index.resolve() in included and capstone.exists() and capstone.resolve() in included:
            _validate_capstone_route(volume_root, chapter, exercise_index, capstone, findings)
    return findings


def _validate_capstone_file(volume_root: Path, chapter: Path, capstone: Path, findings: list[Finding]) -> None:
    text = read_text(capstone)
    for token, code in [
        ("\\newpage", "missing_capstone_newpage"),
        ("\\phantomsection", "missing_capstone_phantomsection"),
        (f"\\label{{cap:{chapter.name}}}", "missing_capstone_label"),
        ("\\begin{tcolorbox}", "missing_capstone_box"),
        ("Problem", "missing_capstone_problem"),
        ("\\begin{remark*}[Dependency ceiling]", "missing_capstone_dependency_ceiling"),
    ]:
        if token not in text:
            findings.append(finding(code, f"Capstone missing {token}.", capstone, volume_root))

    if len(TCOLORBOX_RE.findall(text)) != 1:
        findings.append(
            finding("invalid_capstone_box_count", "Capstone must contain exactly one problem tcolorbox.", capstone, volume_root)
        )

    order = [
        ("newpage", text.find("\\newpage")),
        ("phantomsection", text.find("\\phantomsection")),
        ("capstone_label", text.find(f"\\label{{cap:{chapter.name}}}")),
        ("capstone_box", text.find("\\begin{tcolorbox}")),
        ("dependency_ceiling", text.find("\\begin{remark*}[Dependency ceiling]")),
    ]
    present = [(name, pos) for name, pos in order if pos >= 0]
    for (left_name, left_pos), (right_name, right_pos) in zip(present, present[1:]):
        if right_pos < left_pos:
            findings.append(
                finding(
                    "capstone_structure_order",
                    f"{right_name} appears before {left_name}; expected capstone structural order.",
                    capstone,
                    volume_root,
                )
            )


def _validate_capstone_route(volume_root: Path, chapter: Path, index: Path, capstone: Path, findings: list[Finding]) -> None:
    text = read_text(index)
    expected = latex_input_path(capstone)
    targets = input_targets(text)
    if expected not in targets:
        findings.append(
            finding("unrouted_capstone", "Standard capstone is not routed from proofs/exercises/index.tex.", index, volume_root)
        )
        return
    ordered = [match.group(1).replace("\\", "/").removesuffix(".tex") for match in INPUT_ORDER_RE.finditer(text)]
    if ordered and ordered[-1] != expected:
        findings.append(
            finding("capstone_not_last", "Capstone must be the last input in proofs/exercises/index.tex.", index, volume_root)
        )
    for line_no, raw in enumerate(text.splitlines(), 1):
        line = strip_latex_comment(raw).strip()
        if line and not INPUT_ORDER_RE.fullmatch(line):
            findings.append(
                finding(
                    "exercises_index_contains_rendered_content",
                    "proofs/exercises/index.tex must be a router containing only input lines.",
                    index,
                    volume_root,
                    line_no,
                )
            )
