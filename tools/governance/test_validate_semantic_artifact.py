from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tools" / "governance" / "validate_semantic_artifact.py"
EXAMPLE = ROOT / "constitution" / "schema" / "examples" / "semantic-artifact.example.yaml"


class SemanticArtifactValidationTests(unittest.TestCase):
    def run_validator(self, artifact: Path):
        return subprocess.run(
            [sys.executable, str(VALIDATOR), "--artifact", str(artifact),
             "--governance-root", str(ROOT)],
            capture_output=True, text=True,
        )

    def test_example_validates_with_raw_latex_warnings(self):
        result = self.run_validator(EXAMPLE)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("raw_latex", result.stdout)

    def test_kind_label_mismatch_fails(self):
        data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
        data["identity"]["kind"] = "theorem"
        with tempfile.TemporaryDirectory() as temp:
            artifact = Path(temp) / "artifact.yaml"
            artifact.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            result = self.run_validator(artifact)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must use prefix thm:", result.stdout)

    def test_blocking_ambiguity_fails(self):
        data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
        data["provenance"]["unresolved"] = [{
            "code": "AMBIGUOUS_ORDER_KIND",
            "question": "Does ordered set mean partial or total order?",
            "candidates": ["PartiallyOrderedSet", "TotallyOrderedSet"],
            "blocks_generation": True,
        }]
        with tempfile.TemporaryDirectory() as temp:
            artifact = Path(temp) / "artifact.yaml"
            artifact.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            result = self.run_validator(artifact)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("AMBIGUOUS_ORDER_KIND", result.stdout)


if __name__ == "__main__":
    unittest.main()
