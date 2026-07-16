#!/usr/bin/env python3
"""Validate one routed semantic label, with optional supplied LLM payload data."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import yaml

from semantic_artifact_inventory import VOLUME_NAMES, artifact_package_for, routed_formals
from validate_semantic_scope import label_slug, scope_payload


SCHEMA = "lra.semantic-label-validation/1.0"


def candidate_args(args: argparse.Namespace, volume: str) -> SimpleNamespace:
    return SimpleNamespace(
        repos_root=args.repos_root,
        volume_root=None,
        volume=volume,
        book=None,
        chapter=None,
        section=None,
        label=args.label,
        target=None,
    )


def resolve_label(args: argparse.Namespace) -> tuple[str, Path, Any]:
    volumes = [args.volume] if args.volume else list(VOLUME_NAMES)
    matches: list[tuple[str, Path, Any]] = []
    for volume in volumes:
        try:
            repo_root, _volume_source, _roots, candidates = routed_formals(candidate_args(args, volume))
        except (FileNotFoundError, ValueError):
            continue
        for candidate in candidates:
            if candidate.label == args.label:
                matches.append((volume, repo_root, candidate))
    if not matches:
        volume_hint = f" in volume {args.volume}" if args.volume else ""
        raise ValueError(f"label {args.label!r} was not found in routed source{volume_hint}")
    unique_locations = {
        (volume, candidate.source_file.relative_to(repo_root).as_posix(), candidate.line_start)
        for volume, repo_root, candidate in matches
    }
    if len(unique_locations) > 1:
        rendered = ", ".join(f"{volume}:{path}:{line}" for volume, path, line in sorted(unique_locations))
        raise ValueError(f"label {args.label!r} is ambiguous; specify --volume/--target: {rendered}")
    return matches[0]


def scope_args(args: argparse.Namespace, volume: str, repo_root: Path, candidate: Any, package: dict[str, Any]) -> SimpleNamespace:
    llm_data_dir = args.llm_data_dir
    if llm_data_dir is None:
        llm_data_dir = repo_root / Path(package["directory"]).parent / ".llm-payloads"
    return SimpleNamespace(
        mode="python-llm" if args.with_llm else "python",
        repos_root=args.repos_root,
        volume_root=None,
        volume=volume,
        book=candidate.book_root.stem,
        chapter=candidate.chapter,
        section=candidate.section,
        label=args.label,
        target=None,
        llm_data_dir=llm_data_dir,
        llm_data=args.llm_data,
        require_llm_for_existing=args.require_llm_for_existing,
        no_materialize_llm=args.no_materialize_llm,
        overwrite_materialized=args.overwrite_materialized,
        no_create_missing=args.no_create_missing,
        create_mode=args.create_mode,
        create_dry_run=args.create_dry_run,
        overwrite_generated=args.overwrite_generated,
        create_limit=None,
        allow_pending=args.allow_pending,
    )


def add_label_context(payload: dict[str, Any], args: argparse.Namespace, volume: str, repo_root: Path, candidate: Any) -> dict[str, Any]:
    package = artifact_package_for(candidate, repo_root)
    package_dir = repo_root / package["directory"]
    default_llm_dir = package_dir.parent / ".llm-payloads"
    preferred_llm_payload = (args.llm_data_dir or default_llm_dir) / f"{label_slug(args.label)}.json"
    payload["schema_version"] = SCHEMA
    payload["label_resolution"] = {
        "volume": volume,
        "repo_root": str(repo_root),
        "book": candidate.book_root.stem,
        "chapter": candidate.chapter,
        "section": candidate.section,
        "source_file": candidate.source_file.relative_to(repo_root).as_posix(),
        "source_line_start": candidate.line_start,
        "source_line_end": candidate.line_end,
        "suggested_package": package,
    }
    payload["llm_payload_convention"] = {
        "preferred_path": preferred_llm_payload.as_posix(),
        "package_local_paths": [
            (package_dir / "llm-data.json").relative_to(repo_root).as_posix(),
            (package_dir / "llm-data.yaml").relative_to(repo_root).as_posix(),
            (package_dir / "reviewer-output.json").relative_to(repo_root).as_posix(),
            (package_dir / "reviewer-output.yaml").relative_to(repo_root).as_posix(),
        ],
        "required_payload_fields": ["artifact or artifact_yaml", "corrected_tex"],
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate one routed semantic label with optional LLM payloads.")
    parser.add_argument("label", help="Formal label, e.g. def:supremum.")
    parser.add_argument("--repos-root", type=Path, default=Path(".."))
    parser.add_argument("--volume", choices=tuple(VOLUME_NAMES), help="Optional volume hint; required only when label is ambiguous.")
    parser.add_argument("--with-llm", action="store_true", help="Use python-llm scope mode and supplied payload convention.")
    parser.add_argument("--llm-data-dir", type=Path)
    parser.add_argument("--llm-data", type=Path, action="append")
    parser.add_argument("--require-llm-for-existing", action="store_true")
    parser.add_argument("--no-materialize-llm", action="store_true")
    parser.add_argument("--overwrite-materialized", action="store_true")
    parser.add_argument("--no-create-missing", action="store_true")
    parser.add_argument("--create-mode", choices=("prompt", "packet"), default="prompt")
    parser.add_argument("--create-dry-run", action="store_true")
    parser.add_argument("--overwrite-generated", action="store_true")
    parser.add_argument("--allow-pending", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=("yaml", "json"), default="yaml")
    args = parser.parse_args()

    try:
        volume, repo_root, candidate = resolve_label(args)
        package = artifact_package_for(candidate, repo_root)
        payload, return_code = scope_payload(scope_args(args, volume, repo_root, candidate, package))
        payload = add_label_context(payload, args, volume, repo_root, candidate)
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
