#!/usr/bin/env python3
"""Tests for the Lark-backed governed logic parser."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "governance"))

import semantic_lark_logic_parser as lark_parser  # noqa: E402
import semantic_latex_ast as hand_parser  # noqa: E402


class SemanticLarkLogicParserTests(unittest.TestCase):
    def assert_parsers_agree(self, latex: str) -> None:
        hand = hand_parser.parse_support_formula(latex)
        generated = lark_parser.parse_support_formula(latex)
        self.assertEqual(generated["original_latex"], latex)
        self.assertEqual(generated["ast"], hand["ast"])
        self.assertEqual(generated["mechanical_negation_ast"], hand["mechanical_negation_ast"])

    def test_lark_parser_matches_hand_parser_for_bounded_universal(self):
        self.assert_parsers_agree(r"\forall n \in P\;(S(n) \in P).")

    def test_lark_parser_matches_hand_parser_for_subset_quantifier(self):
        self.assert_parsers_agree(
            r"\forall A\subseteq P\;"
            r"\Bigl(\bigl(1\in A \land "
            r"\forall n\in A,\ S(n)\in A\bigr)"
            r"\Longrightarrow A=P\Bigr)."
        )

    def test_lark_parser_matches_hand_parser_for_injectivity(self):
        self.assert_parsers_agree(r"\forall m,n \in P\;(S(m)=S(n) \Longrightarrow m=n).")

    def test_lark_parser_matches_hand_parser_for_predicate_reading(self):
        self.assert_parsers_agree(r"\operatorname{Injective}(S,P,P).")

    def test_lark_parser_matches_hand_parser_for_unbounded_quantified_predicate(self):
        self.assert_parsers_agree(r"\exists P\;\exists S\;\operatorname{PeanoSystem}(P,S,1).")

    def test_lark_parser_matches_hand_parser_for_predicate_with_tuple_argument(self):
        self.assert_parsers_agree(
            r"\operatorname{IteratorFunction}(f,(P,S,1),W,c,g)"
            r"\Longrightarrow f(1)=c."
        )


if __name__ == "__main__":
    unittest.main()
