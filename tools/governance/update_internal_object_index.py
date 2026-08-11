#!/usr/bin/env python3
"""Incrementally update the internal LRA TeX/Lean object index.

This command keeps the full deterministic indexer as the source of truth while
making the common edit loop cheap: hash current TeX/Lean files, re-index files
whose bytes changed, remove records for deleted files, and merge unchanged
records from the previous index.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

try:
    from index_internal_objects import (
        build_index,
        build_match_report,
        index_lean_file,
        index_tex_file,
        lean_files,
        relpath,
        tex_files,
    )
except ModuleNotFoundError:
    from tools.governance.index_internal_objects import (
        build_index,
        build_match_report,
        index_lean_file,
        index_tex_file,
        lean_files,
        relpath,
        tex_files,
    )

try:
    from internal_object_sqlite import build_family_databases
except ModuleNotFoundError:
    from tools.governance.internal_object_sqlite import build_family_databases


STATE_SCHEMA = "lra.internal-object-index-state/1.0"
DELTA_SCHEMA = "lra.internal-object-index-delta/1.0"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolved(path: Path) -> str:
    return str(path.resolve())


def file_key(source_family: str, root: Path, path: Path) -> str:
    return "|".join([source_family, resolved(root), relpath(path, root)])


def record_file_key(record: dict[str, Any]) -> str:
    return "|".join(
        [
            str(record.get("source_family") or ""),
            resolved(Path(str(record.get("repo_root") or ""))),
            str(record.get("path") or ""),
        ]
    )


def current_file_state(tex_roots: list[Path], lean_roots: list[Path], artifact_source: str) -> dict[str, dict[str, Any]]:
    files: dict[str, dict[str, Any]] = {}
    for root in tex_roots:
        root = root.resolve()
        for path in tex_files(root, artifact_source):
            files[file_key("tex", root, path)] = {
                "source_family": "tex",
                "repo_root": str(root),
                "path": relpath(path, root),
                "sha256": file_sha256(path),
            }
    for root in lean_roots:
        root = root.resolve()
        for path in lean_files(root):
            files[file_key("lean", root, path)] = {
                "source_family": "lean",
                "repo_root": str(root),
                "path": relpath(path, root),
                "sha256": file_sha256(path),
            }
    return files


def load_yaml(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data if isinstance(data, dict) else None


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def serialize_payload(payload: dict[str, Any], fmt: str) -> str:
    if fmt == "json":
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)


def build_inputs(tex_roots: list[Path], lean_roots: list[Path]) -> dict[str, list[str]]:
    return {
        "tex_roots": [str(root.resolve()) for root in tex_roots],
        "lean_roots": [str(root.resolve()) for root in lean_roots],
    }


def object_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "objects": len(records),
        "tex": sum(1 for item in records if item.get("source_family") == "tex"),
        "lean": sum(1 for item in records if item.get("source_family") == "lean"),
    }


def records_for_file(file_info: dict[str, Any]) -> list[dict[str, Any]]:
    root = Path(str(file_info["repo_root"]))
    path = root / str(file_info["path"])
    if file_info["source_family"] == "tex":
        return [asdict(record) for record in index_tex_file(path, root)]
    if file_info["source_family"] == "lean":
        return [asdict(record) for record in index_lean_file(path, root)]
    raise ValueError(f"unsupported source family: {file_info['source_family']}")


def build_full_payload(args: argparse.Namespace, current_files: dict[str, dict[str, Any]]) -> dict[str, Any]:
    payload = build_index(
        tex_roots=args.tex_root,
        lean_roots=args.lean_root,
        artifact_source=args.tex_artifact_source,
    )
    payload["delta"] = {
        "schema_version": DELTA_SCHEMA,
        "mode": "full",
        "state_file": str(args.state),
        "files": {
            "total": len(current_files),
            "changed": len(current_files),
            "unchanged": 0,
            "deleted": 0,
        },
    }
    return payload


def build_delta_payload(
    args: argparse.Namespace,
    previous_payload: dict[str, Any],
    previous_state: dict[str, Any],
    current_files: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    previous_files = previous_state.get("files") or {}
    if not isinstance(previous_files, dict):
        previous_files = {}
    changed = sorted(
        key
        for key, info in current_files.items()
        if key not in previous_files or previous_files[key].get("sha256") != info.get("sha256")
    )
    deleted = sorted(key for key in previous_files if key not in current_files)
    changed_or_deleted = set(changed) | set(deleted)
    records = [
        item
        for item in previous_payload.get("objects", [])
        if isinstance(item, dict)
        and record_file_key(item) in current_files
        and record_file_key(item) not in changed_or_deleted
    ]
    for key in changed:
        records.extend(records_for_file(current_files[key]))
    records.sort(key=lambda item: (str(item.get("source_family")), str(item.get("path")), int(item.get("line") or 0), str(item.get("object_id"))))
    return {
        "schema_version": "lra.internal-object-index/1.0",
        "inputs": build_inputs(args.tex_root, args.lean_root),
        "counts": object_counts(records),
        "objects": records,
        "delta": {
            "schema_version": DELTA_SCHEMA,
            "mode": "delta",
            "state_file": str(args.state),
            "files": {
                "total": len(current_files),
                "changed": len(changed),
                "unchanged": len(current_files) - len(changed),
                "deleted": len(deleted),
            },
            "changed_files": changed,
            "deleted_files": deleted,
        },
    }


def write_state(path: Path, args: argparse.Namespace, current_files: dict[str, dict[str, Any]]) -> None:
    state = {
        "schema_version": STATE_SCHEMA,
        "inputs": build_inputs(args.tex_root, args.lean_root),
        "options": {
            "tex_artifact_source": args.tex_artifact_source,
        },
        "files": current_files,
    }
    write_text_atomic(path, yaml.safe_dump(state, sort_keys=False, allow_unicode=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tex-root", action="append", type=Path, default=[], help="Volume TeX repo/root to scan. May repeat.")
    parser.add_argument("--lean-root", action="append", type=Path, default=[], help="Lean repo/root to scan. May repeat.")
    parser.add_argument(
        "--tex-artifact-source",
        choices=("source", "corrected", "all"),
        default="source",
        help="When artifact directories contain both source.tex and corrected.tex, choose which to index.",
    )
    parser.add_argument("--output", type=Path, required=True, help="Index output file.")
    parser.add_argument("--state", type=Path, help="Delta state file. Defaults to <output>.state.yaml.")
    parser.add_argument("--format", choices=("yaml", "json"), default="yaml")
    parser.add_argument("--full", action="store_true", help="Force a full rebuild and refresh the delta state.")
    parser.add_argument("--include-match-report", action="store_true", help="Include Lean <-> TeX candidate matches and missing-link counts.")
    parser.add_argument("--candidate-limit", type=int, default=5)
    parser.add_argument("--sqlite-dir", type=Path, help="Directory for separate TeX and Lean SQLite indexes. Defaults to <output-dir>/sqlite.")
    parser.add_argument("--no-sqlite", action="store_true", help="Do not build SQLite indexes.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.tex_root and not args.lean_root:
        print("ERROR: pass at least one --tex-root or --lean-root", file=sys.stderr)
        return 2
    args.state = args.state or args.output.with_suffix(args.output.suffix + ".state.yaml")
    args.tex_root = [root.resolve() for root in args.tex_root]
    args.lean_root = [root.resolve() for root in args.lean_root]
    current_files = current_file_state(args.tex_root, args.lean_root, args.tex_artifact_source)
    previous_payload = load_yaml(args.output)
    previous_state = load_yaml(args.state)
    if args.full or not previous_payload or not previous_state:
        payload = build_full_payload(args, current_files)
    else:
        payload = build_delta_payload(args, previous_payload, previous_state, current_files)
    if args.include_match_report:
        payload["match_report"] = build_match_report(payload, limit=args.candidate_limit)
    write_text_atomic(args.output, serialize_payload(payload, args.format))
    write_state(args.state, args, current_files)
    if not args.no_sqlite:
        sqlite_dir = args.sqlite_dir or args.output.parent / "sqlite"
        families = []
        if args.tex_root:
            families.append("tex")
        if args.lean_root:
            families.append("lean")
        for result in build_family_databases(
            payload["objects"], families=families, sqlite_dir=sqlite_dir, source_path=args.output
        ):
            print(f"{result['family']} SQLite index written: objects={result['objects']} database={result['database']}")
    delta = payload["delta"]["files"]
    print(
        "internal object index updated: "
        f"objects={payload['counts']['objects']} tex={payload['counts']['tex']} lean={payload['counts']['lean']} "
        f"files={delta['total']} changed={delta['changed']} deleted={delta['deleted']} mode={payload['delta']['mode']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
