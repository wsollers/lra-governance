#!/usr/bin/env python3
"""Build and query the full-text SQLite FTS5 index for authored TeX files."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import tempfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    from index_internal_objects import infer_volume_path_metadata, relpath, tex_files
except ModuleNotFoundError:
    from tools.governance.index_internal_objects import infer_volume_path_metadata, relpath, tex_files


DATABASE_NAME = "tex-fulltext-search.sqlite"
SCHEMA_VERSION = "lra.internal-tex-fulltext-fts5/1.0"
WORD_RE = re.compile(r"[A-Za-z0-9]+")


def database_path(sqlite_dir: Path) -> Path:
    return sqlite_dir / DATABASE_NAME


def _connect(path: Path, *, read_only: bool = False) -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True) if read_only else sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def _chunks(path: Path, root: Path) -> Iterable[dict[str, str | int | None]]:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    meta = infer_volume_path_metadata(path, root)
    for start in range(0, len(lines), 80):
        end = min(len(lines), start + 80)
        text = "\n".join(lines[start:end]).strip()
        if text:
            yield {
                "repo_root": str(root.resolve()),
                "path": relpath(path, root),
                "line_start": start + 1,
                "line_end": end,
                "volume": meta["volume"],
                "book": meta["book"],
                "chapter": meta["chapter"],
                "topic": meta["topic"],
                "content": text,
            }


def build_database(tex_roots: Iterable[Path], *, sqlite_dir: Path, artifact_source: str, source_path: Path | None = None) -> dict[str, Any]:
    db_path = database_path(sqlite_dir)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix="tex-fulltext-", suffix=".sqlite", dir=db_path.parent)
    os.close(handle)
    temp_path = Path(temp_name)
    count = 0
    try:
        with closing(_connect(temp_path)) as connection:
            connection.executescript(
                """
                CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE documents (
                    row_id INTEGER PRIMARY KEY,
                    repo_root TEXT NOT NULL, path TEXT NOT NULL,
                    line_start INTEGER NOT NULL, line_end INTEGER NOT NULL,
                    volume TEXT, book TEXT, chapter TEXT, topic TEXT, content TEXT NOT NULL
                );
                CREATE INDEX documents_path_idx ON documents(repo_root, path, line_start);
                CREATE INDEX documents_volume_idx ON documents(volume);
                CREATE VIRTUAL TABLE documents_fts USING fts5(content, path, tokenize = 'unicode61 remove_diacritics 2');
                """
            )
            for root in tex_roots:
                root = root.resolve()
                for path in tex_files(root, artifact_source):
                    for record in _chunks(path, root):
                        cursor = connection.execute(
                            """INSERT INTO documents (repo_root, path, line_start, line_end, volume, book, chapter, topic, content)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            tuple(record[key] for key in ("repo_root", "path", "line_start", "line_end", "volume", "book", "chapter", "topic", "content")),
                        )
                        connection.execute("INSERT INTO documents_fts(rowid, content, path) VALUES (?, ?, ?)", (cursor.lastrowid, record["content"], record["path"]))
                        count += 1
            metadata = {
                "schema": SCHEMA_VERSION,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "chunk_count": str(count),
                "source_path": str(source_path.resolve()) if source_path else "",
            }
            connection.executemany("INSERT INTO metadata(key, value) VALUES (?, ?)", metadata.items())
            connection.execute("PRAGMA optimize")
            connection.commit()
        os.replace(temp_path, db_path)
    finally:
        temp_path.unlink(missing_ok=True)
    return {"database": str(db_path), "chunks": count}


def _fts_query(query: str) -> str:
    terms = [match.group(0).casefold() for match in WORD_RE.finditer(query)]
    return " AND ".join(f'"{term.replace(chr(34), chr(34) * 2)}"' for term in dict.fromkeys(terms[:12]))


def search_database(db_path: Path, query: str, *, limit: int = 10, volume: str | None = None) -> list[dict[str, Any]]:
    match = _fts_query(query)
    if not match:
        return []
    filters = ["documents_fts MATCH ?"]
    params: list[Any] = [match]
    if volume:
        filters.append("lower(d.volume) = ?")
        params.append(volume.casefold())
    params.append(max(1, limit))
    sql = """
        SELECT d.repo_root, d.path, d.line_start, d.line_end, d.volume, d.book, d.chapter, d.topic,
               snippet(documents_fts, 0, '', '', ' ... ', 36) AS snippet,
               bm25(documents_fts, 5.0, 1.0) AS rank
        FROM documents_fts JOIN documents d ON d.row_id = documents_fts.rowid
        WHERE """ + " AND ".join(filters) + " ORDER BY rank LIMIT ?"
    with closing(_connect(db_path, read_only=True)) as connection:
        return [dict(row) for row in connection.execute(sql, params)]


def metadata(db_path: Path) -> dict[str, str]:
    with closing(_connect(db_path, read_only=True)) as connection:
        return {str(row["key"]): str(row["value"]) for row in connection.execute("SELECT key, value FROM metadata")}
