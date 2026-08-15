from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "constitution" / "schema" / "concept-discovery-receipt.schema.json"
FORMAL_LABELS = (
    "Definition",
    "Theorem",
    "Lemma",
    "Proposition",
    "Corollary",
    "Exercise",
    "Example",
    "Counterexample",
)
BAD_CONTEXT = {
    "proof_or_citation_context": re.compile(r"\b(proof|citation|bibliograph|reference)\b", re.IGNORECASE),
    "running_header": re.compile(r"\b(running header|chapter header|page header)\b", re.IGNORECASE),
    "alternate_meaning": re.compile(r"\b(not the sequence concept|alternate meaning|not mathematical sequence)\b", re.IGNORECASE),
}


@dataclass(frozen=True)
class TextLine:
    index: int
    page: str | int
    section: str | None
    text: str
    locator: str


def load_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a mapping")
    return data


def phrase_regex(phrase: str) -> str:
    parts = [re.escape(part) for part in phrase.split()]
    return r"(?i)\b" + r"\s+".join(parts) + r"\b"


def line_objects(record: dict[str, Any]) -> list[TextLine]:
    return [
        TextLine(
            index=int(item["index"]),
            page=item.get("page", "?"),
            section=item.get("section"),
            text=str(item["text"]),
            locator=str(item.get("locator") or f"line:{item['index']}"),
        )
        for item in record.get("lines", [])
    ]


def window_text(lines: list[TextLine], start: int, width: int = 2) -> str:
    return " ".join(line.text for line in lines[start : start + width])


def formal_label_line(lines: list[TextLine], match_index: int) -> TextLine | None:
    label_pattern = re.compile(r"\b(" + "|".join(FORMAL_LABELS) + r")\b", re.IGNORECASE)
    for line in lines:
        if abs(line.index - match_index) <= 2 and label_pattern.search(line.text):
            return line
    return None


def rejection_reason(lines: list[TextLine], start: int, text: str, *, has_label: bool) -> str | None:
    context = " ".join(line.text for line in lines[max(0, start - 2) : start + 3]) + " " + text
    for reason, pattern in BAD_CONTEXT.items():
        if pattern.search(context):
            return reason
    if not has_label:
        return "no_formal_label_proximity"
    return None


def discover_source_hits(record: dict[str, Any], *, phrase: str, candidate_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    lines = line_objects(record)
    pattern = re.compile(phrase_regex(phrase), re.IGNORECASE)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    fallbacks: list[dict[str, Any]] = []
    extraction_quality = record.get("extraction_quality", "indexed_text")
    if extraction_quality in {"empty_extraction", "damaged_extraction", "ambiguous_extraction"}:
        fallbacks.append({
            "source_id": record["source_id"],
            "reason": extraction_quality,
            "result": "unresolved",
        })
        if not record.get("direct_pdf_lines"):
            return accepted, rejected, fallbacks
        lines = [
            TextLine(
                index=int(item["index"]),
                page=item.get("page", "?"),
                section=item.get("section"),
                text=str(item["text"]),
                locator=str(item.get("locator") or f"pdf-line:{item['index']}"),
            )
            for item in record["direct_pdf_lines"]
        ]
        extraction_quality = "direct_pdf"

    seen_locations: set[str] = set()
    for offset in range(len(lines)):
        text = window_text(lines, offset)
        if not pattern.search(text):
            continue
        first = lines[offset]
        label = formal_label_line(lines, first.index)
        reason = rejection_reason(lines, offset, text, has_label=label is not None)
        locator = first.locator
        if reason:
            rejected.append({
                "source_id": record["source_id"],
                "locator": locator,
                "reason": reason,
                "matched_text": text,
            })
            continue
        if locator in seen_locations:
            continue
        seen_locations.add(locator)
        kind_match = re.search(r"\b(" + "|".join(FORMAL_LABELS) + r")\b", label.text if label else "", re.IGNORECASE)
        accepted.append({
            "source_id": record["source_id"],
            "independent_source_key": record.get("independent_source_key", record["source_id"]),
            "kind": kind_match.group(1).title() if kind_match else "Statement",
            "label": (label.text.strip() if label else "formal statement"),
            "physical_page": first.page,
            "section": first.section,
            "index_line": first.index,
            "locator": locator,
            "inspection_surface": "direct_pdf" if extraction_quality == "direct_pdf" else "indexed_text",
            "extraction_quality": "direct_pdf" if extraction_quality == "direct_pdf" else record.get("extraction_quality", "indexed_text"),
            "matched_text": text,
            "supported_candidate_id": candidate_id,
        })
    if fallbacks and accepted:
        fallbacks[-1]["result"] = "accepted_hit"
    return accepted, rejected, fallbacks


def build_receipt(config: dict[str, Any]) -> dict[str, Any]:
    concept = config["concept"]
    phrase = config["query"]["exact_phrase"]
    candidate_id = config["query"]["supported_candidate_id"]
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    fallbacks: list[dict[str, Any]] = []
    for source in config["primary_sources"]:
        hits, false_hits, source_fallbacks = discover_source_hits(source, phrase=phrase, candidate_id=candidate_id)
        accepted.extend(hits)
        rejected.extend(false_hits)
        fallbacks.extend(source_fallbacks)

    accepted = sorted(accepted, key=lambda item: (item["source_id"], item["index_line"], item["locator"]))
    rejected = sorted(rejected, key=lambda item: (item["source_id"], item["locator"], item["reason"]))
    fallbacks = sorted(fallbacks, key=lambda item: item["source_id"])
    independent = {item["independent_source_key"] for item in accepted}
    exception = config.get("reviewed_exception")
    return {
        "schema_version": "lra.source-grounded-concept-discovery-receipt/0.1",
        "receipt_id": config["receipt_id"],
        "concept": concept,
        "query": {
            "exact_phrase": phrase,
            "case_insensitive": True,
            "whitespace_tolerant_regex": phrase_regex(phrase),
            "formal_labels": list(FORMAL_LABELS),
        },
        "primary_source_lane": {
            "profile_or_source_list": config["profile_or_source_list"],
            "profile_revision": config["profile_revision"],
            "minimum_independent_close_sources": 5,
            "minimum_satisfied": len(independent) >= 5 or exception is not None,
            "reviewed_exception": exception,
            "sources_searched": sorted(source["source_id"] for source in config["primary_sources"]),
            "accepted_hits": accepted,
            "rejected_false_positives": rejected,
            "direct_pdf_fallbacks": fallbacks,
        },
        "mathlib_lane": {
            "searched": bool(config.get("mathlib_hits")),
            "pinned_version_or_commit": config.get("mathlib_commit"),
            "hits": sorted(config.get("mathlib_hits", []), key=lambda item: (item["module"], item["declaration"])),
        },
        "internal_lra_lane": {
            "searched": False,
            "role": "not_discovery_evidence",
        },
        "unresolved_ambiguity": list(config.get("unresolved_ambiguity", [])),
    }


def validate_receipt(receipt: dict[str, Any]) -> list[str]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    return [
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(receipt), key=lambda item: list(item.absolute_path))
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a source-grounded concept candidate discovery receipt.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    receipt = build_receipt(load_mapping(args.config))
    errors = validate_receipt(receipt)
    if errors:
        print("concept candidate discovery: FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    text = json.dumps(receipt, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
