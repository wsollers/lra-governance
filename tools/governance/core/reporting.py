from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .finding import Finding


def print_report(title: str, findings: list[Finding]) -> None:
    sev = Counter(finding.severity for finding in findings)
    print(
        f"{title}: {len(findings)} issue(s) "
        f"[{sev.get('error', 0)} error, {sev.get('warning', 0)} warning, {sev.get('review', 0)} review]"
    )
    by_file: dict[str, list[Finding]] = {}
    for item in findings:
        by_file.setdefault(item.path, []).append(item)
    for path in sorted(by_file):
        print(f"\n  {path}")
        for item in sorted(by_file[path], key=lambda finding: (finding.line, finding.code)):
            print(f"    L{item.line:<4} {item.severity:<7} {item.code}: {item.message}")
    if not findings:
        print("\n  clean.")


def write_json_report(path: Path, volume_root: Path, findings: list[Finding]) -> None:
    records = [finding.__dict__ for finding in findings]
    path.write_text(
        json.dumps({"volume_root": str(volume_root), "records": records}, indent=2) + "\n",
        encoding="utf-8",
    )
