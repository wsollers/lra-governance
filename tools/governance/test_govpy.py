#!/usr/bin/env python3
"""Tests for the scripts/govpy.py launcher contract.

All tests set GOVPY_NO_BOOTSTRAP=1 so no venv is provisioned during test runs;
the launcher then uses an existing .venv if present or the current interpreter.
"""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVPY = ROOT / "scripts" / "govpy.py"


def run_govpy(args, cwd=None):
    env = {**os.environ, "GOVPY_NO_BOOTSTRAP": "1"}
    return subprocess.run(
        [sys.executable, str(GOVPY), *args],
        cwd=cwd or ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


class GovpyTests(unittest.TestCase):
    def test_forwards_exit_code_and_arguments(self):
        result = run_govpy(["-c", "import sys; sys.exit(7)"])
        self.assertEqual(result.returncode, 7)

    def test_resolves_leading_tool_path_against_governance_root(self):
        # From an unrelated cwd, a root-relative tool path must still resolve.
        result = run_govpy(
            ["capabilities/generate_task_index.py", "--check"],
            cwd=Path(__file__).resolve().parent,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("task index current", result.stdout)

    def test_no_arguments_is_a_usage_error(self):
        result = run_govpy([])
        self.assertEqual(result.returncode, 2)

    def test_help_prints_usage(self):
        result = run_govpy(["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("govpy", result.stdout)

    def test_warns_when_running_outside_the_venv(self):
        if (ROOT / ".venv").exists():
            self.skipTest("a local .venv exists; fallback warning not expected")
        result = run_govpy(["-c", "pass"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("govpy: WARNING", result.stderr)


if __name__ == "__main__":
    unittest.main()
