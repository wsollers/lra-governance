#!/usr/bin/env python3
"""Orchestrate semantic validation for a routed volume scope.

Modes:
- python: create missing request artifacts and validate existing packages.
- python-llm: additionally consume supplied LLM/reviewer payloads for missing
  packages, optionally materializing passing payloads into package files.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from create_semantic_validation_artifacts import build_generation_request, create_requests
from semantic_artifact_inventory import VOLUME_NAMES, artifact_package_for, routed_formals
from validate_semantic_logic import extract_llm_artifact_and_tex, load_mapping, load_serialized_mapping, validate


SCHEMA = "lra.semantic-scope-validation/1.0"
PASS_RESULTS = {"pass", "pass_with_warnings"}


def label_slug(label: str) -> str:
    return label.replace(":", "-")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def payload_identity_label(payload_path: Path) -> str | None:
    try:
        payload = load_serialized_mapping(payload_path)
        artifact, _corrected_tex = extract_llm_artifact_and_tex(payload)
    except Exception:
        return None
    identity = artifact.get("identity")
    if isinstance(identity, dict) and isinstance(identity.get("label"), str):
        return identity["label"]
    return None


def indexed_llm_payloads(paths: list[Path] | None) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for path in paths or []:
        label = payload_identity_label(path)
        if label:
            out[label] = path
    return out


def find_llm_payload(label: str, package_dir: Path, llm_data_dir: Path | None, explicit: dict[str, Path]) -> Path | None:
    if label in explicit:
        return explicit[label]
    slug = label_slug(label)
    candidates: list[Path] = []
    if llm_data_dir is not None:
        candidates.extend(
            [
                llm_data_dir / f"{slug}.json",
                llm_data_dir / f"{slug}.yaml",
                llm_data_dir / f"{slug}.yml",
            ]
        )
    candidates.extend(
        [
            package_dir / "llm-data.json",
            package_dir / "llm-data.yaml",
            package_dir / "reviewer-output.json",
            package_dir / "reviewer-output.yaml",
        ]
    )
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def validate_existing_package(repo_root: Path, candidate: Any, package: dict[str, Any]) -> dict[str, Any]:
    artifact = repo_root / package["artifact"]
    corrected = repo_root / package["corrected_tex"]
    result = validate(load_mapping(artifact), corrected.read_text(encoding="utf-8")).as_json()
    return {
        "label": candidate.label,
        "status": "validated_package",
        "candidate": candidate.as_json(repo_root),
        "artifact": artifact.relative_to(repo_root).as_posix(),
        "corrected_tex": corrected.relative_to(repo_root).as_posix(),
        "result": result,
    }


def validate_llm_payload(
    repo_root: Path,
    candidate: Any,
    package: dict[str, Any],
    payload_path: Path,
    *,
    materialize: bool,
    overwrite: bool,
) -> dict[str, Any]:
    payload = load_serialized_mapping(payload_path)
    artifact_data, corrected_tex = extract_llm_artifact_and_tex(payload)
    corrected_source = "llm_payload"
    if corrected_tex is None:
        corrected_tex = candidate.text
        corrected_source = "routed_source"
    result = validate(artifact_data, corrected_tex).as_json()
    item: dict[str, Any] = {
        "label": candidate.label,
        "status": "validated_llm_payload",
        "candidate": candidate.as_json(repo_root),
        "llm_data": payload_path.relative_to(repo_root).as_posix() if payload_path.is_relative_to(repo_root) else str(payload_path),
        "corrected_tex_source": corrected_source,
        "suggested_package": package,
        "result": result,
        "materialized": False,
    }
    if result["result"] in PASS_RESULTS and materialize and corrected_source == "llm_payload":
        artifact_path = repo_root / package["artifact"]
        corrected_path = repo_root / package["corrected_tex"]
        if overwrite or not artifact_path.exists():
            write_yaml(artifact_path, artifact_data)
        if overwrite or not corrected_path.exists():
            write_text(corrected_path, corrected_tex)
        item["materialized"] = artifact_path.exists() and corrected_path.exists()
        item["artifact"] = artifact_path.relative_to(repo_root).as_posix()
        item["corrected_tex"] = corrected_path.relative_to(repo_root).as_posix()
    elif result["result"] in PASS_RESULTS and materialize:
        item["materialization_blocked"] = "LLM payload did not include corrected_tex"
    return item


def scope_payload(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    if args.volume is None:
        raise ValueError("--volume is required for scoped semantic validation")
    if args.mode == "python-llm" and not args.llm_data_dir and not args.llm_data:
        raise ValueError("--mode python-llm requires --llm-data-dir or --llm-data")

    repo_root, volume_source, _roots, candidates = routed_formals(args)
    explicit_payloads = indexed_llm_payloads(args.llm_data)
    items: list[dict[str, Any]] = []
    generation_queue: list[dict[str, Any]] = []
    failures = 0
    pending = 0
    llm_validated = 0
    packages_validated = 0

    for candidate in candidates:
        package = artifact_package_for(candidate, repo_root)
        package_dir = repo_root / package["directory"]
        if package["exists"]:
            item = validate_existing_package(repo_root, candidate, package)
            packages_validated += 1
            if item["result"]["result"] not in PASS_RESULTS:
                failures += 1
            if args.mode == "python-llm":
                llm_payload = find_llm_payload(candidate.label, package_dir, args.llm_data_dir, explicit_payloads)
                if llm_payload is not None:
                    llm_item = validate_llm_payload(
                        repo_root,
                        candidate,
                        package,
                        llm_payload,
                        materialize=False,
                        overwrite=False,
                    )
                    item["llm_result"] = llm_item
                    llm_validated += 1
                    if llm_item["result"]["result"] not in PASS_RESULTS:
                        failures += 1
                elif args.require_llm_for_existing:
                    item["llm_result"] = {"status": "pending_llm_data", "reason": "no LLM payload found for existing package"}
                    pending += 1
            items.append(item)
            continue

        request = build_generation_request(candidate, repo_root)
        generation_queue.append(request)
        if args.mode == "python":
            items.append(
                {
                    "label": candidate.label,
                    "status": "pending_package",
                    "candidate": candidate.as_json(repo_root),
                    "suggested_package": package,
                }
            )
            pending += 1
            continue

        llm_payload = find_llm_payload(candidate.label, package_dir, args.llm_data_dir, explicit_payloads)
        if llm_payload is None:
            items.append(
                {
                    "label": candidate.label,
                    "status": "pending_llm_data",
                    "candidate": candidate.as_json(repo_root),
                    "suggested_package": package,
                    "generation_request": (package_dir / "generation-request.json").relative_to(repo_root).as_posix(),
                }
            )
            pending += 1
            continue
        item = validate_llm_payload(
            repo_root,
            candidate,
            package,
            llm_payload,
            materialize=not args.no_materialize_llm,
            overwrite=args.overwrite_materialized,
        )
        llm_validated += 1
        if item["result"]["result"] not in PASS_RESULTS:
            failures += 1
        items.append(item)

    creation = None
    if generation_queue and not args.no_create_missing:
        creation = create_requests(
            generation_queue,
            repo_root,
            mode=args.create_mode,
            dry_run=args.create_dry_run,
            overwrite=args.overwrite_generated,
            limit=args.create_limit,
        )

    result = "fail" if failures else ("pending" if pending else "pass")
    exit_code = 1 if failures else (0 if result == "pass" or args.allow_pending else 2)
    return (
        {
            "schema_version": SCHEMA,
            "mode": args.mode,
            "repo_root": str(repo_root),
            "volume": args.volume,
            "volume_source": volume_source.relative_to(repo_root).as_posix(),
            "filters": {
                "book": args.book,
                "chapter": args.chapter,
                "section": args.section,
                "label": args.label,
                "target": args.target.as_posix() if args.target else None,
            },
            "formal_candidates": len(candidates),
            "validated_packages": packages_validated,
            "validated_llm_payloads": llm_validated,
            "pending_count": pending,
            "failure_count": failures,
            "generation_queue": generation_queue,
            "creation": creation,
            "result": result,
            "items": items,
        },
        exit_code,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a routed semantic scope, optionally with supplied LLM data.")
    parser.add_argument("--mode", choices=("python", "python-llm"), default="python")
    parser.add_argument("--repos-root", type=Path)
    parser.add_argument("--volume-root", type=Path)
    parser.add_argument("--volume", choices=tuple(VOLUME_NAMES), required=True)
    parser.add_argument("--book")
    parser.add_argument("--chapter")
    parser.add_argument("--section")
    parser.add_argument("--label")
    parser.add_argument("--target", type=Path)
    parser.add_argument("--llm-data-dir", type=Path)
    parser.add_argument("--llm-data", type=Path, action="append", help="One or more JSON/YAML LLM payloads.")
    parser.add_argument("--require-llm-for-existing", action="store_true")
    parser.add_argument("--no-materialize-llm", action="store_true")
    parser.add_argument("--overwrite-materialized", action="store_true")
    parser.add_argument("--no-create-missing", action="store_true")
    parser.add_argument("--create-mode", choices=("prompt", "packet"), default="prompt")
    parser.add_argument("--create-dry-run", action="store_true")
    parser.add_argument("--overwrite-generated", action="store_true")
    parser.add_argument("--create-limit", type=int)
    parser.add_argument("--allow-pending", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=("yaml", "json"), default="yaml")
    args = parser.parse_args()

    try:
        payload, return_code = scope_payload(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
