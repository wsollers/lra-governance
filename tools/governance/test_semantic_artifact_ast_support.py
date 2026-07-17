#!/usr/bin/env python3
"""Tests for augmenting semantic artifacts with parsed support ASTs."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "governance"))

import semantic_artifact_ast_support as support  # noqa: E402


class SemanticArtifactAstSupportTests(unittest.TestCase):
    def test_augments_artifact_without_replacing_original_latex(self):
        artifact = {
            "identity": {"label": "ax:peano-successor-closure", "kind": "axiom"},
            "statement": {
                "canonical_latex": r"If $n \in P$, then $S(n)\in P$.",
                "semantic_ast": {"kind": "raw_latex", "latex": "old"},
            },
            "logical_forms": {
                "standard_quantified": {
                    "latex": r"\[\forall n \in P\;(S(n) \in P).\]",
                    "ast": {"kind": "raw_latex", "latex": "old"},
                },
                "predicate_reading": None,
                "negation": {
                    "mechanical": {"latex": "old", "ast": {"kind": "raw_latex", "latex": "old"}},
                    "approved_normal_form": None,
                    "normalization_requires": [],
                },
            },
        }
        corrected_tex = r"""
\begin{remark*}[Predicate reading]
\[
\operatorname{SuccessorClosedIn}(S,P).
\]
\end{remark*}
"""
        updated = support.augment_artifact(artifact, corrected_tex)
        self.assertEqual(
            updated["logical_forms"]["standard_quantified"]["latex"],
            r"\[\forall n \in P\;(S(n) \in P).\]",
        )
        self.assertEqual(updated["statement"]["canonical_latex"], r"If $n \in P$, then $S(n)\in P$.")
        self.assertEqual(updated["statement"]["semantic_ast"]["kind"], "forall")
        self.assertEqual(updated["logical_forms"]["standard_quantified"]["ast"]["kind"], "forall")
        self.assertEqual(updated["logical_forms"]["predicate_reading"]["ast"]["kind"], "predicate")
        witnesses = updated["logical_forms"]["standard_quantified"]["parser_witnesses"]
        self.assertEqual(witnesses["original_latex"], r"\[\forall n \in P\;(S(n) \in P).\]")
        self.assertEqual(witnesses["hand_parser"]["ast"], witnesses["lark_parser"]["ast"])
        self.assertTrue(witnesses["parsers_agree"])
        self.assertEqual(updated["logical_forms"]["negation"]["mechanical"]["ast"]["kind"], "not")
        self.assertEqual(updated["logical_forms"]["negation"]["approved_normal_form"]["ast"]["kind"], "exists")
        parameter_ids = {item["id"] for item in updated["parameters"]}
        self.assertIn("P", parameter_ids)
        self.assertIn("S", parameter_ids)


if __name__ == "__main__":
    unittest.main()
