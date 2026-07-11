#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import tempfile
from collections import Counter
from pathlib import Path

from core.file_inventory import files_to_validate
from core.formal_blocks import clear_formal_block_cache
from core.preprocess import preprocess_tex_files
from core.reporting import print_report, write_json_report
from core.validator_runner import default_file_inventory, run_validator
from core.volume import chapter_roots, resolve_volume
from validators import block_discipline, book_toc, caption_hygiene, capstones, chapter_router, dedication_page, dependency_blocks, dependency_graphs, figure_fragments, formal_decoration, formal_reading_required, frontmatter_standard, input_resolution, interpretation_blocks, labels, latex_integrity, math_boxes, notes_structure, operator_metadata, pdf_string_headings, print_edition_routing, proof_coverage, proof_file_contract, proof_layout, proof_order, proof_routing, proof_stub_state, reference_voice, structural_chrome, structural_positions, unicode_tex, volume_shape


VALIDATORS = [
    ("volume_shape", volume_shape),
    ("chapter_router", chapter_router),
    ("input_resolution", input_resolution),
    ("book_toc", book_toc),
    ("frontmatter_standard", frontmatter_standard),
    ("dedication_page", dedication_page),
    ("print_edition_routing", print_edition_routing),
    ("proof_routing", proof_routing),
    ("proof_layout", proof_layout),
    ("proof_file_contract", proof_file_contract),
    ("proof_coverage", proof_coverage),
    ("proof_order", proof_order),
    ("proof_stub_state", proof_stub_state),
    ("notes_structure", notes_structure),
    ("structural_chrome", structural_chrome),
    ("structural_positions", structural_positions),
    ("block_discipline", block_discipline),
    ("math_boxes", math_boxes),
    ("interpretation_blocks", interpretation_blocks),
    ("formal_decoration", formal_decoration),
    ("formal_reading_required", formal_reading_required),
    ("operator_metadata", operator_metadata),
    ("reference_voice", reference_voice),
    ("labels", labels),
    ("capstones", capstones),
    ("latex_integrity", latex_integrity),
    ("unicode_tex", unicode_tex),
    ("pdf_string_headings", pdf_string_headings),
    ("caption_hygiene", caption_hygiene),
    ("figure_fragments", figure_fragments),
    ("dependency_blocks", dependency_blocks),
    ("dependency_graphs", dependency_graphs),
]


SCOPED_VALIDATOR_NAMES = {
    "input_resolution",
    "print_edition_routing",
    "proof_routing",
    "proof_file_contract",
    "proof_coverage",
    "proof_order",
    "proof_stub_state",
    "notes_structure",
    "structural_chrome",
    "structural_positions",
    "block_discipline",
    "math_boxes",
    "interpretation_blocks",
    "formal_decoration",
    "formal_reading_required",
    "operator_metadata",
    "reference_voice",
    "labels",
    "latex_integrity",
    "pdf_string_headings",
    "caption_hygiene",
    "figure_fragments",
    "dependency_blocks",
}


def _counts(findings):
    sev = Counter(f.severity for f in findings)
    return sev.get("error", 0), sev.get("warning", 0), sev.get("review", 0)


def _resolve_chapter_filter(volume_root: Path, value: str | None) -> str | None:
    if not value:
        return None
    chapters = chapter_roots(volume_root)
    matches = []
    raw = Path(value)
    for chapter in chapters:
        rel = chapter.relative_to(volume_root).as_posix()
        if value == chapter.name or value == rel or raw == chapter or raw.resolve() == chapter:
            matches.append(rel)
    if not matches:
        names = ", ".join(chapter.relative_to(volume_root).as_posix() for chapter in chapters)
        raise ValueError(f"No chapter target matches {value!r}. Available chapters: {names}")
    if len(matches) > 1:
        raise ValueError(f"Chapter target {value!r} is ambiguous: {', '.join(matches)}")
    return matches[0]


def _book_roots(volume_root: Path) -> list[Path]:
    return sorted(
        child.resolve()
        for child in volume_root.iterdir()
        if child.is_dir() and child.name.startswith("book-")
    )


def _resolve_book_scope(volume_root: Path, value: str | None) -> tuple[Path | None, str | None]:
    if not value:
        return None, None
    books = _book_roots(volume_root)
    matches = []
    raw = Path(value)
    for book in books:
        rel = book.relative_to(volume_root).as_posix()
        if value == book.name or value == rel or raw == book or raw.resolve() == book:
            matches.append(book)
    if not matches:
        names = ", ".join(book.relative_to(volume_root).as_posix() for book in books)
        raise ValueError(f"No book target matches {value!r}. Available books: {names}")
    if len(matches) > 1:
        rels = ", ".join(book.relative_to(volume_root).as_posix() for book in matches)
        raise ValueError(f"Book target {value!r} is ambiguous: {rels}")
    book = matches[0]
    return book, book.relative_to(volume_root).as_posix()


def _filter_findings_for_chapter(findings, chapter_rel: str | None):
    if not chapter_rel:
        return findings
    prefix = f"{chapter_rel}/"
    return [finding for finding in findings if finding.path == chapter_rel or finding.path.startswith(prefix)]


def _validators_for_scope(book_scope: str | None):
    if not book_scope:
        return VALIDATORS
    return [(name, validator) for name, validator in VALIDATORS if name in SCOPED_VALIDATOR_NAMES]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run all LRA governance validators over one volume.")
    parser.add_argument("volume", help="Volume repo root or volume-* source directory.")
    parser.add_argument(
        "--chapter",
        help="Filter the printed/JSON report to one chapter. The full volume is still validated and remains the failure gate.",
    )
    parser.add_argument(
        "--book",
        help="Validate one book directory with scoped validators, e.g. book-sets. This is a scoped gate, not a full-volume gate.",
    )
    parser.add_argument("--json", help="Write machine-readable report.")
    parser.add_argument("--fail-on-errors", action="store_true")
    parser.add_argument(
        "--preprocess-dir",
        type=Path,
        help="Directory for comment-stripped TeX mirrors and a preprocessing manifest. Defaults to an ephemeral temp directory.",
    )
    parser.add_argument("--no-preprocess", action="store_true", help="Disable preprocessing and text-cache warmup.")
    args = parser.parse_args(argv)

    try:
        volume = resolve_volume(args.volume)
    except (FileNotFoundError, ValueError) as exc:
        print(f"fatal: {exc}", file=sys.stderr)
        return 1

    try:
        chapter_filter = _resolve_chapter_filter(volume.root, args.chapter)
        book_root, book_scope = _resolve_book_scope(volume.root, args.book)
    except ValueError as exc:
        print(f"fatal: {exc}", file=sys.stderr)
        return 1

    if book_root:
        inventory = files_to_validate([book_root], only_reachable=False)
    else:
        inventory = default_file_inventory(volume.root)
    temp_context = None
    if not args.no_preprocess:
        clear_formal_block_cache()
        if args.preprocess_dir:
            preprocess_dir = args.preprocess_dir
        else:
            temp_context = tempfile.TemporaryDirectory(prefix="lra-validate-")
            preprocess_dir = Path(temp_context.name)
        preprocessed = preprocess_tex_files(inventory, volume.root, preprocess_dir)
        print(
            f"preprocessed {preprocessed.file_count} file(s) to {preprocessed.output_dir} "
            f"in {preprocessed.elapsed_seconds:.2f}s"
        )
    all_findings = []
    validators = _validators_for_scope(book_scope)
    for _name, validator in validators:
        all_findings.extend(run_validator(validator, volume.root, inventory))

    report_findings = _filter_findings_for_chapter(all_findings, chapter_filter)
    report_title = f"validate volume: {volume.root}"
    if book_scope:
        report_title += f" (scoped to book: {book_scope}; validators: {len(validators)}/{len(VALIDATORS)})"
    elif chapter_filter:
        report_title += f" (report filtered to chapter: {chapter_filter}; gate: full volume)"
    print_report(report_title, report_findings)
    if chapter_filter and not book_scope:
        errors, warnings, reviews = _counts(all_findings)
        print(f"\nfull volume gate: {len(all_findings)} issue(s) [{errors} error, {warnings} warning, {reviews} review]")
    if args.json:
        write_json_report(Path(args.json), volume.root, report_findings)
        print(f"\njson report: {args.json}")

    errors = _counts(all_findings)[0]
    if args.fail_on_errors and errors:
        if temp_context is not None:
            temp_context.cleanup()
        return 2
    if temp_context is not None:
        temp_context.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
