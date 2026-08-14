from __future__ import annotations

import sys
from pathlib import Path

from core.finding import Finding, finding
from core.volume import routed_chapter_roots


CONSTITUTION = Path(__file__).resolve().parents[3] / "constitution"
if str(CONSTITUTION) not in sys.path:
    sys.path.insert(0, str(CONSTITUTION))

from auditor.audits.toolkits import (  # noqa: E402
    inventory_chapter_toolkits,
    inventory_findings,
)


def validate(volume_root: Path, files=None) -> list[Finding]:
    """Enforce one complete Toolkit per routed formal-bearing topic."""
    findings: list[Finding] = []
    for chapter in routed_chapter_roots(volume_root):
        for item in inventory_findings(inventory_chapter_toolkits(chapter)):
            path = chapter / item.get("file", "")
            details = item.get("message", "Toolkit coverage violation.")
            missing = item.get("covers") or []
            if missing:
                details += " Missing labels: " + ", ".join(missing) + "."
            findings.append(
                finding(
                    item.get("type", "toolkit_coverage"),
                    details,
                    path,
                    volume_root,
                    severity="error",
                )
            )
    return findings
