from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import jsonschema


PILOT_ROOT = Path(__file__).resolve().parent
MATERIALIZER = PILOT_ROOT / "materialize.py"
PACKAGE = PILOT_ROOT / "test-cases" / "upper-bound" / "concept-package.json"
REQUEST = PILOT_ROOT / "test-cases" / "upper-bound" / "request.json"


class MaterializeTest(unittest.TestCase):
    def test_upper_bound_documents_match_pilot_schemas(self) -> None:
        pairs = [
            (PILOT_ROOT / "schemas" / "request.schema.json", REQUEST),
            (PILOT_ROOT / "schemas" / "concept-package.schema.json", PACKAGE),
        ]
        for schema_path, instance_path in pairs:
            with self.subTest(instance=instance_path.name):
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                instance = json.loads(instance_path.read_text(encoding="utf-8"))
                jsonschema.validate(instance, schema)

    def test_legacy_package_is_blocked_before_any_output_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            lean_root = Path(temporary_directory)
            (lean_root / "LRA").mkdir()
            (lean_root / "LRA" / "Pilot.lean").write_text(
                "import LRA.Pilot.Existing\n\n/-! Existing pilot root. -/\n",
                encoding="utf-8",
            )
            command = [
                sys.executable,
                str(MATERIALIZER),
                "--package",
                str(PACKAGE),
                "--lean-root",
                str(lean_root),
            ]
            result = subprocess.run(command, check=False, capture_output=True, text=True)

            self.assertEqual(2, result.returncode)
            self.assertIn("legacy package format", result.stderr)
            self.assertIn("approval of the current normalized revision", result.stderr)
            pilot_root = (lean_root / "LRA" / "Pilot.lean").read_text(encoding="utf-8")
            self.assertIn("import LRA.Pilot.Existing", pilot_root)
            self.assertNotIn("LRA LEAN AUTHORING PILOT", pilot_root)
            self.assertFalse((lean_root / "LRA" / "Pilot").exists())

    def test_check_mode_also_requires_current_revision_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            lean_root = Path(temporary_directory)
            (lean_root / "LRA").mkdir()
            (lean_root / "LRA" / "Pilot.lean").write_text("/-! Empty pilot root. -/\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(MATERIALIZER),
                    "--package",
                    str(PACKAGE),
                    "--lean-root",
                    str(lean_root),
                    "--check",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(2, result.returncode)
            self.assertIn("cannot be materialized", result.stderr)


if __name__ == "__main__":
    unittest.main()
