from __future__ import annotations

import json
import subprocess
import sys
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LABEL_VALIDATOR = ROOT / "tools" / "governance" / "validate_semantic_label.py"
TEMP_ROOT = ROOT / ".test-tmp" / "semantic-label"

if str(ROOT / "tools" / "governance") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools" / "governance"))

from test_validate_semantic_logic import CORRECTED_TEX, real_upper_bound_artifact  # noqa: E402


@contextmanager
def temp_dir():
    path = TEMP_ROOT / str(uuid.uuid4())
    path.mkdir(parents=True, exist_ok=True)
    yield path


def write_fake_volume(root: Path, roman: str = "i") -> Path:
    volume = root / f"lra-volume-{roman}"
    target = volume / f"volume-{roman}" / "book-order" / "bounds"
    target.mkdir(parents=True)
    (volume / f"volume-{roman}-book-order.tex").write_text(
        rf"\input{{volume-{roman}/book-order/bounds/index}}" + "\n",
        encoding="utf-8",
    )
    (target / "index.tex").write_text(
        r"\chapter{Bounds}" + "\n" + rf"\input{{volume-{roman}/book-order/bounds/routed}}" + "\n",
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


class ValidateSemanticLabelTests(unittest.TestCase):
    def test_label_only_with_llm_creates_request_and_reports_payload_path(self):
        with temp_dir() as root:
            volume = write_fake_volume(root)
            output = root / "label.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(LABEL_VALIDATOR),
                    "def:real-upper-bound",
                    "--repos-root",
                    str(root),
                    "--with-llm",
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
        self.assertEqual(report["label_resolution"]["volume"], "i")
        self.assertEqual(report["label_resolution"]["chapter"], "bounds")
        self.assertIn("def-real-upper-bound.json", report["llm_payload_convention"]["preferred_path"])
        self.assertTrue(request.exists())

    def test_label_only_with_supplied_llm_payload_materializes_package(self):
        with temp_dir() as root:
            volume = write_fake_volume(root)
            llm_dir = root / "llm"
            llm_dir.mkdir()
            (llm_dir / "def-real-upper-bound.json").write_text(
                json.dumps({"artifact": real_upper_bound_artifact(), "corrected_tex": CORRECTED_TEX}, indent=2),
                encoding="utf-8",
            )
            output = root / "label.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(LABEL_VALIDATOR),
                    "def:real-upper-bound",
                    "--repos-root",
                    str(root),
                    "--with-llm",
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
        self.assertTrue((package / "artifact.yaml").exists())
        self.assertTrue((package / "corrected.tex").exists())

    def test_label_only_requires_volume_when_ambiguous(self):
        with temp_dir() as root:
            write_fake_volume(root, "i")
            write_fake_volume(root, "ii")
            result = subprocess.run(
                [
                    sys.executable,
                    str(LABEL_VALIDATOR),
                    "def:real-upper-bound",
                    "--repos-root",
                    str(root),
                    "--with-llm",
                ],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("ambiguous", result.stderr)
        self.assertIn("--volume", result.stderr)


if __name__ == "__main__":
    unittest.main()
