"""Compatibility contracts between deterministic stub renderers and validators.

This suite is intentionally named in CI. A generator or validator change must
keep these boundary tests green so independently maintained templates and rules
cannot drift apart.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
import contextlib
import io
from pathlib import Path


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from generators.capstone_stub import render_capstone_stub  # noqa: E402
from generators.chapter_stub import stub_chapter  # noqa: E402
from generators.proof_stub import render_proof_stub  # noqa: E402
from generators.section_stub import stub_section  # noqa: E402
from generators.volume_stub import render_volume_stub  # noqa: E402
from test_validate_volume import TMP, make_volume, validate_with_inventory, write  # noqa: E402
from validate_volume import VALIDATORS, main as validate_volume_main  # noqa: E402
from validators import (  # noqa: E402
    capstones,
    chapter_stub,
    dependency_blocks,
    latex_integrity,
    planned_volume_stub,
    proof_coverage,
    proof_file_contract,
    proof_layout,
    proof_routing,
    proof_stub_state,
    unicode_tex,
)


class StubGeneratorValidatorContractTests(unittest.TestCase):
    def tearDown(self):
        if TMP.exists():
            shutil.rmtree(TMP)

    def assert_valid(self, volume: Path, validators) -> None:
        for name, validator in validators:
            with self.subTest(validator=name):
                findings = validate_with_inventory(validator, volume)
                self.assertEqual(findings, [], [f"{item.code}: {item.message}" for item in findings])

    def test_generated_proof_stub_passes_every_applicable_proof_validator(self):
        volume = make_volume()
        proof = render_proof_stub(
            "proposition",
            "order",
            "Order",
            "Every ordered integer is ordered.",
            [("ax:order-foundation", "Order foundation")],
            statement_label="prop:order",
        )
        write(volume / "integers" / "proofs" / "order" / "prf-order.tex", proof)

        self.assert_valid(
            volume,
            [
                ("proof_layout", proof_layout),
                ("proof_file_contract", proof_file_contract),
                ("proof_stub_state", proof_stub_state),
                ("proof_routing", proof_routing),
                ("proof_coverage", proof_coverage),
                ("dependency_blocks", dependency_blocks),
                ("latex_integrity", latex_integrity),
                ("unicode_tex", unicode_tex),
            ],
        )

    def test_generated_capstone_stub_passes_capstone_validators(self):
        volume = make_volume()
        capstone = render_capstone_stub(
            "integers",
            "Integers",
            [("prop:order", "Order")],
        )
        write(
            volume / "integers" / "proofs" / "exercises" / "capstone-integers.tex",
            capstone,
        )

        self.assert_valid(
            volume,
            [
                ("capstones", capstones),
                ("dependency_blocks", dependency_blocks),
                ("latex_integrity", latex_integrity),
                ("unicode_tex", unicode_tex),
            ],
        )

    def test_generated_chapter_and_section_pass_integrated_validator_registry(self):
        volume = TMP / "lra-volume-test" / "volume-ii"
        write(volume / "index.tex", "")
        write(volume / "main.tex", "")

        stub_chapter(volume, "ordered-fields", "Ordered Fields", [], ["Order"])
        stub_section(volume / "ordered-fields", "Completion Fields")

        self.assert_valid(volume, VALIDATORS)

    def test_chapter_stub_validator_detects_generator_manifest_drift(self):
        volume = TMP / "lra-volume-test" / "volume-ii"
        write(volume / "index.tex", "")
        write(volume / "main.tex", "")
        stub_chapter(volume, "ordered-fields", "Ordered Fields", [], [])
        manifest = volume / "ordered-fields" / "chapter.yaml"
        manifest.write_text(
            manifest.read_text(encoding="utf-8").replace(
                "status: planned", "status: draft", 1
            ),
            encoding="utf-8",
        )

        findings = validate_with_inventory(chapter_stub, volume)
        self.assertIn("chapter_stub_bad_status", {item.code for item in findings})
        with contextlib.redirect_stdout(io.StringIO()):
            exit_code = validate_volume_main(
                [str(volume), "--no-preprocess", "--fail-on-errors"]
            )
        self.assertEqual(exit_code, 2)

    def test_chapter_stub_validator_rejects_retired_breadcrumb_macro(self):
        volume = TMP / "lra-volume-test" / "volume-ii"
        write(volume / "index.tex", "")
        write(volume / "main.tex", "")
        stub_chapter(volume, "ordered-fields", "Ordered Fields", [], [])
        router = volume / "ordered-fields" / "index.tex"
        text = router.read_text(encoding="utf-8")
        start = text.index("\\lrameta{")
        end = text.index("\\LraBreadcrumb", start) + len("\\LraBreadcrumb")
        router.write_text(
            text[:start] + "\\breadcrumb{Series}{Volume}{Book}{Chapter}" + text[end:],
            encoding="utf-8",
        )

        findings = validate_with_inventory(chapter_stub, volume)
        self.assertIn("chapter_router_shape", {item.code for item in findings})

    def test_chapter_stub_validator_finds_missing_required_router(self):
        volume = TMP / "lra-volume-test" / "volume-ii"
        write(volume / "index.tex", "")
        write(volume / "main.tex", "")
        stub_chapter(volume, "ordered-fields", "Ordered Fields", [], [])
        (volume / "ordered-fields" / "notes" / "index.tex").unlink()

        findings = validate_with_inventory(chapter_stub, volume)
        self.assertIn("chapter_stub_missing_path", {item.code for item in findings})

    def test_generated_planned_volume_passes_planned_volume_validator(self):
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
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            for relative, content in files.items():
                write(repo / relative, content)
            volume = repo / "volume-iii"
            self.assert_valid(volume, [("planned_volume_stub", planned_volume_stub)])
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = validate_volume_main([str(volume), "--no-preprocess", "--fail-on-errors"])
            self.assertEqual(exit_code, 0)

    def test_planned_volume_validator_detects_generator_manifest_drift(self):
        files = render_volume_stub(
            "volume-iii",
            "Analysis and Topology",
            "Covers the supplied scope only.",
            [{"subject": "bounds", "display_title": "Bounds"}],
        )
        files["volume-iii/chapter.yaml"] = files["volume-iii/chapter.yaml"].replace(
            "status: planned", "status: draft", 1
        )
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            for relative, content in files.items():
                write(repo / relative, content)
            volume = repo / "volume-iii"
            findings = validate_with_inventory(planned_volume_stub, volume)
            self.assertIn("planned_volume_stub_bad_status", {item.code for item in findings})
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = validate_volume_main([str(volume), "--no-preprocess", "--fail-on-errors"])
            self.assertEqual(exit_code, 2)


if __name__ == "__main__":
    unittest.main()
