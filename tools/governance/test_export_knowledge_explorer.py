import sys
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


if __name__ == "__main__":
    unittest.main()
