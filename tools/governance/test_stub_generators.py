from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock
import sys

import yaml

from generators.breadcrumb import render_breadcrumb
from generators.capstone_stub import render_capstone_stub
from generators.chapter_stub import render_chapter_stub_files
from generators.proof_stub import render_proof_stub
from generators.volume_stub import render_volume_stub


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "constitution") not in sys.path:
    sys.path.insert(0, str(ROOT / "constitution"))


class ProofStubTests(unittest.TestCase):
    def test_explicit_statement_link_and_dependencies_are_rendered(self):
        inputs = dict(
            kind="lemma",
            slug="order-bound",
            title="Order Bound",
            statement_body=r"For every $x$, one has $x \leq M$.",
            deps=[("def:order", "Order"), ("thm:upper-bound", "Upper Bound")],
            statement_label="lem:order-bound",
        )
        first = render_proof_stub(**inputs)
        second = render_proof_stub(**inputs)
        self.assertEqual(first, second)
        self.assertIn(r"\LRAProofFor{lem:order-bound}", first)
        self.assertIn(r"\begin{lemma*}[Order Bound]", first)
        self.assertIn(r"\hyperref[def:order]{Order}", first)
        self.assertIn(r"\hyperref[thm:upper-bound]{Upper Bound}", first)

    def test_rejects_label_kind_mismatch(self):
        with self.assertRaisesRegex(ValueError, "must start with lem:"):
            render_proof_stub(
                "lemma", "order-bound", "Order Bound", "Claim.",
                statement_label="thm:order-bound",
            )

class VolumeStubTests(unittest.TestCase):
    def test_registry_order_and_frontispiece_are_input_owned(self):
        files = render_volume_stub(
            "volume-iii",
            "Analysis and Topology",
            "Covers the supplied scope only.",
            [
                {"subject": "bounds", "display_title": "Bounds"},
                {"subject": "limits", "display_title": "Limits"},
            ],
            frontispiece={
                "mathematician": "Carl Friedrich Gauss",
                "years": "1777-1855",
                "image": "images/gauss.png",
            },
        )
        self.assertEqual(
            set(files),
            {"volume-iii/index.tex", "volume-iii/chapter.yaml"},
        )
        self.assertLess(files["volume-iii/index.tex"].index("Bounds"), files["volume-iii/index.tex"].index("Limits"))
        manifest = yaml.safe_load(files["volume-iii/chapter.yaml"])
        self.assertEqual(manifest["frontispiece"]["years"], "1777-1855")
        self.assertEqual([item["subject"] for item in manifest["chapters"]], ["bounds", "limits"])

    def test_rejects_duplicate_chapters(self):
        with self.assertRaisesRegex(ValueError, "duplicate chapter subject"):
            render_volume_stub(
                "volume-iii", "Title", "Scope",
                [
                    {"subject": "bounds", "display_title": "Bounds"},
                    {"subject": "bounds", "display_title": "More Bounds"},
                ],
            )


class OtherStubTests(unittest.TestCase):
    def test_breadcrumb_uses_registry_neighbors(self):
        registry = [
            {"subject": "a", "display_title": "A"},
            {"subject": "b", "display_title": "B"},
            {"subject": "c", "display_title": "C"},
        ]
        self.assertEqual(render_breadcrumb("b", "Ignored", registry), r"\breadcrumb{b}{A}{B}{C}")

    def test_capstone_renders_only_supplied_dependencies(self):
        text = render_capstone_stub("bounds", "Bounds", [("def:order", "Order")])
        self.assertIn(r"\hyperref[def:order]{Order}", text)
        self.assertNotIn("Upper Bound", text)

    def test_legacy_capstone_stub_mode_does_not_call_model(self):
        from auditor.generators import capstone as legacy

        with mock.patch.object(legacy.loader, "prompt", side_effect=AssertionError("model prompt used")):
            text = legacy.generate_capstone(
                "bounds", "Bounds", [], [], mode="stub",
                dependencies=[("def:order", "Order")],
            )
        self.assertIn(r"\hyperref[def:order]{Order}", text)

    def test_chapter_preview_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "volume-iii"
            files = render_chapter_stub_files(
                root,
                "bounds",
                "Bounds",
                [{"subject": "bounds", "display_title": "Bounds"}],
                [],
            )
            self.assertIn("bounds/index.tex", files)
            self.assertIn("bounds/proofs/exercises/capstone-bounds.tex", files)
            self.assertFalse(root.exists())


if __name__ == "__main__":
    unittest.main()
