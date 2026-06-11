import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import repair_generated_latex as r


class RepairGeneratedLatexTests(unittest.TestCase):
    def test_repairs_malformed_return_link(self):
        text = (
            r"\begin{remark*}[Return]" "\n"
            r"\hyperref[prop:order-duality]{Return to Theorem (\texorpdfstring{\hyperref[prf:order-duality).}" "\n"
            r"\end{remark*}" "\n"
        )

        new, n = r.repair_return_links(text)

        self.assertEqual(n, 1)
        self.assertIn(r"\hyperref[prop:order-duality]{Return to Theorem}", new)
        self.assertNotIn(r"\texorpdfstring", new)

    def test_repairs_only_malformed_stub_title(self):
        text = (
            r"\label{prf:cantors-intersection-theorem}" "\n"
            r"\begin{theorem*}[\texorpdfstring{\hyperref[prf:cantors-intersection-theorem]" "\n"
            "TODO: Restate the theorem.\n"
            r"\end{theorem*}" "\n"
        )

        new, n = r.repair_bad_stub_titles(text)

        self.assertEqual(n, 1)
        self.assertIn(r"\begin{theorem*}[Cantors Intersection Theorem]", new)

    def test_leaves_valid_split_hyperref_title_alone(self):
        text = (
            r"\label{prf:order-duality}" "\n"
            r"\begin{theorem*}[\texorpdfstring{\hyperref[prf:order-duality]" "\n"
            r"{Duality Principle for Posets}}{Duality Principle for Posets}]" "\n"
            r"\end{theorem*}" "\n"
        )

        new, n = r.repair_bad_stub_titles(text)

        self.assertEqual(n, 0)
        self.assertEqual(new, text)

    def test_replaces_stale_chapter_proofs_notes_route(self):
        index = Path("volume-iii/analysis/real-analysis/index.tex")
        text = r"\input{volume-iii/analysis/real-analysis/proofs/notes/index}" "\n"
        with patch.object(r, "target_exists", side_effect=lambda _p, t: t.endswith("/proofs/index")):
            new, n = r.repair_stale_proofs_notes_inputs(index, text)

        self.assertEqual(n, 1)
        self.assertIn(r"\input{volume-iii/analysis/real-analysis/proofs/index}", new)

    def test_drops_stale_proofs_index_legacy_notes_route(self):
        proof_index = Path("volume-iv/algebra/x/proofs/index.tex")
        text = (
            r"\input{volume-iv/algebra/x/proofs/notes/index}" "\n"
            r"\input{volume-iv/algebra/x/proofs/ordered-sets/index}" "\n"
        )
        with patch.object(r, "target_exists", return_value=False):
            new, n = r.repair_stale_proofs_notes_inputs(proof_index, text)

        self.assertEqual(n, 1)
        self.assertNotIn("proofs/notes/index", new)
        self.assertIn("ordered-sets/index", new)

    def test_inserts_missing_outer_enumerate_for_orphan_items(self):
        text = (
            r"\section{Abstract Algebra}" "\n"
            r"\item \textbf{Groups}" "\n"
            r"\begin{enumerate}" "\n"
            r"\item Subgroups" "\n"
            r"\end{enumerate}" "\n"
            r"\end{enumerate}" "\n"
        )

        new, n = r.repair_missing_outer_enumerate(text)

        self.assertEqual(n, 1)
        self.assertEqual(new.count(r"\begin{enumerate}"), new.count(r"\end{enumerate}"))
        self.assertIn(r"\begin{enumerate}", new.splitlines()[1])

    def test_wires_breadcrumb_macros_after_boxes(self):
        writes = {}
        preamble = Path("repo/common/volume-preamble.tex")

        def fake_read(path):
            self.assertEqual(path, preamble)
            return "\\input{common/preamble}\n\\input{common/boxes}\n\\input{common/colors}\n"

        def fake_write(path, text, apply):
            self.assertTrue(apply)
            writes[path] = text

        with patch.object(Path, "exists", return_value=True), \
             patch.object(r, "read", side_effect=fake_read), \
             patch.object(r, "write", side_effect=fake_write):
            with redirect_stdout(StringIO()):
                n = r.repair_breadcrumb_preamble(Path("repo"), apply=True)

        self.assertEqual(n, 1)
        self.assertIn("\\input{common/boxes}\n\\input{common/breadcrumb-macros}", writes[preamble])


if __name__ == "__main__":
    unittest.main()
