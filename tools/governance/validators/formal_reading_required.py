from __future__ import annotations

import re
import os
from pathlib import Path

from core.formal_blocks import formal_blocks_for_file
from core.finding import Finding, finding
from core.file_inventory import validator_files
from formal_reading import find_triggers, has_formal_reading, is_marked_simple, load_concept_surface_forms


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    surface_forms = _surface_forms(volume_root)
    for tex in validator_files(volume_root, files):
        _validate_file(volume_root, tex, surface_forms, findings)
    return findings


def _validate_file(volume_root: Path, path: Path, surface_forms: list[str], findings: list[Finding]) -> None:
    for block in formal_blocks_for_file(path):
        triggers = find_triggers(block.body, surface_forms)
        unique = sorted(set(triggers))
        if is_marked_simple(block.body + block.decoration):
            if triggers:
                findings.append(
                    finding(
                        "simple_but_triggers",
                        f"Marked simple but invokes {unique[:4]}; logic or registered concepts mean it is not simple.",
                        path,
                        volume_root,
                        block.line,
                    )
                )
        if not has_formal_reading(block.decoration):
            findings.append(
                finding(
                    "formal_reading_missing",
                    "Formal statement has no Standard quantified statement formal reading.",
                    path,
                    volume_root,
                    block.line,
                )
            )


def _surface_forms(volume_root: Path) -> list[str]:
    for root in _candidate_canonical_dirs(volume_root):
        if (root / "predicates.yaml").exists() or (root / "structures.yaml").exists():
            forms, _report = load_concept_surface_forms(root)
            return forms
    return []


def _candidate_canonical_dirs(volume_root: Path):
    volume_root = volume_root.resolve()
    repo_root = volume_root.parent
    env_root = os.environ.get("LRA_GOVERNANCE_ROOT")
    if env_root:
        yield Path(env_root).resolve()
    yield repo_root
    yield repo_root.parent / "lra-governance"
    yield repo_root / "canonical"
    yield repo_root / "docs" / "canonical"
    yield repo_root.parent / "Learning-Real-Analysis"
    yield repo_root.parent / "Learning-Real-Analysis" / "canonical"
