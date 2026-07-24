from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "governance"))

import compare_volume_formal_ast_parsers as compare  # noqa: E402


class VolumeFormalAstParserComparisonTests(unittest.TestCase):
    def test_audit_equivalence_collapses_raw_surface_spacing(self):
        hand = {"kind": "raw_latex", "latex": r"A \to B"}
        lark = {"kind": "raw_latex", "latex": "AtoB"}

        self.assertNotEqual(hand, lark)
        self.assertTrue(compare.ast_equivalent_for_audit(hand, lark))

    def test_audit_equivalence_collapses_binder_surface_noise(self):
        hand = {"kind": "variable", "binder_id": "(g_circ_f)^-1"}
        lark = {"kind": "variable", "binder_id": "(gcirc_f)^-1"}

        self.assertNotEqual(hand, lark)
        self.assertTrue(compare.ast_equivalent_for_audit(hand, lark))

    def test_audit_equivalence_preserves_structural_kind_difference(self):
        hand = {"kind": "raw_latex", "latex": "x"}
        lark = {"kind": "relation", "left": {"kind": "variable", "binder_id": "x"}, "relation": "=", "right": {"kind": "variable", "binder_id": "x"}}

        self.assertFalse(compare.ast_equivalent_for_audit(hand, lark))

    def test_audit_equivalence_collapses_raw_and_variable_surface_terms(self):
        hand = {"kind": "raw_latex", "latex": "A/{sim}"}
        lark = {"kind": "variable", "binder_id": "A/sim"}

        self.assertTrue(compare.ast_equivalent_for_audit(hand, lark))

    def test_audit_equivalence_collapses_application_and_variable_surface_terms(self):
        hand = {
            "kind": "application",
            "function": "log",
            "arguments": [{"kind": "variable", "binder_id": "x+sqrtx^2+1"}],
        }
        lark = {"kind": "variable", "binder_id": "log_(x+sqrtx^2+1)"}

        self.assertTrue(compare.ast_equivalent_for_audit(hand, lark))

    def test_compare_cases_reports_strict_and_audit_mismatch_counts(self):
        hand_ast = {"kind": "raw_latex", "latex": r"A \to B"}
        lark_ast = {"kind": "raw_latex", "latex": "AtoB"}

        def fake_parse(name: str, _formula: str):
            return {
                "parser": name,
                "status": "pass",
                "ast": hand_ast if name == "hand" else lark_ast,
            }

        with patch.object(compare, "parse_with", side_effect=fake_parse):
            report = compare.compare_cases(
                [
                    {
                        "id": "case1",
                        "source": {},
                        "tex": r"\[A\to B\]",
                    }
                ]
            )

        summary = report["summary"]
        self.assertEqual(summary["both_parse_count"], 1)
        self.assertEqual(summary["ast_mismatch_count"], 1)
        self.assertEqual(summary["audit_equivalent_count"], 1)
        self.assertEqual(summary["audit_mismatch_count"], 0)
        self.assertTrue(report["failures"][0]["audit_equivalent"])


if __name__ == "__main__":
    unittest.main()
