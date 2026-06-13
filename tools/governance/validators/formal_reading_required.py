from __future__ import annotations

import re
from pathlib import Path

from core.finding import Finding, finding
from core.tex import read_text, strip_latex_comments
from core.file_inventory import files_to_validate
from formal_reading import find_triggers, has_formal_reading, is_marked_simple, load_concept_surface_forms


FORMAL_RE = re.compile(
    r"\\begin\{(?P<env>definition|axiom|theorem|lemma|proposition|corollary)\}"
    r"(?:\[(?P<title>[^\]]*)\])?",
    re.IGNORECASE,
)


def validate(volume_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    surface_forms = _surface_forms(volume_root)
    for tex in files_to_validate([volume_root]):
        _validate_file(volume_root, tex, surface_forms, findings)
    return findings


def _validate_file(volume_root: Path, path: Path, surface_forms: list[str], findings: list[Finding]) -> None:
    text = strip_latex_comments(read_text(path))
    blocks = list(_formal_blocks(text))
    for index, (begin, end_pos) in enumerate(blocks):
        next_pos = blocks[index + 1][0].start() if index + 1 < len(blocks) else len(text)
        block_text = text[begin.start():end_pos]
        decoration = text[end_pos:next_pos]
        triggers = find_triggers(block_text, surface_forms)
        if not triggers:
            continue
        line = text.count("\n", 0, begin.start()) + 1
        unique = sorted(set(triggers))
        if is_marked_simple(block_text + decoration):
            findings.append(
                finding(
                    "simple_but_triggers",
                    f"Marked simple but invokes {unique[:4]}; logic or registered concepts mean it is not simple.",
                    path,
                    volume_root,
                    line,
                )
            )
        elif not has_formal_reading(decoration):
            findings.append(
                finding(
                    "formal_reading_missing",
                    f"Statement invokes {unique[:4]} but has no Standard quantified statement formal reading.",
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


def _surface_forms(volume_root: Path) -> list[str]:
    for root in _candidate_canonical_dirs(volume_root):
        if (root / "predicates.yaml").exists() or (root / "structures.yaml").exists():
            forms, _report = load_concept_surface_forms(root)
            return forms
    return []


def _candidate_canonical_dirs(volume_root: Path):
    volume_root = volume_root.resolve()
    repo_root = volume_root.parent
    yield repo_root
    yield repo_root / "canonical"
    yield repo_root / "docs" / "canonical"
    yield repo_root.parent / "Learning-Real-Analysis"
    yield repo_root.parent / "Learning-Real-Analysis" / "canonical"
