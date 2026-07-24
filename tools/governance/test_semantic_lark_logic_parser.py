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

    def test_lark_parser_matches_hand_parser_for_quantifier_scoped_implication(self):
        self.assert_parsers_agree(r"\forall x\in A\;P(x)\Longrightarrow Q.")

    def test_lark_parser_matches_hand_parser_for_parenthesized_quantifier_implication(self):
        self.assert_parsers_agree(r"(\forall x\in A\;P(x))\Longrightarrow Q.")

    def test_lark_parser_matches_hand_parser_for_predicate_reading(self):
        self.assert_parsers_agree(r"\operatorname{Injective}(S,P,P).")

    def test_lark_parser_matches_hand_parser_for_synthetic_predicate(self):
        self.assert_parsers_agree(r"P_{14}\bigl(S_{2},S_{5},S_{5},S_{4}\bigr).")

    def test_lark_parser_matches_hand_parser_for_synthetic_relation(self):
        self.assert_parsers_agree(r"R_{5}\bigl(\mathcal{T}_{6},c_{1},R_{2}\bigr).")

    def test_lark_parser_matches_hand_parser_for_unbounded_quantified_predicate(self):
        self.assert_parsers_agree(r"\exists P\;\exists S\;\operatorname{PeanoSystem}(P,S,1).")

    def test_lark_parser_matches_hand_parser_for_predicate_with_tuple_argument(self):
        self.assert_parsers_agree(
            r"\operatorname{IteratorFunction}(f,(P,S,1),W,c,g)"
            r"\Longrightarrow f(1)=c."
        )

    def test_lark_parser_matches_hand_parser_for_aligned_iterator_relation(self):
        self.assert_parsers_agree(
            r"""
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
        )

    def test_lark_parser_matches_hand_parser_for_typed_unique_binder(self):
        self.assert_parsers_agree(
            r"\exists! f:P\to W\;\operatorname{IteratorFunction}(f,(P,S,1),W,c,g)."
        )

    def test_lark_parser_matches_hand_parser_for_bounded_unique_binder(self):
        self.assert_parsers_agree(r"\exists! u\in P\;(S(u)=x).")

    def test_lark_parser_matches_hand_parser_for_expanded_universal_restriction(self):
        self.assert_parsers_agree(r"(\forall x)\bigl(x\in A\rightarrow P(x)\bigr).")

    def test_lark_parser_matches_hand_parser_for_expanded_existential_restriction(self):
        self.assert_parsers_agree(r"(\exists x)\bigl(x\in A\land P(x)\bigr).")

    def test_lark_parser_matches_hand_parser_for_expanded_unique_existential_restriction(self):
        self.assert_parsers_agree(r"(\exists! x)\bigl(x\in A\land P(x)\bigr).")

    def test_lark_parser_matches_hand_parser_for_expanded_quantifier_before_iff(self):
        self.assert_parsers_agree(r"(\exists! x)\bigl(x\in A\land P(x)\bigr)\leftrightarrow Q.")

    def test_lark_parser_matches_hand_parser_for_literal_colon_function_type(self):
        self.assert_parsers_agree(r"g:W\to W.")

    def test_lark_parser_matches_hand_parser_for_typed_signature_with_finite_set_domain(self):
        latex = r"a:\{P_1,\ldots,P_n\}\to\mathbb{B}."
        self.assert_parsers_agree(latex)
        ast = lark_parser.parse_support_formula(latex)["ast"]
        self.assertEqual(ast["right"]["function"], "function_space")
        self.assertEqual(ast["right"]["arguments"][0], {"kind": "raw_latex", "latex": "{P_1,ldots,P_n}"})

    def test_lark_parser_matches_hand_parser_for_subscripted_function_application(self):
        self.assert_parsers_agree(r"f_\varphi(b_1,\ldots,b_n)=\widehat v(\varphi).")

    def test_lark_parser_matches_hand_parser_for_mathcal_operator_application(self):
        self.assert_parsers_agree(r"\mathcal{P}(A)\subseteq\mathcal{P}(B).")

    def test_lark_parser_matches_hand_parser_for_set_builder_rhs_raw_term(self):
        self.assert_parsers_agree(
            r"R_{\varphi}^{\mathcal M}"
            r"="
            r"\{(a_1,\ldots,a_n)\in D^n: "
            r"\mathcal M,s[x_1\mapsto a_1,\ldots,x_n\mapsto a_n]\models\varphi\}."
        )

    def test_lark_parser_matches_hand_parser_for_operator_with_spacing_and_comma(self):
        self.assert_parsers_agree(r"\; \operatorname{Relation}(R,P,W),")

    def test_lark_parser_matches_hand_parser_for_mapsto(self):
        self.assert_parsers_agree(r"(n,w)\mapsto (S(n),\Phi(n,w)).")

    def test_lark_parser_matches_hand_parser_for_limited_parenthesized_quantifier_body(self):
        self.assert_parsers_agree(r"\forall n\in P\;(S(n)\neq 1)\land Q.")

    def test_lark_parser_matches_hand_parser_for_underscored_function_application(self):
        self.assert_parsers_agree(r"g_a(F(a,n))=G(a,n).")

    def test_lark_parser_matches_hand_parser_for_multi_typed_binder(self):
        self.assert_parsers_agree(
            r"\forall f,h\colon P\to W\;"
            r"\bigl(\operatorname{StageDependentRecursionSolution}(f,(P,S,1),W,c,\Phi)"
            r"\land \operatorname{StageDependentRecursionSolution}(h,(P,S,1),W,c,\Phi)"
            r"\Longrightarrow f=h\bigr)."
        )

    def test_lark_parser_matches_hand_parser_for_set_builder_rhs(self):
        self.assert_parsers_agree(
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

    def test_lark_parser_matches_hand_parser_for_negated_existential_rhs(self):
        self.assert_parsers_agree(
            r"\forall x \in P,\quad "
            r"x=1\Longleftrightarrow\neg\exists u \in P,\ S(u)=x."
        )

    def test_lark_parser_matches_hand_parser_for_mathcal_subscripted_raw_predicate(self):
        self.assert_parsers_agree(
            r"\mathcal C_{\mathrm{it}}(R)"
            r"\Longleftrightarrow"
            r"\operatorname{IteratorRelation}(R,(P,S,1),W,c,g)."
        )

    def test_lark_parser_matches_hand_parser_for_mathcal_subscripted_argument(self):
        self.assert_parsers_agree(
            r"\operatorname{MinimalRelation}(R^*,\mathcal C_{\mathrm{it}})"
            r"\Longrightarrow"
            r"\operatorname{IteratorRelation}(R^*,(P,S,1),W,c,g)."
        )

    def test_lark_parser_matches_hand_parser_for_text_proposition_in_conjunction(self):
        self.assert_parsers_agree(
            r"\exists! \theta:P\to Q\;"
            r"\bigl(\theta \text{ is bijective}\land \theta(1_P)=1_Q"
            r"\land \forall n\in P\;(\theta(S_P(n))=S_Q(\theta(n)))\bigr)."
        )

    def test_lark_parser_matches_hand_parser_for_parenthesized_bounded_quantifier_prefix_chain(self):
        self.assert_parsers_agree(
            r"(\exists x\in A)\,(\forall y\in B)\,\bigl(x\in A\land y\in B\bigr)."
        )

    def test_lark_parser_matches_hand_parser_for_prefix_quantifier_equiv_body(self):
        self.assert_parsers_agree(r"(\exists! x_{12}\in A_{6})\,R_{4}\equiv P_{7}.")

    def test_lark_parser_rejects_prefix_quantifier_missing_equiv_rhs(self):
        with self.assertRaises(Exception):
            lark_parser.parse_support_formula(r"(\exists! x_{12}\in A_{6})\,R_{4}\equiv.")

    def test_lark_parser_matches_hand_parser_for_prefix_quantifier_scope_boundary(self):
        latex = r"(\exists x\in A)\,\bigl((\forall y\in B)\,P(y)\lor Q\bigr)."
        self.assert_parsers_agree(latex)
        ast = lark_parser.parse_support_formula(latex)["ast"]
        self.assertEqual(ast["kind"], "exists")
        self.assertEqual(ast["body"]["kind"], "or")
        self.assertEqual(ast["body"]["left"]["kind"], "forall")

    def test_lark_parser_matches_hand_parser_for_grouped_prefix_quantifier_body(self):
        self.assert_parsers_agree(
            r"(\exists x\in A)\,\bigl((\forall y\in B)\,\bigl(P(y)\lor Q\bigr)\bigr)."
        )

    def test_lark_parser_matches_hand_parser_for_subscripted_binder_symbol_surface(self):
        self.assert_parsers_agree(r"(\exists x_{5}\in A_{5})\,x_{5}\in A_{5}.")

    def test_lark_parser_matches_hand_parser_for_synthetic_registry_predicate_call(self):
        self.assert_parsers_agree(
            r"c_{4}=c_{4}\quad\text{or}\quad"
            r"P_{23}\bigl(f_{15},f_{5},\mathbb{T}_{3},\mathbb{T}_{2}\bigr)."
        )

    def test_lark_parser_matches_hand_parser_for_zero_arity_synthetic_predicate(self):
        self.assert_parsers_agree(r"P_{6}.")

    def test_lark_parser_matches_hand_parser_for_predicate_symbol_term_in_vdash(self):
        self.assert_parsers_agree(r"S_{1}\vdash P_{6}.")

    def test_lark_parser_matches_hand_parser_for_text_and_or_connectives(self):
        self.assert_parsers_agree(
            r"A\neq\varnothing"
            r"\quad\text{and}\quad"
            r"(\forall a\in A)(a\leq s)"
            r"\ \text{or}\ "
            r"(\forall u\in\mathbb{R})(s\leq u)."
        )

    def test_lark_parser_matches_hand_parser_for_non_connective_text_atom(self):
        self.assert_parsers_agree(r"\theta \text{ is bijective}.")

    def test_lark_parser_matches_hand_parser_for_presburger_signature_symbols(self):
        self.assert_parsers_agree(
            r"\operatorname{PresburgerSignature}(\mathcal{L})"
            r"\Longleftrightarrow"
            r"\mathcal{L} = \{0,S,+,<\}"
            r"\land \operatorname{ar}(S)=1"
            r"\land \operatorname{ar}(+)=2"
            r"\land \operatorname{ar}(<)=2."
        )

    def test_lark_parser_matches_hand_parser_for_strong_induction_bracket_block(self):
        self.assert_parsers_agree(
            r"\Bigl["
            r"\bigl(\forall k\in P,\ \neg(k<1)\bigr)"
            r"\land"
            r"\bigl(\forall k,n\in P,\ k<S(n)\Longleftrightarrow(k<n\lor k=n)\bigr)"
            r"\land\\"
            r"\qquad"
            r"\forall n \in P,\quad"
            r"\left("
            r"\left(\forall k \in P,\ k < n \Longrightarrow \varphi(k)\right)"
            r"\Longrightarrow"
            r"\varphi(n)"
            r"\right)"
            r"\Bigr]"
            r"\Longrightarrow"
            r"\forall n \in P,\ \varphi(n)."
        )

    def test_lark_parser_matches_hand_parser_for_short_symbolic_implication_and_iff(self):
        self.assert_parsers_agree(
            r"\bigl(x\in A\,\rightarrow\,\bigl(y\in B\,\leftrightarrow\,z\in C\bigr)\bigr)."
        )

    def test_lark_parser_matches_hand_parser_for_text_implies_and_iff_connectives(self):
        self.assert_parsers_agree(
            r"x\in A\quad\text{implies}\quad"
            r"\bigl(y\in B\quad\text{if and only if}\quad z\in C\bigr)."
        )

    def test_lark_parser_matches_hand_parser_for_non_connective_implies_text_atom(self):
        self.assert_parsers_agree(r"\theta \text{ implies no choice of } x.")

    def test_lark_parser_matches_hand_parser_for_satisfaction_and_provability(self):
        self.assert_parsers_agree(r"\Gamma\models\varphi\Longrightarrow\Gamma\vdash\varphi.")

    def test_lark_parser_matches_hand_parser_for_formula_equivalence_relation(self):
        self.assert_parsers_agree(r"(\varphi\lor\psi)\equiv\varphi.")

    def test_lark_parser_matches_hand_parser_for_nested_formula_object_equivalence_tree(self):
        latex = r"\varphi\uparrow\psi\equiv\neg(\varphi\land(\psi\lor\chi))."
        self.assert_parsers_agree(latex)
        ast = lark_parser.parse_support_formula(latex)["ast"]
        self.assertEqual(ast["left"]["operator"], r"\uparrow")
        self.assertEqual(ast["right"]["kind"], "formula_not")
        self.assertEqual(ast["right"]["operand"]["right"]["operator"], r"\lor")

    def test_lark_parser_matches_hand_parser_for_formula_object_implication_equivalence(self):
        self.assert_parsers_agree(r"\varphi\to\psi\equiv\neg\varphi\lor\psi.")

    def test_lark_parser_matches_hand_parser_for_nested_formula_object_implication_equivalence(self):
        self.assert_parsers_agree(r"\neg(\varphi\to\psi)\equiv\varphi\land\neg\psi.")

    def test_lark_parser_matches_hand_parser_for_formula_object_biconditional_expansion(self):
        self.assert_parsers_agree(
            r"\varphi\leftrightarrow\psi\equiv(\varphi\to\psi)\land(\psi\to\varphi)."
        )

    def test_lark_parser_matches_hand_parser_for_quantified_formula_object_conjunction(self):
        self.assert_parsers_agree(
            r"\forall x\,(\varphi\land\psi)\equiv(\forall x\,\varphi)\land(\forall x\,\psi)."
        )

    def test_lark_parser_matches_hand_parser_for_quantified_formula_object_disjunction(self):
        self.assert_parsers_agree(
            r"\exists x\,(\varphi\lor\psi)\equiv(\exists x\,\varphi)\lor(\exists x\,\psi)."
        )

    def test_lark_parser_matches_hand_parser_for_equivalence_relation_inside_implication(self):
        self.assert_parsers_agree(r"\varphi\equiv\psi\Longrightarrow C[\varphi]\equiv C[\psi].")

    def test_lark_parser_matches_hand_parser_for_equivalence_relations_under_connective(self):
        self.assert_parsers_agree(
            r"(\varphi\equiv\psi\land\psi\equiv\chi)\Longrightarrow\varphi\equiv\chi."
        )

    def test_lark_parser_matches_hand_parser_for_equiv_under_symbolic_implication(self):
        self.assert_parsers_agree(
            r"(R_{4}\equiv P_{6}\land\circ\in\{\neg,\land,\lor,\to,\leftrightarrow\})"
            r"\rightarrow Q."
        )

    def test_lark_parser_rejects_symbolic_implication_with_equiv_missing_rhs(self):
        with self.assertRaises(Exception):
            lark_parser.parse_support_formula(r"R_{4}\equiv P_{6}\rightarrow.")

    def test_lark_parser_matches_hand_parser_for_spaced_implication_operand(self):
        self.assert_parsers_agree(r"\varphi \;\Rightarrow\; \forall x\,\varphi.")

    def test_lark_parser_matches_hand_parser_for_unbounded_existential_after_implication(self):
        self.assert_parsers_agree(r"\varphi[t/x] \;\Rightarrow\; \exists x\,\varphi.")

    def test_lark_parser_matches_hand_parser_for_curried_interpretation_application(self):
        self.assert_parsers_agree(
            r"I(f)\bigl(\llbracket t_1\rrbracket_{\mathcal M,s},\ldots,\llbracket t_n\rrbracket_{\mathcal M,s}\bigr)=y."
        )

    def test_lark_parser_matches_hand_parser_for_set_builder_canonical_spacing(self):
        self.assert_parsers_agree(
            r"\mathcal{L}(\Sigma)=\{s\in A^* \mid s\in\operatorname{Terms}(\Sigma)\text{ or }s\in\operatorname{WFF}(\Sigma)\}."
        )

    def test_lark_parser_matches_hand_parser_for_mid_set_builder_rhs(self):
        self.assert_parsers_agree(
            r"T=\{\varphi\in\operatorname{Sentences}(\mathcal{L})\mid\Gamma\vdash\varphi\}."
        )

    def test_lark_parser_matches_hand_parser_for_spaced_mid_set_builder_rhs(self):
        self.assert_parsers_agree(
            r"T=\{\varphi\in\operatorname{Sentences}(\mathcal{L})\mid       \Gamma\vdash\varphi\}."
        )

    def test_lark_parser_matches_hand_parser_for_set_union_builder_rhs(self):
        self.assert_parsers_agree(r"A \cup B=\{\, x \mid x \in A \lor x \in B \,\}.")

    def test_lark_parser_matches_hand_parser_for_set_difference_builder_rhs(self):
        self.assert_parsers_agree(r"A \setminus B=\{\, x \mid x \in A \land x \notin B \,\}.")

    def test_lark_parser_matches_hand_parser_for_powerset_builder_rhs(self):
        self.assert_parsers_agree(r"\mathcal{P}(A):=\{\, S \mid S \subseteq A \,\}.")

    def test_lark_parser_matches_hand_parser_for_spaced_powerset_builder_rhs(self):
        self.assert_parsers_agree(r"\mathcal{P}(A) \;:=\; \{\, S \mid S \subseteq A \,\}.")

    def test_lark_parser_matches_hand_parser_for_spaced_indexed_aggregate_term(self):
        self.assert_parsers_agree(r"\bigcup_{C \in \mathcal{C}} C = A.")

    def test_lark_parser_matches_hand_parser_for_indexed_aggregate_set_builder_rhs(self):
        self.assert_parsers_agree(
            r"\bigcap_{i \in I} A_i \;:=\; \{\, x \mid \forall i \in I,\; x \in A_i \,\}."
        )

    def test_lark_parser_matches_hand_parser_for_bigm_set_builder_separator(self):
        self.assert_parsers_agree(
            r"\prod_{i \in I} A_i \;:=\; "
            r"\Bigl\{ f : I \to \bigcup_{i \in I} A_i \;\Bigm|\; "
            r"\forall i \in I,\; f(i) \in A_i \Bigr\}."
        )

    def test_lark_parser_matches_hand_parser_for_compact_mid_after_domain(self):
        self.assert_parsers_agree(
            r"\operatorname{dom}(R) \;:=\; \{\,a\in A\mid \exists b\in B,\ (a,b)\in R\,\}."
        )

    def test_lark_parser_matches_hand_parser_for_raw_arrow_type_surface(self):
        self.assert_parsers_agree(r"A\to B,")

    def test_lark_parser_matches_hand_parser_for_raw_mathbb_function_space_surface(self):
        self.assert_parsers_agree(r"\mathbb{C}\times\mathbb{C}\to\mathbb{C}.")

    def test_lark_parser_matches_hand_parser_for_composition_inverse_surface(self):
        self.assert_parsers_agree(r"(g \circ f)^{-1} = f^{-1} \circ g^{-1}.")

    def test_lark_parser_matches_hand_parser_for_raw_indexed_union_text_definition(self):
        self.assert_parsers_agree(
            r"\bigcup_{i \in I} A_i \;:=\; "
            r"\{\, x \mid \exists i \in I \text{ such that } x \in A_i \,\}."
        )

    def test_lark_parser_matches_hand_parser_for_modular_equivalence_definition(self):
        self.assert_parsers_agree(r"a\equiv b \pmod n \quad:\Longleftrightarrow\quad n\mid (a-b).")

    def test_lark_parser_matches_hand_parser_for_side_conditioned_formula_equivalence(self):
        self.assert_parsers_agree(
            r"\forall x\,\varphi \;\equiv\; \forall y\,\varphi[y/x] "
            r"\quad\text{(provided $y$ is not free in $\varphi$).}"
        )

    def test_lark_parser_matches_hand_parser_for_product_builder_rhs(self):
        self.assert_parsers_agree(r"A\times B=\{\, (a,b) \mid a \in A \text{ and } b \in B \,\}.")

    def test_lark_parser_matches_hand_parser_for_chained_equality(self):
        self.assert_parsers_agree(r"A=B=C.")

    def test_lark_parser_matches_hand_parser_for_chained_equality_with_set_builder(self):
        self.assert_parsers_agree(
            r"A \triangle B=(A \setminus B)\cup(B \setminus A)=\{\, x \mid x \in A \lor x \in B \,\}."
        )

    def test_lark_parser_matches_hand_parser_for_colon_equals_not_equality_chain(self):
        self.assert_parsers_agree(r"A:=B.")

    def test_lark_parser_matches_hand_parser_for_coloneqq_definition(self):
        self.assert_parsers_agree(r"m+n \coloneqq f_m(n).")

    def test_lark_parser_rejects_empty_coloneqq_definition(self):
        with self.assertRaises(Exception):
            lark_parser.parse_support_formula(r"m+n \coloneqq.")

    def test_lark_parser_matches_hand_parser_for_colon_equals_chained_definition(self):
        self.assert_parsers_agree(
            r"0_{\mathbb{R}}:=(0_{\mathbb{Q}})^{\ast} =\{r\in\mathbb{Q}:r<0_{\mathbb{Q}}\}."
        )

    def test_lark_parser_matches_hand_parser_for_set_builder_union_with_order_guards(self):
        self.assert_parsers_agree(
            r"\alpha\cdot\beta := "
            r"\{r\in\mathbb{Q}:r<0_{\mathbb{Q}}\} "
            r"\cup \{p\cdot q:p\in\alpha,\ q\in\beta,\ p\ge 0_{\mathbb{Q}},\ q\ge 0_{\mathbb{Q}}\}."
        )

    def test_lark_parser_matches_hand_parser_for_infinity_chained_inequality(self):
        self.assert_parsers_agree(r"-\infty<x<+\infty.")

    def test_lark_parser_matches_hand_parser_for_side_conditioned_asymptotic_term(self):
        self.assert_parsers_agree(r"f(x)=o(g(x))\qquad (x\to a).")
        self.assert_parsers_agree(r"f(x)=o(g(x))\qquad (x\to\infty).")

    def test_lark_parser_matches_hand_parser_for_comma_separated_mathsf_signature(self):
        self.assert_parsers_agree(r"\mathsf{succ},\mathsf{pred}:Z\to Z.")

    def test_lark_parser_matches_hand_parser_for_preference_implication_raw_operands(self):
        self.assert_parsers_agree(r"x \succsim y \;\Rightarrow\; x \succsim' y.")

    def test_lark_parser_matches_hand_parser_for_quantified_custom_infix_implication(self):
        self.assert_parsers_agree(
            r"\forall a,a',b,b'\in A,\, "
            r"\bigl(a\sim a'\land b\sim b'\bigr) "
            r"\Longrightarrow \bigl(a\mathbin{O}b\bigr)\sim\bigl(a'\mathbin{O}b'\bigr)."
        )

    def test_lark_parser_matches_hand_parser_for_comma_chained_formula_object_laws(self):
        self.assert_parsers_agree(
            r"\varphi\land\top\equiv\varphi, \qquad \varphi\lor\bot\equiv\varphi."
        )

    def test_lark_parser_matches_hand_parser_for_comma_chained_quantified_formula_object_laws(self):
        self.assert_parsers_agree(
            r"\forall x\,\forall y\,\varphi \equiv \forall y\,\forall x\,\varphi, "
            r"\qquad \exists x\,\exists y\,\varphi \equiv \exists y\,\exists x\,\varphi."
        )

    def test_lark_parser_matches_hand_parser_for_widehat_typed_signature(self):
        self.assert_parsers_agree(r"\widehat v:\WFF\to\mathbb{B}.")

    def test_lark_parser_matches_hand_parser_for_restriction_terms(self):
        self.assert_parsers_agree(
            r"v|_{\operatorname{Var}(\varphi)}=w|_{\operatorname{Var}(\varphi)}."
        )

    def test_lark_parser_matches_hand_parser_for_syntax_symbol_set_membership(self):
        self.assert_parsers_agree(r"\circ\in\{\neg,\land,\lor,\to,\leftrightarrow\}.")

    def test_lark_parser_matches_hand_parser_for_syntax_symbol_set_membership_under_connective(self):
        self.assert_parsers_agree(
            r"R_{4}\equiv P_{6}\land \circ\in\{\neg,\land,\lor,\to,\leftrightarrow\}."
        )

    def test_lark_parser_matches_hand_parser_for_syntax_symbol_membership_as_equiv_operand(self):
        self.assert_parsers_agree(r"\circ\in\{\neg,\land,\lor,\to,\leftrightarrow\}\equiv P_{1}.")

    def test_lark_parser_matches_hand_parser_for_text_clause_with_relation_words(self):
        self.assert_parsers_agree(r"\widehat v(P)=v(P)\quad\text{for every }P\in\Prop.")

    def test_lark_parser_matches_hand_parser_for_operatorname_set_expression_terms(self):
        self.assert_parsers_agree(
            r"\operatorname{Var}(\varphi)=\operatorname{Var}(\psi)\cup\operatorname{Var}(\chi)."
        )

    def test_lark_parser_matches_hand_parser_for_widehat_formula_object_argument(self):
        self.assert_parsers_agree(
            r"\widehat v(\varphi\land\psi)=\True"
            r"\Longleftrightarrow"
            r"\widehat v(\varphi)=\True\text{ and }\widehat v(\psi)=\True,"
        )

    def test_lark_parser_matches_hand_parser_for_colon_equals_declaration(self):
        self.assert_parsers_agree(r"\mathbb{B} := \{\mathrm{False},\mathrm{True}\}.")

    def test_lark_parser_matches_hand_parser_for_quantifier_body_with_substitution_models(self):
        self.assert_parsers_agree(r"\forall d\in D\;(\mathcal M,s[x\mapsto d]\models\psi).")

    def test_lark_parser_matches_hand_parser_for_tupled_signature_declaration(self):
        self.assert_parsers_agree(r"\operatorname{Re},\operatorname{Im}:\mathbb{C}\to\mathbb{R}")

    def test_lark_parser_matches_hand_parser_for_bracket_semantics_substitution_terms(self):
        self.assert_parsers_agree(
            r"\llbracket t[u/x]\rrbracket_{\mathcal M,s}"
            r" = "
            r"\llbracket t\rrbracket_{\mathcal M,\, s[x\mapsto\llbracket u\rrbracket_{\mathcal M,s}]}."
        )

    def test_lark_parser_matches_hand_parser_for_prime_marked_relation_surface(self):
        self.assert_parsers_agree(
            r"\forall a,b \in M,\quad a \leq b \;\Longrightarrow\; f(a) \leq' f(b)."
        )

    def test_lark_parser_matches_hand_parser_for_subscripted_sim_relation_as_raw_atoms(self):
        self.assert_parsers_agree(
            r"(a,b)\sim_{\mathbb{C}}(c,d)\Longrightarrow(c,d)\sim_{\mathbb{C}}(a,b)."
        )

    def test_lark_parser_matches_hand_parser_for_mathbin_infix_terms(self):
        self.assert_parsers_agree(r"x=x' \Longrightarrow x\mathbin{O}y=x'\mathbin{O}y.")

    def test_lark_parser_matches_hand_parser_for_subscripted_operatorname_application_term(self):
        self.assert_parsers_agree(r"\varphi\equiv \operatorname{CDNF}_{P_1,\ldots,P_n}(\varphi).")

    def test_lark_parser_matches_hand_parser_for_mathrm_named_function_application(self):
        self.assert_parsers_agree(r"\mathrm{depth}(\varphi)=\mathrm{depth}(\psi).")
        ast = lark_parser.parse_support_formula(r"\mathrm{depth}(\varphi)=\mathrm{depth}(\psi).")["ast"]
        self.assertEqual(ast["left"]["kind"], "application")
        self.assertEqual(ast["left"]["function"], "mathrmdepth")
        self.assertEqual(ast["right"]["kind"], "application")
        self.assertEqual(ast["right"]["function"], "mathrmdepth")

    def test_lark_parser_matches_hand_parser_for_mathcal_tuple_symbols(self):
        self.assert_parsers_agree(r"\mathcal{L}=(\mathcal{C},\mathcal{F},\mathcal{R},\operatorname{ar}).")

    def test_lark_parser_matches_hand_parser_for_indexed_set_operation_surfaces(self):
        self.assert_parsers_agree(
            r"U\setminus\bigcup_{i\in I}A_i = \bigcap_{i\in I}(U\setminus A_i)."
        )

    def test_lark_parser_matches_hand_parser_for_parenthesized_set_infix_surfaces(self):
        self.assert_parsers_agree(r"A \cap (B \cup C) = (A \cap B) \cup (A \cap C).")
        self.assert_parsers_agree(r"A \cup (B \cap C) = (A \cup B) \cap (A \cup C).")

    def test_lark_parser_matches_hand_parser_for_relation_algebra_term_subtrees(self):
        self.assert_parsers_agree(r"T\circ(S\circ R)=(T\circ S)\circ R.")

    def test_lark_parser_matches_hand_parser_for_set_algebra_term_subtrees(self):
        self.assert_parsers_agree(r"A \cap (B \cup C) = (A \cap B) \cup (A \cap C).")

    def test_lark_parser_matches_hand_parser_for_indexed_aggregate_term_subtrees(self):
        self.assert_parsers_agree(r"A\cap\bigcup_{i\in I}B_i=\bigcup_{i\in I}(A\cap B_i).")
        self.assert_parsers_agree(r"A\cup\bigcap_{i\in I}B_i=\bigcap_{i\in I}(A\cup B_i).")

    def test_lark_parser_matches_hand_parser_for_tuple_colon_equals_definition(self):
        self.assert_parsers_agree(r"(a,b) \;:=\; \{\{a\}, \{a,b\}\}.")

    def test_lark_parser_matches_hand_parser_for_comma_chained_relation_laws(self):
        self.assert_parsers_agree(
            r"(R^{-1})^{-1}=R,\qquad (T\circ R)^{-1}=R^{-1}\circ T^{-1}."
        )
        self.assert_parsers_agree(
            r"R\circ(P\cup Q)=(R\circ P)\cup(R\circ Q),"
            r"\qquad (S\cup T)\circ P=(S\circ P)\cup(T\circ P)."
        )

    def test_lark_parser_matches_hand_parser_for_syntax_object_membership(self):
        self.assert_parsers_agree(r"(\varphi\circ\psi)\in\WFF.")

    def test_lark_parser_matches_hand_parser_for_inference_display_as_raw_atom(self):
        self.assert_parsers_agree(r"\varphi,\qquad \varphi\to\psi \quad\therefore\quad \psi")

    def test_lark_parser_rejects_relation_with_missing_rhs(self):
        with self.assertRaises(Exception):
            lark_parser.parse_support_formula(r"n\mapsto")

    def test_lark_parser_rejects_malformed_set_literal(self):
        with self.assertRaises(Exception):
            lark_parser.parse_support_formula(r"\mathcal{L}=\{0,S,+,<.")

    def test_lark_parser_rejects_operator_call_with_missing_argument(self):
        with self.assertRaises(Exception):
            lark_parser.parse_support_formula(r"\operatorname{ar}()=2.")

    def test_lark_parser_rejects_term_operation_missing_operand(self):
        with self.assertRaises(Exception):
            lark_parser.parse_support_formula(r"A\cup=B.")

    def test_lark_parser_rejects_empty_colon_equals_declaration(self):
        with self.assertRaises(Exception):
            lark_parser.parse_support_formula(r"A:=")

    def test_lark_parser_rejects_formula_object_binary_missing_rhs(self):
        with self.assertRaises(Exception):
            lark_parser.parse_support_formula(r"\varphi\equiv(\psi\land).")

    def test_lark_parser_rejects_formula_object_negation_missing_operand(self):
        with self.assertRaises(Exception):
            lark_parser.parse_support_formula(r"\varphi\equiv\neg.")


if __name__ == "__main__":
    unittest.main()
