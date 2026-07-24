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

    def test_quantifier_scopes_over_following_implication(self):
        result = parser.parse_support_formula(r"\forall x\in A\;P(x)\Longrightarrow Q.")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "forall")
        self.assertEqual(ast["body"]["kind"], "implies")
        self.assertEqual(ast["body"]["left"]["kind"], "application")
        self.assertEqual(ast["body"]["right"], {"kind": "variable", "binder_id": "Q"})

    def test_parentheses_can_force_implication_outside_quantifier(self):
        result = parser.parse_support_formula(r"(\forall x\in A\;P(x))\Longrightarrow Q.")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "implies")
        self.assertEqual(ast["left"]["kind"], "forall")
        self.assertEqual(ast["right"], {"kind": "variable", "binder_id": "Q"})

    def test_negates_quantified_biconditional_by_pushing_iff_inside_quantifier(self):
        result = parser.parse_support_formula(r"\forall x\in P,\ A(x)\Longleftrightarrow B(x).")
        negation = result["mechanical_negation_ast"]
        self.assertEqual(negation["kind"], "exists")
        self.assertEqual(negation["body"]["kind"], "or")
        self.assertEqual(negation["body"]["left"]["kind"], "and")
        self.assertEqual(negation["body"]["right"]["kind"], "and")

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

    def test_parses_aligned_iterator_relation_without_synthetic_binders(self):
        latex = r"""
\[
\begin{aligned}
R \text{ is an iterator relation for } (W,c,g)
\Longleftrightarrow\;&
R\subseteq P\times W
\land (1,c)\in R\\
&\land
\forall n\in P\;\forall w\in W\;
\bigl((n,w)\in R\Longrightarrow (S(n),g(w))\in R\bigr).
\end{aligned}
\]
"""
        result = parser.parse_support_formula(latex)
        ast = result["ast"]
        self.assertEqual(ast["kind"], "iff")
        self.assertEqual(ast["left"]["kind"], "raw_latex")
        self.assertEqual(ast["right"]["kind"], "and")
        quantified = ast["right"]["right"]["right"]
        self.assertEqual(quantified["kind"], "forall")
        self.assertEqual(quantified["binder"]["binder_id"], "n")
        self.assertEqual(quantified["binder"]["domain"], {"kind": "variable", "binder_id": "P"})
        self.assertEqual(quantified["body"]["kind"], "forall")
        self.assertEqual(quantified["body"]["binder"]["binder_id"], "w")
        self.assertEqual(quantified["body"]["binder"]["domain"], {"kind": "variable", "binder_id": "W"})

    def test_text_and_or_connectives_split_top_level_clauses(self):
        result = parser.parse_support_formula(
            r"A\neq\varnothing"
            r"\quad\text{and}\quad"
            r"(\forall a\in A)(a\leq s)"
            r"\ \text{or}\ "
            r"(\forall u\in\mathbb{R})(s\leq u)."
        )
        ast = result["ast"]
        self.assertEqual(ast["kind"], "or")
        self.assertEqual(ast["left"]["kind"], "and")
        self.assertEqual(ast["left"]["left"]["relation"], r"\neq")
        self.assertEqual(ast["left"]["right"]["kind"], "forall")
        self.assertEqual(ast["right"]["kind"], "forall")

    def test_non_connective_text_atom_remains_raw(self):
        result = parser.parse_support_formula(r"\theta \text{ is bijective}.")
        self.assertEqual(result["ast"]["kind"], "raw_latex")
        self.assertIn("is bijective", result["ast"]["latex"])

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

    def test_parses_synthetic_test_predicate_call(self):
        result = parser.parse_support_formula(r"P_{14}\bigl(S_{2},S_{5},S_{5},S_{4}\bigr).")
        self.assertEqual(result["ast"]["kind"], "predicate")
        self.assertEqual(result["ast"]["predicate_id"], "pred:test-predicate-14")
        self.assertEqual(result["ast"]["name"], "P_{14}")
        self.assertEqual([arg["binder_id"] for arg in result["ast"]["arguments"]], ["S_2", "S_5", "S_5", "S_4"])

    def test_parses_synthetic_test_relation_call(self):
        result = parser.parse_support_formula(r"R_{5}\bigl(\mathcal{T}_{6},c_{1},R_{2}\bigr).")
        self.assertEqual(result["ast"]["kind"], "predicate")
        self.assertEqual(result["ast"]["predicate_id"], "pred:test-relation-5")
        self.assertEqual(result["ast"]["name"], "R_{5}")
        self.assertEqual([arg["binder_id"] for arg in result["ast"]["arguments"]], ["mathcalT_6", "c_1", "R_2"])

    def test_parses_zero_arity_synthetic_predicate_in_formula_position(self):
        result = parser.parse_support_formula(r"P_{6}.")
        self.assertEqual(result["ast"]["kind"], "predicate")
        self.assertEqual(result["ast"]["predicate_id"], "pred:test-predicate-6")
        self.assertEqual(result["ast"]["arguments"], [])

    def test_keeps_synthetic_predicate_symbol_as_term_in_vdash_relation(self):
        result = parser.parse_support_formula(r"S_{1}\vdash P_{6}.")
        self.assertEqual(result["ast"]["kind"], "relation")
        self.assertEqual(result["ast"]["right"], {"kind": "variable", "binder_id": "P_6"})

    def test_resolves_operatorname_by_registry_surface_form(self):
        two_arg = parser.parse_support_formula(r"\operatorname{TotalRelation}(R,A).")
        three_arg = parser.parse_support_formula(r"\operatorname{TotalOnDomain}(R,A,B).")
        old_three_arg = parser.parse_support_formula(r"\operatorname{TotalRelation}(R,A,B).")

        self.assertEqual(two_arg["ast"]["predicate_id"], "pred:total-relation")
        self.assertEqual(three_arg["ast"]["predicate_id"], "pred:total-on-domain")
        self.assertEqual(old_three_arg["ast"]["predicate_id"], "pred:total-relation")

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

    def test_parses_typed_function_binder_and_unique_existence(self):
        result = parser.parse_support_formula(
            r"\exists! f:P\to W\;\operatorname{IteratorFunction}(f,(P,S,1),W,c,g)."
        )
        ast = result["ast"]
        self.assertEqual(ast["kind"], "exists_unique")
        self.assertEqual(ast["binder"]["binder_id"], "f")
        self.assertEqual(
            ast["binder"]["domain"],
            {
                "kind": "application",
                "function": "function_space",
                "arguments": [
                    {"kind": "variable", "binder_id": "P"},
                    {"kind": "variable", "binder_id": "W"},
                ],
            },
        )
        self.assertEqual(ast["body"]["predicate_id"], "pred:iterator-function")

    def test_parses_bounded_unique_existence(self):
        result = parser.parse_support_formula(r"\exists! u\in P\;(S(u)=x).")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "exists_unique")
        self.assertEqual(ast["binder"]["binder_id"], "u")
        self.assertEqual(ast["binder"]["domain"], {"kind": "variable", "binder_id": "P"})
        self.assertEqual(ast["body"]["kind"], "relation")
        self.assertEqual(ast["body"]["relation"], "=")

    def test_desugars_expanded_universal_membership_restriction(self):
        result = parser.parse_support_formula(r"(\forall x)\bigl(x\in A\rightarrow P(x)\bigr).")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "forall")
        self.assertEqual(ast["binder"]["binder_id"], "x")
        self.assertEqual(ast["binder"]["domain"], {"kind": "variable", "binder_id": "A"})
        self.assertEqual(ast["body"]["kind"], "application")
        self.assertEqual(ast["body"]["function"], "P")

    def test_desugars_expanded_existential_membership_restriction(self):
        result = parser.parse_support_formula(r"(\exists x)\bigl(x\in A\land P(x)\bigr).")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "exists")
        self.assertEqual(ast["binder"]["binder_id"], "x")
        self.assertEqual(ast["binder"]["domain"], {"kind": "variable", "binder_id": "A"})
        self.assertEqual(ast["body"]["kind"], "application")
        self.assertEqual(ast["body"]["function"], "P")

    def test_desugars_expanded_unique_existential_membership_restriction(self):
        result = parser.parse_support_formula(r"(\exists! x)\bigl(x\in A\land P(x)\bigr).")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "exists_unique")
        self.assertEqual(ast["binder"]["binder_id"], "x")
        self.assertEqual(ast["binder"]["domain"], {"kind": "variable", "binder_id": "A"})
        self.assertEqual(ast["body"]["kind"], "application")
        self.assertEqual(ast["body"]["function"], "P")

    def test_expanded_quantifier_body_does_not_swallow_following_iff(self):
        result = parser.parse_support_formula(
            r"(\exists! x)\bigl(x\in A\land P(x)\bigr)\leftrightarrow Q."
        )
        ast = result["ast"]
        self.assertEqual(ast["kind"], "iff")
        self.assertEqual(ast["left"]["kind"], "exists_unique")
        self.assertEqual(ast["left"]["body"]["kind"], "application")
        self.assertEqual(ast["right"], {"kind": "variable", "binder_id": "Q"})

    def test_parses_literal_colon_function_type_relation(self):
        result = parser.parse_support_formula(r"g:W\to W.")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "relation")
        self.assertEqual(ast["relation"], r"\colon")
        self.assertEqual(ast["right"]["function"], "function_space")

    def test_parses_typed_signature_with_finite_set_domain_as_raw_literal(self):
        result = parser.parse_support_formula(r"a:\{P_1,\ldots,P_n\}\to\mathbb{B}.")
        ast = result["ast"]
        self.assertEqual(
            ast,
            {
                "kind": "relation",
                "relation": r"\colon",
                "left": {"kind": "variable", "binder_id": "a"},
                "right": {
                    "kind": "application",
                    "function": "function_space",
                    "arguments": [
                        {"kind": "raw_latex", "latex": "{P_1,ldots,P_n}"},
                        {"kind": "variable", "binder_id": "mathbbB"},
                    ],
                },
            },
        )

    def test_parses_subscripted_function_application_as_application(self):
        result = parser.parse_support_formula(r"f_\varphi(b_1,\ldots,b_n)=\widehat v(\varphi).")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "relation")
        self.assertEqual(ast["left"]["kind"], "application")
        self.assertEqual(ast["left"]["function"], "f_varphi")
        self.assertEqual([arg["binder_id"] for arg in ast["left"]["arguments"]], ["b_1", "ldots", "b_n"])

    def test_parses_mathcal_operator_application_as_application(self):
        result = parser.parse_support_formula(r"\mathcal{P}(A)\subseteq\mathcal{P}(B).")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "relation")
        self.assertEqual(ast["left"]["kind"], "application")
        self.assertEqual(ast["left"]["function"], "mathcalP")
        self.assertEqual(ast["right"]["kind"], "application")
        self.assertEqual(ast["right"]["function"], "mathcalP")

    def test_parses_mathrm_named_function_application_as_application(self):
        result = parser.parse_support_formula(r"\mathrm{depth}(\varphi)=\mathrm{depth}(\psi).")
        ast = result["ast"]
        self.assertEqual(ast["left"]["kind"], "application")
        self.assertEqual(ast["left"]["function"], "mathrmdepth")
        self.assertEqual(ast["right"]["kind"], "application")
        self.assertEqual(ast["right"]["function"], "mathrmdepth")

    def test_parses_mathcal_tuple_symbols_without_spurious_underscores(self):
        result = parser.parse_support_formula(r"\mathcal{L}=(\mathcal{C},\mathcal{F},\mathcal{R},\operatorname{ar}).")
        ast = result["ast"]
        self.assertEqual(ast["left"], {"kind": "variable", "binder_id": "mathcalL"})
        self.assertEqual(
            [item["binder_id"] for item in ast["right"]["elements"]],
            ["mathcalC", "mathcalF", "mathcalR", "operatornamear"],
        )

    def test_parses_indexed_set_operations_with_compact_index_surface(self):
        result = parser.parse_support_formula(
            r"U\setminus\bigcup_{i\in I}A_i = \bigcap_{i\in I}(U\setminus A_i)."
        )
        ast = result["ast"]
        self.assertEqual(ast["left"]["kind"], "term_operation")
        self.assertEqual(ast["left"]["operator"], r"\setminus")
        self.assertEqual(ast["left"]["left"], {"kind": "variable", "binder_id": "U"})
        self.assertEqual(ast["left"]["right"]["kind"], "indexed_term_operation")
        self.assertEqual(ast["left"]["right"]["operator"], r"\bigcup")
        self.assertEqual(ast["left"]["right"]["body"], {"kind": "variable", "binder_id": "A_i"})
        self.assertEqual(ast["right"]["kind"], "indexed_term_operation")
        self.assertEqual(ast["right"]["operator"], r"\bigcap")
        self.assertEqual(ast["right"]["body"]["operator"], r"\setminus")

    def test_parses_relation_algebra_terms_as_subtrees(self):
        result = parser.parse_support_formula(r"T\circ(S\circ R)=(T\circ S)\circ R.")
        ast = result["ast"]
        self.assertEqual(ast["left"]["kind"], "term_operation")
        self.assertEqual(ast["left"]["operator"], r"\circ")
        self.assertEqual(ast["left"]["right"]["operator"], r"\circ")
        self.assertEqual(ast["right"]["kind"], "term_operation")
        self.assertEqual(ast["right"]["left"]["operator"], r"\circ")

    def test_parses_set_algebra_terms_as_subtrees(self):
        result = parser.parse_support_formula(r"A \cap (B \cup C) = (A \cap B) \cup (A \cap C).")
        ast = result["ast"]
        self.assertEqual(ast["left"]["kind"], "term_operation")
        self.assertEqual(ast["left"]["operator"], r"\cap")
        self.assertEqual(ast["left"]["right"]["operator"], r"\cup")
        self.assertEqual(ast["right"]["kind"], "term_operation")
        self.assertEqual(ast["right"]["operator"], r"\cup")

    def test_parses_indexed_aggregate_terms_as_subtrees(self):
        result = parser.parse_support_formula(r"A\cap\bigcup_{i\in I}B_i=\bigcup_{i\in I}(A\cap B_i).")
        ast = result["ast"]
        self.assertEqual(ast["left"]["operator"], r"\cap")
        aggregate = ast["left"]["right"]
        self.assertEqual(aggregate["kind"], "indexed_term_operation")
        self.assertEqual(aggregate["operator"], r"\bigcup")
        self.assertEqual(aggregate["index"]["binder_id"], "i")
        self.assertEqual(aggregate["index"]["domain"], {"kind": "variable", "binder_id": "I"})
        self.assertEqual(ast["right"]["kind"], "indexed_term_operation")
        self.assertEqual(ast["right"]["body"]["operator"], r"\cap")

    def test_parses_colon_equals_tuple_definition_without_stray_equals(self):
        result = parser.parse_support_formula(r"(a,b) \;:=\; \{\{a\}, \{a,b\}\}.")
        ast = result["ast"]
        self.assertEqual(ast["relation"], r"\colon")
        self.assertEqual(ast["left"]["kind"], "tuple")
        self.assertEqual(ast["right"], {"kind": "raw_latex", "latex": r"{\{a\},\{a,b\}}"})

    def test_parses_comma_chained_relation_laws_as_sequence(self):
        result = parser.parse_support_formula(
            r"(R^{-1})^{-1}=R,\qquad (T\circ R)^{-1}=R^{-1}\circ T^{-1}."
        )
        ast = result["ast"]
        self.assertEqual(ast["kind"], "formula_sequence")
        self.assertEqual(ast["left"]["kind"], "relation")
        self.assertEqual(ast["right"]["kind"], "relation")
        self.assertEqual(ast["right"]["right"]["kind"], "term_operation")

    def test_comma_variable_list_remains_tuple_not_formula_sequence(self):
        result = parser.parse_support_formula(r"x,y,z.")
        self.assertEqual(result["ast"]["kind"], "raw_latex")

    def test_rejects_term_operation_missing_operand(self):
        with self.assertRaises(parser.SemanticLatexParseError):
            parser.parse_support_formula(r"A\cup=B.")

    def test_parses_set_builder_rhs_as_raw_latex(self):
        result = parser.parse_support_formula(
            r"R_{\varphi}^{\mathcal M}"
            r"="
            r"\{(a_1,\ldots,a_n)\in D^n: "
            r"\mathcal M,s[x_1\mapsto a_1,\ldots,x_n\mapsto a_n]\models\varphi\}."
        )
        ast = result["ast"]
        self.assertEqual(ast["right"]["kind"], "raw_latex")
        self.assertIn("COLON", ast["right"]["latex"])
        self.assertIn("modelsvarphi", ast["right"]["latex"])

    def test_parses_operatorname_with_spacing_macro_and_trailing_comma(self):
        result = parser.parse_support_formula(r"\; \operatorname{Relation}(R,P,W),")
        self.assertEqual(result["ast"]["kind"], "predicate")
        self.assertEqual(result["ast"]["predicate_id"], "pred:relation")

    def test_parses_mapsto_relation(self):
        result = parser.parse_support_formula(r"(n,w)\mapsto (S(n),\Phi(n,w)).")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "relation")
        self.assertEqual(ast["relation"], r"\mapsto")
        self.assertEqual(ast["left"]["kind"], "tuple")
        self.assertEqual(ast["right"]["kind"], "tuple")

    def test_parenthesized_quantifier_body_does_not_swallow_following_conjunction(self):
        result = parser.parse_support_formula(r"\forall n\in P\;(S(n)\neq 1)\land Q.")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "and")
        self.assertEqual(ast["left"]["kind"], "forall")
        self.assertEqual(ast["right"], {"kind": "variable", "binder_id": "Q"})

    def test_parses_parenthesized_bounded_quantifier_prefix_chain(self):
        result = parser.parse_support_formula(
            r"(\exists x\in A)\,(\forall y\in B)\,\bigl(x\in A\land y\in B\bigr)."
        )
        ast = result["ast"]
        self.assertEqual(ast["kind"], "exists")
        self.assertEqual(ast["binder"]["binder_id"], "x")
        self.assertEqual(ast["body"]["kind"], "forall")
        self.assertEqual(ast["body"]["binder"]["binder_id"], "y")
        self.assertEqual(ast["body"]["body"]["kind"], "and")

    def test_parenthesized_bounded_quantifier_prefix_scopes_equiv_body(self):
        result = parser.parse_support_formula(r"(\exists! x_{12}\in A_{6})\,R_{4}\equiv P_{7}.")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "exists_unique")
        self.assertEqual(ast["binder"]["binder_id"], "x_12")
        self.assertEqual(ast["binder"]["domain"], {"kind": "variable", "binder_id": "A_6"})
        self.assertEqual(ast["body"]["kind"], "relation")
        self.assertEqual(ast["body"]["relation"], r"\equiv")
        self.assertEqual(ast["body"]["left"], {"kind": "formula_variable", "name": "R_4"})
        self.assertEqual(ast["body"]["right"], {"kind": "formula_variable", "name": "P_7"})

    def test_parenthesized_bounded_quantifier_prefix_rejects_missing_equiv_rhs(self):
        with self.assertRaises(parser.SemanticLatexParseError):
            parser.parse_support_formula(r"(\exists! x_{12}\in A_{6})\,R_{4}\equiv.")

    def test_parenthesized_quantifier_prefix_scopes_over_next_formula_unit(self):
        result = parser.parse_support_formula(
            r"(\exists x\in A)\,\bigl((\forall y\in B)\,P(y)\lor Q\bigr)."
        )
        ast = result["ast"]
        self.assertEqual(ast["kind"], "exists")
        self.assertEqual(ast["body"]["kind"], "or")
        self.assertEqual(ast["body"]["left"]["kind"], "forall")
        self.assertEqual(ast["body"]["left"]["body"]["kind"], "application")
        self.assertEqual(ast["body"]["right"], {"kind": "variable", "binder_id": "Q"})

    def test_grouped_body_keeps_connective_inside_parenthesized_quantifier_prefix(self):
        result = parser.parse_support_formula(
            r"(\exists x\in A)\,\bigl((\forall y\in B)\,\bigl(P(y)\lor Q\bigr)\bigr)."
        )
        ast = result["ast"]
        self.assertEqual(ast["kind"], "exists")
        self.assertEqual(ast["body"]["kind"], "forall")
        self.assertEqual(ast["body"]["body"]["kind"], "or")

    def test_parses_underscored_function_application(self):
        result = parser.parse_support_formula(r"g_a(F(a,n))=G(a,n).")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "relation")
        self.assertEqual(ast["left"]["kind"], "application")
        self.assertEqual(ast["left"]["function"], "g_a")

    def test_parses_multi_typed_binder_and_superscripted_relation(self):
        result = parser.parse_support_formula(
            r"\forall f,h\colon P\to W\;"
            r"\bigl(\operatorname{StageDependentRecursionSolution}(f,(P,S,1),W,c,\Phi)"
            r"\land \operatorname{StageDependentRecursionSolution}(h,(P,S,1),W,c,\Phi)"
            r"\Longrightarrow f=h\bigr)."
        )
        ast = result["ast"]
        self.assertEqual(ast["kind"], "forall")
        self.assertEqual(ast["binder"]["binder_id"], "f")
        self.assertEqual(ast["body"]["kind"], "forall")
        self.assertEqual(ast["body"]["binder"]["binder_id"], "h")
        self.assertEqual(ast["body"]["body"]["kind"], "implies")

    def test_parses_square_bracket_grouped_implication(self):
        result = parser.parse_support_formula(
            r"\Bigl[(\forall k\in P,\ \neg(k<1))"
            r"\land(\forall k,n\in P,\ k<S(n)\Longleftrightarrow(k<n\lor k=n))"
            r"\Bigr]\Longrightarrow\forall n\in P,\ \varphi(n)."
        )
        ast = result["ast"]
        self.assertEqual(ast["kind"], "implies")
        self.assertEqual(ast["left"]["kind"], "and")
        self.assertEqual(ast["right"]["kind"], "forall")

    def test_parses_short_symbolic_implication_and_iff(self):
        result = parser.parse_support_formula(
            r"\bigl(x\in A\,\rightarrow\,\bigl(y\in B\,\leftrightarrow\,z\in C\bigr)\bigr)."
        )
        ast = result["ast"]
        self.assertEqual(ast["kind"], "implies")
        self.assertEqual(ast["right"]["kind"], "iff")

    def test_parses_text_implies_and_iff_connectives(self):
        result = parser.parse_support_formula(
            r"x\in A\quad\text{implies}\quad"
            r"\bigl(y\in B\quad\text{if and only if}\quad z\in C\bigr)."
        )
        ast = result["ast"]
        self.assertEqual(ast["kind"], "implies")
        self.assertEqual(ast["right"]["kind"], "iff")

    def test_non_connective_text_implies_word_remains_raw(self):
        result = parser.parse_support_formula(r"\theta \text{ implies no choice of } x.")
        self.assertEqual(result["ast"]["kind"], "raw_latex")

    def test_parses_set_builder_rhs_as_raw_term_not_variable(self):
        result = parser.parse_support_formula(
            r"""
\[
\operatorname{PresburgerArithmetic}(T)
\Longleftrightarrow
T=
\left\{
\varphi:
\varphi \text{ is an }\mathcal L_{\mathrm{Pres}}\text{-sentence and }
(\mathbb{N},0,S,+,<)\models\varphi
\right\}.
\]
"""
        )
        rhs = result["ast"]["right"]["right"]
        self.assertEqual(rhs["kind"], "raw_latex")
        self.assertNotIn("binder_id", rhs)

    def test_parses_satisfaction_and_provability_as_relations(self):
        result = parser.parse_support_formula(r"\Gamma\models\varphi\Longrightarrow\Gamma\vdash\varphi.")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "implies")
        self.assertEqual(ast["left"]["relation"], r"\models")
        self.assertEqual(ast["right"]["relation"], r"\vdash")

    def test_parses_formula_equivalence_as_relation(self):
        result = parser.parse_support_formula(r"(\varphi\lor\psi)\equiv\varphi.")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "relation")
        self.assertEqual(ast["relation"], r"\equiv")
        self.assertEqual(ast["left"]["kind"], "formula_connective")
        self.assertEqual(ast["left"]["operator"], r"\lor")
        self.assertEqual(ast["left"]["left"], {"kind": "formula_variable", "name": "varphi"})
        self.assertEqual(ast["left"]["right"], {"kind": "formula_variable", "name": "psi"})
        self.assertEqual(ast["right"], {"kind": "formula_variable", "name": "varphi"})

    def test_parses_nested_formula_object_equivalence_tree(self):
        result = parser.parse_support_formula(
            r"\varphi\uparrow\psi\equiv\neg(\varphi\land(\psi\lor\chi))."
        )
        ast = result["ast"]
        self.assertEqual(ast["kind"], "relation")
        self.assertEqual(ast["relation"], r"\equiv")
        self.assertEqual(ast["left"]["operator"], r"\uparrow")
        self.assertEqual(ast["right"]["kind"], "formula_not")
        nested = ast["right"]["operand"]
        self.assertEqual(nested["operator"], r"\land")
        self.assertEqual(nested["right"]["operator"], r"\lor")

    def test_parses_formula_object_implication_equivalence_tree(self):
        result = parser.parse_support_formula(r"\varphi\to\psi\equiv\neg\varphi\lor\psi.")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "relation")
        self.assertEqual(ast["left"]["operator"], r"\to")
        self.assertEqual(ast["right"]["operator"], r"\lor")

    def test_parses_formula_object_biconditional_expansion_tree(self):
        result = parser.parse_support_formula(
            r"\varphi\leftrightarrow\psi\equiv(\varphi\to\psi)\land(\psi\to\varphi)."
        )
        ast = result["ast"]
        self.assertEqual(ast["left"]["operator"], r"\leftrightarrow")
        self.assertEqual(ast["right"]["operator"], r"\land")
        self.assertEqual(ast["right"]["left"]["operator"], r"\to")
        self.assertEqual(ast["right"]["right"]["operator"], r"\to")

    def test_parses_equivalence_relations_inside_meta_implication(self):
        result = parser.parse_support_formula(r"\varphi\equiv\psi\Longrightarrow C[\varphi]\equiv C[\psi].")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "implies")
        self.assertEqual(ast["left"]["relation"], r"\equiv")
        self.assertEqual(ast["right"]["relation"], r"\equiv")

    def test_parses_equivalence_relations_under_connective_as_subtrees(self):
        result = parser.parse_support_formula(
            r"(\varphi\equiv\psi\land\psi\equiv\chi)\Longrightarrow\varphi\equiv\chi."
        )
        ast = result["ast"]
        self.assertEqual(ast["kind"], "implies")
        self.assertEqual(ast["left"]["kind"], "and")
        self.assertEqual(ast["left"]["left"]["relation"], r"\equiv")
        self.assertEqual(ast["left"]["right"]["relation"], r"\equiv")
        self.assertEqual(ast["right"]["relation"], r"\equiv")

    def test_equiv_relation_does_not_preempt_symbolic_implication(self):
        result = parser.parse_support_formula(
            r"(R_{4}\equiv P_{6}\land\circ\in\{\neg,\land,\lor,\to,\leftrightarrow\})"
            r"\rightarrow Q."
        )
        ast = result["ast"]
        self.assertEqual(ast["kind"], "implies")
        self.assertEqual(ast["left"]["kind"], "and")
        self.assertEqual(ast["left"]["left"]["relation"], r"\equiv")
        self.assertEqual(ast["left"]["right"]["relation"], r"\in")

    def test_symbolic_implication_with_equiv_rejects_missing_rhs(self):
        with self.assertRaises(parser.SemanticLatexParseError):
            parser.parse_support_formula(r"R_{4}\equiv P_{6}\rightarrow.")

    def test_strips_spacing_macros_from_implication_operands(self):
        result = parser.parse_support_formula(r"\varphi \;\Rightarrow\; \forall x\,\varphi.")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "implies")
        self.assertEqual(ast["left"], {"kind": "variable", "binder_id": "varphi"})
        self.assertEqual(ast["right"]["kind"], "forall")

    def test_parses_unbounded_existential_after_implication(self):
        result = parser.parse_support_formula(r"\varphi[t/x] \;\Rightarrow\; \exists x\,\varphi.")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "implies")
        self.assertEqual(ast["right"]["kind"], "exists")
        self.assertEqual(ast["right"]["binder"]["binder_id"], "x")

    def test_parses_curried_interpretation_application_generically(self):
        result = parser.parse_support_formula(
            r"I(f)\bigl(\llbracket t_1\rrbracket_{\mathcal M,s},\ldots,\llbracket t_n\rrbracket_{\mathcal M,s}\bigr)=y."
        )
        ast = result["ast"]
        self.assertEqual(ast["left"]["kind"], "application")
        self.assertEqual(ast["left"]["function"], "I")
        self.assertEqual(ast["left"]["arguments"][0], {"kind": "variable", "binder_id": "f"})
        self.assertEqual(len(ast["left"]["arguments"]), 4)

    def test_parses_set_builder_rhs_with_canonical_spacing(self):
        result = parser.parse_support_formula(
            r"\mathcal{L}(\Sigma)=\{s\in A^* \mid s\in\operatorname{Terms}(\Sigma)\text{ or }s\in\operatorname{WFF}(\Sigma)\}."
        )
        ast = result["ast"]
        self.assertEqual(ast["right"]["kind"], "raw_latex")
        self.assertIn(r"\{sin A^*", ast["right"]["latex"])
        self.assertIn("lor", ast["right"]["latex"])

    def test_parses_set_builder_rhs_with_canonical_membership_spacing(self):
        result = parser.parse_support_formula(r"A\cup B=\{\, x \mid x \in A \lor x \in B \,\}.")
        ast = result["ast"]
        self.assertEqual(ast["right"]["kind"], "raw_latex")
        self.assertEqual(ast["right"]["latex"], r"\{x mid xin A lor xin B\}")

    def test_parses_chained_equality_as_adjacent_relation_sequence(self):
        result = parser.parse_support_formula(r"A=B=C.")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "formula_sequence")
        self.assertEqual(ast["left"]["relation"], "=")
        self.assertEqual(ast["left"]["left"], {"kind": "variable", "binder_id": "A"})
        self.assertEqual(ast["left"]["right"], {"kind": "variable", "binder_id": "B"})
        self.assertEqual(ast["right"]["left"], {"kind": "variable", "binder_id": "B"})
        self.assertEqual(ast["right"]["right"], {"kind": "variable", "binder_id": "C"})

    def test_colon_equals_definition_is_not_chained_equality(self):
        result = parser.parse_support_formula(r"A:=B.")
        self.assertEqual(result["ast"]["kind"], "relation")
        self.assertEqual(result["ast"]["relation"], r"\colon")

    def test_coloneqq_definition_is_colon_relation_without_stray_token(self):
        result = parser.parse_support_formula(r"m+n \coloneqq f_m(n).")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "relation")
        self.assertEqual(ast["relation"], r"\colon")
        self.assertEqual(ast["left"], {"kind": "variable", "binder_id": "m+n"})
        self.assertEqual(
            ast["right"],
            {
                "kind": "application",
                "function": "f_m",
                "arguments": [{"kind": "variable", "binder_id": "n"}],
            },
        )

    def test_coloneqq_definition_rejects_missing_rhs(self):
        with self.assertRaises(parser.SemanticLatexParseError):
            parser.parse_support_formula(r"m+n \coloneqq.")

    def test_colon_equals_chained_definition_keeps_rhs_raw(self):
        result = parser.parse_support_formula(
            r"0_{\mathbb{R}}:=(0_{\mathbb{Q}})^{\ast} =\{r\in\mathbb{Q}:r<0_{\mathbb{Q}}\}."
        )
        ast = result["ast"]
        self.assertEqual(ast["kind"], "relation")
        self.assertEqual(ast["relation"], r"\colon")
        self.assertEqual(ast["right"]["kind"], "raw_latex")
        self.assertIn("COLON", ast["right"]["latex"])

    def test_colon_equals_set_builder_union_with_order_guards_keeps_rhs_raw(self):
        result = parser.parse_support_formula(
            r"\alpha\cdot\beta := "
            r"\{r\in\mathbb{Q}:r<0_{\mathbb{Q}}\} "
            r"\cup \{p\cdot q:p\in\alpha,\ q\in\beta,\ p\ge 0_{\mathbb{Q}},\ q\ge 0_{\mathbb{Q}}\}."
        )
        ast = result["ast"]
        self.assertEqual(ast["kind"], "relation")
        self.assertEqual(ast["relation"], r"\colon")
        self.assertEqual(ast["right"]["kind"], "raw_latex")
        self.assertIn("pge 0", ast["right"]["latex"])
        self.assertNotIn("GEQ", ast["right"]["latex"])

    def test_infinity_command_does_not_become_membership_relation(self):
        result = parser.parse_support_formula(r"-\infty<x<+\infty.")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "relation")
        self.assertEqual(ast["relation"], "<")
        self.assertEqual(ast["left"], {"kind": "variable", "binder_id": "-infty"})

    def test_side_conditioned_asymptotic_term_remains_raw(self):
        result = parser.parse_support_formula(r"f(x)=o(g(x))\qquad (x\to a).")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "relation")
        self.assertEqual(ast["right"]["kind"], "raw_latex")
        self.assertNotEqual(ast["right"].get("kind"), "application")

    def test_parses_comma_separated_mathsf_typed_signature(self):
        result = parser.parse_support_formula(r"\mathsf{succ},\mathsf{pred}:Z\to Z.")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "relation")
        self.assertEqual(ast["relation"], r"\colon")
        self.assertEqual(ast["left"]["kind"], "tuple")
        self.assertEqual([item["binder_id"] for item in ast["left"]["elements"]], ["mathsfsucc", "mathsfpred"])
        self.assertEqual(ast["right"]["function"], "function_space")

    def test_modular_equivalence_definition_uses_top_level_biconditional(self):
        result = parser.parse_support_formula(r"a\equiv b \pmod n \quad:\Longleftrightarrow\quad n\mid (a-b).")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "iff")
        self.assertEqual(ast["left"]["kind"], "relation")
        self.assertEqual(ast["left"]["relation"], r"\equiv")

    def test_side_conditioned_formula_equivalence_remains_raw(self):
        result = parser.parse_support_formula(
            r"\forall x\,\varphi \;\equiv\; \forall y\,\varphi[y/x] "
            r"\quad\text{(provided $y$ is not free in $\varphi$).}"
        )
        self.assertEqual(result["ast"]["kind"], "raw_latex")

    def test_parses_mid_set_builder_rhs_as_raw_term(self):
        result = parser.parse_support_formula(
            r"T=\{\varphi\in\operatorname{Sentences}(\mathcal{L})\mid\Gamma\vdash\varphi\}."
        )
        ast = result["ast"]
        self.assertEqual(ast["right"]["kind"], "raw_latex")
        self.assertNotIn("binder_id", ast["right"])

    def test_preference_implication_operands_remain_raw(self):
        result = parser.parse_support_formula(r"x \succsim y \;\Rightarrow\; x \succsim' y.")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "implies")
        self.assertEqual(ast["left"]["kind"], "raw_latex")
        self.assertEqual(ast["right"]["kind"], "raw_latex")

    def test_custom_infix_after_application_remains_raw(self):
        result = parser.parse_support_formula(r"a\sim a'\Longrightarrow f(a)\sim f(a').")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "implies")
        self.assertEqual(ast["left"]["kind"], "raw_latex")
        self.assertEqual(ast["right"]["kind"], "raw_latex")

    def test_parses_comma_chained_formula_object_equivalence_laws(self):
        result = parser.parse_support_formula(
            r"\varphi\land\top\equiv\varphi, \qquad \varphi\lor\bot\equiv\varphi."
        )
        ast = result["ast"]
        self.assertEqual(ast["kind"], "formula_sequence")
        self.assertEqual(ast["left"]["kind"], "relation")
        self.assertEqual(ast["left"]["left"]["operator"], r"\land")
        self.assertEqual(ast["left"]["left"]["right"], {"kind": "formula_variable", "name": "top"})
        self.assertEqual(ast["right"]["left"]["operator"], r"\lor")
        self.assertEqual(ast["right"]["left"]["right"], {"kind": "formula_variable", "name": "bot"})

    def test_parses_comma_chained_quantified_formula_object_laws(self):
        result = parser.parse_support_formula(
            r"\forall x\,\forall y\,\varphi \equiv \forall y\,\forall x\,\varphi, "
            r"\qquad \exists x\,\exists y\,\varphi \equiv \exists y\,\exists x\,\varphi."
        )
        ast = result["ast"]
        self.assertEqual(ast["kind"], "formula_sequence")
        self.assertEqual(ast["left"]["left"]["kind"], "formula_quantifier")
        self.assertEqual(ast["left"]["left"]["body"]["kind"], "formula_quantifier")
        self.assertEqual(ast["right"]["left"]["kind"], "formula_quantifier")

    def test_rejects_formula_object_binary_missing_rhs(self):
        with self.assertRaises(parser.SemanticLatexParseError):
            parser.parse_support_formula(r"\varphi\equiv(\psi\land).")

    def test_rejects_formula_object_negation_missing_operand(self):
        with self.assertRaises(parser.SemanticLatexParseError):
            parser.parse_support_formula(r"\varphi\equiv\neg.")

    def test_parses_widehat_typed_signature(self):
        result = parser.parse_support_formula(r"\widehat v:\WFF\to\mathbb{B}.")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "relation")
        self.assertEqual(ast["relation"], r"\colon")
        self.assertEqual(ast["left"], {"kind": "variable", "binder_id": "widehat_v"})
        self.assertEqual(ast["right"]["function"], "function_space")

    def test_parses_restriction_terms_generically(self):
        result = parser.parse_support_formula(
            r"v|_{\operatorname{Var}(\varphi)}=w|_{\operatorname{Var}(\varphi)}."
        )
        ast = result["ast"]
        self.assertEqual(ast["kind"], "relation")
        self.assertEqual(ast["relation"], "=")
        self.assertEqual(ast["left"]["kind"], "raw_latex")
        self.assertEqual(ast["right"]["kind"], "raw_latex")

    def test_parses_syntax_symbol_set_membership(self):
        result = parser.parse_support_formula(r"\circ\in\{\neg,\land,\lor,\to,\leftrightarrow\}.")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "relation")
        self.assertEqual(ast["relation"], r"\in")
        self.assertEqual(ast["left"], {"kind": "variable", "binder_id": "circ"})
        self.assertEqual(ast["right"]["kind"], "raw_latex")

    def test_syntax_symbol_membership_can_be_equiv_operand(self):
        result = parser.parse_support_formula(r"\circ\in\{\neg,\land,\lor,\to,\leftrightarrow\}\equiv P_{1}.")
        ast = result["ast"]
        self.assertEqual(ast["kind"], "relation")
        self.assertEqual(ast["relation"], r"\equiv")
        self.assertEqual(ast["left"]["relation"], r"\in")
        self.assertEqual(ast["left"]["left"], {"kind": "variable", "binder_id": "circ"})

    def test_non_connective_text_clause_with_relation_words_remains_raw(self):
        result = parser.parse_support_formula(
            r"\widehat v(P)=v(P)\quad\text{for every }P\in\Prop."
        )
        self.assertEqual(result["ast"]["kind"], "raw_latex")

    def test_rejects_quantifier_without_body(self):
        with self.assertRaises(parser.SemanticLatexParseError):
            parser.parse_support_formula(r"\forall n\in P\;")

    def test_rejects_unique_existence_without_body(self):
        with self.assertRaises(parser.SemanticLatexParseError):
            parser.parse_support_formula(r"\exists! u\in P\;")

    def test_rejects_relation_with_missing_rhs(self):
        with self.assertRaises(parser.SemanticLatexParseError):
            parser.parse_support_formula(r"n\mapsto")


if __name__ == "__main__":
    unittest.main()
