from __future__ import annotations

import json
import subprocess
import sys
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCOPE_VALIDATOR = ROOT / "tools" / "governance" / "validate_semantic_scope.py"
TEMP_ROOT = ROOT / ".test-tmp" / "semantic-scope"

if str(ROOT / "tools" / "governance") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools" / "governance"))

from test_validate_semantic_logic import CORRECTED_TEX, real_upper_bound_artifact  # noqa: E402


@contextmanager
def temp_dir():
    path = TEMP_ROOT / str(uuid.uuid4())
    path.mkdir(parents=True, exist_ok=True)
    yield path


def write_fake_volume(root: Path) -> Path:
    volume = root / "lra-volume-i"
    target = volume / "volume-i" / "book-order" / "bounds"
    target.mkdir(parents=True)
    (volume / "volume-i-book-order.tex").write_text(
        r"\input{volume-i/book-order/bounds/index}" + "\n",
        encoding="utf-8",
    )
    (target / "index.tex").write_text(
        r"\chapter{Bounds}" + "\n" + r"\input{volume-i/book-order/bounds/routed}" + "\n",
        encoding="utf-8",
    )
    routed_tex = CORRECTED_TEX.replace(
        r"\begin{definition}",
        r"\begin{definition}[Upper Bound in the Real Line]",
    ).replace(
        r"\end{definition}",
        r"\label{def:real-upper-bound}\end{definition}",
    )
    (target / "routed.tex").write_text(routed_tex, encoding="utf-8")
    return volume


class ValidateSemanticScopeTests(unittest.TestCase):
    def test_python_llm_materializes_and_validates_supplied_payload(self):
        with temp_dir() as root:
            volume = write_fake_volume(root)
            llm_dir = root / "llm"
            llm_dir.mkdir()
            payload = {
                "artifact": real_upper_bound_artifact(),
                "corrected_tex": CORRECTED_TEX,
            }
            (llm_dir / "def-real-upper-bound.json").write_text(
                json.dumps(payload, indent=2),
                encoding="utf-8",
            )
            output = root / "scope.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCOPE_VALIDATOR),
                    "--mode",
                    "python-llm",
                    "--repos-root",
                    str(root),
                    "--volume",
                    "i",
                    "--chapter",
                    "bounds",
                    "--llm-data-dir",
                    str(llm_dir),
                    "--format",
                    "json",
                    "--output",
                    str(output),
                ],
                capture_output=True,
                text=True,
            )
            report = json.loads(output.read_text(encoding="utf-8"))
            package = volume / "volume-i" / "book-order" / "bounds" / "def-real-upper-bound"

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(report["result"], "pass")
        self.assertEqual(report["validated_llm_payloads"], 1)
        self.assertEqual(report["pending_count"], 0)
        self.assertTrue((package / "artifact.yaml").exists())
        self.assertTrue((package / "corrected.tex").exists())
        artifact = yaml.safe_load((package / "artifact.yaml").read_text(encoding="utf-8"))
        self.assertEqual(artifact["identity"]["label"], "def:real-upper-bound")

    def test_python_llm_without_payload_reports_pending_and_creates_request(self):
        with temp_dir() as root:
            volume = write_fake_volume(root)
            output = root / "scope.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCOPE_VALIDATOR),
                    "--mode",
                    "python-llm",
                    "--repos-root",
                    str(root),
                    "--volume",
                    "i",
                    "--chapter",
                    "bounds",
                    "--llm-data-dir",
                    str(root / "missing-llm"),
                    "--format",
                    "json",
                    "--output",
                    str(output),
                ],
                capture_output=True,
                text=True,
            )
            report = json.loads(output.read_text(encoding="utf-8"))
            request = volume / "volume-i" / "book-order" / "bounds" / "def-real-upper-bound" / "generation-request.json"

        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["result"], "pending")
        self.assertEqual(report["pending_count"], 1)
        self.assertEqual(report["items"][0]["status"], "pending_llm_data")
        self.assertTrue(request.exists())

    def test_python_llm_requires_llm_input_location(self):
        with temp_dir() as root:
            write_fake_volume(root)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCOPE_VALIDATOR),
                    "--mode",
                    "python-llm",
                    "--repos-root",
                    str(root),
                    "--volume",
                    "i",
                    "--chapter",
                    "bounds",
                ],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("requires --llm-data-dir or --llm-data", result.stderr)


if __name__ == "__main__":
    unittest.main()
