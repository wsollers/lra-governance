import unittest

import normalize_proof_layers as npl


class NormalizeProofLayersTests(unittest.TestCase):
    def test_converts_bold_heading_inside_existing_proof_env(self):
        text = (
            "\\begin{proof}\n"
            "\\textbf{Professional Standard Proof.}~\\\\\n"
            "Proof body.\n"
            "\\end{proof}\n"
        )

        normalized, changed = npl.normalize_text(text)

        self.assertGreater(changed, 0)
        self.assertIn("\\begin{proof}[Professional Standard Proof]\n\\LRAProofBodyStart\nProof body.", normalized)
        self.assertNotIn("\\textbf{Professional Standard Proof.}", normalized)

    def test_wraps_standalone_detailed_heading_before_structure_block(self):
        text = (
            "\\end{dependencies}\n\n"
            "\\textbf{Detailed Learning Proof.}~\\\\\n"
            "TODO: Expand the proof into a detailed learning proof.\n\n"
            "\\begin{remark*}[Proof structure]\n"
            "TODO.\n"
            "\\end{remark*}\n"
        )

        normalized, changed = npl.normalize_text(text)

        self.assertGreater(changed, 0)
        self.assertIn("\\begin{proof}[Detailed Learning Proof]\n\\LRAProofBodyStart\nTODO:", normalized)
        self.assertIn("detailed learning proof.\n\\end{proof}\n\n\\begin{remark*}[Proof structure]", normalized)

    def test_idempotent_for_canonical_shape(self):
        text = (
            "\\begin{proof}[Professional Standard Proof]\n"
            "\\LRAProofBodyStart\n"
            "Proof body.\n"
            "\\end{proof}\n"
        )

        normalized, changed = npl.normalize_text(text)

        self.assertEqual(changed, 0)
        self.assertEqual(normalized, text)

    def test_converts_standalone_professional_heading_before_proof_env(self):
        text = (
            "\\textbf{Professional Standard Proof.}~\\\\\n"
            "% MIGRATION TODO: preserved.\n"
            "\\begin{proof}\n"
            "[Proof (Professional Standard)]\n"
            "Proof body.\n"
            "\\end{proof}\n"
        )

        normalized, changed = npl.normalize_text(text)

        self.assertGreater(changed, 0)
        self.assertIn("\\begin{proof}[Professional Standard Proof]\n\\LRAProofBodyStart\n% MIGRATION TODO: preserved.\nProof body.", normalized)
        self.assertNotIn("\\textbf{Professional Standard Proof.}", normalized)
        self.assertNotIn("[Proof (Professional Standard)]", normalized)

    def test_removes_nested_detailed_pseudo_proof(self):
        text = (
            "\\begin{proof}[Detailed Learning Proof]\n"
            "\\LRAProofBodyStart\n"
            "TODO: Expand the professional proof into a detailed learning proof.\n\n"
            "\\begin{proof}[Proof (Detailed Learning)]\n"
            "Detailed body.\n"
            "\\end{proof}\n"
        )

        normalized, changed = npl.normalize_text(text)

        self.assertGreater(changed, 0)
        self.assertNotIn("\\begin{proof}\n", normalized)
        self.assertNotIn("\\begin{proof}[Proof (Detailed Learning)]", normalized)
        self.assertEqual(normalized.count("\\begin{proof}[Detailed Learning Proof]"), 1)
        self.assertIn("\\LRAProofBodyStart\nDetailed body.", normalized)
        self.assertNotIn("TODO: Expand", normalized)

    def test_closes_standalone_detailed_heading_at_eof(self):
        text = (
            "\\textbf{Detailed Learning Proof.}~\\\\\n"
            "TODO: Expand the proof into a detailed learning proof.\n"
        )

        normalized, changed = npl.normalize_text(text)

        self.assertGreater(changed, 0)
        self.assertTrue(normalized.endswith("\\end{proof}\n"))


if __name__ == "__main__":
    unittest.main()
