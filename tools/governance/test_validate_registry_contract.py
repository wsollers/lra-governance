from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tools" / "governance" / "validate_registry_contract.py"


def write_registry(root: Path, *, predicate: dict, structure: dict) -> None:
    (root / "predicates.yaml").write_text(
        yaml.safe_dump({"predicates": [predicate]}, sort_keys=False),
        encoding="utf-8",
    )
    (root / "structures.yaml").write_text(
        yaml.safe_dump({"structures": [structure]}, sort_keys=False),
        encoding="utf-8",
    )


class RegistryContractValidationTests(unittest.TestCase):
    def run_validator(self, root: Path):
        return subprocess.run(
            [sys.executable, str(VALIDATOR), "--governance-root", str(root), "--format", "json"],
            capture_output=True,
            text=True,
        )

    def test_accepts_valid_registry_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_registry(
                root,
                predicate={
                    "id": "pred:tends-to",
                    "name": "TendsTo",
                    "kind": "predicate",
                    "category": "analysis",
                    "arguments": [
                        {"name": "f", "role": "function"},
                        {"name": "a", "role": "source_point"},
                    ],
                    "returns": "truth_value",
                    "carried_context": [
                        {"kind": "domain", "source": "type_of_argument", "argument": "f"}
                    ],
                    "description": "Limit predicate.",
                },
                structure={
                    "id": "struct:function-space",
                    "name": "FunctionSpace",
                    "kind": "structure",
                    "category": "function",
                    "constructor": r"\mathsf{FunctionSpace}",
                    "arguments": [
                        {"name": "A", "role": "domain"},
                        {"name": "B", "role": "codomain"},
                    ],
                    "carrier_argument": None,
                    "structural_arguments": ["A", "B"],
                    "carried_context": [
                        {"kind": "domain", "source": "argument", "argument": "A"},
                        {"kind": "codomain", "source": "argument", "argument": "B"},
                    ],
                    "description": "Function-space constructor.",
                },
            )

            result = self.run_validator(root)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_position_and_carried_context_mismatches(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_registry(
                root,
                predicate={
                    "id": "pred:bad",
                    "name": "Bad",
                    "kind": "predicate",
                    "category": "logic",
                    "arguments": [
                        {"name": "x", "role": "point", "position": 2},
                    ],
                    "returns": "object",
                    "carried_context": [
                        {"kind": "domain", "source": "type_of_argument", "argument": "missing"}
                    ],
                    "description": "Bad predicate.",
                },
                structure={
                    "id": "struct:bad",
                    "name": "BadStructure",
                    "kind": "structure",
                    "category": "logic",
                    "constructor": r"\mathsf{BadStructure}",
                    "arguments": [{"name": "A", "role": "carrier"}],
                    "carrier_argument": "B",
                    "structural_arguments": ["C"],
                    "description": "Bad structure.",
                },
            )

            result = self.run_validator(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("declares position 2", result.stdout)
        self.assertIn("predicates must return truth_value", result.stdout)
        self.assertIn("references unknown argument 'missing'", result.stdout)
        self.assertIn("carrier_argument 'B' is not an argument", result.stdout)
        self.assertIn("structural_argument 'C' is not an argument", result.stdout)

    def test_live_registry_satisfies_contract(self):
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--governance-root", str(ROOT)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
