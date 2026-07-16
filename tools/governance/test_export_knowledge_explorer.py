import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools" / "governance"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from extraction_pipeline import export_knowledge_explorer  # noqa: E402


class ExportKnowledgeExplorerTests(unittest.TestCase):
    def test_failure_modes_display_text_and_structured_items_are_separate(self):
        node = {
            "support_blocks": [
                {
                    "canonical_title": "failure modes",
                    "body_tex": (
                        "\\begin{description}\n"
                        "  \\item[Not an upper bound.] \\(s\\) misses an element of \\(A\\).\n"
                        "  \\item[Not least.] A smaller upper bound exists.\n"
                        "\\end{description}"
                    ),
                    "modes": [
                        {
                            "title": "Not an upper bound.",
                            "body_tex": "\\(s\\) misses an element of \\(A\\).",
                            "displays": [],
                        },
                        {
                            "title": "Not least.",
                            "body_tex": "A smaller upper bound exists.",
                            "displays": [],
                        },
                    ],
                }
            ]
        }

        failure_modes = export_knowledge_explorer.failure_modes_text_for(node)
        failure_mode_items = export_knowledge_explorer.failure_mode_items_for(node)

        self.assertIn("\\begin{description}", failure_modes)
        self.assertIn("Not an upper bound", failure_modes)
        self.assertEqual(["Not an upper bound.", "Not least."], [item["title"] for item in failure_mode_items])

    def test_semantic_relationship_edges_are_collected_and_grouped(self):
        artifact = {
            "relationships": {
                "dependency_edges": [
                    {
                        "kind": "equivalent-language",
                        "target": "def:epsilon-neighbourhood",
                        "display": "Centered Open Interval",
                        "notes": "Packages the output tolerance geometrically.",
                    }
                ],
                "ontology_edges": [
                    {
                        "kind": "instantiates",
                        "target": "pred:tends-to",
                        "display": "TendsTo",
                        "notes": "Real-line epsilon-delta instance.",
                    },
                    {
                        "kind": "uses",
                        "target": "pred:is-cluster",
                        "display": "IsCluster",
                        "notes": "Nonvacuity condition.",
                    },
                ],
                "provenance_edges": [],
                "proof_edges": [
                    {
                        "kind": "related-proof",
                        "target": "prf:limit-unique",
                        "display": "Uniqueness proof",
                        "notes": "Downstream proof link.",
                    },
                    {
                        "kind": "supports",
                        "target": "thm:limit-unique",
                        "display": "Uniqueness of Limits",
                        "notes": "The theorem uses this definition.",
                    },
                ],
            }
        }
        exported = {"id": "def:limit-function"}

        edges = export_knowledge_explorer.apply_semantic_artifact_relationships(exported, artifact)

        self.assertEqual(
            [
                ("equivalent-language", "dependency_edges", "def:epsilon-neighbourhood"),
                ("instantiates", "ontology_edges", "pred:tends-to"),
                ("uses", "ontology_edges", "pred:is-cluster"),
                ("related-proof", "proof_edges", "prf:limit-unique"),
                ("supports", "proof_edges", "thm:limit-unique"),
            ],
            [(edge["kind"], edge["namespace"], edge["to"]) for edge in edges],
        )
        self.assertEqual("pred:tends-to", exported["semantic_relationships"]["ontology_edges"][0]["target"])
        self.assertEqual("thm:limit-unique", exported["semantic_relationships"]["proof_edges"][1]["target"])

    def test_semantic_artifacts_are_discovered_by_identity_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            artifact_dir = run_dir / "semantic" / "def-limit-function"
            artifact_dir.mkdir(parents=True)
            (artifact_dir / "artifact.yaml").write_text(
                "\n".join(
                    [
                        "identity:",
                        "  label: def:limit-function",
                        "relationships:",
                        "  ontology_edges:",
                        "    - kind: instantiates",
                        "      target: pred:tends-to",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            artifacts = export_knowledge_explorer.collect_semantic_artifacts(run_dir)

        self.assertIn("def:limit-function", artifacts)
        self.assertEqual(
            "pred:tends-to",
            artifacts["def:limit-function"]["relationships"]["ontology_edges"][0]["target"],
        )


if __name__ == "__main__":
    unittest.main()
