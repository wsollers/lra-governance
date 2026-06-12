from __future__ import annotations

from pathlib import Path

from core.finding import Finding, finding
from core.volume import chapter_roots

import audit_proof_layout


def validate(volume_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    chapters = chapter_roots(volume_root)
    summary = audit_proof_layout.audit_root(volume_root, refactor_mode=False, chapters=chapters)
    for audit in summary.audits:
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
