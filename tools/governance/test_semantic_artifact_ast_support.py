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

    def test_replaces_stale_synthetic_binder_domains_when_aligned_latex_parses(self):
        aligned = r"""
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
        stale = {
            "kind": "forall",
            "binder": {
                "binder_id": "f1",
                "symbol": "f_1",
                "domain": {"kind": "raw_latex", "latex": "ambient context"},
            },
            "restriction": None,
            "body": {"kind": "raw_latex", "latex": aligned},
        }
        artifact = {
            "identity": {"label": "def:iterator-relation", "kind": "definition"},
            "statement": {"canonical_latex": aligned, "semantic_ast": stale},
            "logical_forms": {
                "standard_quantified": {"latex": aligned, "ast": stale},
                "predicate_reading": None,
                "negation": {
                    "mechanical": {"latex": "old", "ast": stale},
                    "approved_normal_form": None,
                    "normalization_requires": [],
                },
            },
        }

        updated = support.augment_artifact(artifact, "")

        ast = updated["logical_forms"]["standard_quantified"]["ast"]
        self.assertEqual(ast["kind"], "iff")
        self.assertNotIn("ambient context", repr(updated))
        quantified = ast["right"]["right"]["right"]
        self.assertEqual(quantified["binder"]["domain"], {"kind": "variable", "binder_id": "P"})
        self.assertEqual(quantified["body"]["binder"]["domain"], {"kind": "variable", "binder_id": "W"})

    def test_removes_stale_synthetic_binder_domains_when_latex_does_not_parse(self):
        stale = {
            "kind": "forall",
            "binder": {
                "binder_id": "f1",
                "symbol": "f_1",
                "domain": {"kind": "raw_latex", "latex": "ambient context"},
            },
            "restriction": None,
            "body": {"kind": "raw_latex", "latex": r"\forall n\in P\;(\forall m\in P)"},
        }
        artifact = {
            "identity": {"label": "thm:unsupported", "kind": "theorem"},
            "statement": {"canonical_latex": "unsupported", "semantic_ast": stale},
            "logical_forms": {
                "standard_quantified": {
                    "latex": r"\forall n\in P\;(\forall m\in P)",
                    "ast": stale,
                },
            },
        }

        updated = support.augment_artifact(artifact, "")

        self.assertNotIn("semantic_ast", updated["statement"])
        self.assertNotIn("ast", updated["logical_forms"]["standard_quantified"])
        self.assertIn("parser_witnesses", updated["logical_forms"]["standard_quantified"])
        self.assertNotIn("ambient context", repr(updated))

    def test_parameter_completion_uses_latex_symbol_aliases(self):
        artifact = {
            "identity": {"label": "def:stage-dependent-recursion-solution", "kind": "definition"},
            "parameters": [{"id": r"\Phi", "symbol": r"\Phi"}],
            "statement": {"canonical_latex": "", "semantic_ast": {"kind": "raw_latex", "latex": "old"}},
            "logical_forms": {
                "standard_quantified": {
                    "latex": r"\operatorname{StageDependentRecursionSolution}(f,(P,S,1),W,c,\Phi).",
                    "ast": {"kind": "raw_latex", "latex": "old"},
                },
            },
        }

        updated = support.augment_artifact(artifact, "")

        parameter_ids = [item["id"] for item in updated["parameters"]]
        self.assertIn(r"\Phi", parameter_ids)
        self.assertNotIn("Phi", parameter_ids)

    def test_standard_form_with_setup_display_prefers_quantified_claim_display(self):
        standard = r"""With $G\colon P\times W\to P\times W$ defined by
\[
(n,w)\mapsto (S(n),\Phi(n,w)),
\]
one has
\[
\exists! H\colon P\to P\times W\;
\left[
H(1)=(1,c)\land
\forall n\in P,\ H(S(n))=G(H(n))
\right].
\]"""
        artifact = {
            "identity": {"label": "thm:general-recursion-by-state-encoding", "kind": "theorem"},
            "statement": {"canonical_latex": standard, "semantic_ast": {"kind": "raw_latex", "latex": "old"}},
            "logical_forms": {
                "standard_quantified": {
                    "latex": standard,
                    "ast": {"kind": "raw_latex", "latex": "old"},
                },
            },
        }

        updated = support.augment_artifact(artifact, "")

        ast = updated["logical_forms"]["standard_quantified"]["ast"]
        self.assertEqual(ast["kind"], "exists_unique")
        self.assertEqual(ast["binder"]["binder_id"], "H")
        self.assertEqual(ast["body"]["right"]["kind"], "forall")
        witness_ast = updated["logical_forms"]["standard_quantified"]["parser_witnesses"]["hand_parser"]["ast"]
        self.assertEqual(witness_ast, ast)


if __name__ == "__main__":
    unittest.main()
