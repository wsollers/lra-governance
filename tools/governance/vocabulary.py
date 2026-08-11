#!/usr/bin/env python3
"""Build and query a compact runtime index of the canonical LRA vocabulary.

The four YAML registries remain the source of truth.  This tool exposes small,
agent-friendly lookup results without placing the complete registries in model
context.  Query commands refresh a missing or stale SQLite index by default.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
import textwrap
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml


SCHEMA_VERSION = "2"


@dataclass(frozen=True)
class RegistrySpec:
    kind: str
    filename: str
    root_key: str
    id_prefix: str


REGISTRIES = {
    "predicate": RegistrySpec("predicate", "predicates.yaml", "predicates", "pred:"),
    "structure": RegistrySpec("structure", "structures.yaml", "structures", "struct:"),
    "notation": RegistrySpec("notation", "notation.yaml", "notation", "not:"),
    "relation": RegistrySpec("relation", "relations.yaml", "relations", "rel:"),
}


class VocabularyError(RuntimeError):
    pass


def governance_root(start: Path | None = None) -> Path:
    if start is not None:
        root = start.expanduser().resolve()
        if all((root / spec.filename).exists() for spec in REGISTRIES.values()):
            return root
        raise VocabularyError(f"canonical vocabulary files not found under: {root}")

    root = Path(__file__).resolve().parents[2]
    if all((root / spec.filename).exists() for spec in REGISTRIES.values()):
        return root
    raise VocabularyError(f"canonical vocabulary files not found under: {root}")


def _catalog_index_root(root: Path) -> Path | None:
    catalog_root = os.environ.get("LRA_SOURCES_ROOT")
    catalog = Path(catalog_root).expanduser() if catalog_root else root.parent / "lra-sources"
    pointer = catalog / "index.yaml"
    if not pointer.exists():
        return None
    try:
        data = yaml.safe_load(pointer.read_text(encoding="utf-8")) or {}
    except Exception:
        return None
    value = data.get("source_index_root") if isinstance(data, dict) else None
    return Path(str(value)).expanduser() if value else None


def default_index_path(root: Path) -> Path:
    explicit = os.environ.get("LRA_VOCABULARY_INDEX")
    if explicit:
        return Path(explicit).expanduser().resolve(strict=False)

    source_index_root = os.environ.get("LRA_SOURCE_INDEX_ROOT")
    index_root = Path(source_index_root).expanduser() if source_index_root else _catalog_index_root(root)
    if index_root is not None:
        return (index_root / "governance" / "canonical-vocabulary.sqlite").resolve(strict=False)

    return (root / "build" / "canonical-vocabulary.sqlite").resolve(strict=False)


def load_document(root: Path, spec: RegistrySpec) -> dict[str, Any]:
    path = root / spec.filename
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        raise VocabularyError(f"{path}: YAML parse failed: {exc}") from exc
    if not isinstance(data, dict):
        raise VocabularyError(f"{path}: root must be a mapping")
    entries = data.get(spec.root_key)
    if not isinstance(entries, list):
        raise VocabularyError(f"{path}: {spec.root_key} must be a list")
    return data


def source_hashes(root: Path) -> dict[str, str]:
    return {
        spec.filename: hashlib.sha256((root / spec.filename).read_bytes()).hexdigest()
        for spec in REGISTRIES.values()
    }


def normalize(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def _strings(value: object) -> Iterable[str]:
    if isinstance(value, str):
        if value.strip():
            yield value.strip()
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _strings(item)


def entry_aliases(entry: dict[str, Any]) -> list[tuple[str, str]]:
    aliases: list[tuple[str, str]] = []
    for field in ("id", "name", "symbol", "constructor", "template"):
        value = entry.get(field)
        if value:
            aliases.append((field, str(value)))
    for value in entry.get("surface_forms") or []:
        if value:
            aliases.append(("surface_form", str(value)))
    return list(dict.fromkeys(aliases))


def _entry_id(spec: RegistrySpec, entry: dict[str, Any], index: int) -> str:
    value = str(entry.get("id") or "").strip()
    if value:
        return value
    if spec.kind == "relation":
        edge = "-".join(
            re.sub(r"[^a-z0-9]+", "-", str(entry.get(field) or "").casefold()).strip("-")
            for field in ("kind", "from", "to")
        ).strip("-")
        return f"rel:{edge or index}"
    raise VocabularyError(f"{spec.filename} entry {index}: missing id")


def validate_documents(root: Path) -> list[str]:
    errors: list[str] = []

    for spec in REGISTRIES.values():
        try:
            data = load_document(root, spec)
        except VocabularyError as exc:
            errors.append(str(exc))
            continue
        for index, entry in enumerate(data.get(spec.root_key) or [], start=1):
            if not isinstance(entry, dict):
                errors.append(f"{spec.filename} entry {index}: must be a mapping")
                continue
            try:
                entry_id = _entry_id(spec, entry, index)
            except VocabularyError as exc:
                errors.append(str(exc))
                continue
            if spec.kind != "relation" and not entry_id.startswith(spec.id_prefix):
                errors.append(f"{entry_id}: id must start with {spec.id_prefix}")

            if spec.kind == "predicate":
                for field in ("name", "category", "arguments", "returns", "description"):
                    if field not in entry:
                        errors.append(f"{entry_id}: missing required field {field!r}")
                if entry.get("kind") != "predicate":
                    errors.append(f"{entry_id}: kind must be predicate")
                if entry.get("returns") != "truth_value":
                    errors.append(f"{entry_id}: returns must be truth_value")
            elif spec.kind == "structure":
                for field in ("name", "category", "constructor", "arguments", "description"):
                    if field not in entry:
                        errors.append(f"{entry_id}: missing required field {field!r}")
                if entry.get("kind") != "structure":
                    errors.append(f"{entry_id}: kind must be structure")
            elif spec.kind == "notation":
                for field in ("symbol", "category", "description"):
                    if field not in entry:
                        errors.append(f"{entry_id}: missing required field {field!r}")

    try:
        try:
            from validate_registry_contract import validate_registry
        except ModuleNotFoundError:
            from tools.governance.validate_registry_contract import validate_registry

        contract = validate_registry(root)
        errors.extend(contract.errors)
    except Exception as exc:
        errors.append(f"registry contract validation failed to run: {exc}")
    return list(dict.fromkeys(errors))


def duplicate_ids(root: Path) -> dict[str, list[dict[str, Any]]]:
    """Report canonical ID collisions without preventing a lossless index build."""
    locations: dict[str, list[dict[str, Any]]] = {}
    for spec in REGISTRIES.values():
        data = load_document(root, spec)
        for source_index, entry in enumerate(data.get(spec.root_key) or [], start=1):
            if not isinstance(entry, dict):
                continue
            entry_id = _entry_id(spec, entry, source_index)
            locations.setdefault(entry_id, []).append(
                {"file": spec.filename, "entry": source_index, "kind": spec.kind}
            )
    return {entry_id: items for entry_id, items in locations.items() if len(items) > 1}


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def build_index(root: Path, index_path: Path) -> dict[str, Any]:
    errors = validate_documents(root)
    if errors:
        raise VocabularyError("canonical vocabulary validation failed:\n- " + "\n- ".join(errors))

    index_path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix="vocabulary-", suffix=".sqlite", dir=index_path.parent)
    os.close(handle)
    temp_path = Path(temp_name)
    counts: dict[str, int] = {}
    testing_count = 0
    id_occurrences: dict[str, int] = {}
    collisions = duplicate_ids(root)

    try:
        with closing(_connect(temp_path)) as connection:
            connection.executescript(
                """
                PRAGMA journal_mode=DELETE;
                CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE entries (
                    entry_key TEXT PRIMARY KEY,
                    entry_id TEXT NOT NULL,
                    registry TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    name TEXT,
                    symbol TEXT,
                    category TEXT,
                    description TEXT,
                    testing INTEGER NOT NULL DEFAULT 0,
                    source_file TEXT NOT NULL,
                    source_index INTEGER NOT NULL,
                    record_json TEXT NOT NULL
                );
                CREATE TABLE aliases (
                    entry_key TEXT NOT NULL REFERENCES entries(entry_key),
                    alias_type TEXT NOT NULL,
                    alias TEXT NOT NULL,
                    normalized TEXT NOT NULL
                );
                CREATE INDEX aliases_normalized_idx ON aliases(normalized);
                CREATE INDEX entries_id_idx ON entries(entry_id);
                CREATE INDEX entries_kind_idx ON entries(kind, testing);
                CREATE VIRTUAL TABLE entries_fts USING fts5(entry_key UNINDEXED, content);
                """
            )

            for spec in REGISTRIES.values():
                data = load_document(root, spec)
                entries = data.get(spec.root_key) or []
                counts[spec.kind] = len(entries)
                for source_index, entry in enumerate(entries, start=1):
                    entry_id = _entry_id(spec, entry, source_index)
                    id_occurrences[entry_id] = id_occurrences.get(entry_id, 0) + 1
                    occurrence = id_occurrences[entry_id]
                    entry_key = entry_id if occurrence == 1 else f"{entry_id}#{occurrence}"
                    testing = int(entry.get("testing") is True)
                    testing_count += testing
                    name = str(entry.get("name") or "")
                    symbol = str(entry.get("symbol") or entry.get("constructor") or "")
                    description = str(entry.get("description") or "")
                    connection.execute(
                        """INSERT INTO entries
                           (entry_key, entry_id, registry, kind, name, symbol, category, description,
                            testing, source_file, source_index, record_json)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            entry_key,
                            entry_id,
                            spec.root_key,
                            spec.kind,
                            name,
                            symbol,
                            str(entry.get("category") or ""),
                            description,
                            testing,
                            spec.filename,
                            source_index,
                            json.dumps(entry, ensure_ascii=False, sort_keys=False),
                        ),
                    )
                    aliases = entry_aliases(entry)
                    if not aliases:
                        aliases = [("id", entry_id)]
                    for alias_type, alias in aliases:
                        connection.execute(
                            "INSERT INTO aliases(entry_key, alias_type, alias, normalized) VALUES (?, ?, ?, ?)",
                            (entry_key, alias_type, alias, normalize(alias)),
                        )
                    searchable = " ".join(dict.fromkeys(_strings(entry)))
                    connection.execute(
                        "INSERT INTO entries_fts(entry_key, content) VALUES (?, ?)",
                        (entry_key, searchable),
                    )

            metadata = {
                "schema_version": SCHEMA_VERSION,
                "governance_root": str(root),
                "source_hashes": json.dumps(source_hashes(root), sort_keys=True),
                "counts": json.dumps(counts, sort_keys=True),
                "testing_count": str(testing_count),
                "duplicate_ids": json.dumps(collisions, sort_keys=True),
            }
            connection.executemany(
                "INSERT INTO metadata(key, value) VALUES (?, ?)", metadata.items()
            )
            connection.commit()
        os.replace(temp_path, index_path)
    finally:
        temp_path.unlink(missing_ok=True)

    return {
        "index": str(index_path),
        "counts": counts,
        "entry_count": sum(counts.values()),
        "testing_count": testing_count,
        "active_count": sum(counts.values()) - testing_count,
        "duplicate_ids": collisions,
    }


def index_status(root: Path, index_path: Path) -> dict[str, Any]:
    status: dict[str, Any] = {
        "index": str(index_path),
        "exists": index_path.exists(),
        "fresh": False,
        "source_hashes": source_hashes(root),
    }
    if not index_path.exists():
        return status
    try:
        with closing(_connect(index_path)) as connection:
            metadata = dict(connection.execute("SELECT key, value FROM metadata"))
            status["schema_version"] = metadata.get("schema_version")
            status["indexed_source_hashes"] = json.loads(metadata.get("source_hashes", "{}"))
            status["counts"] = json.loads(metadata.get("counts", "{}"))
            status["testing_count"] = int(metadata.get("testing_count", "0"))
            status["duplicate_ids"] = json.loads(metadata.get("duplicate_ids", "{}"))
            status["fresh"] = (
                metadata.get("schema_version") == SCHEMA_VERSION
                and status["indexed_source_hashes"] == status["source_hashes"]
            )
    except (sqlite3.DatabaseError, ValueError, TypeError) as exc:
        status["error"] = str(exc)
    return status


def ensure_index(root: Path, index_path: Path, refresh: bool) -> dict[str, Any]:
    status = index_status(root, index_path)
    if status.get("fresh"):
        return status
    if not refresh:
        raise VocabularyError(f"vocabulary index is missing or stale: {index_path}")
    build_index(root, index_path)
    return index_status(root, index_path)


def _entry_payload(row: sqlite3.Row, *, full: bool) -> dict[str, Any]:
    source = {"file": row["source_file"], "entry": row["source_index"]}
    if full:
        payload = {
            "id": row["entry_id"],
            "source": source,
            "record": json.loads(row["record_json"]),
        }
        if row["entry_key"] != row["entry_id"]:
            payload["index_key"] = row["entry_key"]
        return payload

    description = (row["description"] or "").strip()
    if len(description) > 240:
        description = description[:237].rstrip() + "..."
    payload = {
        "id": row["entry_id"],
        "kind": row["kind"],
        "name": row["name"] or None,
        "symbol": row["symbol"] or None,
        "category": row["category"] or None,
        "description": description or None,
        "testing": bool(row["testing"]),
        "source": source,
    }
    if row["entry_key"] != row["entry_id"]:
        payload["index_key"] = row["entry_key"]
    return payload


def exact_matches(
    index_path: Path,
    query: str,
    *,
    kind: str | None,
    include_testing: bool,
    full: bool,
) -> list[dict[str, Any]]:
    clauses = ["a.normalized = ?"]
    params: list[Any] = [normalize(query)]
    if kind:
        clauses.append("e.kind = ?")
        params.append(kind)
    if not include_testing:
        clauses.append("e.testing = 0")
    sql = (
        "SELECT DISTINCT e.* FROM aliases a JOIN entries e ON e.entry_key = a.entry_key "
        "WHERE " + " AND ".join(clauses) + " ORDER BY e.kind, e.entry_id, e.entry_key"
    )
    with closing(_connect(index_path)) as connection:
        return [_entry_payload(row, full=full) for row in connection.execute(sql, params)]


def search_entries(
    index_path: Path,
    query: str,
    *,
    kind: str | None,
    include_testing: bool,
    limit: int,
) -> list[dict[str, Any]]:
    exact = exact_matches(
        index_path,
        query,
        kind=kind,
        include_testing=include_testing,
        full=False,
    )
    if exact:
        return exact[:limit]

    tokens = re.findall(r"[A-Za-z0-9]+", query.casefold())
    params: list[Any] = []
    clauses: list[str] = []
    if tokens:
        fts_query = " OR ".join(f'"{token}"*' for token in tokens)
        sql = (
            "SELECT e.*, bm25(entries_fts) AS rank FROM entries_fts "
            "JOIN entries e ON e.entry_key = entries_fts.entry_key WHERE entries_fts MATCH ?"
        )
        params.append(fts_query)
    else:
        sql = (
            "SELECT DISTINCT e.*, 0.0 AS rank FROM aliases a "
            "JOIN entries e ON e.entry_key = a.entry_key WHERE a.normalized LIKE ?"
        )
        params.append(f"%{normalize(query)}%")
    if kind:
        clauses.append("e.kind = ?")
        params.append(kind)
    if not include_testing:
        clauses.append("e.testing = 0")
    if clauses:
        sql += " AND " + " AND ".join(clauses)
    sql += " ORDER BY rank, e.kind, e.entry_id, e.entry_key LIMIT ?"
    params.append(limit)
    with closing(_connect(index_path)) as connection:
        return [_entry_payload(row, full=False) for row in connection.execute(sql, params)]


def _candidate_entry(path: Path, spec: RegistrySpec) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and spec.root_key in data:
        data = data[spec.root_key]
    if isinstance(data, list):
        if len(data) != 1:
            raise VocabularyError("candidate file must contain exactly one entry")
        data = data[0]
    if not isinstance(data, dict):
        raise VocabularyError("candidate file must contain one YAML mapping")
    return data


def _append_entry_text(original: str, spec: RegistrySpec, entry: dict[str, Any]) -> str:
    marker = f"{spec.root_key}:"
    if not re.search(rf"(?m)^{re.escape(marker)}(?:\s*\[\])?\s*$", original):
        raise VocabularyError(f"cannot locate appendable root list {marker} in {spec.filename}")
    rendered = yaml.safe_dump([entry], sort_keys=False, allow_unicode=True, width=120).rstrip()
    marker_match = re.search(rf"(?m)^{re.escape(marker)}(?:\s*\[\])?\s*$", original)
    assert marker_match is not None
    following = original[marker_match.end():]
    first_item = re.search(r"(?m)^([ \t]*)-\s", following)
    list_indent = first_item.group(1) if first_item else "  "
    indented = textwrap.indent(rendered, list_indent)
    empty_marker = re.compile(rf"(?m)^{re.escape(marker)}\s*\[\]\s*$")
    if empty_marker.search(original):
        return empty_marker.sub(marker, original).rstrip() + "\n" + indented + "\n"
    return original.rstrip() + "\n\n" + indented + "\n"


def add_entry(
    root: Path,
    index_path: Path,
    *,
    kind: str,
    candidate_path: Path,
    write: bool,
) -> dict[str, Any]:
    spec = REGISTRIES[kind]
    entry = _candidate_entry(candidate_path, spec)
    current_errors = validate_documents(root)
    if current_errors:
        raise VocabularyError("current canonical vocabulary is invalid:\n- " + "\n- ".join(current_errors))

    entry_id = _entry_id(spec, entry, 1)
    for other_spec in REGISTRIES.values():
        data = load_document(root, other_spec)
        for index, existing in enumerate(data.get(other_spec.root_key) or [], start=1):
            if _entry_id(other_spec, existing, index) == entry_id:
                raise VocabularyError(f"canonical id already exists: {entry_id}")
    target = root / spec.filename
    original_bytes = target.read_bytes()
    original = original_bytes.decode("utf-8")
    updated = _append_entry_text(original, spec, entry)
    preview = updated[len(original.rstrip()):].strip()
    if not write:
        return {"write": False, "target": str(target), "id": entry_id, "preview": preview}

    handle, temp_name = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=target.parent)
    os.close(handle)
    temp_path = Path(temp_name)
    try:
        temp_path.write_text(updated, encoding="utf-8", newline="\n")
        os.replace(temp_path, target)
        errors = validate_documents(root)
        if errors:
            target.write_bytes(original_bytes)
            raise VocabularyError("candidate rejected; canonical file restored:\n- " + "\n- ".join(errors))
        result = build_index(root, index_path)
    except Exception:
        if target.read_bytes() != original_bytes:
            target.write_bytes(original_bytes)
        raise
    finally:
        temp_path.unlink(missing_ok=True)
    return {"write": True, "target": str(target), "id": entry_id, "index_result": result}


def print_payload(payload: object, output_format: str) -> None:
    if output_format == "yaml":
        print(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True).rstrip())
    elif output_format == "text":
        if isinstance(payload, dict):
            for key, value in payload.items():
                print(f"{key}: {value}")
        else:
            print(payload)
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=False))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--governance-root", type=Path)
    parser.add_argument("--index", type=Path, help="SQLite index path")
    parser.add_argument("--no-refresh", action="store_true", help="fail instead of rebuilding a stale index")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("reindex", help="validate YAML and rebuild the SQLite index")
    sub.add_parser("status", help="report index location, counts, and freshness")
    sub.add_parser("validate", help="validate canonical YAML and index freshness")

    for command in ("exists", "get", "search"):
        item = sub.add_parser(command)
        item.add_argument("query")
        item.add_argument("--kind", choices=tuple(REGISTRIES))
        item.add_argument("--include-testing", action="store_true")
        item.add_argument("--format", choices=("json", "yaml", "text"), default="json")
        if command == "search":
            item.add_argument("--limit", type=int, default=8)

    item = sub.add_parser("add", help="validate and append one canonical entry; dry-run by default")
    item.add_argument("kind", choices=tuple(REGISTRIES))
    item.add_argument("candidate", type=Path)
    item.add_argument("--write", action="store_true")
    item.add_argument("--format", choices=("json", "yaml", "text"), default="json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        root = governance_root(args.governance_root)
        index_path = (args.index or default_index_path(root)).expanduser().resolve(strict=False)

        if args.command == "reindex":
            print_payload(build_index(root, index_path), "json")
            return 0
        if args.command == "status":
            print_payload(index_status(root, index_path), "json")
            return 0
        if args.command == "validate":
            errors = validate_documents(root)
            collisions = duplicate_ids(root) if not errors else {}
            warnings = [
                f"duplicate canonical id {entry_id!r} at "
                + ", ".join(f"{item['file']} entry {item['entry']}" for item in locations)
                for entry_id, locations in collisions.items()
            ]
            status = index_status(root, index_path)
            payload = {
                "clean": not errors and not warnings,
                "valid": not errors,
                "errors": errors,
                "warnings": warnings,
                "index": status,
            }
            print_payload(payload, "json")
            return 0 if not errors and status.get("fresh") else 1
        if args.command == "add":
            result = add_entry(
                root,
                index_path,
                kind=args.kind,
                candidate_path=args.candidate,
                write=args.write,
            )
            print_payload(result, args.format)
            return 0

        ensure_index(root, index_path, refresh=not args.no_refresh)
        if args.command == "exists":
            matches = exact_matches(
                index_path,
                args.query,
                kind=args.kind,
                include_testing=args.include_testing,
                full=False,
            )
            print_payload({"exists": bool(matches), "count": len(matches), "matches": matches}, args.format)
            return 0 if matches else 1
        if args.command == "get":
            matches = exact_matches(
                index_path,
                args.query,
                kind=args.kind,
                include_testing=args.include_testing,
                full=True,
            )
            if not matches:
                print_payload({"found": False, "query": args.query}, args.format)
                return 1
            if len(matches) > 1:
                print_payload({"found": True, "ambiguous": True, "matches": matches}, args.format)
                return 3
            print_payload(matches[0], args.format)
            return 0
        if args.command == "search":
            matches = search_entries(
                index_path,
                args.query,
                kind=args.kind,
                include_testing=args.include_testing,
                limit=max(1, args.limit),
            )
            print_payload({"query": args.query, "count": len(matches), "matches": matches}, args.format)
            return 0 if matches else 1
    except (OSError, sqlite3.DatabaseError, yaml.YAMLError, VocabularyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
