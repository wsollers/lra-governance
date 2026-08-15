from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.governance import concept_candidate_discovery as discovery


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "constitution" / "schema" / "examples" / "concept-discovery" / "cauchy-sequence-discovery-input.json"
TOOL = ROOT / "tools" / "governance" / "concept_candidate_discovery.py"


class ConceptCandidateDiscoveryTests(unittest.TestCase):
    def fixture(self) -> dict:
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_cross_line_exact_phrase_match_is_accepted(self):
        receipt = discovery.build_receipt(self.fixture())
        hit = next(item for item in receipt["primary_source_lane"]["accepted_hits"] if item["source_id"] == "SRC-ANALYSIS-001")

        self.assertIn("Cauchy sequence", " ".join(hit["matched_text"].split()))
        self.assertEqual(hit["kind"], "Definition")

    def test_five_independent_close_sources_default_is_satisfied(self):
        receipt = discovery.build_receipt(self.fixture())

        self.assertEqual(receipt["primary_source_lane"]["minimum_independent_close_sources"], 5)
        self.assertTrue(receipt["primary_source_lane"]["minimum_satisfied"])
        self.assertEqual(
            len({hit["independent_source_key"] for hit in receipt["primary_source_lane"]["accepted_hits"]}),
            5,
        )

    def test_false_positive_without_formal_statement_or_in_proof_is_rejected(self):
        receipt = discovery.build_receipt(self.fixture())
        reasons = {item["reason"] for item in receipt["primary_source_lane"]["rejected_false_positives"]}

        self.assertIn("proof_or_citation_context", reasons)
        self.assertIn("no_formal_label_proximity", reasons)

    def test_direct_pdf_fallback_is_represented(self):
        receipt = discovery.build_receipt(self.fixture())

        self.assertEqual(
            receipt["primary_source_lane"]["direct_pdf_fallbacks"],
            [{"source_id": "SRC-ANALYSIS-005", "reason": "damaged_extraction", "result": "accepted_hit"}],
        )
        hit = next(item for item in receipt["primary_source_lane"]["accepted_hits"] if item["source_id"] == "SRC-ANALYSIS-005")
        self.assertEqual(hit["inspection_surface"], "direct_pdf")

    def test_mathlib_and_internal_lra_lanes_are_separate(self):
        receipt = discovery.build_receipt(self.fixture())

        self.assertTrue(receipt["mathlib_lane"]["searched"])
        self.assertEqual(receipt["mathlib_lane"]["hits"][0]["declaration"], "Metric.CauchySeq")
        self.assertFalse(receipt["internal_lra_lane"]["searched"])
        self.assertEqual(receipt["internal_lra_lane"]["role"], "not_discovery_evidence")

    def test_receipt_schema_validates(self):
        receipt = discovery.build_receipt(self.fixture())

        self.assertEqual(discovery.validate_receipt(receipt), [])

    def test_cli_writes_valid_receipt_without_internal_lra_search(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "receipt.json"
            result = subprocess.run(
                [sys.executable, str(TOOL), "--config", str(FIXTURE), "--output", str(output)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            receipt = json.loads(output.read_text(encoding="utf-8"))

        self.assertFalse(receipt["internal_lra_lane"]["searched"])
        self.assertEqual(discovery.validate_receipt(receipt), [])

    def test_reviewed_exception_can_satisfy_sparse_source_coverage(self):
        data = self.fixture()
        data["primary_sources"] = data["primary_sources"][:2]
        data["reviewed_exception"] = {
            "reviewer": "source reviewer",
            "rationale": "Calibration fixture with sparse source stack.",
        }

        receipt = discovery.build_receipt(data)

        self.assertTrue(receipt["primary_source_lane"]["minimum_satisfied"])
        self.assertIsNotNone(receipt["primary_source_lane"]["reviewed_exception"])


if __name__ == "__main__":
    unittest.main()
