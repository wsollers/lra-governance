from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tools" / "governance" / "validate_concept_authoring_package.py"
VALID = ROOT / "constitution" / "schema" / "examples" / "concept-authoring" / "valid-approved-package.json"
INVALID_STALE = ROOT / "constitution" / "schema" / "examples" / "concept-authoring" / "invalid-stale-approval-package.json"
LEGACY = ROOT / "pilots" / "lean-authoring" / "test-cases" / "upper-bound" / "concept-package.json"


class ConceptAuthoringPackageTests(unittest.TestCase):
    def run_validator(self, data_or_path):
        if isinstance(data_or_path, Path):
            return subprocess.run([sys.executable, str(VALIDATOR), str(data_or_path)], capture_output=True, text=True)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "package.json"
            path.write_text(json.dumps(data_or_path, indent=2) + "\n", encoding="utf-8")
            return subprocess.run([sys.executable, str(VALIDATOR), str(path)], capture_output=True, text=True)

    def package(self):
        return json.loads(VALID.read_text(encoding="utf-8"))

    def test_valid_approved_package_passes(self):
        result = self.run_validator(VALID)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS", result.stdout)

    def test_unresolved_approved_contract_fails(self):
        data = self.package()
        data["concept_contracts"][0]["normalized_definition"]["state"] = "unresolved"
        result = self.run_validator(data)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unresolved field normalized_definition", result.stdout)

    def test_unknown_evidence_reference_fails(self):
        data = self.package()
        data["candidates"][0]["revisions"][0]["evidence_refs"].append("ev.unknown")
        result = self.run_validator(data)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("references unknown evidence ev.unknown", result.stdout)

    def test_invalid_normalized_revision_fails_schema(self):
        data = self.package()
        data["candidates"][0]["revisions"][0]["artifact_kind"] = "axiom"
        result = self.run_validator(data)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("is not one of", result.stdout)

    def test_current_revision_approval_is_required(self):
        result = self.run_validator(INVALID_STALE)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("generation uses unapproved revision", result.stdout)

    def test_stale_approval_after_edit_fails(self):
        data = json.loads(INVALID_STALE.read_text(encoding="utf-8"))
        data["generation_package"] = None
        result = self.run_validator(data)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("approved without approval of current revision", result.stdout)

    def test_deferred_rejected_and_reassigned_candidates_are_valid_states(self):
        for action, resulting_state in [("deferred", "deferred"), ("rejected", "rejected"), ("reassigned", "reassigned")]:
            data = self.package()
            data["generation_package"] = None
            data["review_events"][-1]["action"] = action
            data["review_events"][-1]["resulting_state"] = resulting_state
            if action == "reassigned":
                data["concept_contracts"].append(copy.deepcopy(data["concept_contracts"][0]))
                data["concept_contracts"][1]["concept_id"] = "concept.lower-bound"
                data["concept_contracts"][1]["contract_revision"] = "rev.contract.lower.v1"
                data["concept_contracts"] = sorted(data["concept_contracts"], key=lambda item: item["concept_id"])
                data["review_events"][-1]["destination_concept_id"] = "concept.lower-bound"
            result = self.run_validator(data)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_invalid_state_transition_fails(self):
        data = self.package()
        data["review_events"][1]["previous_state"] = "none"
        result = self.run_validator(data)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid transition", result.stdout)

    def test_unknown_fields_fail(self):
        data = self.package()
        data["candidates"][0]["unexpected"] = True
        result = self.run_validator(data)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Additional properties are not allowed", result.stdout)

    def test_duplicate_stable_ids_fail(self):
        data = self.package()
        data["evidence"].append(copy.deepcopy(data["evidence"][0]))
        result = self.run_validator(data)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate evidence_id", result.stdout)

    def test_nondeterministic_ordering_fails(self):
        data = self.package()
        data["evidence"] = list(reversed(data["evidence"]))
        result = self.run_validator(data)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be sorted", result.stdout)

    def test_legacy_schema_remains_non_materializable(self):
        result = self.run_validator(LEGACY)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("inspectable but non-materializable", result.stdout)


if __name__ == "__main__":
    unittest.main()
