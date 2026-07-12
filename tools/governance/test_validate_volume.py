import shutil
import subprocess
import sys
import unittest
import json
import inspect
from pathlib import Path
from unittest.mock import patch

from generators.chapter_stub import stub_chapter
from generators.section_stub import stub_section
import dependency_graph
from core.file_inventory import files_to_validate
from core.formal_blocks import clear_formal_block_cache
from core.tex import clear_text_cache
from core import volume as volume_core
from validate_volume import VALIDATORS, _filter_findings_for_inventory
from core.validator_runner import run_validator
from core.finding import finding
from validators import block_discipline, book_toc, capstones, chapter_router, dedication_page, dependency_blocks, dependency_graphs, figure_fragments, formal_decoration, formal_reading_required, frontmatter_standard, input_resolution, interpretation_blocks, labels, latex_integrity, math_boxes, notes_structure, operator_metadata, print_edition_routing, proof_coverage, proof_file_contract, proof_layout, proof_order, proof_routing, proof_stub_state, reference_voice, structural_chrome, structural_positions, unicode_tex, volume_shape


HERE = Path(__file__).resolve().parent
TMP = HERE.parent.parent / ".test-tmp" / "validate-volume"


def write(path: Path, text: str = ""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def validate_with_inventory(validator, volume: Path):
    clear_text_cache()
    clear_formal_block_cache()
    return run_validator(validator, volume, files_to_validate([volume], only_reachable=False))


def make_volume() -> Path:
    if TMP.exists():
        shutil.rmtree(TMP)
    volume = TMP / "lra-volume-test" / "volume-ii"
    chapter = volume / "integers"
    write(volume / "index.tex", r"\input{integers/index}" + "\n")
    write(volume / "main.tex", r"\input{volume-ii/integers/index}" + "\n")
    write(chapter / "chapter.yaml", "subject: integers\n")
    write(
        chapter / "index.tex",
        "\n".join(
            [
                r"\chapter{Integers}",
                r"\label{chap:integers}",
                r"\breadcrumb{integers}{}{Integers}{}",
                r"\input{volume-ii/integers/notes/index}",
                r"\LRAExcludeFromPrintEditionBegin",
                r"\section*{Proofs}",
                r"\input{volume-ii/integers/proofs/index}",
                r"\section*{Capstone}",
                r"\input{volume-ii/integers/proofs/exercises/index}",
                r"\LRAExcludeFromPrintEditionEnd",
                "",
            ]
        ),
    )
    write(chapter / "notes" / "index.tex", r"\input{volume-ii/integers/notes/order/index}" + "\n")
    write(
        chapter / "notes" / "order" / "index.tex",
        r"\section{Order Notes}" "\n"
        r"\input{volume-ii/integers/notes/order/notes-order}" "\n",
    )
    write(
        chapter / "notes" / "order" / "notes-order.tex",
        "\n".join(
            [
                r"\begin{axiombox}{Axiom (Order Foundation)}",
                r"\begin{axiom}[Order Foundation]",
                r"\label{ax:order-foundation}",
                "Order has a foundation.",
                r"\end{axiom}",
                r"\end{axiombox}",
                r"\begin{remark*}[Standard quantified statement]",
                r"\[",
                r"\exists \preceq.",
                r"\]",
                r"\end{remark*}",
                r"\begin{remark*}[Interpretation]",
                "The axiom fixes the order relation used in the chapter.",
                r"\end{remark*}",
                r"\NoLocalDependencies",
                "",
                r"\begin{propositionbox}{Proposition (Order)}",
                r"\begin{proposition}[Order]",
                r"\label{prop:order}",
                "Every ordered integer is ordered.",
                r"\hyperref[prf:order]{\textit{Go to proof.}}",
                r"\end{proposition}",
                r"\end{propositionbox}",
                r"\begin{remark*}[Standard quantified statement]",
                r"\[",
                r"\forall n\in \mathbb{Z},\quad n \preceq n.",
                r"\]",
                r"\end{remark*}",
                r"\begin{remark*}[Interpretation]",
                "The proposition records a reflexive order comparison.",
                r"\end{remark*}",
                r"\begin{dependencies}",
                r"\begin{itemize}",
                r"  \item \hyperref[ax:order-foundation]{Order foundation}.",
                r"\end{itemize}",
                r"\end{dependencies}",
                "",
            ]
        ),
    )
    write(chapter / "proofs" / "index.tex", r"\input{volume-ii/integers/proofs/order/index}" + "\n")
    write(chapter / "proofs" / "order" / "index.tex", r"\input{volume-ii/integers/proofs/order/prf-order}" + "\n")
    write(
        chapter / "proofs" / "order" / "prf-order.tex",
        "\n".join(
            [
                r"\newpage",
                r"\phantomsection",
                r"\label{prf:order}",
                r"\LRAProofFor{prop:order}",
                "",
                r"\begin{remark*}[Return]",
                r"\hyperref[prop:order]{Return to Proposition}",
                r"\end{remark*}",
                "",
                r"\begin{proposition*}[Order]",
                "Every ordered integer is ordered.",
                r"\end{proposition*}",
                "",
                r"\begin{proof}",
                "Professional Standard Proof.",
                r"\end{proof}",
                "",
                r"\begin{proof}",
                "Detailed Learning Proof.",
                r"\end{proof}",
                "",
                r"\begin{remark*}[Proof structure]",
                "Direct verification.",
                r"\end{remark*}",
                "",
                r"\NoLocalDependencies",
                "",
                r"\clearpage",
                "",
            ]
        ),
    )
    write(chapter / "proofs" / "exercises" / "index.tex", r"\input{volume-ii/integers/proofs/exercises/capstone-integers}" + "\n")
    write(
        chapter / "proofs" / "exercises" / "capstone-integers.tex",
        "\n".join(
            [
                r"\newpage",
                r"\phantomsection",
                r"\label{cap:integers}",
                "",
                r"\begin{tcolorbox}",
                r"\textbf{Theorem.}",
                "If integers are ordered, then integers are ordered.",
                r"\end{tcolorbox}",
                "",
                r"\begin{remark*}[Dependencies to state]",
                r"\begin{itemize}",
                r"  \item \hyperref[prop:order]{Order}",
                r"\end{itemize}",
                r"\end{remark*}",
                "",
                r"\begin{remark*}[Dependencies to prove]",
                r"\begin{itemize}",
                r"  \item \hyperref[prop:order]{Order}",
                r"\end{itemize}",
                r"\end{remark*}",
                "",
                r"\begin{remark*}[Dependency ceiling]",
                "Earlier material only.",
                r"\end{remark*}",
                "",
                r"\begin{dependencies}",
                r"\begin{itemize}",
                r"  \item \hyperref[prop:order]{Order}",
                r"\end{itemize}",
                r"\end{dependencies}",
                "",
                r"\clearpage",
                "",
            ]
        ),
    )
    return volume


def make_registered_book_volume() -> tuple[Path, dict]:
    if TMP.exists():
        shutil.rmtree(TMP)
    repo = TMP / "lra-volume-test"
    volume = repo / "volume-ii"
    book = volume / "book-new"
    chapter = book / "chapter-one"
    registry = {
        "roman": "ii",
        "books": [
            {
                "order": 1,
                "slug": "new-book",
                "title": "New Book",
                "tex_root": "volume-ii-new-book.tex",
                "book_dir": "volume-ii/book-new",
                "expected_toc": [
                    {
                        "chapter": "chapter-one",
                        "notes": ["topic-one"],
                    }
                ],
            }
        ],
    }
    write(volume / "index.tex", r"\input{volume-ii/book-new/index}" + "\n")
    write(repo / "volume-ii-new-book.tex", r"\input{volume-ii/book-new/index}" + "\n")
    write(repo / "bibliography" / "volume-ii-new-book.bib", "% bibliography shard\n")
    write(book / "index.tex", r"\input{volume-ii/book-new/chapter-one/index}" + "\n")
    write(chapter / "index.tex", r"\input{volume-ii/book-new/chapter-one/notes/index}" + "\n")
    write(chapter / "chapter.yaml", "subject: chapter one\n")
    write(chapter / "notes" / "index.tex", r"\input{volume-ii/book-new/chapter-one/notes/topic-one/index}" + "\n")
    write(chapter / "notes" / "topic-one" / "index.tex", r"\section{Topic One}" + "\n")
    write(chapter / "proofs" / "index.tex", "% proofs\n")
    return volume, registry


class ValidateVolumeTests(unittest.TestCase):
    def tearDown(self):
        if TMP.exists():
            shutil.rmtree(TMP)

    def test_all_registered_validators_accept_file_inventory(self):
        for name, validator in VALIDATORS:
            with self.subTest(validator=name):
                self.assertIn("files", inspect.signature(validator.validate).parameters)

    def test_full_validator_runner_ignores_unwired_tex_files(self):
        volume = make_volume()
        bad = volume / "integers" / "notes" / "order" / "notes-unwired-bad.tex"
        write(
            bad,
            "\n".join(
                [
                    r"\begin{tikzpicture}",
                    r"\draw (0,0) -- (1,1);",
                    r"\end{tikzpicture}",
                    r"\begin{definition}[Unwired]",
                    r"\label{def:unwired}",
                    "Unwired content.",
                    r"\end{definition}",
                    "",
                ]
            ),
        )

        for name, validator in VALIDATORS:
            with self.subTest(validator=name):
                findings = run_validator(validator, volume)
                bad_findings = [finding for finding in findings if Path(finding.path).resolve() == bad.resolve()]
                self.assertEqual([], bad_findings)

    def test_reporting_gate_drops_findings_for_unwired_tex_files(self):
        volume = make_volume()
        wired = volume / "integers" / "notes" / "order" / "notes-order.tex"
        unwired = volume / "integers" / "notes" / "order" / "notes-unwired-bad.tex"
        write(unwired, "Unwired content.\n")
        findings = [
            finding("wired_issue", "Wired.", wired, volume, severity="warning"),
            finding("unwired_issue", "Unwired.", unwired, volume, severity="warning"),
        ]

        filtered = _filter_findings_for_inventory(findings, volume, files_to_validate([volume]))

        self.assertEqual(["wired_issue"], [item.code for item in filtered])

    def test_core_volume_excludes_special_validation_directories(self):
        volume = make_volume()
        proof_techniques = volume / "proof-techniques"
        write(proof_techniques / "chapter.yaml", "subject: proof techniques\n")
        write(proof_techniques / "notes" / "index.tex", r"\begin{definition}Unlabelled\end{definition}" + "\n")
        write(proof_techniques / "proofs" / "index.tex", r"\begin{proof}Rendered\end{proof}" + "\n")
        lean = volume / "lean"
        write(lean / "chapter.yaml", "subject: lean\n")
        write(lean / "notes" / "index.tex", r"\begin{definition}Unlabelled\end{definition}" + "\n")
        write(lean / "proofs" / "index.tex", r"\begin{proof}Rendered\end{proof}" + "\n")
        real_analysis = volume / "analysis" / "real-analysis"
        write(real_analysis / "chapter.yaml", "subject: real analysis\n")
        write(real_analysis / "notes" / "index.tex", r"\begin{definition}Unlabelled\end{definition}" + "\n")
        write(real_analysis / "proofs" / "index.tex", r"\begin{proof}Rendered\end{proof}" + "\n")

        chapters = {path.relative_to(volume).as_posix() for path in volume_core.chapter_roots(volume)}
        tex_files = {path.relative_to(volume).as_posix() for path in volume_core.iter_tex(volume)}

        self.assertNotIn("proof-techniques", chapters)
        self.assertNotIn("lean", chapters)
        self.assertNotIn("analysis/real-analysis", chapters)
        self.assertFalse(any(path.startswith("proof-techniques/") for path in tex_files))
        self.assertFalse(any(path.startswith("lean/") for path in tex_files))
        self.assertFalse(any(path.startswith("analysis/real-analysis/") for path in tex_files))

    def test_volume_shape_accepts_canonical_fixture(self):
        volume = make_volume()

        self.assertEqual(validate_with_inventory(volume_shape, volume), [])

    def test_validators_ignore_unwired_topic_files(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "orphan-topic" / "index.tex",
            "\n".join(
                [
                    r"\section{Orphan}",
                    r"\begin{toolkitbox}{Unwired Toolkit}",
                    "This bad toolkit has no table and uses an em dash — but is not routed.",
                    r"\end{toolkitbox}",
                    "",
                ]
            ),
        )

        structural_codes = {finding.code for finding in run_validator(structural_chrome, volume)}
        unicode_codes = {finding.code for finding in run_validator(unicode_tex, volume)}
        shape_codes = {finding.code for finding in run_validator(volume_shape, volume)}

        self.assertNotIn("toolkit_missing_table", structural_codes)
        self.assertNotIn("non_ascii_tex_character", unicode_codes)
        self.assertNotIn("orphan_proofs_topic", shape_codes)

    def test_reachable_inventory_does_not_fallback_to_directory_walk(self):
        root = TMP / "unrouted-tree"
        write(root / "loose" / "bad.tex", "Loose file.\n")

        self.assertEqual(files_to_validate([root]), [])

    def test_volume_shape_flags_legacy_capstone_and_flat_proof(self):
        volume = make_volume()
        chapter = volume / "integers"
        write(chapter / "capstone.tex", "% legacy\n")
        write(chapter / "proofs" / "prf-flat.tex", "% flat\n")

        codes = {finding.code for finding in validate_with_inventory(volume_shape, volume)}

        self.assertIn("legacy_chapter_path", codes)
        self.assertIn("flat_proof_file", codes)

    def test_volume_shape_flags_extra_exercises_artifacts(self):
        volume = make_volume()
        write(volume / "integers" / "proofs" / "exercises" / "ex-extra.tex", "% old exercise proof\n")
        write(volume / "integers" / "proofs" / "exercises" / "legacy-topic" / "index.tex", "% old topic\n")

        codes = [finding.code for finding in validate_with_inventory(volume_shape, volume)]

        self.assertEqual(codes.count("noncanonical_exercises_path"), 2)

    def test_volume_shape_allows_note_topic_without_proof_obligations(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "reference" / "index.tex",
            r"\section{Reference}" "\n"
            r"\input{volume-ii/integers/notes/reference/notes-reference}" "\n",
        )
        write(
            volume / "integers" / "notes" / "reference" / "notes-reference.tex",
            "\n".join(
                [
                    r"\begin{remark*}[Reference]",
                    "This note topic has no theorem-like proof obligation.",
                    r"\end{remark*}",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(volume_shape, volume)}

        self.assertNotIn("missing_matching_proofs_topic", codes)

    def test_volume_shape_requires_proof_topic_for_theorem_like_note_topic(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "theorems" / "index.tex",
            r"\section{Theorems}" "\n"
            r"\input{volume-ii/integers/notes/theorems/notes-theorem}" "\n",
        )
        write(
            volume / "integers" / "notes" / "theorems" / "notes-theorem.tex",
            "\n".join(
                [
                    r"\begin{theorem}[Needs proof topic]",
                    r"\label{thm:needs-proof-topic}",
                    "This theorem-like statement requires a matching proof topic.",
                    r"\end{theorem}",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(volume_shape, volume)}

        self.assertIn("missing_matching_proofs_topic", codes)

    def test_volume_shape_schema_declares_exercises_allowlist(self):
        schema = json.loads((HERE.parents[1] / "docs" / "governance" / "volume-structure.schema.json").read_text(encoding="utf-8"))

        self.assertEqual(schema["required_chapter_files"], ["index.tex", "chapter.yaml", "notes/index.tex", "proofs/index.tex"])
        self.assertEqual(schema["required_chapter_dirs"], ["notes", "proofs"])
        self.assertEqual(schema["exercises_allowed_files"], ["index.tex", "capstone-{chapter}.tex"])
        self.assertEqual(schema["proof_topic_required_envs"], ["theorem", "lemma", "proposition", "corollary"])

    def test_book_toc_accepts_registered_book_fixture(self):
        volume, registry = make_registered_book_volume()

        with patch.object(book_toc, "_registry_for", return_value=registry):
            self.assertEqual(validate_with_inventory(book_toc, volume), [])

    def test_frontmatter_standard_accepts_canonical_volume_frontmatter(self):
        volume, registry = make_registered_book_volume()
        registry.update(
            {
                "display_title": "Origins of Numbers",
                "series_title": "From Cantor to Ito",
                "frontmatter_mathematician": "Richard Dedekind",
                "mathematician_lifespan": "1831-1916",
                "image_path": "images/dedekind.png",
            }
        )
        repo = volume.parent
        book = registry["books"][0]
        book["frontmatter_mathematician"] = "Book Mathematician"
        book["mathematician_lifespan"] = "1900-2000"
        book["image_path"] = "images/book.png"
        write(volume / "frontmatter.tex", r"\newcommand{\LRAFrontMatterPage}[6]{\includegraphics{#6}}" + "\n")
        write(repo / "images" / "dedekind.png", "png\n")
        write(repo / "images" / "book.png", "png\n")
        write(
            repo / "volume-ii.tex",
            "\n".join(
                [
                    r"\input{volume-ii/frontmatter}",
                    r"\LRAFrontMatterPage{From Cantor to Ito}{Origins of Numbers}{}{Richard Dedekind}{1831-1916}{images/dedekind.png}",
                    "",
                ]
            ),
        )
        write(
            repo / book["tex_root"],
            "\n".join(
                [
                    r"\input{volume-ii/frontmatter}",
                    r"\LRAFrontMatterPage{From Cantor to Ito}{Origins of Numbers}{New Book}{Book Mathematician}{1900-2000}{images/book.png}",
                    "",
                ]
            ),
        )
        write(volume / "index.tex", r"\part{Origins of Numbers}" + "\n" + r"\input{volume-ii/book-new/index}" + "\n")

        with patch.object(frontmatter_standard, "_registry_for", return_value=registry):
            self.assertEqual(validate_with_inventory(frontmatter_standard, volume), [])

    def test_frontmatter_standard_reports_migration_drift(self):
        volume, registry = make_registered_book_volume()
        registry.update(
            {
                "display_title": "Origins of Numbers",
                "series_title": "From Cantor to Ito",
                "frontmatter_mathematician": "Richard Dedekind",
                "mathematician_lifespan": "1831-1916",
                "image_path": "images/dedekind.png",
            }
        )
        write(volume / "frontmatter.tex", "% missing renderer contract\n")
        write(volume.parent / "volume-ii.tex", r"\begin{titlepage}Legacy\end{titlepage}" + "\n")
        write(volume / "index.tex", r"\part{Numbers}" + "\n")

        with patch.object(frontmatter_standard, "_registry_for", return_value=registry):
            codes = {finding.code for finding in validate_with_inventory(frontmatter_standard, volume)}

        self.assertIn("frontmatter_renderer_missing_macro", codes)
        self.assertIn("frontmatter_renderer_missing_image", codes)
        self.assertIn("root_missing_frontmatter_input", codes)
        self.assertIn("root_inline_frontmatter", codes)
        self.assertIn("root_missing_frontmatter_call", codes)
        self.assertIn("part_title_mismatch", codes)

    def test_dedication_page_accepts_exactly_once_after_frontmatter(self):
        volume, registry = make_registered_book_volume()
        repo = volume.parent
        write(
            repo / "volume-ii.tex",
            "\n".join(
                [
                    r"\LRAFrontMatterPage{From Cantor to Ito}{Origins of Numbers}{}{Richard Dedekind}{1831-1916}{images/dedekind.png}",
                    r"\input{common/dedication}",
                    r"\tableofcontents",
                    "",
                ]
            ),
        )
        write(
            repo / registry["books"][0]["tex_root"],
            "\n".join(
                [
                    r"\LRAFrontMatterPage{From Cantor to Ito}{Origins of Numbers}{New Book}{Book Mathematician}{1900-2000}{images/book.png}",
                    r"\input{common/dedication}",
                    r"\tableofcontents",
                    "",
                ]
            ),
        )

        with patch.object(dedication_page, "_registry_for", return_value=registry):
            self.assertEqual(validate_with_inventory(dedication_page, volume), [])

    def test_dedication_page_flags_count_and_order(self):
        volume, registry = make_registered_book_volume()
        repo = volume.parent
        write(
            repo / "volume-ii.tex",
            "\n".join(
                [
                    r"\input{common/dedication}",
                    r"\LRAFrontMatterPage{From Cantor to Ito}{Origins of Numbers}{}{Richard Dedekind}{1831-1916}{images/dedekind.png}",
                    r"\tableofcontents",
                    "",
                ]
            ),
        )
        write(
            repo / registry["books"][0]["tex_root"],
            "\n".join(
                [
                    r"\LRAFrontMatterPage{From Cantor to Ito}{Origins of Numbers}{New Book}{Book Mathematician}{1900-2000}{images/book.png}",
                    r"\tableofcontents",
                    r"\input{common/dedication}",
                    r"\input{common/dedication}",
                    "",
                ]
            ),
        )

        with patch.object(dedication_page, "_registry_for", return_value=registry):
            codes = {finding.code for finding in validate_with_inventory(dedication_page, volume)}

        self.assertIn("dedication_before_frontmatter", codes)
        self.assertIn("dedication_input_count", codes)

    def test_book_toc_requires_volume_index_route_for_registered_book(self):
        volume, registry = make_registered_book_volume()
        (volume / "index.tex").write_text("% missing book route\n", encoding="utf-8")

        with patch.object(book_toc, "_registry_for", return_value=registry):
            codes = {finding.code for finding in validate_with_inventory(book_toc, volume)}

        self.assertIn("book_not_routed_from_volume_index", codes)

    def test_book_toc_requires_book_bibliography_shard(self):
        volume, registry = make_registered_book_volume()
        (volume.parent / "bibliography" / "volume-ii-new-book.bib").unlink()

        with patch.object(book_toc, "_registry_for", return_value=registry):
            codes = {finding.code for finding in validate_with_inventory(book_toc, volume)}

        self.assertIn("missing_book_bibliography_shard", codes)

    def test_book_toc_flags_unregistered_book_directory(self):
        volume, registry = make_registered_book_volume()
        write(volume / "book-unregistered" / "index.tex", "% unregistered\n")

        with patch.object(book_toc, "_registry_for", return_value=registry):
            codes = {finding.code for finding in validate_with_inventory(book_toc, volume)}

        self.assertIn("unregistered_book_dir", codes)

    def test_book_toc_flags_duplicate_registry_order(self):
        volume, registry = make_registered_book_volume()
        registry["books"].append(
            {
                "order": 1,
                "slug": "other-book",
                "title": "Other Book",
                "tex_root": "volume-ii-other-book.tex",
                "book_dir": "volume-ii/book-other",
                "expected_toc": [],
            }
        )

        with patch.object(book_toc, "_registry_for", return_value=registry):
            codes = {finding.code for finding in validate_with_inventory(book_toc, volume)}

        self.assertIn("book_registry_duplicate_order", codes)

    def test_print_edition_routing_flags_macro_below_proofs(self):
        volume = make_volume()
        write(
            volume / "integers" / "proofs" / "order" / "index.tex",
            r"\LRAProofsInput{volume-ii/integers/proofs/order/prf-order}" + "\n",
        )

        codes = {finding.code for finding in validate_with_inventory(print_edition_routing, volume)}

        self.assertIn("legacy_print_edition_input_macro", codes)

    def test_proof_routing_accepts_canonical_fixture(self):
        volume = make_volume()

        self.assertEqual(validate_with_inventory(proof_routing, volume), [])

    def test_proof_routing_flags_unrouted_proof_file(self):
        volume = make_volume()
        write(volume / "integers" / "proofs" / "order" / "prf-extra.tex", "% proof\n")

        codes = {finding.code for finding in validate_with_inventory(proof_routing, volume)}

        self.assertIn("unrouted_proof_topic_file", codes)

    def test_proof_routing_flags_rendered_content_in_indexes(self):
        volume = make_volume()
        write(
            volume / "integers" / "proofs" / "index.tex",
            r"\subsection*{Proof Topics}" "\n"
            r"\input{volume-ii/integers/proofs/order/index}" "\n",
        )
        write(
            volume / "integers" / "proofs" / "order" / "index.tex",
            r"\subsection*{Order Proofs}" "\n"
            r"\input{volume-ii/integers/proofs/order/prf-order}" "\n",
        )

        codes = {finding.code for finding in validate_with_inventory(proof_routing, volume)}

        self.assertIn("proofs_index_contains_rendered_content", codes)
        self.assertIn("proofs_topic_index_contains_rendered_content", codes)

    def test_proof_routing_flags_exercises_routed_from_proofs_index(self):
        volume = make_volume()
        write(
            volume / "integers" / "proofs" / "index.tex",
            r"\input{volume-ii/integers/proofs/order/index}" "\n"
            r"\input{volume-ii/integers/proofs/exercises/index}" "\n",
        )

        codes = {finding.code for finding in validate_with_inventory(proof_routing, volume)}

        self.assertIn("proofs_index_routes_exercises", codes)

    def test_proof_layout_accepts_canonical_fixture(self):
        volume = make_volume()

        self.assertEqual(validate_with_inventory(proof_layout, volume), [])

    def test_proof_layout_ignores_unrouted_proof_files(self):
        volume = make_volume()
        write(
            volume / "integers" / "proofs" / "order" / "prf-retired.tex",
            "\n".join(
                [
                    r"\newpage",
                    r"\phantomsection",
                    r"\label{prf:retired}",
                    r"\LRAProofFor{prop:retired}",
                    "",
                    r"\begin{remark*}[Return]",
                    r"\hyperref[prop:retired]{Return to Proposition}",
                    r"\end{remark*}",
                    "",
                    r"\begin{proposition*}[Retired]",
                    "Retired statement.",
                    r"\end{proposition*}",
                    "",
                    r"\begin{proof}",
                    "TODO: professional standard proof for retired.",
                    r"\end{proof}",
                    "",
                    r"\begin{proof}",
                    "TODO: detailed learning proof for retired.",
                    r"\end{proof}",
                    "",
                    r"\NoLocalDependencies",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in run_validator(proof_layout, volume)}

        self.assertNotIn("proof_not_in_topic_index", codes)
        self.assertNotIn("unknown_note_topic", codes)

    def test_proof_file_contract_accepts_canonical_fixture(self):
        volume = make_volume()

        self.assertEqual(validate_with_inventory(proof_file_contract, volume), [])

    def test_proof_file_contract_flags_label_order_and_body_labels(self):
        volume = make_volume()
        proof = volume / "integers" / "proofs" / "order" / "prf-order.tex"
        proof.write_text(
            "\n".join(
                [
                    r"\begin{remark*}[Return]",
                    r"\hyperref[prop:order]{Return}",
                    r"\end{remark*}",
                    r"\label{prf:order}",
                    r"\LRAProofFor{prop:order}",
                    r"\begin{proposition*}[Order]",
                    r"\label{prop:inside-restatement}",
                    r"\end{proposition*}",
                    r"\begin{proof}",
                    r"\label{bad:inside-proof}",
                    r"\end{proof}",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(proof_file_contract, volume)}

        self.assertIn("proof_label_after_environment", codes)
        self.assertIn("label_inside_restatement", codes)
        self.assertIn("label_inside_proof_environment", codes)

    def test_proof_file_contract_flags_return_dependency_trailer_and_restatement_type(self):
        volume = make_volume()
        proof = volume / "integers" / "proofs" / "order" / "prf-order.tex"
        proof.write_text(
            "\n".join(
                [
                    r"\newpage",
                    r"\phantomsection",
                    r"\label{prf:order}",
                    r"\LRAProofFor{prop:order}",
                    r"\begin{remark*}[Return]",
                    r"\hyperref[lem:wrong]{Return}",
                    r"\end{remark*}",
                    r"\begin{lemma*}[Wrong type]",
                    "Restated.",
                    r"\end{lemma*}",
                    r"\begin{dependencies}",
                    r"\begin{itemize}",
                    r"  \item \hyperref[fig:bad]{Bad target}.",
                    r"\end{itemize}",
                    r"\end{dependencies}",
                    r"\clearpage",
                    "trailing content",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(proof_file_contract, volume)}

        self.assertIn("return_navigation_mismatch", codes)
        self.assertIn("invalid_proof_dependency_target", codes)
        self.assertIn("content_after_clearpage", codes)
        self.assertIn("restatement_type_mismatch", codes)

    def test_proof_file_contract_requires_exactly_one_return_navigation(self):
        volume = make_volume()
        proof = volume / "integers" / "proofs" / "order" / "prf-order.tex"
        proof.write_text(
            "\n".join(
                [
                    r"\label{prf:order}",
                    r"\LRAProofFor{prop:order}",
                    r"\begin{proposition*}[Order]",
                    "Restated.",
                    r"\end{proposition*}",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(proof_file_contract, volume)}

        self.assertIn("missing_return_navigation", codes)

        proof.write_text(
            "\n".join(
                [
                    r"\label{prf:order}",
                    r"\LRAProofFor{prop:order}",
                    r"\begin{remark*}[Return]",
                    r"\hyperref[prop:order]{Return}",
                    r"\end{remark*}",
                    r"\begin{remark*}[Return]",
                    r"\hyperref[prop:order]{Return again}",
                    r"\end{remark*}",
                    r"\begin{proposition*}[Order]",
                    "Restated.",
                    r"\end{proposition*}",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(proof_file_contract, volume)}

        self.assertIn("multiple_return_navigation", codes)

    def test_proof_file_contract_flags_restatement_count_layer_order_and_todo_placement(self):
        volume = make_volume()
        proof = volume / "integers" / "proofs" / "order" / "prf-order.tex"
        proof.write_text(
            "\n".join(
                [
                    "TODO outside allowed layers.",
                    r"\label{prf:order}",
                    r"\LRAProofFor{prop:order}",
                    r"\begin{remark*}[Return]",
                    r"\hyperref[prop:order]{Return}",
                    r"\end{remark*}",
                    r"\begin{proposition*}[Order one]",
                    "Restated.",
                    r"\end{proposition*}",
                    r"\begin{proposition*}[Order two]",
                    "Restated again.",
                    r"\end{proposition*}",
                    r"\begin{proof}",
                    "Detailed Learning Proof.",
                    r"\end{proof}",
                    r"\begin{proof}",
                    "Professional Standard Proof.",
                    r"\end{proof}",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(proof_file_contract, volume)}

        self.assertIn("invalid_restatement_count", codes)
        self.assertIn("proof_layer_order", codes)
        self.assertIn("todo_outside_stub_layers", codes)

    def test_proof_coverage_accepts_canonical_fixture(self):
        volume = make_volume()

        self.assertEqual(validate_with_inventory(proof_coverage, volume), [])

    def test_proof_coverage_flags_missing_proof_label_and_association(self):
        volume = make_volume()
        proof = volume / "integers" / "proofs" / "order" / "prf-order.tex"
        proof.write_text(
            "\n".join(
                [
                    r"\begin{remark*}[Return]",
                    r"\hyperref[prop:order]{Return}",
                    r"\end{remark*}",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        codes = {finding.code for finding in validate_with_inventory(proof_coverage, volume)}

        self.assertIn("missing_proof_file", codes)
        self.assertIn("missing_proof_association", codes)

    def test_proof_order_accepts_canonical_fixture(self):
        volume = make_volume()

        self.assertEqual(validate_with_inventory(proof_order, volume), [])

    def test_proof_order_flags_topic_and_file_order(self):
        volume = make_volume()
        write(volume / "integers" / "notes" / "index.tex", "\n".join([
            r"\input{volume-ii/integers/notes/order/index}",
            r"\input{volume-ii/integers/notes/algebra/index}",
            "",
        ]))
        write(volume / "integers" / "notes" / "algebra" / "index.tex", "")
        write(volume / "integers" / "proofs" / "algebra" / "index.tex", "")
        write(volume / "integers" / "proofs" / "index.tex", "\n".join([
            r"\input{volume-ii/integers/proofs/algebra/index}",
            r"\input{volume-ii/integers/proofs/order/index}",
            r"\input{volume-ii/integers/proofs/exercises/index}",
            "",
        ]))
        note = volume / "integers" / "notes" / "order" / "notes-order.tex"
        note.write_text(
            "\n".join(
                [
                    r"\begin{lemma}[First]",
                    r"\label{lem:first}",
                    "First.",
                    r"\end{lemma}",
                    r"\begin{lemma}[Second]",
                    r"\label{lem:second}",
                    "Second.",
                    r"\end{lemma}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        write(volume / "integers" / "proofs" / "order" / "index.tex", "\n".join([
            r"\input{volume-ii/integers/proofs/order/prf-second}",
            r"\input{volume-ii/integers/proofs/order/prf-first}",
            "",
        ]))

        codes = {finding.code for finding in validate_with_inventory(proof_order, volume)}

        self.assertIn("proof_topic_order_mismatch", codes)
        self.assertIn("proof_file_order_mismatch", codes)

    def test_proof_order_flags_topic_route_order_mismatch(self):
        volume = make_volume()
        write(volume / "integers" / "notes" / "index.tex", "\n".join([
            r"\input{volume-ii/integers/notes/order/index}",
            r"\input{volume-ii/integers/notes/algebra/index}",
            "",
        ]))
        write(volume / "integers" / "notes" / "algebra" / "index.tex", "")
        write(volume / "integers" / "proofs" / "algebra" / "index.tex", "")
        write(volume / "integers" / "proofs" / "index.tex", "\n".join([
            r"\input{volume-ii/integers/proofs/algebra/index}",
            r"\input{volume-ii/integers/proofs/order/index}",
            "",
        ]))

        codes = {finding.code for finding in validate_with_inventory(proof_order, volume)}

        self.assertIn("proof_topic_order_mismatch", codes)

    def test_proof_stub_state_accepts_canonical_fixture(self):
        volume = make_volume()

        self.assertEqual(validate_with_inventory(proof_stub_state, volume), [])

    def test_proof_stub_state_flags_authored_professional_with_stub_detailed(self):
        volume = make_volume()
        write(
            volume / "integers" / "proofs" / "order" / "prf-extra.tex",
            "\n".join(
                [
                    r"\begin{proof}[Professional Standard Proof]",
                    "A real proof sentence establishes the result.",
                    r"\end{proof}",
                    r"\begin{proof}[Detailed Learning Proof]",
                    "TODO",
                    r"\end{proof}",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(proof_stub_state, volume)}

        self.assertIn("mixed_authored_professional_detailed_stub", codes)

    def test_proof_layout_ignores_todo_in_comments_for_stub_state(self):
        volume = make_volume()
        proof = volume / "integers" / "proofs" / "order" / "prf-order.tex"
        proof.write_text(
            proof.read_text(encoding="utf-8").replace(
                "Professional Standard Proof.",
                "% TODO: historical migration note, not proof-body stub state.\nProfessional Standard Proof.",
            ),
            encoding="utf-8",
        )

        codes = {finding.code for finding in validate_with_inventory(proof_layout, volume)}

        self.assertNotIn("partial_stub", codes)

    def test_notes_structure_accepts_canonical_fixture(self):
        volume = make_volume()

        self.assertEqual(validate_with_inventory(notes_structure, volume), [])

    def test_notes_structure_flags_unrouted_body(self):
        volume = make_volume()
        write(volume / "integers" / "notes" / "order" / "notes-extra.tex", "% body\n")

        codes = {finding.code for finding in validate_with_inventory(notes_structure, volume)}

        self.assertIn("unrouted_notes_topic_body", codes)

    def test_notes_structure_ignores_unrouted_figure_assets(self):
        volume = make_volume()
        write(volume / "integers" / "notes" / "order" / "figure-order.tex", "% figure asset\n")

        codes = {finding.code for finding in validate_with_inventory(notes_structure, volume)}

        self.assertNotIn("unrouted_notes_topic_body", codes)

    def test_notes_structure_rejects_starred_section_in_topic_index(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "index.tex",
            r"\section*{Order Notes}" "\n"
            r"\input{volume-ii/integers/notes/order/notes-order}" "\n",
        )

        codes = {finding.code for finding in validate_with_inventory(notes_structure, volume)}

        self.assertIn("notes_topic_index_contains_rendered_content", codes)
        self.assertIn("notes_topic_index_missing_section", codes)

    def test_notes_structure_allows_section_in_topic_index(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "index.tex",
            r"\section{Order Notes}" "\n"
            r"\input{volume-ii/integers/notes/order/notes-order}" "\n",
        )

        codes = {finding.code for finding in validate_with_inventory(notes_structure, volume)}

        self.assertNotIn("notes_topic_index_contains_rendered_content", codes)
        self.assertNotIn("notes_topic_index_missing_section", codes)

    def test_notes_structure_allows_texorpdfstring_section_in_topic_index(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "index.tex",
            r"\section{\texorpdfstring{Order on $\mathbb{R}$}{Order on R}}" "\n"
            r"\input{volume-ii/integers/notes/order/notes-order}" "\n",
        )

        codes = {finding.code for finding in validate_with_inventory(notes_structure, volume)}

        self.assertNotIn("notes_topic_index_contains_rendered_content", codes)
        self.assertNotIn("notes_topic_index_missing_section", codes)

    def test_notes_structure_rejects_section_in_topic_body(self):
        volume = make_volume()
        note = volume / "integers" / "notes" / "order" / "notes-order.tex"
        note.write_text(
            r"\section{Body-Level Heading}" "\n"
            + note.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        codes = {finding.code for finding in validate_with_inventory(notes_structure, volume)}

        self.assertIn("notes_topic_body_section_heading", codes)

    def test_notes_structure_flags_duplicate_section_in_multi_file_topic_index(self):
        volume = make_volume()
        write(volume / "integers" / "notes" / "order" / "notes-extra.tex", "% extra body\n")
        write(
            volume / "integers" / "notes" / "order" / "index.tex",
            r"\section{Order Foundations}" "\n"
            r"\input{volume-ii/integers/notes/order/notes-order}" "\n"
            r"\section{Extra Order Notes}" "\n"
            r"\input{volume-ii/integers/notes/order/notes-extra}" "\n",
        )

        codes = {finding.code for finding in validate_with_inventory(notes_structure, volume)}

        self.assertIn("notes_topic_index_duplicate_section", codes)
        self.assertNotIn("unrouted_notes_topic_body", codes)

    def test_notes_structure_flags_duplicate_texorpdfstring_section_in_multi_file_topic_index(self):
        volume = make_volume()
        write(volume / "integers" / "notes" / "order" / "notes-extra.tex", "% extra body\n")
        write(
            volume / "integers" / "notes" / "order" / "index.tex",
            r"\section{\texorpdfstring{Order on $\mathbb{Q}$}{Order on Q}}" "\n"
            r"\input{volume-ii/integers/notes/order/notes-order}" "\n"
            r"\section{\texorpdfstring{Order on $\mathbb{R}$}{Order on R}}" "\n"
            r"\input{volume-ii/integers/notes/order/notes-extra}" "\n",
        )

        codes = {finding.code for finding in validate_with_inventory(notes_structure, volume)}

        self.assertIn("notes_topic_index_duplicate_section", codes)
        self.assertNotIn("unrouted_notes_topic_body", codes)

    def test_notes_structure_allows_toolkit_boxes_in_topic_index(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "index.tex",
            "\n".join(
                [
                    r"\section{Order Notes}",
                    r"\begin{toolkitbox}{Order Toolkit}",
                    "Rendered prose is allowed inside the toolkit.",
                    r"\begin{itemize}",
                    r"  \item Table/list content is ignored by the router validator.",
                    r"\end{itemize}",
                    r"\end{toolkitbox}",
                    r"\begin{toolkitbox}{Second Order Toolkit}",
                    r"\begin{tabular}{l l}",
                    r"A & B \\",
                    r"\end{tabular}",
                    r"\end{toolkitbox}",
                    r"\input{volume-ii/integers/notes/order/notes-order}",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(notes_structure, volume)}

        self.assertNotIn("notes_topic_index_contains_rendered_content", codes)

    def test_block_discipline_accepts_canonical_fixture(self):
        volume = make_volume()

        self.assertEqual(validate_with_inventory(block_discipline, volume), [])

    def test_block_discipline_flags_top_level_prose_and_plain_remark(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    "Loose prose.",
                    r"\begin{remark}",
                    "Plain remark.",
                    r"\end{remark}",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(block_discipline, volume)}

        self.assertIn("top_level_prose", codes)
        self.assertIn("plain_remark_or_example", codes)

    def test_block_discipline_flags_proof_inside_note(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{proof}",
                    "This belongs in the proof vault.",
                    r"\end{proof}",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(block_discipline, volume)}

        self.assertIn("proof_inside_note", codes)

    def test_block_discipline_flags_topicbox_or_exposition_in_proof(self):
        volume = make_volume()
        write(
            volume / "integers" / "proofs" / "order" / "prf-extra.tex",
            "\n".join(
                [
                    r"\begin{topicbox}{Proof idea}",
                    "This structural box is not allowed in proof files.",
                    r"\end{topicbox}",
                    r"\begin{exposition}",
                    "This exposition block is not allowed in proof files.",
                    r"\end{exposition}",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(block_discipline, volume)}

        self.assertIn("topicbox_or_exposition_in_proof", codes)

    def test_formal_reading_accepts_canonical_fixture(self):
        volume = make_volume()

        self.assertEqual(validate_with_inventory(formal_reading_required, volume), [])

    def test_formal_reading_flags_trigger_without_reading(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{lemma}[Universal order]",
                    r"\label{lem:universal-order}",
                    "For all ordered integers, order is reflexive.",
                    r"\end{lemma}",
                    r"\NoLocalDependencies",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(formal_reading_required, volume)}

        self.assertIn("formal_reading_missing", codes)

    def test_formal_reading_flags_simple_with_trigger(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{lemma}[Universal order]",
                    r"\label{lem:simple-universal-order}",
                    "lra:simple. For every ordered integer, order is reflexive.",
                    r"\end{lemma}",
                    r"\NoLocalDependencies",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(formal_reading_required, volume)}

        self.assertIn("simple_but_triggers", codes)

    def test_structural_chrome_accepts_canonical_fixture(self):
        volume = make_volume()

        self.assertEqual(validate_with_inventory(structural_chrome, volume), [])

    def test_structural_chrome_flags_toolkit_body_and_raw_toolkit(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\subsection*{Order}",
                    r"\begin{toolkitbox}{Toolkit}",
                    "orients def:order",
                    r"\end{toolkitbox}",
                    r"\begin{tcolorbox}[title={Toolkit: Order}]",
                    "raw toolkit",
                    r"\end{tcolorbox}",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(structural_chrome, volume)}

        self.assertIn("toolkit_not_in_notes_router", codes)
        self.assertIn("toolkit_hand_rolled", codes)

    def test_structural_chrome_flags_toolkit_misplaced_and_contains_formal(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "index.tex",
            "\n".join(
                [
                    r"\section{Order}",
                    "loose intro",
                    r"\begin{toolkitbox}{Toolkit}",
                    r"\begin{definition}[Bad]",
                    r"\label{def:bad-toolkit}",
                    "Bad.",
                    r"\end{definition}",
                    r"\end{toolkitbox}",
                    r"\input{volume-ii/integers/notes/order/notes-order}",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(structural_chrome, volume)}

        self.assertIn("toolkit_misplaced", codes)
        self.assertIn("toolkit_contains_formal", codes)

    def test_structural_chrome_validates_toolkit_link_targets(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "index.tex",
            "\n".join(
                [
                    r"\section{Order Notes}",
                    r"\begin{toolkitbox}{Order Toolkit}",
                    r"\begin{tabular}{l l}",
                    r"\textbf{Name} & \textbf{Meaning} \\",
                    r"\hyperref[prop:order]{Order} & valid target \\",
                    r"\hyperref[def:missing-order]{Missing} & invalid target \\",
                    r"\end{tabular}",
                    r"\end{toolkitbox}",
                    r"\input{volume-ii/integers/notes/order/notes-order}",
                    "",
                ]
            ),
        )

        findings = validate_with_inventory(structural_chrome, volume)
        codes = {finding.code for finding in findings}
        self.assertIn("toolkit_link_unknown_target", codes)
        self.assertTrue(
            any(
                finding.code == "toolkit_link_unknown_target"
                and "def:missing-order" in finding.message
                and finding.severity == "error"
                for finding in findings
            )
        )

    def test_structural_chrome_warns_for_nonleading_toolkit_links(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "index.tex",
            "\n".join(
                [
                    r"\section{Order Notes}",
                    r"\begin{toolkitbox}{Order Toolkit}",
                    r"\begin{tabular}{l l}",
                    r"\textbf{Name} & \textbf{Meaning} \\",
                    r"Order & \hyperref[prop:order]{valid target} \\",
                    r"\end{tabular}",
                    r"\end{toolkitbox}",
                    r"\input{volume-ii/integers/notes/order/notes-order}",
                    "",
                ]
            ),
        )

        findings = validate_with_inventory(structural_chrome, volume)
        self.assertTrue(
            any(
                finding.code == "toolkit_link_not_leading_cell"
                and finding.severity == "warning"
                for finding in findings
            )
        )

    def test_structural_chrome_flags_toolkit_table_shape(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "index.tex",
            "\n".join(
                [
                    r"\section{Order Notes}",
                    r"\begin{toolkitbox}{Order Toolkit}",
                    r"\begin{tabular}{l l l}",
                    r"\textbf{Name} & \textbf{Meaning} & \textbf{Extra} \\",
                    r"\hyperref[prop:order]{Order} & valid target & extra \\",
                    r"\end{tabular}",
                    r"\end{toolkitbox}",
                    r"\begin{toolkitbox}{Role Toolkit}",
                    r"\begin{tabular}{l l}",
                    r"\textbf{Name} & \textbf{Role} \\",
                    r"\hyperref[prop:order]{Order} & valid target \\",
                    r"\end{tabular}",
                    r"\end{toolkitbox}",
                    r"\begin{toolkitbox}{Concept Toolkit}",
                    r"\begin{tabular}{l l}",
                    r"\textbf{Concept} & \textbf{Meaning} \\",
                    r"\hyperref[prop:order]{Order} & valid target \\",
                    r"\end{tabular}",
                    r"\end{toolkitbox}",
                    r"\begin{toolkitbox}{Missing Table}",
                    "plain list",
                    r"\end{toolkitbox}",
                    r"\input{volume-ii/integers/notes/order/notes-order}",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(structural_chrome, volume)}

        self.assertIn("toolkit_table_not_two_columns", codes)
        self.assertIn("toolkit_second_column_not_meaning", codes)
        self.assertIn("toolkit_first_column_not_name", codes)
        self.assertIn("toolkit_missing_table", codes)

    def test_structural_chrome_flags_inline_tikzpicture(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{tikzpicture}",
                    r"\draw (0,0) -- (1,1);",
                    r"\end{tikzpicture}",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(structural_chrome, volume)}

        self.assertIn("inline_tikzpicture", codes)

    def test_structural_chrome_allows_standalone_tikz_figure_file(self):
        volume = make_volume()
        write(
            volume / "integers" / "figures" / "fig-order-diagram.tex",
            "\n".join(
                [
                    r"\begin{tikzpicture}",
                    r"\draw (0,0) -- (1,1);",
                    r"\end{tikzpicture}",
                    "",
                ]
            ),
        )
        with (volume / "integers" / "notes" / "order" / "notes-order.tex").open("a", encoding="utf-8") as handle:
            handle.write(
                "\n".join(
                    [
                        r"\begin{figure}[H]",
                        r"\input{volume-ii/integers/figures/fig-order-diagram}",
                        r"\caption{Order diagram}",
                        r"\label{fig:order-diagram}",
                        r"\end{figure}",
                        "",
                    ]
                )
            )

        findings = validate_with_inventory(structural_chrome, volume)
        figure_findings = [
            finding
            for finding in findings
            if finding.code == "inline_tikzpicture" and "fig-order-diagram" in finding.path
        ]

        self.assertEqual([], figure_findings)

    def test_structural_chrome_flags_retired_text_and_hand_rolled_breadcrumb(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{tcolorbox}[colback=breadcrumb]",
                    "manual breadcrumb",
                    r"\end{tcolorbox}",
                    "Structural Roadmap",
                    "Structural Role",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(structural_chrome, volume)}

        self.assertIn("breadcrumb_hand_rolled", codes)
        self.assertIn("structural_roadmap_present", codes)
        self.assertIn("structural_role_present", codes)

    def test_reference_voice_accepts_canonical_fixture(self):
        volume = make_volume()

        self.assertEqual(validate_with_inventory(reference_voice, volume), [])

    def test_reference_voice_flags_classroom_voice(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{remark*}[Orientation]",
                    "We now ask students to compare these forms.",
                    r"\end{remark*}",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(reference_voice, volume)}

        self.assertIn("non_reference_voice", codes)

    def test_reference_voice_accepts_mathematical_class(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{remark*}[Interpretation]",
                    "The equivalence class records all representatives of the same object.",
                    r"\end{remark*}",
                    "",
                ]
            ),
        )

        self.assertEqual(validate_with_inventory(reference_voice, volume), [])

    def test_formal_decoration_accepts_canonical_fixture(self):
        volume = make_volume()

        self.assertEqual(validate_with_inventory(formal_decoration, volume), [])

    def test_operator_metadata_flags_unregistered_operatorname(self):
        volume = make_volume()
        note = volume / "integers" / "notes" / "order" / "notes-order.tex"
        note.write_text(
            "\n".join(
                [
                    r"\begin{remark*}[Predicate reading]",
                    r"\[",
                    r"\operatorname{UnknownLocalPredicate}(x)",
                    r"\quad\text{and}\quad",
                    r"\operatorname{IsContinuous}(f,I,X,Y)",
                    r"\quad\text{and}\quad",
                    r"\operatorname{Carrier}(X)",
                    r"\]",
                    r"\end{remark*}",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        findings = validate_with_inventory(operator_metadata, volume)

        self.assertEqual([finding.code for finding in findings], ["unregistered_operatorname"])
        self.assertIn("UnknownLocalPredicate", findings[0].message)

    def test_formal_decoration_flags_source_and_expository_claims(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{lemma}[Decorated]",
                    r"\label{lem:decorated}",
                    "Decorated.",
                    r"\end{lemma}",
                    r"\begin{remark*}[Historical note]",
                    "This follows a source tradition.",
                    r"\end{remark*}",
                    r"\begin{remark*}[Examples]",
                    r"\label{ex:bad-decoration}",
                    "This should not label a formal example here.",
                    r"\end{remark*}",
                    r"\NoLocalDependencies",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(formal_decoration, volume)}

        self.assertIn("source_crosswalk_without_citation", codes)
        self.assertIn("formal_claim_inside_expository_block", codes)

    def test_formal_decoration_accepts_source_comparison_with_bottom_citation(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{definition}[Source Compared]",
                    r"\label{def:source-compared}",
                    "A source-compared object is organized for comparison.",
                    r"\end{definition}",
                    r"\begin{remark*}[Interpretation]",
                    "The object is used only to exercise source comparison metadata.",
                    r"\end{remark*}",
                    r"\begin{remark*}[Source comparison]",
                    "Compared with Dedekind's presentation, this version separates the",
                    "ambient set from the ordering relation.",
                    r"\citet{DedekindContinuityIrrationalNumbers}",
                    r"\end{remark*}",
                    r"\NoLocalDependencies",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(formal_decoration, volume)}

        self.assertNotIn("unknown_decoration_block", codes)
        self.assertNotIn("source_crosswalk_without_citation", codes)
        self.assertNotIn("source_comparison_citation_not_at_bottom", codes)

    def test_formal_decoration_flags_source_comparison_without_citation(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{definition}[Uncited Source Comparison]",
                    r"\label{def:uncited-source-comparison}",
                    "An uncited comparison has no source evidence.",
                    r"\end{definition}",
                    r"\begin{remark*}[Interpretation]",
                    "The object is used only to exercise source comparison metadata.",
                    r"\end{remark*}",
                    r"\begin{remark*}[Source comparison]",
                    "Compared with a source presentation, this version is reorganized.",
                    r"\end{remark*}",
                    r"\NoLocalDependencies",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(formal_decoration, volume)}

        self.assertIn("source_crosswalk_without_citation", codes)

    def test_formal_decoration_flags_source_comparison_citation_not_at_bottom(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{definition}[Midstream Source Comparison]",
                    r"\label{def:midstream-source-comparison}",
                    "A midstream comparison cites before the final prose.",
                    r"\end{definition}",
                    r"\begin{remark*}[Interpretation]",
                    "The object is used only to exercise source comparison metadata.",
                    r"\end{remark*}",
                    r"\begin{remark*}[Source comparison]",
                    r"\citet{TaoAnalysisI}",
                    "The block continues after the citation.",
                    r"\end{remark*}",
                    r"\NoLocalDependencies",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(formal_decoration, volume)}

        self.assertIn("source_comparison_citation_not_at_bottom", codes)

    def test_formal_decoration_rejects_named_comparison_block_titles(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{definition}[Named Comparison]",
                    r"\label{def:named-comparison}",
                    "A named comparison uses an obsolete title.",
                    r"\end{definition}",
                    r"\begin{remark*}[Interpretation]",
                    "The object is used only to exercise source comparison metadata.",
                    r"\end{remark*}",
                    r"\begin{remark*}[Comparison with Feferman]",
                    r"This title is no longer canonical. \citet{FefermanNumberSystems1964}",
                    r"\end{remark*}",
                    r"\NoLocalDependencies",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(formal_decoration, volume)}

        self.assertIn("unknown_decoration_block", codes)

    def test_formal_decoration_flags_order_unknown_forbidden_and_parent(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{axiom}[Decorated]",
                    r"\label{ax:decorated}",
                    "Decorated.",
                    r"\end{axiom}",
                    r"\begin{remark*}[Dependencies]",
                    "Legacy dependencies wording.",
                    r"\end{remark*}",
                    r"\begin{remark*}[Interpretation]",
                    "Interpretation.",
                    r"\end{remark*}",
                    r"\begin{remark*}[Examples]",
                    "Forbidden on axioms.",
                    r"\end{remark*}",
                    r"\begin{remark*}[Failure mode decomposition]",
                    "Needs parent failure modes.",
                    r"\end{remark*}",
                    r"\begin{remark*}[Custom block]",
                    "Unknown.",
                    r"\end{remark*}",
                    r"\NoLocalDependencies",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(formal_decoration, volume)}

        self.assertIn("decoration_order", codes)
        self.assertIn("forbidden_decoration_block", codes)
        self.assertIn("unknown_decoration_block", codes)

    def test_formal_decoration_requires_predicate_reading_for_multiple_binders(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{definition}[Binary Relation]",
                    r"\label{def:binary-relation-extra}",
                    "A relation is binary when it compares two inputs.",
                    r"\end{definition}",
                    r"\begin{remark*}[Standard quantified statement]",
                    r"\[",
                    r"\forall x,y\in A,\quad R(x,y).",
                    r"\]",
                    r"\end{remark*}",
                    r"\begin{remark*}[Interpretation]",
                    "The statement reads the relation as a two-input predicate.",
                    r"\end{remark*}",
                    r"\NoLocalDependencies",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(formal_decoration, volume)}

        self.assertIn("predicate_reading_missing", codes)

    def test_formal_decoration_flags_unstructured_failure_modes(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{proposition}[Conditional Order]",
                    r"\label{prop:conditional-order-extra}",
                    r"If $x \leq y$, then $x$ is below $y$.",
                    r"\hyperref[prf:conditional-order-extra]{\textit{Go to proof.}}",
                    r"\end{proposition}",
                    r"\begin{remark*}[Standard quantified statement]",
                    r"\[",
                    r"\forall x,y\in A,\quad x \leq y \Rightarrow x \preceq y.",
                    r"\]",
                    r"\end{remark*}",
                    r"\begin{remark*}[Predicate reading]",
                    r"\[",
                    r"P(x,y) \Rightarrow Q(x,y).",
                    r"\]",
                    r"\end{remark*}",
                    r"\begin{remark*}[Failure modes]",
                    r"\begin{description}",
                    r"\item[Missing antecedent.]",
                    "The antecedent may fail.",
                    r"\[",
                    r"\exists x,y\in A,\quad x \nleq y.",
                    r"\]",
                    r"\end{description}",
                    r"\end{remark*}",
                    r"\begin{remark*}[Interpretation]",
                    "The statement transfers an order comparison into another relation.",
                    r"\end{remark*}",
                    r"\NoLocalDependencies",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(formal_decoration, volume)}

        self.assertIn("failure_modes_missing_exposition_item", codes)
        self.assertIn("failure_mode_missing_predicate_display", codes)

    def test_formal_decoration_flags_duplicate_support_blocks(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{definition}[Duplicate Support Blocks]",
                    r"\label{def:duplicate-support-blocks}",
                    "A duplicate support block test is an ordered object.",
                    r"\end{definition}",
                    r"\begin{remark*}[Standard quantified statement]",
                    "For every admissible object, the definition applies.",
                    r"\end{remark*}",
                    r"\begin{remark*}[Interpretation]",
                    "First interpretation.",
                    r"\end{remark*}",
                    r"\begin{remark*}[Interpretation]",
                    "Second interpretation.",
                    r"\end{remark*}",
                    r"\begin{remark*}[Failure modes]",
                    r"\begin{description}",
                    r"\item[Exposition.]",
                    "First failure family.",
                    r"\item[First branch.]",
                    r"\[",
                    r"\exists x\in A,\quad x \notin A.",
                    r"\]",
                    r"\end{description}",
                    r"\end{remark*}",
                    r"\begin{remark*}[Failure modes]",
                    r"\begin{description}",
                    r"\item[Exposition.]",
                    "Second failure family.",
                    r"\item[Second branch.]",
                    r"\[",
                    r"\exists y\in A,\quad y \notin A.",
                    r"\]",
                    r"\end{description}",
                    r"\end{remark*}",
                    r"\begin{remark*}[Exposition]",
                    "First exposition.",
                    r"\end{remark*}",
                    r"\begin{remark*}[Exposition]",
                    "Second exposition.",
                    r"\end{remark*}",
                    r"\begin{remark*}[Examples]",
                    "First example.",
                    r"\end{remark*}",
                    r"\begin{remark*}[Examples]",
                    "Second example.",
                    r"\end{remark*}",
                    r"\begin{dependencies}",
                    r"\begin{itemize}",
                    r"  \item \hyperref[def:ordered-set]{Ordered Set}",
                    r"\end{itemize}",
                    r"\end{dependencies}",
                    "",
                ]
            ),
        )

        findings = validate_with_inventory(formal_decoration, volume)
        duplicate_findings = [
            finding for finding in findings
            if finding.code == "duplicate_decoration_block"
        ]

        self.assertEqual(len(duplicate_findings), 1)
        self.assertIn("interpretation", duplicate_findings[0].message)

    def test_formal_decoration_requires_matching_go_to_proof_link(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{theorem}[Missing Link]",
                    r"\label{thm:missing-link}",
                    "Missing proof navigation.",
                    r"\end{theorem}",
                    r"\NoLocalDependencies",
                    "",
                    r"\begin{lemma}[Wrong Link]",
                    r"\label{lem:wrong-link}",
                    "Wrong proof navigation.",
                    r"\hyperref[prf:not-wrong-link]{\textit{Go to proof.}}",
                    r"\end{lemma}",
                    r"\NoLocalDependencies",
                    "",
                    r"\begin{definition}[No Proof Link Needed]",
                    r"\label{def:no-proof-link-needed}",
                    "Definitions do not need proof navigation.",
                    r"\end{definition}",
                    r"\NoLocalDependencies",
                    "",
                ]
            ),
        )

        findings = validate_with_inventory(formal_decoration, volume)
        by_code = {finding.code: finding for finding in findings}

        self.assertIn("missing_go_to_proof_link", by_code)
        self.assertIn("wrong_go_to_proof_target", by_code)
        self.assertTrue(all(
            finding.severity == "error"
            for finding in findings
            if finding.code in {"missing_go_to_proof_link", "wrong_go_to_proof_target"}
        ))
        self.assertNotIn("def:no-proof-link-needed", "\n".join(f.message for f in findings))

    def test_formal_decoration_errors_on_blocks_inside_formal_blocks(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{theorembox}{Bad Box}",
                    r"\begin{theorem}[Bad Box]",
                    r"\label{thm:bad-box-decoration}",
                    "Statement.",
                    r"\end{theorem}",
                    r"\begin{remark*}[Standard quantified statement]",
                    "This support block belongs after the box.",
                    r"\end{remark*}",
                    r"\end{theorembox}",
                    r"\begin{proposition}[Bad Inline]",
                    r"\label{prop:bad-inline-decoration}",
                    "Statement.",
                    r"\textbf{Failure modes.}",
                    "This support heading belongs after the proposition.",
                    r"\end{proposition}",
                    "",
                ]
            ),
        )

        findings = validate_with_inventory(formal_decoration, volume)
        matches = [finding for finding in findings if finding.code == "decoration_block_inside_formal_block"]

        self.assertGreaterEqual(len(matches), 2)
        self.assertTrue(all(finding.severity == "error" for finding in matches))

    def test_math_boxes_flags_raw_and_wrong_but_allows_unwrapped_formal_blocks(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "index.tex",
            r"\input{volume-ii/integers/notes/order/notes-order}" "\n"
            r"\input{volume-ii/integers/notes/order/notes-extra}" "\n",
        )
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{tcolorbox}",
                    r"\begin{lemma}[Raw]",
                    r"\label{lem:raw-box}",
                    "Raw box.",
                    r"\end{lemma}",
                    r"\end{tcolorbox}",
                    r"\begin{theorembox}{Wrong}",
                    r"\begin{lemma}[Wrong]",
                    r"\label{lem:wrong-box}",
                    "Wrong box.",
                    r"\end{lemma}",
                    r"\end{theorembox}",
                    r"\begin{lemma}[Bare]",
                    r"\label{lem:bare-box}",
                    "Bare box.",
                    r"\end{lemma}",
                    r"\begin{tcolorbox}",
                    r"\begin{remark*}[Boxed]",
                    "Nonformal boxed content.",
                    r"\end{remark*}",
                    r"\end{tcolorbox}",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(math_boxes, volume)}

        self.assertIn("raw_tcolorbox_wrapper", codes)
        self.assertIn("wrong_box_macro", codes)
        self.assertNotIn("unwrapped_math_env", codes)
        self.assertIn("boxed_nonformal_content", codes)

    def test_math_boxes_warns_on_multi_label_decorative_box(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "index.tex",
            r"\input{volume-ii/integers/notes/order/notes-extra}" "\n",
        )
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{propositionbox}{Definition (Cover, Subcover, Finite Cover)}",
                    r"\label{def:cover-full}",
                    r"\begin{enumerate}",
                    r"\item \label{def:subcover}",
                    "Subcover.",
                    r"\item \label{def:finite-cover}",
                    "Finite cover.",
                    r"\end{enumerate}",
                    r"\end{propositionbox}",
                    "",
                ]
            ),
        )

        findings = validate_with_inventory(math_boxes, volume)
        by_code = {finding.code: finding for finding in findings}

        self.assertEqual(by_code["multiple_formal_labels_in_box"].severity, "warning")

    def test_math_boxes_flags_label_on_decorative_box(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "index.tex",
            r"\input{volume-ii/integers/notes/order/notes-extra}" "\n",
        )
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{theorembox}{Hausdorff Maximum Principle}",
                    r"\label{thm:hausdorff}",
                    "Every poset has a maximal chain.",
                    r"\end{theorembox}",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(math_boxes, volume)}

        self.assertIn("formal_label_on_box", codes)

    def test_math_boxes_checks_canonical_wrapper_when_present(self):
        volume = make_volume()
        note = volume / "integers" / "notes" / "order" / "notes-extra.tex"
        write(
            volume / "integers" / "notes" / "order" / "index.tex",
            r"\input{volume-ii/integers/notes/order/notes-order}" "\n"
            r"\input{volume-ii/integers/notes/order/notes-extra}" "\n",
        )
        write(
            note,
            "\n".join(
                [
                    r"\begin{definition}[Raw Definition]",
                    r"\label{def:raw-definition}",
                    "Raw definition.",
                    r"\end{definition}",
                    r"\begin{axiombox}{Wrong Axiom}",
                    r"\begin{theorem}[Wrong Axiom]",
                    r"\label{thm:wrong-axiom}",
                    "Wrong wrapper.",
                    r"\end{theorem}",
                    r"\end{axiombox}",
                    r"\begin{tcolorbox}",
                    r"\begin{axiom}[Raw Axiom Box]",
                    r"\label{ax:raw-axiom-box}",
                    "Raw tcolorbox.",
                    r"\end{axiom}",
                    r"\end{tcolorbox}",
                    "",
                ]
            ),
        )

        findings = validate_with_inventory(math_boxes, volume)
        by_code = {finding.code: finding for finding in findings}

        self.assertNotIn("unwrapped_math_env", by_code)
        self.assertIn("wrong_box_macro", by_code)
        self.assertIn("raw_tcolorbox_wrapper", by_code)

        env_to_box = {
            "definition": "definitionbox",
            "axiom": "axiombox",
            "theorem": "theorembox",
            "lemma": "lemmabox",
            "proposition": "propositionbox",
            "corollary": "corollarybox",
        }
        canonical = []
        for env, box in env_to_box.items():
            title = env.title()
            canonical.extend(
                [
                    rf"\begin{{{box}}}{{{title}}}",
                    rf"\begin{{{env}}}[{title}]",
                    rf"\label{{{env[:3]}:{env}}}",
                    f"{title}.",
                    rf"\end{{{env}}}",
                    rf"\end{{{box}}}",
                ]
            )
        write(note, "\n".join(canonical + [""]))

        self.assertEqual(validate_with_inventory(math_boxes, volume), [])

    def test_interpretation_blocks_flags_missing_interpretation(self):
        volume = make_volume()
        note = volume / "integers" / "notes" / "order" / "notes-order.tex"
        note.write_text(
            "\n".join(
                [
                    r"\begin{axiom}[Order Foundation]",
                    r"\label{ax:order-foundation}",
                    "Order has a foundation.",
                    r"\end{axiom}",
                    r"\NoLocalDependencies",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        codes = {finding.code for finding in validate_with_inventory(interpretation_blocks, volume)}

        self.assertIn("missing_interpretation", codes)

    def test_interpretation_blocks_accepts_interpretation_remark(self):
        volume = make_volume()
        note = volume / "integers" / "notes" / "order" / "notes-order.tex"
        note.write_text(
            "\n".join(
                [
                    r"\begin{axiom}[Order Foundation]",
                    r"\label{ax:order-foundation}",
                    "Order has a foundation.",
                    r"\end{axiom}",
                    r"\begin{remark*}[Interpretation]",
                    "This fixes the order background.",
                    r"\end{remark*}",
                    r"\NoLocalDependencies",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        self.assertEqual(validate_with_inventory(interpretation_blocks, volume), [])

    def test_labels_flags_duplicate_and_wrong_prefix(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{lemma}[Bad]",
                    r"\label{thm:bad-prefix}",
                    "Bad prefix.",
                    r"\end{lemma}",
                    r"\label{prop:order}",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(labels, volume)}

        self.assertIn("duplicate_label", codes)
        self.assertIn("wrong_label_prefix", codes)

    def test_capstones_accepts_canonical_fixture(self):
        volume = make_volume()

        self.assertEqual(validate_with_inventory(capstones, volume), [])

    def test_capstones_flags_missing_theorem_and_not_last(self):
        volume = make_volume()
        capstone = volume / "integers" / "proofs" / "exercises" / "capstone-integers.tex"
        capstone.write_text(capstone.read_text(encoding="utf-8").replace("Theorem", ""), encoding="utf-8")
        index = volume / "integers" / "proofs" / "exercises" / "index.tex"
        index.write_text(
            r"\input{volume-ii/integers/proofs/exercises/capstone-integers}" "\n"
            r"\input{volume-ii/integers/proofs/exercises/ex-extra}" "\n",
            encoding="utf-8",
        )

        codes = {finding.code for finding in validate_with_inventory(capstones, volume)}

        self.assertIn("missing_capstone_theorem", codes)
        self.assertIn("capstone_not_last", codes)

    def test_capstones_flags_rendered_content_in_exercises_index(self):
        volume = make_volume()
        index = volume / "integers" / "proofs" / "exercises" / "index.tex"
        index.write_text(
            r"\subsection*{Exercise Proofs}" "\n"
            r"\input{volume-ii/integers/proofs/exercises/capstone-integers}" "\n",
            encoding="utf-8",
        )

        codes = {finding.code for finding in validate_with_inventory(capstones, volume)}

        self.assertIn("exercises_index_contains_rendered_content", codes)

    def test_latex_integrity_flags_mismatched_environment(self):
        volume = make_volume()
        path = volume / "integers" / "notes" / "order" / "notes-bad-env.tex"
        write(path, r"\begin{remark*}" "\n" r"\end{proof}" "\n")

        codes = {finding.code for finding in validate_with_inventory(latex_integrity, volume)}

        self.assertIn("mismatched_environment", codes)

    def test_input_resolution_flags_missing_input_target(self):
        volume = make_volume()
        index = volume / "integers" / "proofs" / "index.tex"
        index.write_text(
            r"\input{volume-ii/integers/proofs/missing-topic/index}" "\n",
            encoding="utf-8",
        )

        codes = {finding.code for finding in validate_with_inventory(input_resolution, volume)}

        self.assertIn("missing_input_target", codes)

    def test_structural_positions_flags_embedded_clearpage(self):
        volume = make_volume()
        capstone = volume / "integers" / "proofs" / "exercises" / "capstone-integers.tex"
        capstone.write_text(
            capstone.read_text(encoding="utf-8").replace(
                r"\clearpage",
                "near\n" + r"\clearpage$, find the limit.",
                1,
            ),
            encoding="utf-8",
        )

        codes = {finding.code for finding in validate_with_inventory(structural_positions, volume)}

        self.assertIn("illegal_clearpage_position", codes)

    def test_dependency_blocks_accepts_canonical_fixture(self):
        volume = make_volume()

        self.assertEqual(validate_with_inventory(dependency_blocks, volume), [])

    def test_dependency_blocks_flags_no_local_on_non_axiom(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{definition}[Primitive-looking Definition]",
                    r"\label{def:primitive-looking-definition}",
                    "A primitive-looking definition is not an axiom.",
                    r"\end{definition}",
                    r"\NoLocalDependencies",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(dependency_blocks, volume)}

        self.assertIn("no_local_dependencies_on_non_axiom", codes)

    def test_dependency_blocks_flags_definitional_root_inside_dependencies(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-extra.tex",
            "\n".join(
                [
                    r"\begin{definition}[Primitive Definition]",
                    r"\label{def:primitive-definition}",
                    "A primitive definition is reviewed as a root.",
                    r"\end{definition}",
                    r"\begin{dependencies}",
                    r"\DefinitionalRoot",
                    r"\end{dependencies}",
                    "",
                ]
            ),
        )

        findings = validate_with_inventory(dependency_blocks, volume)
        codes = {finding.code for finding in findings}

        self.assertIn("definitional_root_inside_dependencies", codes)
        self.assertTrue(any(
            finding.code == "definitional_root_inside_dependencies" and finding.severity == "error"
            for finding in findings
        ))

    def test_dependency_blocks_flags_missing_and_bad_targets(self):
        volume = make_volume()
        note = volume / "integers" / "notes" / "order" / "notes-order.tex"
        note.write_text(
            "\n".join(
                [
                    r"\begin{proposition}[Order]",
                    r"\label{prop:order}",
                    "Every ordered integer is ordered.",
                    r"\end{proposition}",
                    r"\begin{dependencies}",
                    r"\begin{itemize}",
                    r"  \item \hyperref[prf:order]{proof target}",
                    r"  \item \hyperref[fig:order]{figure target}",
                    r"\end{itemize}",
                    r"\end{dependencies}",
                    "",
                    r"\begin{lemma}[Missing]",
                    r"\label{lem:missing-deps}",
                    "Missing dependencies.",
                    r"\end{lemma}",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        codes = {finding.code for finding in validate_with_inventory(dependency_blocks, volume)}

        self.assertIn("dependency_targets_proof", codes)
        self.assertIn("invalid_dependency_target_prefix", codes)
        self.assertIn("missing_dependencies", codes)
        self.assertTrue(any(
            finding.code == "missing_dependencies" and finding.severity == "error"
            for finding in validate_with_inventory(dependency_blocks, volume)
        ))

    def test_dependency_graphs_accepts_canonical_fixture(self):
        volume = make_volume()

        self.assertEqual(validate_with_inventory(dependency_graphs, volume), [])

    def test_dependency_graph_uses_live_reachable_files(self):
        volume = make_volume()
        repo = volume.parent
        write(
            volume / "integers" / "notes" / "order" / "orphan-duplicate.tex",
            "\n".join(
                [
                    r"\begin{axiom}[Orphan Duplicate]",
                    r"\label{ax:order-foundation}",
                    "This orphan should not enter the dependency graph universe.",
                    r"\end{axiom}",
                    r"\NoLocalDependencies",
                    "",
                ]
            ),
        )

        universe = dependency_graph.build_universe(repo.parent, repo.name)
        files = {node.file for node in universe.nodes}
        codes = {issue.code for issue in universe.issues}

        self.assertNotIn("volume-ii/integers/notes/order/orphan-duplicate.tex", files)
        self.assertNotIn("duplicate_global_label", codes)

    def test_dependency_graph_closure_uses_merged_cross_volume_edges(self):
        if TMP.exists():
            shutil.rmtree(TMP)
        volume_i = TMP / "lra-volume-i" / "volume-i"
        volume_ii = TMP / "lra-volume-ii" / "volume-ii"
        write(volume_i / "index.tex", r"\input{volume-i/book-sets/index}" + "\n")
        write(volume_i / "book-sets" / "index.tex", r"\input{volume-i/book-sets/notes-order}" + "\n")
        write(
            volume_i / "book-sets" / "notes-order.tex",
            "\n".join(
                [
                    r"\begin{axiom}[Set Foundation]",
                    r"\label{ax:set-foundation}",
                    "Sets have a foundation.",
                    r"\end{axiom}",
                    r"\NoLocalDependencies",
                    "",
                    r"\begin{definition}[Base Structure]",
                    r"\label{def:base-structure}",
                    "A base structure is a set with the foundational datum.",
                    r"\end{definition}",
                    r"\begin{dependencies}",
                    r"\begin{itemize}",
                    r"  \item \hyperref[ax:set-foundation]{Set Foundation}",
                    r"\end{itemize}",
                    r"\end{dependencies}",
                    "",
                ]
            ),
        )
        write(volume_ii / "index.tex", r"\input{volume-ii/book-analysis/index}" + "\n")
        write(volume_ii / "book-analysis" / "index.tex", r"\input{volume-ii/book-analysis/notes-theorem}" + "\n")
        write(
            volume_ii / "book-analysis" / "notes-theorem.tex",
            "\n".join(
                [
                    r"\begin{theorem}[Uses Base Structure]",
                    r"\label{thm:uses-base-structure}",
                    "Every base structure is available for analysis.",
                    r"\end{theorem}",
                    r"\begin{dependencies}",
                    r"\begin{itemize}",
                    r"  \item \hyperref[def:base-structure]{Base Structure}",
                    r"\end{itemize}",
                    r"\end{dependencies}",
                    "",
                ]
            ),
        )

        codes = {finding.code for finding in validate_with_inventory(dependency_graphs, volume_ii)}

        self.assertNotIn("closure_leaf_not_allowed_root", codes)

    def test_dependency_graph_cycles_are_errors(self):
        volume = make_volume()
        cycle_tex = "\n".join(
            [
                r"\begin{theorem}[First Cycle Node]",
                r"\label{thm:first-cycle-node}",
                "First cycle node.",
                r"\end{theorem}",
                r"\begin{dependencies}",
                r"\begin{itemize}",
                r"  \item \hyperref[thm:second-cycle-node]{Second Cycle Node}",
                r"\end{itemize}",
                r"\end{dependencies}",
                "",
                r"\begin{theorem}[Second Cycle Node]",
                r"\label{thm:second-cycle-node}",
                "Second cycle node.",
                r"\end{theorem}",
                r"\begin{dependencies}",
                r"\begin{itemize}",
                r"  \item \hyperref[thm:first-cycle-node]{First Cycle Node}",
                r"\end{itemize}",
                r"\end{dependencies}",
                "",
            ]
        )
        write(volume / "integers" / "notes" / "order" / "notes-order.tex", cycle_tex)

        findings = validate_with_inventory(dependency_graphs, volume)

        self.assertTrue(any(
            finding.code == "dependency_cycle" and finding.severity == "error"
            for finding in findings
        ))

    def test_dependency_graphs_invalid_formal_label_count_is_error(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-order.tex",
            "\n".join(
                [
                    r"\begin{definition}[Bundled Objects]",
                    r"\label{def:first-object}",
                    r"\label{def:second-object}",
                    "This incorrectly bundles two formal labels.",
                    r"\end{definition}",
                    r"\NoLocalDependencies",
                    "",
                ]
            ),
        )

        findings = validate_with_inventory(dependency_graphs, volume)

        self.assertTrue(any(
            finding.code == "invalid_formal_label_count" and finding.severity == "error"
            for finding in findings
        ))

    def test_dependency_graphs_accepts_euclid_book_i_legacy_alias(self):
        if TMP.exists():
            shutil.rmtree(TMP)
        repo = TMP / "lra-volume-i"
        volume = repo / "volume-i"
        propositions = (
            volume
            / "book-geometry"
            / "euclidean-geometry"
            / "notes"
            / "compass-and-straightedge-constructions"
            / "propositions.tex"
        )
        write(volume / "index.tex", r"\input{volume-i/book-geometry/index}" + "\n")
        write(
            volume / "book-geometry" / "index.tex",
            r"\input{volume-i/book-geometry/euclidean-geometry/notes/compass-and-straightedge-constructions/propositions}"
            + "\n",
        )
        write(
            propositions,
            "\n".join(
                [
                    r"\begin{theorem}[Euclid I.1]",
                    r"\label{thm:euclid-i-1}",
                    r"\label{prop:I.1}",
                    "Euclid's historical label is preserved as an alias.",
                    r"\end{theorem}",
                    r"\NoLocalDependencies",
                    "",
                ]
            ),
        )

        dependency_codes = {
            finding.code
            for finding in validate_with_inventory(dependency_graphs, volume)
        }
        label_codes = {finding.code for finding in validate_with_inventory(labels, volume)}

        self.assertNotIn("invalid_formal_label_count", dependency_codes)
        self.assertNotIn("weak_label_slug", label_codes)

    def test_dependency_graphs_rejects_euclid_alias_outside_approved_file(self):
        volume = make_volume()
        write(
            volume / "integers" / "notes" / "order" / "notes-order.tex",
            "\n".join(
                [
                    r"\begin{theorem}[Not Euclid]",
                    r"\label{thm:euclid-i-1}",
                    r"\label{prop:I.1}",
                    "The legacy alias is only approved in Euclid Book I propositions.",
                    r"\end{theorem}",
                    r"\NoLocalDependencies",
                    "",
                ]
            ),
        )

        dependency_findings = validate_with_inventory(dependency_graphs, volume)
        label_codes = {finding.code for finding in validate_with_inventory(labels, volume)}

        self.assertTrue(any(
            finding.code == "invalid_formal_label_count" and finding.severity == "error"
            for finding in dependency_findings
        ))
        self.assertIn("weak_label_slug", label_codes)

    def test_validate_volume_reports_shape_without_fail_fast(self):
        volume = make_volume()
        (volume / "integers" / "proofs" / "exercises" / "capstone-integers.tex").unlink()
        write(
            volume / "integers" / "proofs" / "index.tex",
            r"\input{volume-ii/integers/proofs/order/index}" "\n"
            r"\input{volume-ii/integers/proofs/exercises/index}" "\n",
        )

        result = subprocess.run(
            [
                sys.executable,
                str(HERE / "validate_volume.py"),
                str(volume),
                "--fail-on-errors",
                "--no-preprocess",
            ],
            cwd=HERE,
            text=True,
            capture_output=True,
        )

        self.assertEqual(result.returncode, 2)
        self.assertNotIn("fail-fast", result.stdout)
        self.assertIn("proofs_index_routes_exercises", result.stdout)

    def test_chapter_generator_emits_shape_and_routing_clean_output(self):
        if TMP.exists():
            shutil.rmtree(TMP)
        volume = TMP / "lra-volume-test" / "volume-ii"
        write(volume / "index.tex", "")
        write(volume / "main.tex", "")

        stub_chapter(volume, "ordered-fields", "Ordered Fields", [], ["Order"])

        self.assertEqual(validate_with_inventory(volume_shape, volume), [])
        for name, validator in VALIDATORS:
            self.assertEqual(validate_with_inventory(validator, volume), [], name)

    def test_volume_shape_ignores_canonical_chapter_not_routed_from_volume_index(self):
        volume = make_volume()
        chapter = volume / "orphaned"
        write(chapter / "chapter.yaml", "subject: orphaned\n")
        write(
            chapter / "index.tex",
            "\n".join(
                [
                    r"\chapter{Orphaned}",
                    r"\label{chap:orphaned}",
                    r"\breadcrumb{orphaned}{}{Orphaned}{}",
                    r"\input{volume-ii/orphaned/notes/index}",
                    r"\LRAExcludeFromPrintEditionBegin",
                    r"\section*{Proofs}",
                    r"\input{volume-ii/orphaned/proofs/index}",
                    r"\section*{Capstone}",
                    r"\input{volume-ii/orphaned/proofs/exercises/index}",
                    r"\LRAExcludeFromPrintEditionEnd",
                    "",
                ]
            ),
        )
        write(chapter / "notes" / "index.tex", r"\section{Orphaned}" + "\n")
        write(chapter / "proofs" / "index.tex", "")
        write(chapter / "proofs" / "exercises" / "index.tex", "")
        write(chapter / "proofs" / "exercises" / "capstone-orphaned.tex", "")

        codes = {finding.code for finding in validate_with_inventory(volume_shape, volume)}

        self.assertNotIn("chapter_not_in_volume_index", codes)

    def test_section_generator_emits_shape_accepted_by_validators(self):
        if TMP.exists():
            shutil.rmtree(TMP)
        volume = TMP / "lra-volume-test" / "volume-ii"
        write(volume / "index.tex", "")
        write(volume / "main.tex", "")

        stub_chapter(volume, "ordered-fields", "Ordered Fields", [], ["Order"])
        stub_section(volume / "ordered-fields", "Completion Fields")

        parent_notes_index = (volume / "ordered-fields" / "notes" / "index.tex").read_text(encoding="utf-8")
        topic_notes_index = (
            volume / "ordered-fields" / "notes" / "completion-fields" / "index.tex"
        ).read_text(encoding="utf-8")

        self.assertIn(
            r"\input{volume-ii/ordered-fields/notes/completion-fields/index}",
            parent_notes_index,
        )
        self.assertNotIn(r"\section{Ordered Fields}", parent_notes_index)
        self.assertNotIn(r"\section{Completion Fields}", parent_notes_index)
        self.assertIn(r"\section{Completion Fields}", topic_notes_index)
        self.assertIn(
            r"\input{volume-ii/ordered-fields/proofs/completion-fields/index}",
            (volume / "ordered-fields" / "proofs" / "index.tex").read_text(encoding="utf-8"),
        )
        proof_routes = [
            line.strip()
            for line in (volume / "ordered-fields" / "proofs" / "index.tex").read_text(encoding="utf-8").splitlines()
            if line.strip().startswith(r"\input")
        ]
        self.assertEqual(
            proof_routes[-1:],
            [
                r"\input{volume-ii/ordered-fields/proofs/completion-fields/index}",
            ],
        )
        self.assertEqual(validate_with_inventory(volume_shape, volume), [])
        for name, validator in VALIDATORS:
            self.assertEqual(validate_with_inventory(validator, volume), [], name)

    def test_validators_reject_legacy_chapter_capstone_gate(self):
        volume = make_volume()
        index = volume / "integers" / "index.tex"
        index.write_text(
            index.read_text(encoding="utf-8").replace(
                r"\input{volume-ii/integers/proofs/exercises/index}",
                r"\LRACapstoneInput{volume-ii/integers/proofs/exercises/capstone-integers}",
            ),
            encoding="utf-8",
        )

        router_codes = {finding.code for finding in validate_with_inventory(chapter_router, volume)}
        routing_codes = {finding.code for finding in validate_with_inventory(print_edition_routing, volume)}

        self.assertIn("chapter_router_shape", router_codes)
        self.assertIn("legacy_print_edition_input_macro", routing_codes)

    def test_chapter_router_accepts_metadata_breadcrumb(self):
        volume = make_volume()
        index = volume / "integers" / "index.tex"
        index.write_text(
            index.read_text(encoding="utf-8").replace(
                r"\breadcrumb{integers}{}{Integers}{}",
                "\n".join(
                    [
                        r"\lrameta{",
                        r"  series = {From Cantor to Ito},",
                        r"  volume = {Volume II: Ordered Worlds},",
                        r"  book = {Book I: Number Systems},",
                        r"  chapter = {Chapter 1: Integers},",
                        r"  current = chapter,",
                        r"}",
                        r"\LraBreadcrumb",
                    ]
                ),
            ),
            encoding="utf-8",
        )

        self.assertEqual(validate_with_inventory(chapter_router, volume), [])

    def test_chapter_router_flags_extra_rendered_content(self):
        volume = make_volume()
        index = volume / "integers" / "index.tex"
        index.write_text(index.read_text(encoding="utf-8") + "extra prose\n", encoding="utf-8")

        codes = {finding.code for finding in validate_with_inventory(chapter_router, volume)}

        self.assertIn("chapter_router_shape", codes)

    def test_figure_fragments_enforce_nonfloating_book_fragments(self):
        volume = make_volume()
        figure_dir = volume.parent / "tex" / "figures"
        write(
            figure_dir / "good.tex",
            "\n".join(
                [
                    r"\begin{figure}[H]",
                    r"\centering",
                    r"\caption{Good figure}",
                    r"\label{fig:good}",
                    r"\end{figure}",
                    "",
                ]
            ),
        )
        write(
            figure_dir / "bad.tex",
            "\n".join(
                [
                    r"\documentclass{standalone}",
                    r"\begin{figure}[t]",
                    r"\centering",
                    r"\end{figure}",
                    "",
                ]
            ),
        )
        write(figure_dir / "_src" / "standalone.tex", r"\documentclass{standalone}")

        codes = {finding.code for finding in run_validator(figure_fragments, volume, [figure_dir / "good.tex", figure_dir / "bad.tex"])}

        self.assertIn("figure_fragment_document_tag", codes)
        self.assertIn("figure_fragment_missing_caption", codes)
        self.assertIn("figure_fragment_missing_label", codes)
        self.assertIn("figure_fragment_must_be_nonfloating", codes)
        self.assertNotIn("figure_fragment_missing_figure_environment", codes)

    def test_validate_volume_book_scope_limits_report_paths(self):
        if TMP.exists():
            shutil.rmtree(TMP)
        repo = TMP / "lra-volume-test"
        volume = repo / "volume-ii"
        for book in ("book-a", "book-b"):
            write(volume / book / "index.tex", rf"\input{{chapter/notes/topic/bad}}" + "\n")
            write(
                volume / book / "chapter" / "notes" / "topic" / "bad.tex",
                "\n".join(
                    [
                        r"\begin{definition}[Bad]",
                        rf"\label{{def:{book}-bad}}",
                        "A bad scoped definition.",
                        r"\end{definition}",
                        "",
                    ]
                ),
            )
        report = TMP / "book-a-report.json"
        preprocess_dir = TMP / "preprocessed-book-a"

        completed = subprocess.run(
            [
                sys.executable,
                str(HERE / "validate_volume.py"),
                str(repo),
                "--book",
                "book-a",
                "--json",
                str(report),
                "--preprocess-dir",
                str(preprocess_dir),
            ],
            cwd=HERE,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        data = json.loads(report.read_text(encoding="utf-8"))
        manifest = json.loads((preprocess_dir / "manifest.json").read_text(encoding="utf-8"))
        paths = {record["path"] for record in data["records"]}
        self.assertTrue(paths)
        self.assertEqual(manifest["file_count"], 2)
        self.assertTrue(all(path.startswith("book-a/") for path in paths), paths)
        self.assertFalse(any(path.startswith("book-b/") for path in paths), paths)


if __name__ == "__main__":
    unittest.main()
