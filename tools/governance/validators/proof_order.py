from __future__ import annotations

import re
from pathlib import Path

from core.finding import Finding, finding
from core.file_inventory import validator_files
from core.tex import INPUT_RE, read_text, strip_latex_comments
from core.volume import routed_chapter_roots, is_ignored


NOTE_FORMAL_RE = re.compile(
    r"\\begin\{(?P<env>theorem|lemma|proposition|corollary)\}(?:\[[^\]]*\])?",
    re.IGNORECASE,
)
LABEL_RE = re.compile(r"\\label\{(?P<label>(?:thm|lem|prop|cor):[A-Za-z0-9-]+)\}")


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    for chapter in routed_chapter_roots(volume_root):
        _validate_chapter(volume_root, chapter, findings, files)
    return findings


def _validate_chapter(volume_root: Path, chapter: Path, findings: list[Finding], files=None) -> None:
    notes_index = chapter / "notes" / "index.tex"
    proofs_index = chapter / "proofs" / "index.tex"
    notes_inputs = [_routed_topic_name(target) for target in _ordered_inputs(notes_index)]
    routed_proof_inputs = [_routed_topic_name(target) for target in _ordered_inputs(proofs_index)]
    if notes_inputs and routed_proof_inputs and notes_inputs != routed_proof_inputs:
        findings.append(
            finding(
                "proof_topic_order_mismatch",
                "proofs/index.tex topic order must mirror notes/index.tex topic order.",
                proofs_index,
                volume_root,
            )
        )

    proof_label_order = _proof_label_order(chapter, files)
    proofs_root = chapter / "proofs"
    if not proofs_root.exists():
        return
    for topic_dir in sorted(path for path in proofs_root.iterdir() if path.is_dir() and path.name != "exercises"):
        index = topic_dir / "index.tex"
        actual = [f"prf:{Path(target).stem.removeprefix('prf-')}" for target in _ordered_inputs(index)]
        routed_roots = {label.split(":", 1)[1] for label in actual}
        expected = [label for label in proof_label_order if label.split(":", 1)[1] in routed_roots]
        if expected and actual and actual != expected:
            findings.append(
                finding(
                    "proof_file_order_mismatch",
                    "Proof files must be routed in source theorem order.",
                    index,
                    volume_root,
                    severity="warning",
                )
            )


def _proof_label_order(chapter: Path, files=None) -> list[str]:
    labels: list[tuple[str, Path, int]] = []
    notes_root = chapter / "notes"
    if not notes_root.exists():
        return []
    for tex in validator_files(notes_root, files):
        if is_ignored(tex, chapter):
            continue
        text = strip_latex_comments(read_text(tex))
        for begin in NOTE_FORMAL_RE.finditer(text):
            env = begin.group("env")
            end = re.search(rf"\\end\{{{re.escape(env)}\}}", text[begin.end():], re.IGNORECASE)
            block_end = begin.end() + end.end() if end else len(text)
            block = text[begin.start():block_end]
            match = LABEL_RE.search(block)
            if match:
                line = text.count("\n", 0, begin.start()) + 1
                labels.append((f"prf:{match.group('label').split(':', 1)[1].casefold()}", tex, line))
    return [label for label, _path, _line in sorted(labels, key=lambda item: (item[1].as_posix(), item[2]))]


def _ordered_inputs(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [
        match.group(1).replace("\\", "/").removesuffix(".tex")
        for match in INPUT_RE.finditer(strip_latex_comments(read_text(path)))
    ]


def _routed_topic_name(target: str) -> str:
    path = Path(target)
    return path.parent.name if path.name == "index" else path.name
