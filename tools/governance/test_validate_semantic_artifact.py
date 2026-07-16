from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import hashlib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tools" / "governance" / "validate_semantic_artifact.py"
EXAMPLE = ROOT / "constitution" / "schema" / "examples" / "semantic-artifact.example.yaml"


class SemanticArtifactValidationTests(unittest.TestCase):
    def run_validator(self, artifact: Path, *, repos_root: Path | None = None):
        command = [
            sys.executable,
            str(VALIDATOR),
            "--artifact",
            str(artifact),
            "--governance-root",
            str(ROOT),
            "--format",
            "json",
        ]
        if repos_root is not None:
            command.extend(["--repos-root", str(repos_root)])
        return subprocess.run(
            command,
            capture_output=True, text=True,
        )

    def test_example_validates_with_raw_latex_warnings(self):
        result = self.run_validator(EXAMPLE)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("raw_latex", result.stdout)

    def test_kind_label_mismatch_fails(self):
        data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
        data["identity"]["kind"] = "theorem"
        with tempfile.TemporaryDirectory() as temp:
            artifact = Path(temp) / "artifact.yaml"
            artifact.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            result = self.run_validator(artifact)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must use prefix thm:", result.stdout)

    def test_blocking_ambiguity_fails(self):
        data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
        data["provenance"]["unresolved"] = [{
            "code": "AMBIGUOUS_ORDER_KIND",
            "question": "Does ordered set mean partial or total order?",
            "candidates": ["PartiallyOrderedSet", "TotallyOrderedSet"],
            "blocks_generation": True,
        }]
        with tempfile.TemporaryDirectory() as temp:
            artifact = Path(temp) / "artifact.yaml"
            artifact.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            result = self.run_validator(artifact)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("AMBIGUOUS_ORDER_KIND", result.stdout)

    def test_proof_incomplete_unresolved_is_warning_even_if_marked_blocking(self):
        data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
        data["provenance"]["unresolved"] = [{
            "code": "PROOF_BODY_MISSING",
            "question": "Proof bodies are intentionally reset.",
            "candidates": ["complete proof later"],
            "blocks_generation": True,
        }]
        with tempfile.TemporaryDirectory() as temp:
            artifact = Path(temp) / "artifact.yaml"
            artifact.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            result = self.run_validator(artifact)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PROOF_BODY_MISSING", result.stdout)
        self.assertIn('"governance_ready": "pass_with_warnings"', result.stdout)

    def test_equivalent_characterization_dependency_edge_is_allowed(self):
        data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
        data["relationships"]["dependency_edges"] = [{
            "kind": "equivalent-characterization",
            "target": "def:continuous-at-point",
            "display": "Continuity at a Point",
            "notes": "Sequential characterization of the same concept.",
        }]
        with tempfile.TemporaryDirectory() as temp:
            artifact = Path(temp) / "artifact.yaml"
            artifact.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            result = self.run_validator(artifact)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("FORMAL_KIND_MIGRATION_REQUIRED", result.stdout)

    def test_proof_tool_and_canonical_proof_edges_are_allowed(self):
        data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
        data["relationships"]["dependency_edges"] = [{
            "kind": "proof-tool",
            "target": "thm:extreme-value-theorem",
            "display": "Extreme Value Theorem",
            "notes": "Used in the semantic proof route.",
        }]
        data["relationships"]["proof_edges"] = [{
            "kind": "canonical-proof",
            "target": "prf:rolles-theorem",
            "display": "Proof of Rolle's Theorem",
            "notes": "Attached canonical proof record.",
        }]
        with tempfile.TemporaryDirectory() as temp:
            artifact = Path(temp) / "artifact.yaml"
            artifact.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            result = self.run_validator(artifact)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_claimed_structure_not_used_in_ast(self):
        data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
        if data["logical_forms"].get("predicate_reading") is None:
            data["logical_forms"]["predicate_reading"] = {
                "latex": r"\operatorname{Example}(\varphi)",
                "ast": {"kind": "predicate", "predicate_id": "pred:example", "arguments": []},
                "registry_predicates": [],
                "registry_structures": [],
            }
        data["logical_forms"]["predicate_reading"]["registry_structures"] = ["struct:interval"]
        with tempfile.TemporaryDirectory() as temp:
            artifact = Path(temp) / "artifact.yaml"
            artifact.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            result = self.run_validator(artifact)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("claimed in registry_structures but no AST application uses it", result.stdout)

    def test_rejects_unknown_context_ontology_id(self):
        data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
        data["context"] = [{
            "id": "real_line",
            "kind": "ambient_structure",
            "name": "real line",
            "ontology_id": "struct:real-line",
            "construction": r"\mathbb{R}",
            "ast": {"kind": "constant", "name": r"\mathbb{R}"},
        }]
        with tempfile.TemporaryDirectory() as temp:
            artifact = Path(temp) / "artifact.yaml"
            artifact.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            result = self.run_validator(artifact)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown ontology id", result.stdout)

    def test_rejects_darboux_property_as_darboux_dependency(self):
        data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
        data["identity"]["kind"] = "theorem"
        data["identity"]["label"] = "thm:darboux"
        data["relationships"]["dependency_edges"] = [{
            "kind": "prerequisite",
            "target": "thm:darboux-property",
            "display": "Darboux Property",
            "notes": "Wrongly treats derivative as continuous.",
        }]
        with tempfile.TemporaryDirectory() as temp:
            artifact = Path(temp) / "artifact.yaml"
            artifact.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            result = self.run_validator(artifact)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("thm:darboux-property is not a valid dependency", result.stdout)

    def test_author_derived_origin_requires_composite_evidence_and_derivation_rule(self):
        data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
        data["identity"]["kind"] = "theorem"
        data["identity"]["label"] = "thm:derivative-equivalence"
        data["provenance"]["origin"] = {
            "kind": "author_derived_from_source_components",
            "source_status": "single_primary_statement",
            "primary_source_statement": None,
            "component_sources": [{
                "role": "derivative_definition",
                "source_id": "SRC-000115",
                "label": None,
                "citation": "Bruckner, Elementary Real Analysis",
                "page_range": "398-405",
                "evidence": "Derivative is defined through a difference quotient limit.",
                "notes": None,
            }],
            "derivation_rule": None,
            "requires_review": True,
        }
        with tempfile.TemporaryDirectory() as temp:
            artifact = Path(temp) / "artifact.yaml"
            artifact.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            result = self.run_validator(artifact)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DERIVED_THEOREM_ORIGIN_ROUTE_REQUIRED", result.stdout)
        self.assertIn("DERIVED_THEOREM_COMPONENT_EVIDENCE_REQUIRED", result.stdout)
        self.assertIn("DERIVED_THEOREM_DERIVATION_RULE_REQUIRED", result.stdout)

    def test_author_derived_origin_accepts_component_route(self):
        data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
        data["identity"]["kind"] = "theorem"
        data["identity"]["label"] = "thm:derivative-equivalence"
        data["provenance"]["origin"] = {
            "kind": "author_derived_from_source_components",
            "source_status": "composite_source_route",
            "primary_source_statement": None,
            "component_sources": [
                {
                    "role": "limit_equivalence",
                    "source_id": "SRC-000115",
                    "label": None,
                    "citation": "Bruckner, Elementary Real Analysis",
                    "page_range": "264-272",
                    "evidence": "Function limits are presented in epsilon-delta, sequential, and mapping forms.",
                    "notes": None,
                },
                {
                    "role": "derivative_as_limit",
                    "source_id": "SRC-000115",
                    "label": None,
                    "citation": "Bruckner, Elementary Real Analysis",
                    "page_range": "398-405",
                    "evidence": "The derivative is defined as the limit of the difference quotient.",
                    "notes": None,
                },
            ],
            "derivation_rule": "Instantiate the general limit-equivalence theorem with the punctured-domain difference quotient.",
            "requires_review": True,
        }
        with tempfile.TemporaryDirectory() as temp:
            artifact = Path(temp) / "artifact.yaml"
            artifact.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            result = self.run_validator(artifact)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("DERIVED_THEOREM_", result.stdout)

    def test_unresolved_dependency_label_warns_with_repos_root(self):
        data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
        data["relationships"]["dependency_edges"] = [{
            "kind": "prerequisite",
            "target": "def:not-a-real-label",
            "display": "Missing",
            "notes": "Should warn.",
        }]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "lra-volume-iii"
            repo.mkdir()
            (repo / "source.tex").write_text("\\label{def:existing}\n", encoding="utf-8")
            data["location"]["repository"] = "wsollers/lra-volume-iii"
            data["location"]["source_file"] = "source.tex"
            data["location"]["source_hash"] = "sha256:" + "0" * 64
            artifact = root / "artifact.yaml"
            artifact.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            result = self.run_validator(artifact, repos_root=root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("DEPENDENCY_LABEL_UNRESOLVED", result.stdout)
        self.assertIn("SOURCE_HASH_MISMATCH", result.stdout)
        self.assertIn('"governance_ready": "pass_with_warnings"', result.stdout)

    def derivative_theorem_artifact(self, repo: Path, source_rel: str) -> dict:
        data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
        data["identity"]["kind"] = "theorem"
        data["identity"]["label"] = "thm:derivative-equivalence"
        data["identity"]["title"] = "Derivative Equivalence"
        data["location"]["repository"] = "wsollers/lra-volume-iii"
        data["location"]["source_file"] = source_rel
        source = repo / source_rel
        data["location"]["source_hash"] = "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
        data["relationships"]["dependency_edges"] = [
            {"kind": "prerequisite", "target": "def:derivative-at-a-point", "display": "Derivative", "notes": None},
            {"kind": "prerequisite", "target": "def:topological-definition-of-derivative-at-a-point", "display": "Topological derivative", "notes": None},
            {"kind": "prerequisite", "target": "def:sequential-definition-of-derivative-at-a-point", "display": "Sequential derivative", "notes": None},
        ]
        data["relationships"]["proof_edges"] = [
            {"kind": "related-proof", "target": "prf:derivative-equivalence", "display": "Proof", "notes": None}
        ]
        return data

    def test_theorem_dependency_hypothesis_mismatch_blocks_but_todo_proof_warns(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "lra-volume-iii"
            notes = repo / "volume-iii/book-analysis-ii/differentiation/notes/derivative-definition/notes-derivative-definition.tex"
            proofs = repo / "volume-iii/book-analysis-ii/differentiation/proofs/derivative-definition/prf-derivative-equivalence.tex"
            notes.parent.mkdir(parents=True)
            proofs.parent.mkdir(parents=True)
            notes.write_text(
                r"""
\begin{definition}
\label{def:derivative-at-a-point}
Let \(f:D\to\mathbb{R}\) and \(c\in\operatorname{int}(D)\).
\end{definition}
\begin{definition}
\label{def:topological-definition-of-derivative-at-a-point}
For every neighbourhood \(V\) of \(L\), there exists a neighbourhood \(U\) of \(c\).
\end{definition}
\begin{definition}
\label{def:sequential-definition-of-derivative-at-a-point}
Let \(c\in A\) be a limit point of \(A\).
\end{definition}
\begin{theorem}
\label{thm:derivative-equivalence}
Let \(f:A\to\mathbb{R}\) and let \(c\in A\) be a limit point of \(A\).
The following are equivalent.
\end{theorem}
""",
                encoding="utf-8",
            )
            proofs.write_text(
                r"""
\label{prf:derivative-equivalence}
\LRAProofFor{thm:derivative-equivalence}
\begin{theorem*}
For every \(\varepsilon>0\), there exists a neighbourhood \(V\) of \(c\).
\end{theorem*}
\begin{proof}
TODO: professional standard proof.
\end{proof}
\begin{dependencies}
TODO: list mathematical dependencies.
\end{dependencies}
""",
                encoding="utf-8",
            )
            artifact = root / "artifact.yaml"
            data = self.derivative_theorem_artifact(repo, str(notes.relative_to(repo)).replace("\\", "/"))
            artifact.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

            result = self.run_validator(artifact, repos_root=root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("HYPOTHESIS_ALIGNMENT_REQUIRED", result.stdout)
        self.assertIn("PROOF_NEIGHBOURHOOD_FORM_MISMATCH", result.stdout)
        self.assertIn("PROOF_INCOMPLETE", result.stdout)
        self.assertIn("PROOF_DEPENDENCIES_TODO", result.stdout)


if __name__ == "__main__":
    unittest.main()
