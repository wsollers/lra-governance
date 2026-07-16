#!/usr/bin/env python3
"""Create semantic validation generation-request artifacts for routed formals."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from semantic_artifact_inventory import VOLUME_NAMES, artifact_package_for, routed_formals


REQUEST_SCHEMA = "lra.semantic-validation-artifact-request/1.0"
SUMMARY_SCHEMA = "lra.semantic-validation-artifact-creation/1.0"


def build_generation_request(candidate: Any, repo_root: Path) -> dict[str, Any]:
    package = artifact_package_for(candidate, repo_root)
    source = candidate.as_json(repo_root, include_source_text=False)
    return {
        "schema_version": REQUEST_SCHEMA,
        "label": candidate.label,
        "kind": candidate.kind,
        "title": candidate.title,
        "source": source,
        "suggested_package": package,
        "llm_packet": {
            "task": {
                "mode": "generate_semantic_artifact",
                "requested_action": "create_artifact_package",
            },
            "source": {
                "repository_root": str(repo_root),
                "file": candidate.source_file.relative_to(repo_root).as_posix(),
                "label": candidate.label,
                "environment_kind": candidate.kind,
                "source_line_start": candidate.line_start,
                "source_line_end": candidate.line_end,
                "current_tex": candidate.text,
            },
        },
    }


def request_from_inventory_item(item: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    source_text = item.get("source_text")
    if source_text is None:
        raise ValueError(
            "inventory item does not include source_text; rerun semantic_artifact_inventory.py "
            "with --include-source-text or pass a routed scope directly"
        )
    return {
        "schema_version": REQUEST_SCHEMA,
        "label": item["label"],
        "kind": item["kind"],
        "title": item.get("title"),
        "source": {key: value for key, value in item.items() if key != "source_text"},
        "suggested_package": item["artifact_package"],
        "llm_packet": {
            "task": {
                "mode": "generate_semantic_artifact",
                "requested_action": "create_artifact_package",
            },
            "source": {
                "repository_root": str(repo_root),
                "file": item["source_file"],
                "label": item["label"],
                "environment_kind": item["kind"],
                "source_line_start": item["source_line_start"],
                "source_line_end": item["source_line_end"],
                "current_tex": source_text,
            },
        },
    }


def prompt_text(request: dict[str, Any]) -> str:
    label = request["label"]
    package = request["suggested_package"]["directory"]
    return (
        f"# Semantic Artifact Generation Request\n\n"
        f"Generate the reviewed semantic artifact package for `{label}`.\n\n"
        f"- Target package: `{package}`\n"
        f"- Use `generation-request.json` for metadata and `source.tex` for the exact routed source block.\n"
        f"- Produce the governed semantic package files, including `artifact.yaml` and `corrected.tex`.\n"
        f"- Do not edit volume source directly as part of request generation.\n"
    )


def existing_semantic_package(repo_root: Path, request: dict[str, Any]) -> bool:
    package = request["suggested_package"]
    return (repo_root / package["artifact"]).exists() and (repo_root / package["corrected_tex"]).exists()


def create_requests(
    generation_requests: list[dict[str, Any]],
    repo_root: Path,
    *,
    mode: str = "prompt",
    dry_run: bool = False,
    overwrite: bool = False,
    limit: int | None = None,
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "schema_version": SUMMARY_SCHEMA,
        "mode": mode,
        "dry_run": dry_run,
        "created": [],
        "skipped_existing_request": [],
        "already_packaged": [],
    }
    selected = generation_requests[:limit] if limit is not None else generation_requests
    for request in selected:
        package_dir = repo_root / request["suggested_package"]["directory"]
        request_path = package_dir / "generation-request.json"
        prompt_path = package_dir / "prompt.md"
        source_path = package_dir / "source.tex"
        record = {
            "label": request["label"],
            "directory": package_dir.relative_to(repo_root).as_posix(),
            "generation_request": request_path.relative_to(repo_root).as_posix(),
            "prompt": prompt_path.relative_to(repo_root).as_posix(),
            "source_tex": source_path.relative_to(repo_root).as_posix(),
        }
        if existing_semantic_package(repo_root, request):
            summary["already_packaged"].append(record)
            continue
        if request_path.exists() and not overwrite:
            summary["skipped_existing_request"].append(record)
            continue
        if not dry_run:
            package_dir.mkdir(parents=True, exist_ok=True)
            request_payload = dict(request)
            request_payload["creation_mode"] = mode
            request_path.write_text(json.dumps(request_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            source_path.write_text(request["llm_packet"]["source"]["current_tex"], encoding="utf-8")
            if mode == "prompt":
                prompt_path.write_text(prompt_text(request), encoding="utf-8")
        summary["created"].append(record)

    summary["requested_count"] = len(generation_requests)
    summary["selected_count"] = len(selected)
    summary["created_count"] = len(summary["created"])
    summary["skipped_existing_request_count"] = len(summary["skipped_existing_request"])
    summary["already_packaged_count"] = len(summary["already_packaged"])
    return summary


def load_inventory_requests(path: Path) -> tuple[Path, list[dict[str, Any]]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("inventory must be a mapping")
    repo_root = Path(data["repo_root"]).resolve()
    requests = [
        request_from_inventory_item(item, repo_root)
        for item in data.get("items", [])
        if not item.get("artifact_package", {}).get("exists")
    ]
    return repo_root, requests


def scoped_requests(args: argparse.Namespace) -> tuple[Path, list[dict[str, Any]]]:
    repo_root, _volume_source, _roots, candidates = routed_formals(args)
    requests = []
    for candidate in candidates:
        package = artifact_package_for(candidate, repo_root)
        if not package["exists"]:
            requests.append(build_generation_request(candidate, repo_root))
    return repo_root, requests


def main() -> int:
    parser = argparse.ArgumentParser(description="Create generation-request artifacts for missing semantic packages.")
    parser.add_argument("--inventory", type=Path, help="Inventory JSON/YAML produced with --include-source-text.")
    parser.add_argument("--repos-root", type=Path)
    parser.add_argument("--volume-root", type=Path)
    parser.add_argument("--volume", choices=tuple(VOLUME_NAMES))
    parser.add_argument("--book")
    parser.add_argument("--chapter")
    parser.add_argument("--section")
    parser.add_argument("--label")
    parser.add_argument("--target", type=Path)
    parser.add_argument("--mode", choices=("prompt", "packet"), default="prompt")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=("yaml", "json"), default="yaml")
    args = parser.parse_args()

    try:
        if args.inventory:
            repo_root, requests = load_inventory_requests(args.inventory)
        else:
            repo_root, requests = scoped_requests(args)
        payload = create_requests(
            requests,
            repo_root,
            mode=args.mode,
            dry_run=args.dry_run,
            overwrite=args.overwrite,
            limit=args.limit,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
