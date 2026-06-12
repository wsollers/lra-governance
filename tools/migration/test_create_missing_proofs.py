import unittest
import shutil
from pathlib import Path

import create_missing_proofs as cmp
import identify_missing_proofs as idp


class CreateMissingProofsTests(unittest.TestCase):
    def test_build_stub_uses_proof_environments_for_proof_layers(self):
        stub = cmp.build_stub(
            "sum-zero",
            "cor:sum-zero",
            "Tao 2.2.9",
            "If a+b=0, then a=0 and b=0.",
            None,
        )

        self.assertIn(r"\LRAProofFor{cor:sum-zero}", stub)
        self.assertIn(r"\begin{proof}[Professional Standard Proof]", stub)
        self.assertIn(r"\begin{proof}[Detailed Learning Proof]", stub)
        self.assertEqual(stub.count(r"\LRAProofBodyStart"), 2)
        self.assertNotIn(r"\textbf{Professional Standard Proof.}", stub)
        self.assertNotIn(r"\textbf{Detailed Learning Proof.}", stub)

    def test_build_stub_falls_back_for_nested_linked_titles(self):
        stub = cmp.build_stub(
            "cantors-intersection-theorem",
            "thm:cantors-intersection-theorem",
            r"\texorpdfstring{\hyperref[prf:cantors-intersection-theorem]{Cantor's Intersection Theorem}}{Cantor's Intersection Theorem}",
            "Every nested sequence of nonempty compact sets intersects.",
            None,
        )

        self.assertIn(r"\begin{theorem*}[Cantor's Intersection Theorem]", stub)
        self.assertNotIn(r"\begin{theorem*}[[", stub)

    def test_extract_payload_handles_nested_optional_title(self):
        source = r"""\begin{theorem}[\texorpdfstring{\hyperref[prf:cantors-intersection-theorem]{Cantor's Intersection Theorem}}{Cantor's Intersection Theorem}]
\label{thm:cantors-intersection-theorem}
Every nested sequence of nonempty compact sets intersects.
\end{theorem}
"""
        tmp = Path(__file__).resolve().parents[2] / ".test-tmp" / "create-missing-proofs"
        if tmp.exists():
            shutil.rmtree(tmp)
        try:
            tmp.mkdir(parents=True)
            path = tmp / "note.tex"
            path.write_text(source, encoding="utf-8")
            title, statement, deps = cmp.extract_payload(path, "thm:cantors-intersection-theorem")
        finally:
            if tmp.exists():
                shutil.rmtree(tmp)

        self.assertEqual(title, r"\texorpdfstring{\hyperref[prf:cantors-intersection-theorem]{Cantor's Intersection Theorem}}{Cantor's Intersection Theorem}")
        self.assertEqual(statement, "Every nested sequence of nonempty compact sets intersects.")
        self.assertIsNone(deps)

    def test_root_level_notes_map_to_notes_topic(self):
        chapter = Path("volume-ii") / "integers"
        note = chapter / "notes" / "notes-int-tao-construction.tex"

        self.assertEqual(idp.topic_after("notes", note, chapter), "notes")

    def test_normalized_input_targets_accepts_semantic_proof_macro(self):
        targets = idp.normalized_input_targets(
            r"\LRAProofsInput{volume-ii/integers/proofs/notes/prf-int-order}"
        )

        self.assertIn("volume-ii/integers/proofs/notes/prf-int-order", targets)
        self.assertIn("prf-int-order", targets)

    def test_append_input_creates_router_only_fresh_index(self):
        tmp = Path(__file__).resolve().parents[2] / ".test-tmp" / "append-proof-input"
        if tmp.exists():
            shutil.rmtree(tmp)
        try:
            index = tmp / "volume-ii" / "integers" / "proofs" / "notes" / "index.tex"
            cmp.append_input(
                index,
                "volume-ii/integers/proofs/notes/prf-int-order",
                "\n",
                True,
            )
            text = index.read_text(encoding="utf-8")
        finally:
            if tmp.exists():
                shutil.rmtree(tmp)

        self.assertIn(r"\input{volume-ii/integers/proofs/notes/prf-int-order}", text)
        self.assertNotIn(r"\begin{remark*}[Proof status]", text)
        self.assertNotIn(r"\end{remark*}", text)


if __name__ == "__main__":
    unittest.main()
