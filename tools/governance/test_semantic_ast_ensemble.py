from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "governance" / "semantic_ast_ensemble.py"
sys.path.insert(0, str(ROOT / "tools" / "governance"))
import semantic_ast_ensemble as ensemble  # noqa: E402


FIXTURE = r"""
\begin{theorembox}{Grouped Quantifier Fixture}
\begin{theorem}[Grouped Quantifier Fixture]
\label{thm:grouped-quantifier-fixture}
Let $A\subseteq\mathbb{R}$ be nonempty. Suppose $f:A\to\mathbb{R}$ is monotone.
Assume $a,b,c\in A$ and $a<b<c$.
\[
  \forall a,b,c\in A\;\exists y,z\in\mathbb{R}\;
  \operatorname{Between}(b,a,c)
  \Longleftrightarrow
  \operatorname{Witnesses}(y,z,a,b,c).
\]
\begin{remark*}[Standard quantified statement]
\[
  \forall a,b,c\in A\;\exists y,z\in\mathbb{R}\;
  \operatorname{Between}(b,a,c)
  \Longleftrightarrow
  \operatorname{Witnesses}(y,z,a,b,c).
\]
\end{remark*}
\begin{remark*}[Predicate reading]
\[
  \operatorname{Between}(b,a,c)\Longleftrightarrow\operatorname{Witnesses}(y,z,a,b,c).
\]
\end{remark*}
\begin{dependencies}
\hyperref[def:between]{Between};
\hyperref[def:witnesses]{Witnesses}.
\end{dependencies}
\end{theorem}
\end{theorembox}
"""


IMPLICATION_FIXTURE = r"""
\begin{theorembox}{Implication Fixture}
\begin{theorem}[Implication Fixture]
\label{thm:implication-fixture}
Given $x\in\mathbb{R}$. If $\operatorname{Positive}(x)$, then $\operatorname{Nonzero}(x)$.
\[
  \operatorname{Positive}(x)\Rightarrow\operatorname{Nonzero}(x).
\]
\end{theorem}
\end{theorembox}
"""


BOTCHED_STANDARD_FIXTURE = r"""
\begin{theorembox}{Botched Standard Quantified Fixture}
\begin{theorem}[Botched Standard Quantified Fixture]
\label{thm:botched-standard-quantified-fixture}
Let $A\subseteq\mathbb{R}$ be nonempty and bounded below. Then $-A=\{-a:a\in A\}$ is bounded above and
\[
  \sup(-A)=-\inf A.
\]
\end{theorem}
\end{theorembox}
\begin{remark*}[Standard quantified statement]
\[
\begin{aligned}
&\text{Let }A\subseteq\mathbb{R}\text{ be nonempty and bounded below.}\\
&\sup\{-a:a\in A\}=-\inf A.
\end{aligned}
\]
\end{remark*}
\begin{remark*}[Predicate reading]
\[
\operatorname{GreatestLowerBound}(t,A,P)\Longrightarrow\operatorname{LeastUpperBound}(-t,-A,P).
\]
\end{remark*}
\begin{dependencies}
\hyperref[def:infimum]{Infimum};
\hyperref[def:supremum]{Supremum}.
\end{dependencies}
\begin{remark*}[Failure modes]
\[
\forall a\in A\;(t\le a)\Longleftrightarrow\forall a\in A\;(-a\le -t).
\]
\end{remark*}
"""


GOOD_STANDARD_FIXTURE = r"""
\begin{theorembox}{Good Standard Quantified Fixture}
\begin{theorem}[Good Standard Quantified Fixture]
\label{thm:good-standard-quantified-fixture}
For every $x\in\mathbb{R}$, if $\operatorname{Positive}(x)$, then $\operatorname{Nonzero}(x)$.
\[
  \operatorname{Positive}(x)\Rightarrow\operatorname{Nonzero}(x).
\]
\end{theorem}
\end{theorembox}
\begin{remark*}[Standard quantified statement]
\[
\forall x\in\mathbb{R}\;\bigl(\operatorname{Positive}(x)\Rightarrow\operatorname{Nonzero}(x)\bigr).
\]
\end{remark*}
\begin{remark*}[Predicate reading]
\[
\operatorname{Positive}(x)\Rightarrow\operatorname{Nonzero}(x).
\]
\end{remark*}
\begin{dependencies}
\hyperref[def:positive]{Positive};
\hyperref[def:nonzero]{Nonzero}.
\end{dependencies}
"""


FAILURE_MODE_EXTRA_QUANTIFIER_FIXTURE = r"""
\begin{propositionbox}{Failure Mode Extra Quantifier Fixture}
\begin{proposition}[Failure Mode Extra Quantifier Fixture]
\label{prop:failure-mode-extra-quantifier-fixture}
If $\operatorname{UpperBound}(u,A,P)$, then $\operatorname{UpperBound}(u+c,A+c,P)$.
\end{proposition}
\end{propositionbox}
\begin{remark*}[Standard quantified statement]
\[
(\forall a\in A)(a\leq u)\Longrightarrow(\forall x\in A+c)(x\leq u+c).
\]
\end{remark*}
\begin{remark*}[Predicate reading]
\[
\operatorname{UpperBound}(u,A,P)\Longrightarrow\operatorname{UpperBound}(u+c,A+c,P).
\]
\end{remark*}
\begin{dependencies}
\hyperref[def:real-upper-bound]{Upper Bound}.
\end{dependencies}
\begin{remark*}[Failure modes]
\[
(\exists y\in A+c)(u+c<y).
\]
\end{remark*}
"""


def good_artifact() -> dict:
    return {
        "identity": {"label": "thm:grouped-quantifier-fixture", "kind": "theorem", "title": "Grouped Quantifier Fixture"},
        "statement": {
            "semantic_ast": {
                "kind": "forall",
                "binder": {"binder_id": "a", "symbol": "a", "domain": {"kind": "variable", "name": "A"}},
                "body": {
                    "kind": "forall",
                    "binder": {"binder_id": "b", "symbol": "b", "domain": {"kind": "variable", "name": "A"}},
                    "body": {
                        "kind": "forall",
                        "binder": {"binder_id": "c", "symbol": "c", "domain": {"kind": "variable", "name": "A"}},
                        "body": {
                            "kind": "exists",
                            "binder": {"binder_id": "y", "symbol": "y", "domain": {"kind": "constant", "name": "R"}},
                            "body": {
                                "kind": "exists",
                                "binder": {"binder_id": "z", "symbol": "z", "domain": {"kind": "constant", "name": "R"}},
                                "body": {
                                    "kind": "iff",
                                    "left": {"kind": "predicate", "predicate_id": "pred:between", "arguments": [{}, {}, {}]},
                                    "right": {"kind": "predicate", "predicate_id": "pred:witnesses", "arguments": [{}, {}, {}, {}, {}]},
                                },
                            },
                        },
                    },
                },
            }
        },
        "logical_forms": {},
    }


def bad_artifact() -> dict:
    data = good_artifact()
    data["statement"]["semantic_ast"] = {
        "kind": "forall",
        "binder": {"binder_id": "a", "symbol": "a"},
        "body": {"kind": "predicate", "predicate_id": "pred:between", "arguments": [{}, {}, {}]},
    }
    return data


class SemanticAstEnsembleTests(unittest.TestCase):
    def run_tool(self, source_text: str, artifact: dict | None = None, extra_args: list[str] | None = None):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tex = root / "fixture.tex"
            tex.write_text(source_text, encoding="utf-8")
            command = [sys.executable, str(TOOL), "--target", str(tex), "--repo-root", str(root), "--format", "json"]
            if artifact is not None:
                artifact_path = root / "artifact.yaml"
                artifact_path.write_text(yaml.safe_dump(artifact, sort_keys=False), encoding="utf-8")
                command.extend(["--artifact", str(artifact_path)])
            if extra_args:
                command.extend(extra_args)
            completed = subprocess.run(command, capture_output=True, text=True)
            payload = json.loads(completed.stdout)
            return completed, payload

    def test_extracts_grouped_quantifier_counts_initial_conditions_and_structures(self):
        completed, payload = self.run_tool(FIXTURE)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        report = payload["reports"][0]
        naive = next(item for item in report["ast_candidates"] if item["source"] == "local_naive_driver")
        facts = naive["facts"]
        self.assertEqual({"forall": 3, "exists": 2}, facts["quantifier_variable_counts"])
        self.assertTrue(facts["connectives"]["has_iff"])
        self.assertGreaterEqual(len(facts["let_assumptions"]), 3)
        self.assertTrue(any(item["name"] == "R" for item in facts["structures"]))

    def test_accepts_matching_artifact_ast_for_grouped_quantifiers(self):
        completed, payload = self.run_tool(FIXTURE, good_artifact())
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual("pass", payload["reports"][0]["result"])

    def test_rejects_artifact_missing_grouped_quantifier_variables_and_biconditional(self):
        completed, payload = self.run_tool(FIXTURE, bad_artifact())
        self.assertNotEqual(completed.returncode, 0)
        codes = {finding["code"] for finding in payload["reports"][0]["comparison_findings"]}
        self.assertIn("ARTIFACT_QUANTIFIER_VARIABLE_COUNT_MISMATCH", codes)
        self.assertIn("ARTIFACT_CONNECTIVE_MISSING", codes)

    def test_implication_fixture_exposes_mechanical_derivation_slots(self):
        completed, payload = self.run_tool(IMPLICATION_FIXTURE)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        derivations = payload["reports"][0]["mechanical_derivations"]
        self.assertTrue(derivations["contrapositive_available"])
        self.assertTrue(derivations["converse_available"])
        self.assertTrue(derivations["inverse_available"])

    def test_connective_shape_does_not_treat_prose_if_then_as_symbolic_implication(self):
        facts = ensemble.connective_shape("The definition fails if it omits a value. Then the set is wrong.")
        self.assertFalse(facts["has_implies"])
        self.assertEqual(0, facts["implies_count"])

    def test_failure_mode_quantifiers_do_not_pollute_core_witness_comparison(self):
        completed, payload = self.run_tool(FAILURE_MODE_EXTRA_QUANTIFIER_FIXTURE)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        codes = {finding["code"] for finding in payload["reports"][0]["comparison_findings"]}
        self.assertNotIn("QUANTIFIER_MISSING_FROM_BASELINE", codes)

    def test_uses_explicit_source_index_for_alignment(self):
        with tempfile.TemporaryDirectory() as temp:
            source_index = Path(temp) / "source-index.yaml"
            source_index.write_text(
                yaml.safe_dump(
                    {
                        "sources": [
                            {
                                "source_id": "fake:grouped",
                                "canonical_title": "Grouped Quantifier Fixture",
                                "author": "Fixture Author",
                            }
                        ]
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            completed, payload = self.run_tool(FIXTURE, extra_args=["--source-index", str(source_index)])
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        alignment = payload["reports"][0]["source_alignment"]
        self.assertEqual("matched", alignment["status"])
        self.assertGreaterEqual(alignment["hit_count"], 1)

    def test_flags_botched_standard_quantified_block(self):
        completed, payload = self.run_tool(BOTCHED_STANDARD_FIXTURE)
        self.assertNotEqual(completed.returncode, 0)
        report = payload["reports"][0]
        codes = {finding["code"] for finding in report["comparison_findings"]}
        self.assertIn("STANDARD_QUANTIFIED_CONTAINS_PROSE_LET", codes)
        self.assertIn("STANDARD_QUANTIFIED_LACKS_BINDERS", codes)
        self.assertIn("SUPPORT_BLOCK_HAS_STRONGER_QUANTIFIER_STRUCTURE", codes)
        self.assertIn("PREDICATE_READING_HAS_IMPLICATION_BUT_STANDARD_DOES_NOT", codes)
        self.assertIn("STANDARD_QUANTIFIED_ONLY_RESTATES_CONCLUSION", codes)
        suggestion = report["standard_quantified_suggestion"]
        self.assertEqual("generated_suggestion_requires_review", suggestion["status"])
        self.assertIn(r"\forall A\subseteq \mathbb{R}", suggestion["latex"])
        self.assertIn(r"A\ne\varnothing", suggestion["latex"])
        self.assertIn(r"\operatorname{BoundedBelow}(A,\mathbb{R})", suggestion["latex"])
        self.assertIn(r"\sup(-A)=-\inf A", suggestion["latex"])
        suggestions = report["standard_quantified_suggestions"]
        sources = {item["source"] for item in suggestions}
        self.assertIn("python_conservative_heuristic", sources)
        self.assertTrue({"nltk_prose", "nltk_prose_assisted"} & sources)
        self.assertTrue({"latex2sympy", "latex2sympy_assisted"} & sources)

    def test_accepts_proper_standard_quantified_block_shape(self):
        completed, payload = self.run_tool(GOOD_STANDARD_FIXTURE)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        report = payload["reports"][0]
        codes = {finding["code"] for finding in report["comparison_findings"]}
        self.assertNotIn("STANDARD_QUANTIFIED_CONTAINS_PROSE_LET", codes)
        self.assertNotIn("STANDARD_QUANTIFIED_LACKS_BINDERS", codes)
        self.assertNotIn("STANDARD_QUANTIFIED_ONLY_RESTATES_CONCLUSION", codes)
        self.assertIsNone(report["standard_quantified_suggestion"])
        self.assertEqual([], report["standard_quantified_suggestions"])

    def test_normalizes_aligned_theorem_display_into_expression_chunks(self):
        witness_inputs = ensemble.normalized_expression_witness_inputs(
            [
                r"""
\begin{aligned}
&\text{Let }A\subseteq\mathbb{R}\text{ be nonempty and bounded below.}\\
&\sup(-A)=-\inf A.
\end{aligned}
"""
            ]
        )
        normalized = {item["normalized"] for item in witness_inputs["fragments"]}
        self.assertEqual({"U", "-U"}, normalized)
        self.assertTrue(any(item["reason"] == "prose-assumption-line" for item in witness_inputs["skipped"]))
        placeholder_surfaces = [placeholder["surface"] for item in witness_inputs["fragments"] for placeholder in item["placeholders"]]
        self.assertIn(r"\sup(-A)", placeholder_surfaces)
        self.assertIn(r"\inf A", placeholder_surfaces)

    def test_normalizes_predicate_reading_as_placeholder_atoms(self):
        witness_inputs = ensemble.normalized_expression_witness_inputs(
            [
                r"""
\operatorname{GreatestLowerBound}(t,A,P)
\Longrightarrow
\operatorname{LeastUpperBound}(-t,-A,P).
"""
            ]
        )
        normalized = [item["normalized"] for item in witness_inputs["fragments"]]
        self.assertEqual(["U", "U"], normalized)
        surfaces = [item["placeholders"][0]["surface"] for item in witness_inputs["fragments"]]
        self.assertIn(r"\operatorname{GreatestLowerBound}(t,A,P)", surfaces)
        self.assertIn(r"\operatorname{LeastUpperBound}(-t,-A,P)", surfaces)

    def test_normalizer_rejects_pure_prose_and_quantifier_binders(self):
        witness_inputs = ensemble.normalized_expression_witness_inputs(
            [
                r"\text{Let }A\subseteq\mathbb{R}\text{ be nonempty.}",
                r"\forall a\in A\;(t\le a)",
                r"\neg\operatorname{LeastUpperBound}(-t,-A,P)",
            ]
        )
        self.assertEqual([], witness_inputs["fragments"])
        reasons = {item["reason"] for item in witness_inputs["skipped"]}
        self.assertIn("prose-assumption-line", reasons)
        self.assertIn("not-expression-parser-shaped", reasons)

    def test_unfolds_bounded_predicates_from_sibling_definition_artifacts(self):
        with tempfile.TemporaryDirectory() as temp:
            package_root = Path(temp)
            for slug, label, title, predicate, standard in [
                (
                    "def-bounded-below",
                    "def:bounded-below",
                    "Bounded Below",
                    r"\operatorname{BoundedBelow}(A,P)\Longleftrightarrow(\exists \ell\in S)\operatorname{LowerBound}(\ell,A,P).",
                    r"(\exists \ell\in S)(\forall x\in A)(\ell\leq x).",
                ),
                (
                    "def-bounded-above",
                    "def:bounded-above",
                    "Bounded Above",
                    r"\operatorname{BoundedAbove}(A,P)\Longleftrightarrow(\exists u\in S)\operatorname{UpperBound}(u,A,P).",
                    r"(\exists u\in S)(\forall x\in A)(x\leq u).",
                ),
            ]:
                path = package_root / slug
                path.mkdir()
                (path / "artifact.yaml").write_text(
                    yaml.safe_dump(
                        {
                            "identity": {"label": label, "kind": "definition", "title": title},
                            "logical_forms": {
                                "standard_quantified": {"latex": standard},
                                "predicate_reading": {"latex": predicate},
                            },
                        },
                        sort_keys=False,
                    ),
                    encoding="utf-8",
                )

            definitions = ensemble.load_predicate_unfolding_definitions(package_root)
            result = ensemble.unfold_predicates_in_latex(
                r"\operatorname{BoundedBelow}(A,\mathbb{R})\Longrightarrow\operatorname{BoundedAbove}(-A,\mathbb{R})",
                definitions,
            )

        self.assertEqual("unfolded", result["status"])
        self.assertEqual(2, len(result["used_definitions"]))
        self.assertIn(r"(\exists \ell\in \mathbb{R})(\forall x\in A)(\ell\leq x)", result["latex"])
        self.assertIn(r"(\exists u\in \mathbb{R})(\forall x\in -A)(x\leq u)", result["latex"])
        self.assertEqual([], result["missing_definitions"])

    def test_unfolding_preserves_predicate_when_definition_is_missing(self):
        result = ensemble.unfold_predicates_in_latex(
            r"\operatorname{BoundedBelow}(A,\mathbb{R})",
            {},
        )
        self.assertEqual("not_unfolded", result["status"])
        self.assertIn(r"\operatorname{BoundedBelow}(A,\mathbb{R})", result["latex"])
        self.assertEqual("definition artifact not available", result["missing_definitions"][0]["reason"])

    def test_unfolding_preserves_predicate_on_arity_mismatch(self):
        definitions = {
            "BoundedBelow": {
                "predicate": "BoundedBelow",
                "label": "def:bounded-below",
                "artifact": "fake/artifact.yaml",
                "parameters": ["A", "P"],
                "standard_quantified": r"(\exists \ell\in S)(\forall x\in A)(\ell\leq x).",
            }
        }
        result = ensemble.unfold_predicates_in_latex(r"\operatorname{BoundedBelow}(A)", definitions)
        self.assertEqual("not_unfolded", result["status"])
        self.assertIn(r"\operatorname{BoundedBelow}(A)", result["latex"])
        self.assertEqual("arity mismatch", result["missing_definitions"][0]["reason"])

    def test_unfolds_supremum_infimum_operator_equality_through_definitions(self):
        definitions = {
            "LeastUpperBound": {
                "predicate": "LeastUpperBound",
                "label": "def:supremum",
                "artifact": "def-supremum/artifact.yaml",
                "parameters": ["s", "A", "P"],
                "standard_quantified": (
                    r"A\neq\varnothing\land(\forall x\in A)(x\leq s)"
                    r"\land(\forall u\in S)\bigl[(\forall x\in A)(x\leq u)\Rightarrow s\leq u\bigr]."
                ),
            },
            "GreatestLowerBound": {
                "predicate": "GreatestLowerBound",
                "label": "def:infimum",
                "artifact": "def-infimum/artifact.yaml",
                "parameters": ["i", "A", "P"],
                "standard_quantified": (
                    r"A\neq\varnothing\land(\forall x\in A)(i\leq x)"
                    r"\land(\forall \ell\in S)\bigl[(\forall x\in A)(\ell\leq x)\Rightarrow \ell\leq i\bigr]."
                ),
            },
        }
        result = ensemble.unfold_predicates_in_latex(r"\sup(-A)=-\inf A", definitions)
        self.assertEqual("unfolded", result["status"])
        self.assertEqual("bridged", result["operator_bridge"]["status"])
        self.assertTrue(result["operator_bridge"]["registry_path"].endswith("notation.yaml"))
        self.assertEqual(
            [("GreatestLowerBound", "def:infimum"), ("LeastUpperBound", "def:supremum")],
            [(item["predicate"], item["definition_label"]) for item in result["used_definitions"]],
        )
        self.assertNotIn(r"\sup", result["latex"])
        self.assertNotIn(r"\inf", result["latex"])
        self.assertIn(r"(\exists i\in \mathbb{R})", result["latex"])
        self.assertIn(r"(\forall x\in A)(i\leq x)", result["latex"])
        self.assertIn(r"(\forall x\in -A)(x\leq -i)", result["latex"])

    def test_operator_bridge_requires_registry_metadata(self):
        empty_registry = {"operator_aliases": {}, "operator_bridges": [], "registry_path": "fixture-empty"}
        result = ensemble.unfold_predicates_in_latex(r"\sup(-A)=-\inf A", {}, empty_registry)
        self.assertEqual("not_unfolded", result["status"])
        self.assertEqual("not_bridged", result["operator_bridge"]["status"])
        self.assertIn(r"\sup(-A)=-\inf A", result["latex"])
        self.assertTrue(result["operator_bridge"]["unbridged_operators"])

    def test_default_notation_registry_declares_sup_inf_bridge(self):
        registry = ensemble.load_operator_bridge_registry()
        self.assertIn(r"\sup", registry["operator_aliases"])
        self.assertIn(r"\inf", registry["operator_aliases"])
        self.assertEqual("LeastUpperBound", registry["operator_aliases"][r"\sup"]["result_predicate"])
        self.assertEqual("GreatestLowerBound", registry["operator_aliases"][r"\inf"]["result_predicate"])
        self.assertTrue(
            any(item.get("id") == "bridge:sup-equals-negative-inf" for item in registry["operator_bridges"])
        )

    def test_operator_bridge_reports_unrecognized_supremum_shape(self):
        result = ensemble.unfold_predicates_in_latex(r"\sup(A)+1", {})
        self.assertEqual("not_unfolded", result["status"])
        self.assertEqual("not_bridged", result["operator_bridge"]["status"])
        self.assertTrue(result["operator_bridge"]["unbridged_operators"])
        self.assertIn(r"\sup(A)+1", result["latex"])

    def test_predicate_reading_dependency_verification_passes_when_dependencies_declared(self):
        block = ensemble.FormalBlock(
            path=Path("fixture.tex"),
            repo_relative_path="fixture.tex",
            line_start=1,
            line_end=20,
            env="definition",
            label="def:supremum",
            title="Supremum",
            text=r"""
\begin{definition}[Supremum]\label{def:supremum}...\end{definition}
\begin{remark*}[Predicate reading]
\[
P=\mathsf{OrderedSet}(S,\leq),\qquad
\operatorname{LeastUpperBound}(s,A,P):=
\operatorname{UpperBound}(s,A,P).
\]
\end{remark*}
\begin{dependencies}
\hyperref[def:ordered-set]{Ordered Set};
\hyperref[def:real-upper-bound]{Upper Bound}.
\end{dependencies}
""",
        )
        components = ensemble.component_tex(block)
        result = ensemble.verify_predicate_reading_dependencies(block, components, None)
        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["missing_dependencies"])

    def test_predicate_reading_dependency_verification_reports_missing_dependencies(self):
        block = ensemble.FormalBlock(
            path=Path("fixture.tex"),
            repo_relative_path="fixture.tex",
            line_start=1,
            line_end=20,
            env="definition",
            label="def:supremum",
            title="Supremum",
            text=r"""
\begin{definition}[Supremum]\label{def:supremum}...\end{definition}
\begin{remark*}[Predicate reading]
\[
P=\mathsf{OrderedSet}(S,\leq),\qquad
\operatorname{LeastUpperBound}(s,A,P):=
\operatorname{UpperBound}(s,A,P).
\]
\end{remark*}
\begin{dependencies}
\hyperref[def:supremum]{Supremum}.
\end{dependencies}
""",
        )
        components = ensemble.component_tex(block)
        result = ensemble.verify_predicate_reading_dependencies(block, components, None)
        self.assertEqual("fail", result["status"])
        self.assertIn("def:ordered-set", result["suggested_dependency_additions"])
        self.assertIn("def:real-upper-bound", result["suggested_dependency_additions"])
        missing = {(item["kind"], item["name"], item["expected_dependency"]) for item in result["missing_dependencies"]}
        self.assertIn(("structure", "OrderedSet", "def:ordered-set"), missing)
        self.assertIn(("predicate", "UpperBound", "def:real-upper-bound"), missing)

    def test_predicate_reading_dependency_verification_accepts_abstract_bound_aliases(self):
        block = ensemble.FormalBlock(
            path=Path("fixture.tex"),
            repo_relative_path="fixture.tex",
            line_start=1,
            line_end=20,
            env="definition",
            label="def:bound",
            title="Bound",
            text=r"""
\begin{definition}[Bound]\label{def:bound}...\end{definition}
\begin{remark*}[Predicate reading]
\[
P=\mathsf{OrderedSet}(S,\leq),\qquad
\operatorname{UpperBound}(b,A,P)\lor\operatorname{LowerBound}(b,A,P).
\]
\end{remark*}
\begin{dependencies}
\hyperref[def:ordered-set]{Ordered Set};
\hyperref[def:upper-bound]{Upper Bound};
\hyperref[def:lower-bound]{Lower Bound}.
\end{dependencies}
""",
        )
        components = ensemble.component_tex(block)
        result = ensemble.verify_predicate_reading_dependencies(block, components, None)
        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["missing_dependencies"])

    def test_predicate_reading_dependency_verification_maps_extremal_elements_to_maximum_minimum(self):
        block = ensemble.FormalBlock(
            path=Path("fixture.tex"),
            repo_relative_path="fixture.tex",
            line_start=1,
            line_end=20,
            env="proposition",
            label="prop:attained-extremals",
            title="Attained Extremals",
            text=r"""
\begin{proposition}[Attained Extremals]\label{prop:attained-extremals}...\end{proposition}
\begin{remark*}[Predicate reading]
\[
P=\mathsf{OrderedSet}(\mathbb{R},\leq),\qquad
\operatorname{GreatestElement}(m,A,P)\land\operatorname{LeastElement}(n,A,P).
\]
\end{remark*}
\begin{dependencies}
\hyperref[def:ordered-set]{Ordered Set};
\hyperref[def:maximum]{Maximum};
\hyperref[def:minimum]{Minimum}.
\end{dependencies}
""",
        )
        components = ensemble.component_tex(block)
        result = ensemble.verify_predicate_reading_dependencies(block, components, None)
        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["missing_dependencies"])

    def test_predicate_reading_dependency_verification_accepts_replacement_image_alias(self):
        block = ensemble.FormalBlock(
            path=Path("fixture.tex"),
            repo_relative_path="fixture.tex",
            line_start=1,
            line_end=20,
            env="definition",
            label="def:image-fixture",
            title="Image Fixture",
            text=r"""
\begin{definition}[Image Fixture]\label{def:image-fixture}...\end{definition}
\begin{remark*}[Predicate reading]
\[
\operatorname{FunctionalRelation}(\varphi,A,B)\land
\operatorname{ReplacementImage}(B,A,\varphi).
\]
\end{remark*}
\begin{dependencies}
\hyperref[def:functional-relation]{Functional Relation};
\hyperref[def:image-set]{Image Set}.
\end{dependencies}
""",
        )
        components = ensemble.component_tex(block)
        result = ensemble.verify_predicate_reading_dependencies(block, components, None)
        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["missing_dependencies"])

    def test_predicate_reading_dependency_verification_maps_lub_property_name_to_definition(self):
        block = ensemble.FormalBlock(
            path=Path("fixture.tex"),
            repo_relative_path="fixture.tex",
            line_start=1,
            line_end=20,
            env="definition",
            label="def:least-upper-bound-property",
            title="Least Upper Bound Property",
            text=r"""
\begin{definition}[Least Upper Bound Property]\label{def:least-upper-bound-property}...\end{definition}
\begin{remark*}[Predicate reading]
\[
P=\mathsf{PartiallyOrderedSet}(S,\leq),\qquad
\operatorname{HasLeastUpperBoundProperty}(P).
\]
\end{remark*}
\begin{dependencies}
\hyperref[def:partially-ordered-set]{Partially Ordered Set};
\hyperref[def:supremum]{Supremum}.
\end{dependencies}
""",
        )
        components = ensemble.component_tex(block)
        result = ensemble.verify_predicate_reading_dependencies(block, components, None)
        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["missing_dependencies"])


if __name__ == "__main__":
    unittest.main()
