from __future__ import annotations

import re
from pathlib import Path

from core.finding import Finding, finding
from core.file_inventory import files_to_validate
from core.tex import read_text, strip_latex_comments
from core.volume import chapter_roots


PROOF_ENVS = {"theorem", "lemma", "proposition", "corollary"}
NOTE_FORMAL_RE = re.compile(
    r"\\begin\{(?P<env>theorem|lemma|proposition|corollary)\}(?:\[[^\]]*\])?",
    re.IGNORECASE,
)
LABEL_RE = re.compile(r"\\label\{(?P<label>(?:thm|lem|prop|cor):[a-z0-9-]+)\}")
PROOF_LABEL_RE = re.compile(r"\\label\{(?P<label>prf:[a-z0-9-]+)\}")
PROOF_FOR_RE = re.compile(r"\\LRAProofFor\{(?P<label>(?:thm|lem|prop|cor):[a-z0-9-]+)\}")


def validate(volume_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for chapter in chapter_roots(volume_root):
        _validate_chapter(volume_root, chapter, findings)
    return findings


def _validate_chapter(volume_root: Path, chapter: Path, findings: list[Finding]) -> None:
    proof_labels: set[str] = set()
    proof_for_targets: set[str] = set()
    proofs_root = chapter / "proofs"
    if proofs_root.exists():
        for tex in files_to_validate([proofs_root]):
            if "/proofs/exercises/" in f"/{tex.resolve().relative_to(chapter.resolve()).as_posix()}":
                continue
            text = strip_latex_comments(read_text(tex))
            proof_labels.update(match.group("label") for match in PROOF_LABEL_RE.finditer(text))
            proof_for_targets.update(match.group("label") for match in PROOF_FOR_RE.finditer(text))

    notes_root = chapter / "notes"
    if not notes_root.exists():
        return
    for tex in files_to_validate([notes_root]):
        text = strip_latex_comments(read_text(tex))
        for begin in NOTE_FORMAL_RE.finditer(text):
            env = begin.group("env")
            end = re.search(rf"\\end\{{{re.escape(env)}\}}", text[begin.end():], re.IGNORECASE)
            block_end = begin.end() + end.end() if end else len(text)
            block = text[begin.start():block_end]
            labels = LABEL_RE.findall(block)
            if not labels:
                continue
            label = labels[0]
            line = text.count("\n", 0, begin.start()) + 1
            expected_proof = f"prf:{label.split(':', 1)[1]}"
            if expected_proof not in proof_labels:
                findings.append(
                    finding(
                        "missing_proof_file",
                        f"No proof label found for {label}; expected {expected_proof}.",
                        tex,
                        volume_root,
                        line,
                    )
                )
            if label not in proof_for_targets:
                findings.append(
                    finding(
                        "missing_proof_association",
                        f"No proof file declares \\LRAProofFor{{{label}}}.",
                        tex,
                        volume_root,
                        line,
                    )
                )
