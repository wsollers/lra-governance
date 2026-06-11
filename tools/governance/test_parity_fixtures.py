#!/usr/bin/env python3
"""Parity tests for thin governance validators.

These fixtures lock issue-code coverage before old validators or prompt paths are
retired. They are intentionally code-based rather than snapshotting prose output.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE_ROOT = HERE / "fixtures" / "parity"


def _run_json(args: list[str]) -> dict:
    tmp = HERE.parent.parent / ".test-tmp"
    tmp.mkdir(exist_ok=True)
    out = tmp / "parity-report.json"
    if out.exists():
        out.unlink()
    cmd = [sys.executable, *args, "--json", str(out)]
    proc = subprocess.run(cmd, cwd=HERE, text=True, capture_output=True)
    if proc.returncode not in (0, 1, 2) or not out.exists():
        raise AssertionError(
            f"command failed with {proc.returncode}: {' '.join(cmd)}\n"
            f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    data = json.loads(out.read_text(encoding="utf-8"))
    out.unlink()
    return data


def _run_stdout_json(args: list[str]) -> dict:
    cmd = [sys.executable, *args]
    proc = subprocess.run(cmd, cwd=HERE, text=True, capture_output=True)
    if proc.returncode not in (0, 1, 2):
        raise AssertionError(
            f"command failed with {proc.returncode}: {' '.join(cmd)}\n"
            f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return json.loads(proc.stdout)


def _codes_from_decoration(report: dict) -> set[str]:
    return {record["code"] for record in report["records"]}


def _codes_from_audits(report: dict) -> set[str]:
    codes: set[str] = set()
    for audit in report["audits"]:
        codes.update(finding["code"] for finding in audit["findings"])
    return codes


def _assert_subset(kind: str, expected: list[str], actual: set[str]) -> None:
    missing = sorted(set(expected) - actual)
    assert not missing, f"{kind} missing expected parity code(s): {missing}; actual={sorted(actual)}"


def test_parity_fixtures_cover_expected_codes():
    manifest = json.loads((FIXTURE_ROOT / "manifest.json").read_text(encoding="utf-8"))
    for fixture in manifest["fixtures"]:
        root = FIXTURE_ROOT / fixture["root"]
        chapter = fixture["chapter"]
        expected = fixture["validators"]

        decoration = _run_json([
            "validate_decoration.py",
            "--root", str(root),
            "--chapter", chapter,
        ])
        _assert_subset("decoration", expected["decoration"], _codes_from_decoration(decoration))

        proof_layout = _run_stdout_json([
            "audit_proof_layout.py",
            "--root", str(root),
            "--chapter", chapter,
            "--format", "json",
            "--strict",
        ])
        _assert_subset("proof_layout", expected["proof_layout"], _codes_from_audits(proof_layout))

        volume_layout = _run_stdout_json([
            "audit_volume_layout.py",
            "--root", str(root),
            "--chapter", chapter,
            "--format", "json",
            "--strict",
        ])
        _assert_subset("volume_layout", expected["volume_layout"], _codes_from_audits(volume_layout))


if __name__ == "__main__":
    try:
        test_parity_fixtures_cover_expected_codes()
        print("PASS test_parity_fixtures_cover_expected_codes")
        print("\n1/1 passed")
    except AssertionError as exc:
        print(f"FAIL test_parity_fixtures_cover_expected_codes: {exc}")
        print("\n0/1 passed")
        raise SystemExit(1)
