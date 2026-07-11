#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

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
    ("reference_voice", reference_voice),
    ("labels", labels),
    ("operator_metadata", operator_metadata),
    ("capstones", capstones),
    ("latex_integrity", latex_integrity),
    ("unicode_tex", unicode_tex),
    ("pdf_string_headings", pdf_string_headings),
    ("caption_hygiene", caption_hygiene),
    ("figure_fragments", figure_fragments),
    ("dependency_blocks", dependency_blocks),
    ("dependency_graphs", dependency_graphs),
]


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


def _filter_findings_for_chapter(findings, chapter_rel: str | None):
    if not chapter_rel:
        return findings
    prefix = f"{chapter_rel}/"
    return [finding for finding in findings if finding.path == chapter_rel or finding.path.startswith(prefix)]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run all LRA governance validators over one volume.")
    parser.add_argument("volume", help="Volume repo root or volume-* source directory.")
    parser.add_argument(
        "--chapter",
        help="Filter the printed/JSON report to one chapter. The full volume is still validated and remains the failure gate.",
    )
    parser.add_argument("--json", help="Write machine-readable report.")
    parser.add_argument("--fail-on-errors", action="store_true")
    args = parser.parse_args(argv)

    try:
        volume = resolve_volume(args.volume)
    except (FileNotFoundError, ValueError) as exc:
        print(f"fatal: {exc}", file=sys.stderr)
        return 1

    try:
        chapter_filter = _resolve_chapter_filter(volume.root, args.chapter)
    except ValueError as exc:
        print(f"fatal: {exc}", file=sys.stderr)
        return 1

    inventory = default_file_inventory(volume.root)
    all_findings = []
    for _name, validator in VALIDATORS:
        all_findings.extend(run_validator(validator, volume.root, inventory))

    report_findings = _filter_findings_for_chapter(all_findings, chapter_filter)
    report_title = f"validate volume: {volume.root}"
    if chapter_filter:
        report_title += f" (report filtered to chapter: {chapter_filter}; gate: full volume)"
    print_report(report_title, report_findings)
    if chapter_filter:
        errors, warnings, reviews = _counts(all_findings)
        print(f"\nfull volume gate: {len(all_findings)} issue(s) [{errors} error, {warnings} warning, {reviews} review]")
    if args.json:
        write_json_report(Path(args.json), volume.root, report_findings)
        print(f"\njson report: {args.json}")

    errors = _counts(all_findings)[0]
    if args.fail_on_errors and errors:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
