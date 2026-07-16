import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools" / "governance"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import generate_lean_crosswalk_html  # noqa: E402


class GenerateLeanCrosswalkHtmlTests(unittest.TestCase):
    def test_renders_lra_and_lean_lenses_with_docs_links(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "lean-crosswalk.html"

            generate_lean_crosswalk_html.write_html(ROOT / "lean-crosswalk.yaml", output)

            html = output.read_text(encoding="utf-8")
            self.assertIn("LRA ↔ Lean Crosswalk", html)
            self.assertIn("pred:least-upper-bound", html)
            self.assertIn("IsLUB", html)
            self.assertIn("sSup", html)
            self.assertIn("Bounds.IsSupremum", html)
            self.assertIn("Bounds.SupremumIffIsLUB", html)
            self.assertIn("IsUpperBound s A ∧ ∀ u, IsUpperBound u A → s ≤ u", html)
            self.assertIn("Mathlib/Order/Bounds/Defs.html#IsLUB", html)
            self.assertIn("pred:tends-to", html)
            self.assertIn("Filter.Tendsto", html)
            self.assertIn("document.body.dataset.view='lean'", html)


if __name__ == "__main__":
    unittest.main()
