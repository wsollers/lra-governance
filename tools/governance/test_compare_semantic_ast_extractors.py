from __future__ import annotations

import json
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "governance" / "compare_semantic_ast_extractors.py"


SOURCE = r"""
\begin{definitionbox}{Upper Bound in the Real Line}
\begin{definition}[Upper Bound in the Real Line]
\label{def:real-upper-bound}
Let $A\subseteq\mathbb{R}$ be nonempty and let $u\in\mathbb{R}$.
Equivalently,
\[
  \operatorname{UpperBound}(u,A,P_{\mathbb{R}})\iff(\forall x\in A)(x\leq u).
\]
\end{definition}
\end{definitionbox}
"""

SOURCE_WITH_EMPTYSET = r"""
\begin{definitionbox}{Upper Bound in the Real Line}
\begin{definition}[Upper Bound in the Real Line]
\label{def:real-upper-bound}
Let $A\subseteq\mathbb{R}$ be nonempty and let $u\in\mathbb{R}$.
The element $u$ is an upper bound of $A$ if every element of $A$ is less
than or equal to $u$.
\end{definition}
\end{definitionbox}

\begin{remark*}[Failure modes]
\[
  \operatorname{EmptySet}(A).
\]
\end{remark*}
"""

SOURCE_WITH_LOWERCASE_OPERATOR = r"""
\begin{theorembox}{Rolle's Theorem}
\begin{theorem}[Rolle's Theorem]
\label{thm:rolles-theorem}
\[
  \operatorname{IsContinuous}(f,[a,b],\mathbb{R},\mathbb{R})
  \implies
  \exists c\in(a,b)\;\operatorname{Derivative}(0,f,c,\mathbb{R},\mathbb{R}).
\]
\begin{remark*}[Failure modes]
The old counterexample used \(\operatorname{sgn}(x-1/2)\).
\end{remark*}
\end{theorem}
\end{theorembox}
"""


def artifact(has_iff: bool = True) -> dict:
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
    semantic_ast = {"kind": "iff", "left": predicate, "right": quantified} if has_iff else quantified
    return {
        "identity": {
            "label": "def:real-upper-bound",
            "kind": "definition",
            "title": "Upper Bound in the Real Line",
        },
        "statement": {"semantic_ast": semantic_ast},
        "logical_forms": {
            "standard_quantified": {"ast": semantic_ast},
            "predicate_reading": {"registry_predicates": ["pred:upper-bound"], "registry_structures": []},
        },
        "failure_analysis": {
            "applicability_failures": [
                {
                    "id": "empty_input",
                    "latex": r"A=\varnothing",
                    "predicate": "IsEmpty",
                }
            ],
            "statement_failures": [],
        },
        "relationships": {"dependency_edges": []},
    }


class SemanticAstExtractorComparisonTests(unittest.TestCase):
    def run_tool(self, data: dict, source_text: str = SOURCE, extra_args: list[str] | None = None):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.tex"
            art = root / "artifact.yaml"
            source.write_text(source_text, encoding="utf-8")
            art.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            command = [
                    sys.executable,
                    str(TOOL),
                    "--source-tex",
                    str(source),
                    "--artifact",
                    str(art),
                    "--format",
                    "json",
                ]
            if extra_args:
                command.extend(extra_args)
            return subprocess.run(
                command,
                capture_output=True,
                text=True,
            )

    def test_passes_when_independent_source_facts_match_artifact_ast(self):
        result = self.run_tool(artifact())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn(payload["result"], {"pass", "pass_with_warnings"})
        self.assertTrue(any(item["extractor"] == "surface_regex" for item in payload["source_extractors"]))
        self.assertTrue(any(item["extractor"] == "displayed_math_regex" for item in payload["source_extractors"]))
        available = {item["extractor"] for item in payload["source_extractors"] if item["available"]}
        if importlib.util.find_spec("tree_sitter_language_pack") is not None:
            self.assertIn("tree_sitter_latex", available)
        if importlib.util.find_spec("pylatexenc") is not None:
            self.assertIn("pylatexenc", available)

    def test_fails_when_source_equivalence_is_missing_from_artifact_ast(self):
        result = self.run_tool(artifact(has_iff=False))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SOURCE_LOGICAL_CUE_MISSING_FROM_AST", result.stdout)

    def test_accepts_emptyset_alias_when_registry_is_enabled(self):
        result = self.run_tool(artifact(), SOURCE_WITH_EMPTYSET)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_flags_emptyset_without_alias_registry(self):
        with tempfile.TemporaryDirectory() as temp:
            empty_alias = Path(temp) / "semantic-aliases.yaml"
            empty_alias.write_text("schema_version: lra.semantic-aliases/1.0\npredicate_aliases: []\n", encoding="utf-8")
            result = self.run_tool(
                artifact(),
                SOURCE_WITH_EMPTYSET,
                ["--alias-registry", str(empty_alias)],
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SOURCE_PREDICATE_MISSING_FROM_AST", result.stdout)

    def test_lowercase_operatorname_is_not_treated_as_governed_predicate(self):
        theorem_artifact = {
            "identity": {
                "label": "thm:rolles-theorem",
                "kind": "theorem",
                "title": "Rolle's Theorem",
            },
            "statement": {
                "semantic_ast": {
                    "kind": "implies",
                    "left": {
                        "kind": "predicate",
                        "predicate_id": "pred:is-continuous",
                        "arguments": [],
                    },
                    "right": {
                        "kind": "exists",
                        "binder": {"binder_id": "c", "symbol": "c", "domain": {"kind": "constant", "name": "(a,b)"}},
                        "restriction": None,
                        "body": {
                            "kind": "predicate",
                            "predicate_id": "pred:derivative",
                            "arguments": [],
                        },
                    },
                }
            },
            "logical_forms": {"standard_quantified": {"ast": {"kind": "constant", "name": "dummy"}}},
            "relationships": {"dependency_edges": []},
        }
        result = self.run_tool(theorem_artifact, SOURCE_WITH_LOWERCASE_OPERATOR, ["--target-label", "thm:rolles-theorem"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        surface = next(item for item in payload["source_extractors"] if item["extractor"] == "surface_regex")
        self.assertNotIn("sgn", surface["predicates"])

    def test_target_label_scopes_multi_artifact_source(self):
        source = r"""
\begin{definitionbox}{Definition (First)}
\begin{definition}[First]
\label{def:first}
\[
  \operatorname{FirstThing}(x)
\]
\end{definition}
\end{definitionbox}

\begin{definitionbox}{Definition (Limit of a Function)}
\begin{definition}[Limit of a Function]
\label{def:limit-function}
\[
  \operatorname{TendsTo}(f,A,c,L,\mathbb{R})
  \Longleftrightarrow
  \forall\varepsilon>0\;\exists\delta>0.
\]
\end{definition}
\end{definitionbox}
"""
        limit_artifact = {
            "identity": {
                "label": "def:limit-function",
                "kind": "definition",
                "title": "Limit of a Function",
            },
            "statement": {
                "semantic_ast": {
                    "kind": "iff",
                    "left": {
                        "kind": "predicate",
                        "predicate_id": "pred:tends-to",
                        "arguments": [],
                    },
                    "right": {
                        "kind": "exists",
                        "binder": {
                            "binder_id": "delta",
                            "symbol": r"\delta",
                            "domain": {"kind": "constant", "name": "R"},
                        },
                        "restriction": None,
                        "body": {
                            "kind": "forall",
                            "binder": {
                                "binder_id": "eps",
                                "symbol": r"\varepsilon",
                                "domain": {"kind": "constant", "name": "R"},
                            },
                            "restriction": None,
                            "body": {"kind": "constant", "name": "dummy"},
                        },
                    },
                }
            },
            "logical_forms": {"standard_quantified": {"ast": {"kind": "constant", "name": "dummy"}}},
            "relationships": {"dependency_edges": []},
        }
        result = self.run_tool(limit_artifact, source, ["--target-label", "def:limit-function"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["source_scope"]["target_label"], "def:limit-function")
        self.assertNotIn("firstthing", json.dumps(payload).lower())


if __name__ == "__main__":
    unittest.main()
