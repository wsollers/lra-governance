from __future__ import annotations

import subprocess
import sys
import shutil
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tools" / "governance" / "validate_registry_contract.py"
TEMP_ROOT = ROOT / ".test-tmp" / "registry-contract"


@contextmanager
def temporary_directory():
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    path = TEMP_ROOT / f"case-{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    try:
        yield str(path)
    finally:
        shutil.rmtree(path, ignore_errors=True)


def write_registry(root: Path, *, predicate: dict, structure: dict) -> None:
    (root / "predicates.yaml").write_text(
        yaml.safe_dump({"predicates": [predicate]}, sort_keys=False),
        encoding="utf-8",
    )
    (root / "structures.yaml").write_text(
        yaml.safe_dump({"structures": [structure]}, sort_keys=False),
        encoding="utf-8",
    )
    (root / "notation.yaml").write_text("notation: []\n", encoding="utf-8")


class RegistryContractValidationTests(unittest.TestCase):
    def run_validator(self, root: Path):
        return subprocess.run(
            [sys.executable, str(VALIDATOR), "--governance-root", str(root), "--format", "json"],
            capture_output=True,
            text=True,
        )

    def test_accepts_valid_registry_contract(self):
        with temporary_directory() as temp:
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
        with temporary_directory() as temp:
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

    def test_rejects_unknown_argument_type(self):
        with temporary_directory() as temp:
            root = Path(temp)
            write_registry(
                root,
                predicate={
                    "id": "pred:bad-type",
                    "name": "BadType",
                    "kind": "predicate",
                    "category": "logic",
                    "arguments": [{"name": "x", "role": "object", "type": "banana"}],
                    "returns": "truth_value",
                    "description": "Bad typed predicate.",
                },
                structure={
                    "id": "struct:test",
                    "name": "TestStructure",
                    "kind": "structure",
                    "category": "logic",
                    "constructor": r"\mathsf{TestStructure}",
                    "arguments": [],
                    "carrier_argument": None,
                    "structural_arguments": [],
                    "description": "Test structure.",
                },
            )

            result = self.run_validator(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown type 'banana'", result.stdout)

    def test_live_registry_satisfies_contract(self):
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--governance-root", str(ROOT)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_live_notation_registers_number_systems_and_ordered_variants(self):
        data = yaml.safe_load((ROOT / "notation.yaml").read_text(encoding="utf-8"))
        by_symbol = {
            item["symbol"]: item
            for item in data.get("notation", [])
            if isinstance(item, dict) and item.get("category") == "number_system"
        }

        expected = {
            r"\mathbb{N}",
            r"\mathbb{Z}",
            r"\mathbb{Q}",
            r"\mathbb{R}",
            r"\mathbb{C}",
            r"\mathbb{N}_{>0}",
            r"\mathbb{N}_{\ge 0}",
            r"\mathbb{Z}_{>0}",
            r"\mathbb{Z}_{\ge 0}",
            r"\mathbb{Z}_{<0}",
            r"\mathbb{Z}_{\le 0}",
            r"\mathbb{Q}_{>0}",
            r"\mathbb{Q}_{\ge 0}",
            r"\mathbb{Q}_{<0}",
            r"\mathbb{Q}_{\le 0}",
            r"\mathbb{R}_{>0}",
            r"\mathbb{R}_{\ge 0}",
            r"\mathbb{R}_{<0}",
            r"\mathbb{R}_{\le 0}",
        }

        self.assertEqual(set(by_symbol) & expected, expected)
        self.assertNotIn(r"\mathbb{C}_{>0}", by_symbol)
        self.assertNotIn(r"\mathbb{C}_{\ge 0}", by_symbol)

    def test_live_registries_mark_synthetic_test_entries(self):
        predicates = yaml.safe_load((ROOT / "predicates.yaml").read_text(encoding="utf-8")).get("predicates", [])
        structures = yaml.safe_load((ROOT / "structures.yaml").read_text(encoding="utf-8")).get("structures", [])
        notation = yaml.safe_load((ROOT / "notation.yaml").read_text(encoding="utf-8")).get("notation", [])

        test_predicates = [
            item for item in predicates
            if isinstance(item, dict) and str(item.get("id", "")).startswith("pred:test-predicate-")
        ]
        test_relations = [
            item for item in predicates
            if isinstance(item, dict) and str(item.get("id", "")).startswith("pred:test-relation-")
        ]
        test_structures = [
            item for item in structures
            if isinstance(item, dict) and str(item.get("id", "")).startswith("struct:test-structure-")
        ]
        test_notation = [
            item for item in notation
            if isinstance(item, dict) and item.get("testing") is True and isinstance(item.get("test_symbol"), dict)
        ]

        self.assertEqual(len(test_predicates), 28)
        self.assertEqual(len(test_relations), 12)
        self.assertEqual(len(test_structures), 6)
        self.assertEqual(len(test_notation), 73)
        self.assertTrue(all(item.get("testing") is True for item in test_predicates))
        self.assertTrue(all(item.get("testing") is True for item in test_relations))
        self.assertTrue(all(item.get("testing") is True for item in test_structures))


if __name__ == "__main__":
    unittest.main()
