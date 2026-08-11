#!/usr/bin/env python3
"""Build and query separate SQLite FTS5 indexes for internal LRA objects."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import tempfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml


SCHEMA_VERSION = "lra.internal-object-sqlite-fts5/1.0"
DATABASE_NAMES = {
    "tex": "tex-search.sqlite",
    "lean": "lean-search.sqlite",
    "cpp": "cpp-search.sqlite",
}
WORD_RE = re.compile(r"[A-Za-z0-9]+")


def database_path(sqlite_dir: Path, family: str) -> Path:
    if family not in DATABASE_NAMES:
        raise ValueError(f"unsupported source family: {family}")
    return sqlite_dir / DATABASE_NAMES[family]


def _source_fingerprint(source_path: Path | None) -> str:
    if source_path is None or not source_path.exists():
        return ""
    digest = hashlib.sha256()
    with source_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _connect(path: Path, *, read_only: bool = False) -> sqlite3.Connection:
    if read_only:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    else:
        connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def assert_fts5(connection: sqlite3.Connection) -> None:
    try:
        connection.execute("CREATE VIRTUAL TABLE temp.fts5_probe USING fts5(value)")
        connection.execute("DROP TABLE temp.fts5_probe")
    except sqlite3.Error as exc:
        raise RuntimeError("SQLite FTS5 is not available in this Python build") from exc


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA journal_mode=DELETE;
        PRAGMA synchronous=NORMAL;

        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE objects (
            row_id INTEGER PRIMARY KEY,
            object_id TEXT NOT NULL,
            source_family TEXT NOT NULL,
            kind TEXT NOT NULL,
            name TEXT,
            repo_root TEXT,
            path TEXT NOT NULL,
            line INTEGER,
            end_line INTEGER,
            label TEXT,
            declaration TEXT,
            module TEXT,
            volume TEXT,
            book TEXT,
            chapter TEXT,
            topic TEXT,
            statement TEXT,
            signature TEXT,
            search_text TEXT,
            metadata_json TEXT NOT NULL,
            record_json TEXT NOT NULL
        );

        CREATE INDEX objects_id_idx ON objects(object_id);
        CREATE INDEX objects_kind_idx ON objects(kind);
        CREATE INDEX objects_volume_idx ON objects(volume);
        CREATE INDEX objects_path_idx ON objects(repo_root, path);

        CREATE VIRTUAL TABLE objects_fts USING fts5(
            name,
            label,
            declaration,
            signature,
            statement,
            search_text,
            path,
            tokenize = 'unicode61 remove_diacritics 2'
        );

        CREATE VIRTUAL TABLE objects_trigram USING fts5(
            search_text,
            tokenize = 'trigram'
        );
        """
    )


def _text(record: dict[str, Any], field: str) -> str:
    value = record.get(field)
    return "" if value is None else str(value)


def insert_records(
    connection: sqlite3.Connection,
    records: Iterable[dict[str, Any]],
    *,
    family: str,
) -> int:
    count = 0
    for record in records:
        if record.get("source_family") != family:
            continue
        values = (
            _text(record, "object_id"),
            family,
            _text(record, "kind"),
            _text(record, "name"),
            _text(record, "repo_root"),
            _text(record, "path"),
            int(record.get("line") or 0),
            int(record["end_line"]) if record.get("end_line") is not None else None,
            _text(record, "label"),
            _text(record, "declaration"),
            _text(record, "module"),
            _text(record, "volume"),
            _text(record, "book"),
            _text(record, "chapter"),
            _text(record, "topic"),
            _text(record, "statement"),
            _text(record, "signature"),
            _text(record, "search_text"),
            json.dumps(record.get("metadata") or {}, ensure_ascii=False),
            json.dumps(record, ensure_ascii=False),
        )
        cursor = connection.execute(
            """
            INSERT INTO objects (
                object_id, source_family, kind, name, repo_root, path, line,
                end_line, label, declaration, module, volume, book, chapter,
                topic, statement, signature, search_text, metadata_json,
                record_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )
        row_id = int(cursor.lastrowid)
        connection.execute(
            """
            INSERT INTO objects_fts (
                rowid, name, label, declaration, signature, statement,
                search_text, path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row_id,
                _text(record, "name"),
                _text(record, "label"),
                _text(record, "declaration"),
                _text(record, "signature"),
                _text(record, "statement"),
                _text(record, "search_text"),
                _text(record, "path"),
            ),
        )
        connection.execute(
            "INSERT INTO objects_trigram(rowid, search_text) VALUES (?, ?)",
            (
                row_id,
                " ".join(
                    _text(record, field)
                    for field in (
                        "name", "label", "declaration", "signature",
                        "statement", "search_text", "path",
                    )
                ),
            ),
        )
        count += 1
    return count


def build_database(
    records: Iterable[dict[str, Any]],
    *,
    family: str,
    db_path: Path,
    source_path: Path | None = None,
) -> dict[str, Any]:
    if family not in DATABASE_NAMES:
        raise ValueError(f"unsupported source family: {family}")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(
        prefix=f"{family}-objects-", suffix=".sqlite", dir=db_path.parent
    )
    os.close(handle)
    temp_path = Path(temp_name)
    try:
        with closing(_connect(temp_path)) as connection:
            assert_fts5(connection)
            create_schema(connection)
            count = insert_records(connection, records, family=family)
            metadata = {
                "schema": SCHEMA_VERSION,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "source_family": family,
                "object_count": str(count),
                "source_path": str(source_path.resolve()) if source_path else "",
                "source_sha256": _source_fingerprint(source_path),
            }
            connection.executemany(
                "INSERT INTO metadata(key, value) VALUES (?, ?)", metadata.items()
            )
            connection.execute("PRAGMA optimize")
            connection.commit()
        os.replace(temp_path, db_path)
    finally:
        temp_path.unlink(missing_ok=True)
    return {"database": str(db_path), "family": family, "objects": count}


def build_family_databases(
    records: list[dict[str, Any]],
    *,
    families: Iterable[str],
    sqlite_dir: Path,
    source_path: Path | None = None,
) -> list[dict[str, Any]]:
    return [
        build_database(
            records,
            family=family,
            db_path=database_path(sqlite_dir, family),
            source_path=source_path,
        )
        for family in families
    ]


def metadata(db_path: Path) -> dict[str, str]:
    with closing(_connect(db_path, read_only=True)) as connection:
        return {
            str(row["key"]): str(row["value"])
            for row in connection.execute("SELECT key, value FROM metadata")
        }


def fts_query(terms: Iterable[str]) -> str:
    escaped = []
    for term in terms:
        clean = "".join(WORD_RE.findall(term.casefold()))
        if clean:
            escaped.append(f'"{clean.replace(chr(34), chr(34) * 2)}"*')
    return " OR ".join(dict.fromkeys(escaped))


def trigram_query(terms: Iterable[str]) -> str:
    grams = []
    for term in terms:
        clean = "".join(WORD_RE.findall(term.casefold()))
        grams.extend(clean[index : index + 3] for index in range(max(0, len(clean) - 2)))
    return " OR ".join(f'"{gram}"' for gram in dict.fromkeys(grams))


def query_candidates(
    db_path: Path,
    terms: Iterable[str],
    *,
    source_family: str | None = None,
    kind: str | None = None,
    volume: str | None = None,
    limit: int = 300,
) -> list[dict[str, Any]]:
    term_list = list(terms)
    lexical_match = fts_query(term_list)
    fuzzy_match = trigram_query(term_list)
    if not lexical_match and not fuzzy_match:
        return []

    def statement(table: str, match: str, rank_expression: str) -> tuple[str, list[Any]]:
        clauses = [f"{table} MATCH ?"]
        params: list[Any] = [match]
        if source_family:
            clauses.append("o.source_family = ?")
            params.append(source_family)
        if kind:
            clauses.append("o.kind = ?")
            params.append(kind)
        if volume:
            clauses.append("lower(o.volume) = ?")
            params.append(volume.casefold())
        params.append(max(1, limit))
        sql = (
            f"SELECT o.row_id, o.record_json, {rank_expression} AS rank "
            f"FROM {table} JOIN objects o ON o.row_id = {table}.rowid WHERE "
            + " AND ".join(clauses)
            + " ORDER BY rank LIMIT ?"
        )
        return sql, params

    with closing(_connect(db_path, read_only=True)) as connection:
        candidates: dict[int, sqlite3.Row] = {}
        searches = []
        if lexical_match:
            searches.append(statement(
                "objects_fts", lexical_match,
                "bm25(objects_fts, 5.0, 4.0, 4.0, 3.0, 2.0, 1.5, 1.0)",
            ))
        if fuzzy_match:
            searches.append(statement("objects_trigram", fuzzy_match, "bm25(objects_trigram)"))
        for sql, params in searches:
            for row in connection.execute(sql, params):
                row_id = int(row["row_id"])
                prior = candidates.get(row_id)
                if prior is None or float(row["rank"]) < float(prior["rank"]):
                    candidates[row_id] = row
        rows = []
        for row in candidates.values():
            record = json.loads(row["record_json"])
            record["_fts_rank"] = float(row["rank"])
            rows.append(record)
        return rows


def load_payload(path: Path) -> dict[str, Any]:
    if path.suffix.lower() in {".yaml", ".yml"}:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    else:
        payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("objects"), list):
        raise ValueError(f"{path} is not an internal object index payload")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Existing internal object YAML/JSON index.")
    parser.add_argument("--sqlite-dir", type=Path, required=True, help="Directory for the separate SQLite databases.")
    parser.add_argument(
        "--family",
        action="append",
        choices=sorted(DATABASE_NAMES),
        help="Family to build. May repeat; defaults to every family present in the input.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = load_payload(args.input)
    present = {
        str(record.get("source_family"))
        for record in payload["objects"]
        if isinstance(record, dict) and record.get("source_family") in DATABASE_NAMES
    }
    families = args.family or sorted(present)
    if not families:
        raise SystemExit("input contains no TeX, Lean, or C/C++ records")
    results = build_family_databases(
        payload["objects"],
        families=families,
        sqlite_dir=args.sqlite_dir,
        source_path=args.input,
    )
    for result in results:
        print(
            f"{result['family']} SQLite index written: "
            f"objects={result['objects']} database={result['database']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
