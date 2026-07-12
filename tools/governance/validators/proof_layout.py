from __future__ import annotations

from pathlib import Path
from typing import Iterable

from core.finding import Finding, finding
from core.volume import routed_chapter_roots

import audit_proof_layout


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _live_note_topics(chapter_root: Path, files: list[Path]) -> dict[str, str]:
    topics: dict[str, str] = {}
    notes_root = chapter_root / "notes"
    for path in files:
        if not _is_under(path, notes_root):
            continue
        if path.name == "index.tex":
            continue
        topic = audit_proof_layout.topic_after("notes", path, chapter_root)
        if not topic:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for label in audit_proof_layout.THEOREM_LABEL_RE.findall(text):
            topics[label] = topic
    return topics


def _live_proof_files(chapter_root: Path, files: list[Path]) -> list[Path]:
    proofs_root = chapter_root / "proofs"
    proof_files: list[Path] = []
    for path in files:
        if not _is_under(path, proofs_root):
            continue
        if path.name == "index.tex":
            continue
        try:
            rel_parts = path.relative_to(proofs_root).parts
        except ValueError:
            continue
        if rel_parts and rel_parts[0] == "exercises":
            continue
        proof_files.append(path)
    return sorted(proof_files)


def validate(volume_root: Path, files: Iterable[Path]) -> list[Finding]:
    findings: list[Finding] = []
    chapters = routed_chapter_roots(volume_root)
    inventory = [Path(path).resolve() for path in files]
    audits = []
    root = volume_root.resolve()
    for chapter_root in chapters:
        notes = _live_note_topics(chapter_root, inventory)
        for path in _live_proof_files(chapter_root, inventory):
            audits.append(audit_proof_layout.audit_proof(path, chapter_root, root, notes, False))

    for audit in audits:
        for item in audit.findings:
            findings.append(
                finding(
                    item.code,
                    item.message,
                    volume_root / audit.path,
                    volume_root,
                    0,
                    item.severity,
                )
            )
    return findings
