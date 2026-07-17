#!/usr/bin/env python3
"""Tests for deterministic LaTeX-to-semantic-AST support parsing."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "governance"))

import semantic_latex_ast as parser  # noqa: E402


class SemanticLatexAstTests(unittest.TestCase):
    def test_parses_bounded_universal_and_keeps_original_latex(self):
        latex = r"\forall n \in P\;(S(n) \in P)."
        result = parser.parse_support_formula(latex)
        self.assertEqual(result["original_latex"], latex)
        self.assertEqual(
            result["ast"],
            {
                "kind": "forall",
                "binder": {
                    "binder_id": "n",
                    "symbol": "n",
                    "domain": {"kind": "variable", "binder_id": "P"},
                },
                "restriction": None,
                "body": {
                    "kind": "relation",
                    "relation": r"\in",
                    "left": {
                        "kind": "application",
                        "function": "S",
                        "arguments": [{"kind": "variable", "binder_id": "n"}],
                    },
                    "right": {"kind": "variable", "binder_id": "P"},
                },
            },
        )
        self.assertEqual(
            result["mechanical_negation_ast"],
            {
                "kind": "exists",
                "binder": {
                    "binder_id": "n",
                    "symbol": "n",
                    "domain": {"kind": "variable", "binder_id": "P"},
                },
                "restriction": None,
                "body": {
                    "kind": "relation",
                    "relation": r"\notin",
                    "left": {
                        "kind": "application",
                        "function": "S",
                        "arguments": [{"kind": "variable", "binder_id": "n"}],
                    },
                    "right": {"kind": "variable", "binder_id": "P"},
                },
            },
        )

    def test_parses_multi_binder_implication_and_negation(self):
        latex = r"\forall m,n \in P\;(S(m)=S(n) \Longrightarrow m=n)."
        result = parser.parse_support_formula(latex)
        ast = result["ast"]
        self.assertEqual(ast["kind"], "forall")
        self.assertEqual(ast["binder"]["binder_id"], "m")
        self.assertEqual(ast["body"]["kind"], "forall")
        self.assertEqual(ast["body"]["binder"]["binder_id"], "n")
        self.assertEqual(ast["body"]["body"]["kind"], "implies")
        negation = result["mechanical_negation_ast"]
        self.assertEqual(negation["kind"], "exists")
        self.assertEqual(negation["body"]["kind"], "exists")
        self.assertEqual(negation["body"]["body"]["kind"], "and")
        self.assertEqual(negation["body"]["body"]["right"]["relation"], r"\neq")

    def test_parses_subset_bounded_quantifier_with_grouping_macros(self):
        latex = (
            r"\forall A\subseteq P\;"
            r"\Bigl(\bigl(1\in A \land "
            r"\forall n\in A,\ S(n)\in A\bigr)"
            r"\Longrightarrow A=P\Bigr)."
        )
        result = parser.parse_support_formula(latex)
        ast = result["ast"]
        self.assertEqual(ast["kind"], "forall")
        self.assertEqual(ast["binder"]["binder_id"], "A")
        self.assertEqual(
            ast["binder"]["domain"],
            {
                "kind": "application",
                "function": "subset_of",
                "arguments": [{"kind": "variable", "binder_id": "P"}],
            },
        )
        self.assertEqual(ast["body"]["kind"], "implies")
        self.assertEqual(ast["body"]["left"]["kind"], "and")
        self.assertEqual(ast["body"]["left"]["right"]["kind"], "forall")
        self.assertEqual(result["mechanical_negation_ast"]["kind"], "exists")

    def test_parses_predicate_reading(self):
        result = parser.parse_support_formula(r"\operatorname{Injective}(S,P,P).")
        self.assertEqual(
            result["ast"],
            {
                "kind": "predicate",
                "predicate_id": "pred:injective",
                "name": "Injective",
                "arguments": [
                    {"kind": "variable", "binder_id": "S"},
                    {"kind": "variable", "binder_id": "P"},
                    {"kind": "variable", "binder_id": "P"},
                ],
            },
        )

    def test_parses_operatorname_inside_unbounded_quantifiers(self):
        result = parser.parse_support_formula(r"\exists P\;\exists S\;\operatorname{PeanoSystem}(P,S,1).")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "exists")
        self.assertEqual(ast["binder"]["binder_id"], "P")
        self.assertEqual(ast["body"]["kind"], "exists")
        self.assertEqual(ast["body"]["binder"]["binder_id"], "S")
        self.assertEqual(ast["body"]["body"]["kind"], "predicate")
        self.assertEqual(ast["body"]["body"]["predicate_id"], "pred:peano-system")

    def test_parses_operatorname_with_tuple_argument_inside_implication(self):
        result = parser.parse_support_formula(
            r"\operatorname{IteratorFunction}(f,(P,S,1),W,c,g)"
            r"\Longrightarrow f(1)=c."
        )
        ast = result["ast"]
        self.assertEqual(ast["kind"], "implies")
        predicate = ast["left"]
        self.assertEqual(predicate["kind"], "predicate")
        self.assertEqual(predicate["arguments"][1]["kind"], "tuple")
        self.assertEqual(
            [item["binder_id"] if item["kind"] == "variable" else item["name"] for item in predicate["arguments"][1]["elements"]],
            ["P", "S", "1"],
        )


if __name__ == "__main__":
    unittest.main()
