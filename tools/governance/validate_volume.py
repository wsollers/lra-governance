#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from core.reporting import print_report, write_json_report
from core.volume import resolve_volume
from validators import block_discipline, capstones, chapter_router, dependency_blocks, dependency_graphs, formal_decoration, formal_reading_required, interpretation_blocks, labels, latex_integrity, math_boxes, notes_structure, print_edition_routing, proof_coverage, proof_file_contract, proof_layout, proof_order, proof_routing, proof_stub_state, reference_voice, structural_chrome, volume_shape


VALIDATORS = [
    ("chapter_router", chapter_router),
    ("print_edition_routing", print_edition_routing),
    ("proof_routing", proof_routing),
    ("proof_layout", proof_layout),
    ("proof_file_contract", proof_file_contract),
    ("proof_coverage", proof_coverage),
    ("proof_order", proof_order),
    ("proof_stub_state", proof_stub_state),
    ("notes_structure", notes_structure),
    ("structural_chrome", structural_chrome),
    ("block_discipline", block_discipline),
    ("math_boxes", math_boxes),
    ("interpretation_blocks", interpretation_blocks),
    ("formal_decoration", formal_decoration),
    ("formal_reading_required", formal_reading_required),
    ("reference_voice", reference_voice),
    ("labels", labels),
    ("capstones", capstones),
    ("latex_integrity", latex_integrity),
    ("dependency_blocks", dependency_blocks),
    ("dependency_graphs", dependency_graphs),
]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run all LRA governance validators over one volume.")
    parser.add_argument("volume", help="Volume repo root or volume-* source directory.")
    parser.add_argument("--json", help="Write machine-readable report.")
    parser.add_argument("--fail-on-errors", action="store_true")
    args = parser.parse_args(argv)

    try:
        volume = resolve_volume(args.volume)
    except (FileNotFoundError, ValueError) as exc:
        print(f"fatal: {exc}", file=sys.stderr)
        return 1

    all_findings = []
    shape_findings = volume_shape.validate(volume.root)
    if shape_findings:
        print_report(f"validate volume: {volume.root} [volume_shape fail-fast]", shape_findings)
        if args.json:
            write_json_report(Path(args.json), volume.root, shape_findings)
            print(f"\njson report: {args.json}")
        return 2 if args.fail_on_errors and Counter(f.severity for f in shape_findings).get("error", 0) else 0

    for _name, validator in VALIDATORS:
        all_findings.extend(validator.validate(volume.root))

    print_report(f"validate volume: {volume.root}", all_findings)
    if args.json:
        write_json_report(Path(args.json), volume.root, all_findings)
        print(f"\njson report: {args.json}")

    errors = Counter(f.severity for f in all_findings).get("error", 0)
    if args.fail_on_errors and errors:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
