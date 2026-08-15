from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "constitution" / "schema" / "concept-authoring-package.schema.json"
SUCCESSOR_VERSION = "lra.source-grounded-concept-package/0.2"
LEGACY_VERSION = "lra.lean-concept-package/0.1"

TRANSITIONS = {
    "none": {"discovered"},
    "discovered": {"normalized"},
    "normalized": {"proposed"},
    "proposed": {"approved", "deferred", "rejected", "reassigned"},
    "approved": {"proposed", "generated"},
    "deferred": {"proposed", "reassigned"},
    "rejected": {"proposed", "reassigned"},
    "reassigned": set(),
    "generated": {"lean_validated"},
    "lean_validated": {"publication_approved"},
    "publication_approved": set(),
}
ACTION_STATE = {
    "discovered": "discovered",
    "normalized": "normalized",
    "proposed": "proposed",
    "approved": "approved",
    "approve_with_edit": "approved",
    "deferred": "deferred",
    "rejected": "rejected",
    "reassigned": "reassigned",
    "moved_to_related_concept": "reassigned",
    "generated": "generated",
    "lean_validated": "lean_validated",
    "publication_approved": "publication_approved",
}


class ValidationError(ValueError):
    pass


def load_package(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ValidationError(f"cannot read package: {error}") from error
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as error:
            raise ValidationError(f"cannot parse package as JSON or YAML: {error}") from error
        if not isinstance(data, dict):
            raise ValidationError("package must be an object")
        return data


def _schema_validate(package: dict[str, Any]) -> list[str]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    return [
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(package), key=lambda item: list(item.absolute_path))
    ]


def _require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def _require_sorted(records: list[dict[str, Any]], key: str, errors: list[str], label: str) -> None:
    ids = [item[key] for item in records]
    _require(ids == sorted(ids), errors, f"{label} must be sorted by {key} for deterministic serialization")


def _approved_value(record: dict[str, Any]) -> bool:
    return record.get("state") in {"approved", "not_applicable"}


def semantic_errors(package: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    version = package.get("schema_version")
    if version == LEGACY_VERSION:
        return [f"{LEGACY_VERSION} is inspectable but non-materializable; migrate to {SUCCESSOR_VERSION} without inferring approval"]
    if version != SUCCESSOR_VERSION:
        return [f"unsupported schema_version: {version!r}"]

    contracts = package.get("concept_contracts", [])
    evidence = package.get("evidence", [])
    candidates = package.get("candidates", [])
    events = package.get("review_events", [])

    _require_sorted(contracts, "concept_id", errors, "concept_contracts")
    _require_sorted(evidence, "evidence_id", errors, "evidence")
    _require_sorted(candidates, "candidate_id", errors, "candidates")
    event_order = [(event["timestamp"], event["event_id"]) for event in events]
    _require(event_order == sorted(event_order), errors, "review_events must be sorted by timestamp then event_id")

    concept_ids: set[str] = set()
    contract_revisions: dict[str, str] = {}
    contract_statuses: dict[str, str] = {}
    for contract in contracts:
        concept_id = contract["concept_id"]
        _require(concept_id not in concept_ids, errors, f"duplicate concept_id: {concept_id}")
        concept_ids.add(concept_id)
        contract_revisions[concept_id] = contract["contract_revision"]
        contract_statuses[concept_id] = contract["contract_status"]
        if contract["contract_status"] == "approved":
            for key, value in contract.items():
                if key in {"concept_id", "target", "contract_revision", "contract_status", "reviewer_attribution"}:
                    continue
                _require(_approved_value(value), errors, f"approved contract {concept_id} has unresolved field {key}")
            for key, value in contract["target"].items():
                _require(_approved_value(value), errors, f"approved contract {concept_id} has unresolved target.{key}")

    evidence_ids: set[str] = set()
    supported_candidate_refs: set[str] = set()
    for item in evidence:
        evidence_id = item["evidence_id"]
        _require(evidence_id not in evidence_ids, errors, f"duplicate evidence_id: {evidence_id}")
        evidence_ids.add(evidence_id)
        supported_candidate_refs.update(item["supports_candidate_ids"])
        if item.get("supersedes") is not None:
            _require(item["supersedes"] in evidence_ids, errors, f"evidence {evidence_id} supersedes unknown or later evidence {item['supersedes']}")
        if item["lane"] == "primary_source":
            for field in ("source_id", "source_profile", "source_snapshot", "locator"):
                _require(item.get(field) is not None, errors, f"primary-source evidence {evidence_id} missing {field}")
        if item["lane"] == "external_mathlib":
            for field in ("mathlib_commit", "mathlib_module", "mathlib_declaration", "exact_signature"):
                _require(item.get(field) is not None, errors, f"Mathlib evidence {evidence_id} missing {field}")

    candidate_ids: set[str] = set()
    candidate_concepts: dict[str, str] = {}
    revision_to_candidate: dict[str, str] = {}
    current_revision: dict[str, str] = {}
    revision_meaning_change: dict[str, bool] = {}
    for candidate in candidates:
        candidate_id = candidate["candidate_id"]
        _require(candidate_id not in candidate_ids, errors, f"duplicate candidate_id: {candidate_id}")
        candidate_ids.add(candidate_id)
        candidate_concepts[candidate_id] = candidate["concept_id"]
        _require(candidate["concept_id"] in concept_ids, errors, f"candidate {candidate_id} references unknown concept {candidate['concept_id']}")
        _require(
            contract_revisions.get(candidate["concept_id"]) == candidate["contract_revision"],
            errors,
            f"candidate {candidate_id} references stale or unknown contract revision {candidate['contract_revision']}",
        )
        _require(candidate_id in supported_candidate_refs, errors, f"candidate {candidate_id} has no supporting evidence record")
        _require_sorted(candidate["revisions"], "revision_id", errors, f"candidate {candidate_id} revisions")
        revision_ids = {revision["revision_id"] for revision in candidate["revisions"]}
        _require(candidate["current_revision_id"] in revision_ids, errors, f"candidate {candidate_id} current_revision_id is not present")
        current_revision[candidate_id] = candidate["current_revision_id"]
        for revision in candidate["revisions"]:
            revision_id = revision["revision_id"]
            _require(revision_id not in revision_to_candidate, errors, f"duplicate revision_id: {revision_id}")
            revision_to_candidate[revision_id] = candidate_id
            revision_meaning_change[revision_id] = revision["meaning_change_from_previous"]
            for evidence_ref in revision["evidence_refs"]:
                _require(evidence_ref in evidence_ids, errors, f"revision {revision_id} references unknown evidence {evidence_ref}")
            if revision["recommendation"] == "approve":
                _require(not revision["unresolved_fields"], errors, f"revision {revision_id} recommended for approval has unresolved fields")

    event_ids: set[str] = set()
    approvals: dict[str, set[str]] = {}
    latest_state: dict[str, str] = {}
    for event in events:
        event_id = event["event_id"]
        candidate_id = event["candidate_id"]
        revision_id = event["affected_revision_id"]
        _require(event_id not in event_ids, errors, f"duplicate event_id: {event_id}")
        event_ids.add(event_id)
        _require(candidate_id in candidate_ids, errors, f"review event {event_id} references unknown candidate {candidate_id}")
        _require(revision_to_candidate.get(revision_id) == candidate_id, errors, f"review event {event_id} references revision outside candidate")
        expected_state = ACTION_STATE[event["action"]]
        _require(event["resulting_state"] == expected_state, errors, f"review event {event_id} action/resulting_state mismatch")
        previous = event["previous_state"]
        _require(event["resulting_state"] in TRANSITIONS.get(previous, set()), errors, f"invalid transition in {event_id}: {previous} -> {event['resulting_state']}")
        if candidate_id in latest_state:
            _require(previous == latest_state[candidate_id], errors, f"review event {event_id} previous_state does not match candidate history")
        latest_state[candidate_id] = event["resulting_state"]
        if event["action"] == "approve_with_edit":
            _require(event.get("edited_revision_id") == revision_id, errors, f"approve_with_edit {event_id} must name edited_revision_id")
        if event["action"] in {"reassigned", "moved_to_related_concept"}:
            _require(event.get("destination_concept_id") in concept_ids, errors, f"reassignment {event_id} must name a known destination concept")
        if event["resulting_state"] == "approved":
            approvals.setdefault(candidate_id, set()).add(revision_id)

    for candidate_id, revision_id in current_revision.items():
        if revision_id not in approvals.get(candidate_id, set()) and latest_state.get(candidate_id) == "approved":
            errors.append(f"candidate {candidate_id} is approved without approval of current revision {revision_id}")
        if latest_state.get(candidate_id) == "approved":
            stale_revisions = [
                revision["revision_id"]
                for candidate in candidates if candidate["candidate_id"] == candidate_id
                for revision in candidate["revisions"]
                if revision["revision_id"] > max(approvals.get(candidate_id, {''})) and revision["meaning_change_from_previous"]
            ]
            _require(not stale_revisions, errors, f"candidate {candidate_id} has stale approval after meaning-changing revisions")

    generation = package.get("generation_package")
    if generation is not None:
        approved_pairs = generation["approved_candidate_revisions"]
        _require(
            approved_pairs == sorted(approved_pairs, key=lambda item: (item["candidate_id"], item["revision_id"])),
            errors,
            "generation_package.approved_candidate_revisions must be sorted by candidate_id, revision_id",
        )
        for pair in approved_pairs:
            candidate_id = pair["candidate_id"]
            revision_id = pair["revision_id"]
            concept_id = candidate_concepts.get(candidate_id)
            _require(contract_statuses.get(concept_id) == "approved", errors, f"generation uses candidate with unapproved concept contract: {candidate_id}")
            _require(current_revision.get(candidate_id) == revision_id, errors, f"generation uses stale revision {candidate_id}/{revision_id}")
            _require(revision_id in approvals.get(candidate_id, set()), errors, f"generation uses unapproved revision {candidate_id}/{revision_id}")
            _require(latest_state.get(candidate_id) in {"approved", "generated", "lean_validated", "publication_approved"}, errors, f"generation uses candidate {candidate_id} in state {latest_state.get(candidate_id)!r}")
    for receipt in package.get("generation_receipts", []):
        artifacts = receipt["emitted_artifacts"]
        _require(artifacts == sorted(artifacts, key=lambda item: item["path"]), errors, f"receipt {receipt['receipt_id']} artifacts must be path-sorted")

    return errors


def validate(path: Path) -> list[str]:
    package = load_package(path)
    if package.get("schema_version") == LEGACY_VERSION:
        return semantic_errors(package)
    errors = _schema_validate(package)
    if not errors:
        errors.extend(semantic_errors(package))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a source-grounded concept authoring package.")
    parser.add_argument("package", type=Path)
    args = parser.parse_args(argv)
    errors = validate(args.package)
    if errors:
        print("concept-authoring package: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("concept-authoring package: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
