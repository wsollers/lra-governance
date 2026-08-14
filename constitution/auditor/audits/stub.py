"""Deterministically audit a planned chapter stub."""

import sys
from pathlib import Path

from auditor import client
from auditor.report import save_audit_report


TOOLS_ROOT = Path(__file__).resolve().parents[3] / "tools" / "governance"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from validators.chapter_stub import validate_chapter  # noqa: E402


def _report_for_findings(chapter: str, findings) -> dict:
    checks = []
    for item in findings:
        status = "FAIL" if item.severity == "error" else "NONCOMPLIANT"
        location = item.path + (f":{item.line}" if item.line else "")
        checks.append(
            {
                "block_id": item.code,
                "requirement": "R",
                "status": status,
                "finding": f"{location}: {item.message}",
            }
        )
    if not checks:
        checks.append(
            {
                "block_id": "chapter_stub_contract",
                "requirement": "R",
                "status": "PASS",
                "finding": "",
            }
        )
    failed = sum(check["status"] == "FAIL" for check in checks)
    noncompliant = sum(check["status"] == "NONCOMPLIANT" for check in checks)
    report = {
        "audit_type": "stub_chapter",
        "artifact_type": "stub_chapter",
        "label": chapter,
        "summary": {
            "total_checks": len(checks),
            "passed": sum(check["status"] == "PASS" for check in checks),
            "failed": failed,
            "noncompliant": noncompliant,
            "conditional_met": 0,
            "conditional_unmet": 0,
            "conditional_violation": 0,
            "dependent_met": 0,
            "dependent_unmet": 0,
            "dependent_violation": 0,
            "forbidden_violation": 0,
            "stub": True,
        },
        "checks": checks,
        "violations": [
            {
                "block_id": check["block_id"],
                "status": check["status"],
                "finding": check["finding"],
            }
            for check in checks
            if check["status"] != "PASS"
        ],
    }
    client.validate_audit_report(report)
    return report


def audit_stub_chapter(
    chapter_path: Path,
    chapter_registry: list[dict] | None = None,
) -> dict:
    """Audit a chapter stub without a model invocation."""
    chapter_path = Path(chapter_path).resolve()
    chapter = chapter_path.name
    report = _report_for_findings(
        chapter,
        validate_chapter(chapter_path, chapter_registry=chapter_registry),
    )
    report["_report_path"] = str(save_audit_report(report, chapter, "audit-stub"))

    return report
