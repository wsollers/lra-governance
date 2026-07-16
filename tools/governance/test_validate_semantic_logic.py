from __future__ import annotations

import subprocess
import sys
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tools" / "governance" / "validate_semantic_logic.py"
TEMP_ROOT = ROOT / ".test-tmp" / "semantic-logic"
SUPREMUM_REFERENCE = ROOT.parent / "lra-volume-iii" / "build" / "reference" / "def-supremum-reference" / "def-supremum"
LIMIT_REFERENCE = ROOT.parent / "lra-volume-iii" / "build" / "reference" / "def-limit-function-reference" / "def-limit-function"


def real_upper_bound_artifact() -> dict:
    predicate = {
        "kind": "predicate",
        "predicate_id": "pred:upper-bound",
        "arguments": [
            {"kind": "variable", "binder_id": "u"},
            {"kind": "variable", "binder_id": "A"},
            {"kind": "variable", "binder_id": "ctx_real_order"},
        ],
    }
    quantified = {
        "kind": "forall",
        "binder": {
            "binder_id": "x",
            "symbol": "x",
            "domain": {"kind": "variable", "binder_id": "A"},
        },
        "restriction": None,
        "body": {
            "kind": "relation",
            "relation": r"\leq",
            "left": {"kind": "variable", "binder_id": "x"},
            "right": {"kind": "variable", "binder_id": "u"},
        },
    }
    return {
        "identity": {"label": "def:real-upper-bound", "kind": "definition"},
        "context": [{"id": "ctx_real_order", "kind": "ambient_structure", "name": "ordered reals"}],
        "parameters": [
            {"id": "A", "symbol": "A"},
            {"id": "u", "symbol": "u"},
        ],
        "assumptions": [
            {"id": "A_nonempty", "kind": "nonemptiness", "latex": r"A\neq\varnothing"},
        ],
        "statement": {
            "canonical_latex": r"\operatorname{UpperBound}(u,A,P_{\mathbb{R}})\iff(\forall x\in A)(x\leq u).",
            "semantic_ast": {"kind": "iff", "left": predicate, "right": quantified},
        },
        "logical_forms": {
            "standard_quantified": {
                "latex": r"\operatorname{UpperBound}(u,A,P_{\mathbb{R}})\iff(\forall x\in A)(x\leq u).",
                "ast": {"kind": "iff", "left": predicate, "right": quantified},
            },
            "predicate_reading": {
                "latex": r"\operatorname{UpperBound}(u,A,P_{\mathbb{R}}).",
                "ast": predicate,
            },
            "negation": {
                "mechanical": {
                    "latex": r"(\exists x\in A)\neg(x\leq u).",
                    "ast": {
                        "kind": "exists",
                        "binder": {
                            "binder_id": "x_counterexample",
                            "symbol": "x",
                            "domain": {"kind": "variable", "binder_id": "A"},
                        },
                        "restriction": None,
                        "body": {
                            "kind": "not",
                            "operand": {
                                "kind": "relation",
                                "relation": r"\leq",
                                "left": {"kind": "variable", "binder_id": "x_counterexample"},
                                "right": {"kind": "variable", "binder_id": "u"},
                            },
                        },
                    },
                },
                "approved_normal_form": {
                    "latex": r"(\exists x\in A)(u<x).",
                    "ast": {
                        "kind": "exists",
                        "binder": {
                            "binder_id": "x_counterexample",
                            "symbol": "x",
                            "domain": {"kind": "variable", "binder_id": "A"},
                        },
                        "restriction": None,
                        "body": {
                            "kind": "relation",
                            "relation": "<",
                            "left": {"kind": "variable", "binder_id": "u"},
                            "right": {"kind": "variable", "binder_id": "x_counterexample"},
                        },
                    },
                },
                "normalization_requires": [
                    {
                        "id": "real_total_order",
                        "reason": "The real order is total.",
                        "dependency_label": "def:reals",
                    }
                ],
            },
            "contrapositive": None,
        },
        "failure_analysis": {
            "applicability_failures": [{"id": "outside_declared_scope"}],
            "statement_failures": [{"id": "counterexample_above_candidate"}],
        },
    }


CORRECTED_TEX = r"""
\begin{definition}[Upper Bound in the Real Line]
\operatorname{UpperBound}(u,A,P_{\mathbb{R}})
\[
  (\forall x\in A)(x\leq u).
\]
Equivalently, \operatorname{UpperBound}(u,A,P_{\mathbb{R}}).
\end{definition}
"""


@contextmanager
def temp_dir():
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    path = TEMP_ROOT / f"case-{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    yield str(path)


class SemanticLogicValidationTests(unittest.TestCase):
    def run_validator(self, artifact_data: dict):
        return self.run_validator_with_tex(artifact_data, CORRECTED_TEX)

    def run_validator_with_tex(self, artifact_data: dict, corrected_tex: str):
        with temp_dir() as temp:
            root = Path(temp)
            artifact = root / "artifact.yaml"
            corrected = root / "corrected.tex"
            artifact.write_text(yaml.safe_dump(artifact_data, sort_keys=False), encoding="utf-8")
            corrected.write_text(corrected_tex, encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--artifact",
                    str(artifact),
                    "--corrected-tex",
                    str(corrected),
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
            )

    def test_accepts_explicit_definition_iff_ast(self):
        result = self.run_validator(real_upper_bound_artifact())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"result": "pass"', result.stdout)

    def test_accepts_llm_payload_with_embedded_artifact_yaml_and_tex(self):
        with temp_dir() as temp:
            root = Path(temp)
            packet = root / "llm.json"
            packet.write_text(
                yaml.safe_dump(
                    {
                        "artifact_yaml": yaml.safe_dump(real_upper_bound_artifact(), sort_keys=False),
                        "corrected_tex": CORRECTED_TEX,
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--llm-data",
                    str(packet),
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"result": "pass"', result.stdout)

    def test_rejects_label_resolution_without_specified_volume(self):
        with temp_dir() as temp:
            root = Path(temp)
            artifact = root / "artifact.yaml"
            artifact.write_text(yaml.safe_dump(real_upper_bound_artifact(), sort_keys=False), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--artifact",
                    str(artifact),
                    "--label",
                    "def:real-upper-bound",
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--volume is required", result.stderr)

    def test_resolves_candidate_source_from_specified_volume(self):
        with temp_dir() as temp:
            root = Path(temp)
            volume = root / "lra-volume-i"
            target = volume / "volume-i" / "book-order" / "bounds"
            target.mkdir(parents=True)
            (volume / "volume-i-book-order.tex").write_text(
                r"\input{volume-i/book-order/bounds/index}" + "\n",
                encoding="utf-8",
            )
            (target / "index.tex").write_text(
                r"\chapter{Bounds}" + "\n" + r"\input{volume-i/book-order/bounds/notes-upper-lower-bounds}" + "\n",
                encoding="utf-8",
            )
            source = target / "notes-upper-lower-bounds.tex"
            source.write_text(CORRECTED_TEX.replace(r"\begin{definition}", r"\begin{definition}[Upper Bound in the Real Line]").replace(r"\end{definition}", r"\label{def:real-upper-bound}\end{definition}"), encoding="utf-8")
            artifact = root / "artifact.yaml"
            artifact.write_text(yaml.safe_dump(real_upper_bound_artifact(), sort_keys=False), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--artifact",
                    str(artifact),
                    "--repos-root",
                    str(root),
                    "--volume",
                    "i",
                    "--target",
                    "volume-i/book-order/bounds",
                    "--label",
                    "def:real-upper-bound",
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"source_resolution"', result.stdout)
        self.assertIn('"label": "def:real-upper-bound"', result.stdout)

    def test_missing_routed_artifact_becomes_generation_queue_not_failure(self):
        with temp_dir() as temp:
            root = Path(temp)
            volume = root / "lra-volume-i"
            target = volume / "volume-i" / "book-order" / "bounds"
            target.mkdir(parents=True)
            (volume / "volume-i-book-order.tex").write_text(
                r"\input{volume-i/book-order/bounds/index}" + "\n",
                encoding="utf-8",
            )
            (target / "index.tex").write_text(
                r"\chapter{Bounds}" + "\n" + r"\input{volume-i/book-order/bounds/notes-upper-lower-bounds}" + "\n",
                encoding="utf-8",
            )
            (target / "notes-upper-lower-bounds.tex").write_text(
                CORRECTED_TEX.replace(r"\begin{definition}", r"\begin{definition}[Upper Bound in the Real Line]").replace(r"\end{definition}", r"\label{def:real-upper-bound}\end{definition}"),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--repos-root",
                    str(root),
                    "--volume",
                    "i",
                    "--chapter",
                    "bounds",
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"generation_queue"', result.stdout)
        self.assertIn('"label": "def:real-upper-bound"', result.stdout)
        self.assertNotIn("def:unrouted", result.stdout)

    def test_unrouted_tex_is_not_semantic_generation_source(self):
        with temp_dir() as temp:
            root = Path(temp)
            volume = root / "lra-volume-i"
            target = volume / "volume-i" / "book-order" / "bounds"
            target.mkdir(parents=True)
            (volume / "volume-i-book-order.tex").write_text(
                r"\input{volume-i/book-order/bounds/index}" + "\n",
                encoding="utf-8",
            )
            (target / "index.tex").write_text(
                r"\chapter{Bounds}" + "\n" + r"\input{volume-i/book-order/bounds/routed}" + "\n",
                encoding="utf-8",
            )
            (target / "routed.tex").write_text(
                r"\begin{definition}[Routed]\label{def:routed}Routed.\end{definition}" + "\n",
                encoding="utf-8",
            )
            (target / "unrouted.tex").write_text(
                r"\begin{definition}[Unrouted]\label{def:unrouted}Unrouted.\end{definition}" + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--repos-root",
                    str(root),
                    "--volume",
                    "i",
                    "--chapter",
                    "bounds",
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"label": "def:routed"', result.stdout)
        self.assertNotIn("def:unrouted", result.stdout)

    def test_rejects_definition_iff_latex_with_rhs_only_ast(self):
        data = real_upper_bound_artifact()
        rhs = data["statement"]["semantic_ast"]["right"]
        data["statement"]["semantic_ast"] = rhs
        data["logical_forms"]["standard_quantified"]["ast"] = rhs
        result = self.run_validator(data)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DEFINITIONAL_BICONDITIONAL_OMITTED_FROM_AST", result.stdout)
        self.assertIn("STANDARD_FORM_LATEX_AST_MISMATCH", result.stdout)

    def test_rejects_strict_normalization_without_order_dependency(self):
        data = real_upper_bound_artifact()
        data["logical_forms"]["negation"]["normalization_requires"] = []
        result = self.run_validator(data)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MISSING_ORDER_NORMALIZATION_ASSUMPTION", result.stdout)

    def test_rejects_wrong_implication_negation_shape(self):
        data = real_upper_bound_artifact()
        consequent = data["statement"]["semantic_ast"]["right"]
        antecedent = data["statement"]["semantic_ast"]["left"]
        data["statement"]["semantic_ast"]["right"] = {
            "kind": "implies",
            "left": antecedent,
            "right": consequent,
        }
        data["logical_forms"]["negation"]["mechanical"]["ast"] = {
            "kind": "implies",
            "left": {"kind": "not", "operand": consequent},
            "right": {"kind": "not", "operand": antecedent},
        }
        result = self.run_validator(data)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("NEGATION_DERIVATION_MISMATCH", result.stdout)

    def test_rejects_quantified_latex_without_ast_binders(self):
        data = real_upper_bound_artifact()
        data["identity"] = {"label": "thm:darboux", "kind": "theorem"}
        implication = {
            "kind": "implies",
            "left": {"kind": "predicate", "predicate_id": "pred:is-open-interval", "arguments": []},
            "right": {"kind": "exists", "binder": {"binder_id": "c", "symbol": "c", "domain": {"kind": "raw_latex", "latex": "(x,y)"}}, "restriction": None, "body": {"kind": "raw_latex", "latex": "f'(c)=lambda"}},
        }
        data["statement"] = {"canonical_latex": r"P\Rightarrow\exists c\,Q(c).", "semantic_ast": implication}
        data["logical_forms"]["standard_quantified"] = {
            "latex": r"\forall I\;\forall f\;\forall x\;\forall y\;\forall\lambda\;(P\Rightarrow\exists c\,Q(c)).",
            "ast": implication,
        }
        data["logical_forms"]["predicate_reading"] = {"latex": "P", "ast": implication["left"]}
        data["logical_forms"]["negation"] = {"mechanical": {"latex": r"\neg(P\Rightarrow Q)", "ast": {"kind": "not", "operand": implication}}, "approved_normal_form": None, "normalization_requires": []}
        result = self.run_validator_with_tex(data, r"\begin{theorem} \forall I\;\forall f\;\forall x\;\forall y\;\forall\lambda\; P\Rightarrow\exists c Q. \begin{remark*}[Failure modes]\(\neg(P\Rightarrow Q)\)\end{remark*}\end{theorem}")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("QUANTIFIED_LATEX_AST_MISMATCH", result.stdout)

    def test_rejects_comma_bound_quantifier_variables_missing_from_ast(self):
        data = real_upper_bound_artifact()
        data["identity"] = {"label": "thm:paired-variables", "kind": "theorem"}
        body = {"kind": "raw_latex", "latex": "P(x,y)"}
        data["statement"] = {"canonical_latex": r"\forall x,y\in I\;P(x,y).", "semantic_ast": body}
        data["logical_forms"]["standard_quantified"] = {
            "latex": r"\forall x,y\in I\;P(x,y).",
            "ast": {
                "kind": "forall",
                "binder": {"binder_id": "x", "symbol": "x", "domain": {"kind": "raw_latex", "latex": "I"}},
                "restriction": None,
                "body": body,
            },
        }
        data["logical_forms"]["predicate_reading"] = {"latex": r"P(x,y).", "ast": body}
        data["logical_forms"]["negation"] = {"mechanical": {"latex": r"\exists x,y\in I\;\neg P(x,y).", "ast": {"kind": "not", "operand": data["logical_forms"]["standard_quantified"]["ast"]}}, "approved_normal_form": None, "normalization_requires": []}
        result = self.run_validator_with_tex(data, r"\begin{theorem}\(\forall x,y\in I\;P(x,y)\).\end{theorem}")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("QUANTIFIED_VARIABLE_AST_MISMATCH", result.stdout)

    def test_rejects_corrected_tex_missing_recorded_logical_forms(self):
        data = real_upper_bound_artifact()
        data["identity"] = {"label": "thm:sample-implication", "kind": "theorem"}
        implication = {"kind": "implies", "left": {"kind": "raw_latex", "latex": "P"}, "right": {"kind": "raw_latex", "latex": "Q"}}
        data["statement"] = {"canonical_latex": r"P\Rightarrow Q.", "semantic_ast": implication}
        data["logical_forms"]["standard_quantified"] = {"latex": r"P\Rightarrow Q.", "ast": implication}
        data["logical_forms"]["predicate_reading"] = {"latex": r"P\Rightarrow Q.", "ast": implication}
        data["logical_forms"]["negation"] = {
            "mechanical": {"latex": r"\neg(P\Rightarrow Q).", "ast": {"kind": "not", "operand": implication}},
            "approved_normal_form": {"latex": r"P\land\neg Q.", "ast": {"kind": "and", "left": implication["left"], "right": {"kind": "not", "operand": implication["right"]}}},
            "normalization_requires": [],
        }
        data["logical_forms"]["contrapositive"] = {
            "latex": r"\neg Q\Rightarrow\neg P.",
            "ast": {"kind": "implies", "left": {"kind": "not", "operand": implication["right"]}, "right": {"kind": "not", "operand": implication["left"]}},
        }
        result = self.run_validator_with_tex(data, r"\begin{theorem} \(P\Rightarrow Q\). \end{theorem}")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("YAML_TEX_LOGICAL_FORM_MISSING", result.stdout)

    def theorem_equivalence_artifact(self, ast: dict) -> dict:
        data = real_upper_bound_artifact()
        data["identity"] = {"label": "thm:three-way-equivalence", "kind": "theorem"}
        data["statement"] = {
            "canonical_latex": r"E\Longleftrightarrow N\Longleftrightarrow S.",
            "semantic_ast": ast,
        }
        data["logical_forms"]["standard_quantified"] = {
            "latex": r"E\Longleftrightarrow N\Longleftrightarrow S.",
            "ast": ast,
        }
        data["logical_forms"]["predicate_reading"] = {
            "latex": r"E\Longleftrightarrow N\Longleftrightarrow S.",
            "ast": ast,
        }
        data["logical_forms"]["negation"] = {
            "mechanical": {
                "latex": r"\exists d\;\neg((E\Longleftrightarrow N)\land(N\Longleftrightarrow S)).",
                "ast": {
                    "kind": "exists",
                    "binder": {"binder_id": "d", "symbol": "d", "domain": {"kind": "raw_latex", "latex": "theorem data"}},
                    "restriction": None,
                    "body": {"kind": "not", "operand": ast},
                },
            },
            "approved_normal_form": None,
            "normalization_requires": [],
        }
        return data

    def test_rejects_nested_iff_as_three_way_equivalence(self):
        nested = {
            "kind": "iff",
            "left": {"kind": "raw_latex", "latex": "E"},
            "right": {
                "kind": "iff",
                "left": {"kind": "raw_latex", "latex": "N"},
                "right": {"kind": "raw_latex", "latex": "S"},
            },
        }
        result = self.run_validator(self.theorem_equivalence_artifact(nested))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("THREE_WAY_EQUIVALENCE_AST_INVALID", result.stdout)

    def test_rejects_iff_to_conjunction_as_three_way_equivalence(self):
        iff_to_and = {
            "kind": "iff",
            "left": {"kind": "raw_latex", "latex": "E"},
            "right": {
                "kind": "and",
                "left": {"kind": "raw_latex", "latex": "N"},
                "right": {"kind": "raw_latex", "latex": "S"},
            },
        }
        result = self.run_validator(self.theorem_equivalence_artifact(iff_to_and))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("THREE_WAY_EQUIVALENCE_AST_INVALID", result.stdout)

    def test_accepts_conjunction_of_adjacent_iff_pairs_as_three_way_equivalence(self):
        adjacent_pairs = {
            "kind": "and",
            "left": {
                "kind": "iff",
                "left": {"kind": "raw_latex", "latex": "E"},
                "right": {"kind": "raw_latex", "latex": "N"},
            },
            "right": {
                "kind": "iff",
                "left": {"kind": "raw_latex", "latex": "N"},
                "right": {"kind": "raw_latex", "latex": "S"},
            },
        }
        result = self.run_validator(self.theorem_equivalence_artifact(adjacent_pairs))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_tends_to_with_domain_as_source_point_argument(self):
        data = real_upper_bound_artifact()
        data["identity"] = {"label": "def:limit-function", "kind": "definition"}
        data["parameters"] = [
            {"id": "f", "symbol": "f", "role": "function"},
            {"id": "A", "symbol": "A", "role": "domain subset"},
            {"id": "c", "symbol": "c", "role": "source cluster point"},
            {"id": "L", "symbol": "L", "role": "target limit"},
            {"id": "R", "symbol": r"\mathbb{R}", "role": "ambient real line"},
        ]
        data["context"] = []
        tends_to_wrong = {
            "kind": "predicate",
            "predicate_id": "pred:tends-to",
            "arguments": [
                {"kind": "variable", "binder_id": "f"},
                {"kind": "variable", "binder_id": "A"},
                {"kind": "variable", "binder_id": "c"},
                {"kind": "variable", "binder_id": "L"},
                {"kind": "variable", "binder_id": "R"},
            ],
        }
        body = {
            "kind": "forall",
            "binder": {"binder_id": "eps", "symbol": r"\varepsilon", "domain": {"kind": "variable", "binder_id": "R"}},
            "restriction": None,
            "body": {"kind": "constant", "name": "placeholder"},
        }
        data["statement"] = {
            "canonical_latex": r"\operatorname{TendsTo}(f,A,c,L,\mathbb{R})\Longleftrightarrow\forall\varepsilon>0.",
            "semantic_ast": {"kind": "iff", "left": tends_to_wrong, "right": body},
        }
        data["logical_forms"]["standard_quantified"] = {"latex": r"\forall\varepsilon>0.", "ast": body}
        data["logical_forms"]["predicate_reading"] = {"latex": "", "ast": tends_to_wrong}
        data["logical_forms"]["negation"] = {
            "mechanical": {"latex": "", "ast": {"kind": "exists", "binder": {"binder_id": "eps0", "symbol": r"\varepsilon_0", "domain": {"kind": "variable", "binder_id": "R"}}, "restriction": None, "body": {"kind": "not", "operand": {"kind": "constant", "name": "placeholder"}}}},
            "approved_normal_form": None,
            "normalization_requires": [],
        }
        result = self.run_validator(data)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("pred:tends-to argument 2 (A) has role", result.stdout)

    def limit_artifact_for_domain_convention(self, *, function_type: dict | None, quantified_domain: str) -> dict:
        data = real_upper_bound_artifact()
        data["identity"] = {"label": "def:limit-function", "kind": "definition"}
        parameters = [
            {"id": "f", "symbol": "f", "role": "function", "implicit": False},
            {"id": "A", "symbol": "A", "role": "domain subset", "implicit": False},
            {"id": "B", "symbol": "B", "role": "domain subset", "implicit": False},
            {"id": "c", "symbol": "c", "role": "source point", "implicit": False},
            {"id": "L", "symbol": "L", "role": "target limit", "implicit": False},
            {"id": "R", "symbol": r"\mathbb{R}", "role": "ambient real line", "implicit": False},
        ]
        if function_type is not None:
            parameters[0]["type"] = function_type
        data["parameters"] = parameters
        data["context"] = []
        predicate = {
            "kind": "predicate",
            "predicate_id": "pred:tends-to",
            "arguments": [
                {"kind": "variable", "binder_id": "f"},
                {"kind": "variable", "binder_id": "c"},
                {"kind": "variable", "binder_id": "L"},
                {"kind": "variable", "binder_id": "R"},
                {"kind": "variable", "binder_id": "R"},
            ],
        }
        quantified = {
            "kind": "forall",
            "binder": {
                "binder_id": "x",
                "symbol": "x",
                "domain": {"kind": "variable", "binder_id": quantified_domain},
            },
            "restriction": None,
            "body": {"kind": "constant", "name": "placeholder"},
        }
        data["statement"] = {
            "canonical_latex": r"\operatorname{TendsTo}(f,c,L,\mathbb{R},\mathbb{R})\Longleftrightarrow P.",
            "semantic_ast": {"kind": "iff", "left": predicate, "right": quantified},
        }
        data["logical_forms"]["standard_quantified"] = {"latex": "P.", "ast": quantified}
        data["logical_forms"]["predicate_reading"] = {"latex": "", "ast": predicate}
        data["logical_forms"]["negation"] = {
            "mechanical": {"latex": "", "ast": {"kind": "not", "operand": quantified}},
            "approved_normal_form": None,
            "normalization_requires": [],
        }
        return data

    def test_rejects_tends_to_without_declared_function_domain(self):
        data = self.limit_artifact_for_domain_convention(function_type=None, quantified_domain="A")

        result = self.run_validator(data)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("typed-function-domain semantics", result.stdout)
        self.assertIn("has no declared domain-bearing function type", result.stdout)

    def test_rejects_tends_to_when_quantified_domain_differs_from_function_domain(self):
        data = self.limit_artifact_for_domain_convention(
            function_type={"kind": "raw_latex", "latex": r"f:A\to\mathbb{R}"},
            quantified_domain="B",
        )

        result = self.run_validator(data)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("quantified form does not range over that declared domain", result.stdout)

    def cluster_artifact(self, first_arg: dict, *, first_type: dict) -> dict:
        pred = {
            "kind": "predicate",
            "predicate_id": "pred:is-cluster",
            "arguments": [
                first_arg,
                {"kind": "variable", "binder_id": "A"},
                {"kind": "variable", "binder_id": "R"},
            ],
        }
        body = {"kind": "constant", "name": "placeholder"}
        return {
            "identity": {"label": "def:cluster-point-r", "kind": "definition"},
            "context": [],
            "parameters": [
                {"id": "n", "symbol": "n", "role": "point", "type": first_type, "implicit": False},
                {"id": "A", "symbol": "A", "role": "subset", "type": {"kind": "application", "function": "subset_of", "arguments": [{"kind": "variable", "binder_id": "R"}]}, "implicit": False},
                {"id": "R", "symbol": r"\mathbb{R}", "role": "ambient", "type": {"kind": "constant", "name": r"\mathbf{Set}"}, "implicit": False},
                {"id": "N", "symbol": r"\mathbb{N}", "role": "ambient", "type": {"kind": "constant", "name": r"\mathbf{Set}"}, "implicit": False},
            ],
            "assumptions": [],
            "statement": {
                "canonical_latex": r"\operatorname{IsCluster}(n,A,\mathbb{R})\Longleftrightarrow P.",
                "semantic_ast": {"kind": "iff", "left": pred, "right": body},
            },
            "logical_forms": {
                "standard_quantified": {"latex": "P.", "ast": body},
                "predicate_reading": {"latex": "", "ast": pred},
                "negation": {
                    "mechanical": {"latex": "", "ast": {"kind": "not", "operand": body}},
                    "approved_normal_form": None,
                    "normalization_requires": [],
                },
                "contrapositive": None,
            },
            "failure_analysis": {
                "applicability_failures": [{"id": "bad_context"}],
                "statement_failures": [{"id": "not_cluster"}],
            },
        }

    def test_rejects_registry_argument_typed_over_wrong_ambient(self):
        data = self.cluster_artifact(
            {"kind": "variable", "binder_id": "n"},
            first_type={"kind": "application", "function": "element_of", "arguments": [{"kind": "variable", "binder_id": "N"}]},
        )
        result = self.run_validator(data)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("typed over a different ambient", result.stdout)

    def test_accepts_explicit_coercion_for_wrong_source_ambient(self):
        data = self.cluster_artifact(
            {
                "kind": "application",
                "function": "coerce",
                "arguments": [{"kind": "variable", "binder_id": "n"}, {"kind": "variable", "binder_id": "R"}],
            },
            first_type={"kind": "application", "function": "element_of", "arguments": [{"kind": "variable", "binder_id": "N"}]},
        )
        result = self.run_validator(data)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_accepts_supremum_reference_derivations_when_available(self):
        if not SUPREMUM_REFERENCE.exists():
            self.skipTest("def:supremum reference package is not available")
        result = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                "--artifact",
                str(SUPREMUM_REFERENCE / "artifact.yaml"),
                "--corrected-tex",
                str(SUPREMUM_REFERENCE / "corrected.tex"),
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"result": "pass"', result.stdout)

    def test_accepts_limit_reference_with_renamed_negation_witness_when_available(self):
        if not LIMIT_REFERENCE.exists():
            self.skipTest("def:limit-function local reference package is not available")
        result = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                "--artifact",
                str(LIMIT_REFERENCE / "artifact.yaml"),
                "--corrected-tex",
                str(LIMIT_REFERENCE / "corrected.tex"),
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"result": "pass"', result.stdout)


if __name__ == "__main__":
    unittest.main()
