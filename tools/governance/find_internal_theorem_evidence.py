#!/usr/bin/env python3
"""Find internal evidence for a theorem/definition before using web lookup.

The tool searches local LRA evidence surfaces:

- Knowledge Explorer ``knowledge.json`` nodes;
- lra-source-profiles source indexes and registry metadata;
- active/named source-profile markdown exports;
- source PDF filenames/metadata, when no markdown cache is available.

It is intentionally an evidence finder, not a mathematical validator.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml


WORD_RE = re.compile(r"[a-z0-9]+")


@dataclass
class EvidenceHit:
    source_type: str
    source: str
    title: str | None = None
    source_id: str | None = None
    label: str | None = None
    score: int = 0
    matched_terms: list[str] = field(default_factory=list)
    snippet: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_json(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "source": self.source,
            "title": self.title,
            "source_id": self.source_id,
            "label": self.label,
            "score": self.score,
            "matched_terms": self.matched_terms,
            "snippet": self.snippet,
            "metadata": self.metadata,
        }


def tokens(text: str) -> list[str]:
    return WORD_RE.findall(text.lower())


def query_terms(query: str) -> list[str]:
    terms = []
    for token in tokens(query):
        if token in {"theorem", "definition", "lemma", "proposition", "corollary", "of", "the", "a", "an"}:
            continue
        terms.append(token)
    return terms


def score_text(text: str, terms: list[str]) -> tuple[int, list[str]]:
    lower = text.lower()
    matched = [term for term in terms if term in lower]
    score = sum(10 for _ in matched)
    if terms and all(term in lower for term in terms):
        score += 35
    quoted = " ".join(terms)
    if quoted and quoted in lower:
        score += 25
    return score, matched


def snippet_for(text: str, terms: list[str], *, radius: int = 220) -> str:
    lower = text.lower()
    positions = [lower.find(term) for term in terms if lower.find(term) >= 0]
    if not positions:
        clean = " ".join(text.split())
        return clean[: radius * 2]
    center = min(positions)
    start = max(0, center - radius)
    end = min(len(text), center + radius)
    return " ".join(text[start:end].split())


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8", errors="ignore"))


def search_knowledge_file(path: Path, terms: list[str]) -> list[EvidenceHit]:
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except (OSError, json.JSONDecodeError):
        return []
    hits: list[EvidenceHit] = []
    for node in data.get("nodes", []) if isinstance(data, dict) else []:
        if not isinstance(node, dict):
            continue
        fields = [
            str(node.get("id") or ""),
            str(node.get("name") or ""),
            str(node.get("statement_tex") or ""),
            str(node.get("formal") or ""),
            str(node.get("fully_quantified_form") or ""),
            str(node.get("failure_modes") or ""),
            " ".join(str(item) for item in node.get("depends_on_ids") or []),
        ]
        haystack = "\n".join(fields)
        score, matched = score_text(haystack, terms)
        if score <= 0:
            continue
        if str(node.get("id") or "").lower().endswith("-".join(terms)):
            score += 30
        hits.append(
            EvidenceHit(
                source_type="knowledge_explorer",
                source=str(path),
                title=str(node.get("name") or "") or None,
                label=str(node.get("id") or "") or None,
                score=score,
                matched_terms=matched,
                snippet=snippet_for(haystack, terms),
                metadata={
                    "chapter": node.get("chapter"),
                    "deck": node.get("deck"),
                    "source": node.get("source"),
                    "depends_on_ids": node.get("depends_on_ids") or [],
                },
            )
        )
    return hits


def discover_knowledge_files(paths: Iterable[Path]) -> list[Path]:
    files: set[Path] = set()
    for root in paths:
        if root.is_file() and root.name == "knowledge.json":
            files.add(root.resolve())
        elif root.is_dir():
            files.update(path.resolve() for path in root.rglob("knowledge.json") if ".explorer" in path.parts or path.name == "knowledge.json")
    return sorted(files)


def search_source_registry(path: Path, terms: list[str]) -> list[EvidenceHit]:
    if not path.exists():
        return []
    try:
        data = load_yaml(path)
    except Exception:
        return []
    hits: list[EvidenceHit] = []
    for source in data.get("sources", []) if isinstance(data, dict) else []:
        if not isinstance(source, dict):
            continue
        fields = [
            str(source.get("source_id") or ""),
            str(source.get("canonical_title") or ""),
            str(source.get("author") or ""),
            str(source.get("canonical_file") or ""),
        ]
        haystack = "\n".join(fields)
        score, matched = score_text(haystack, terms)
        if score <= 0:
            continue
        hits.append(
            EvidenceHit(
                source_type="source_registry",
                source=str(path),
                title=str(source.get("canonical_title") or "") or None,
                source_id=str(source.get("source_id") or "") or None,
                score=score,
                matched_terms=matched,
                snippet=snippet_for(haystack, terms),
                metadata={
                    "author": source.get("author"),
                    "canonical_file": source.get("canonical_file"),
                    "status": source.get("status"),
                },
            )
        )
    return hits


def search_source_index(path: Path, terms: list[str]) -> list[EvidenceHit]:
    if not path.exists():
        return []
    try:
        data = load_yaml(path)
    except Exception:
        return []
    hits: list[EvidenceHit] = []
    for source in data.get("sources", []) if isinstance(data, dict) else []:
        if not isinstance(source, dict):
            continue
        haystack = yaml.safe_dump(source, sort_keys=True, allow_unicode=True)
        score, matched = score_text(haystack, terms)
        if score <= 0:
            continue
        hits.append(
            EvidenceHit(
                source_type="source_index",
                source=str(path),
                title=str(source.get("canonical_title") or source.get("title") or "") or None,
                source_id=str(source.get("source_id") or "") or None,
                score=score + 15,
                matched_terms=matched,
                snippet=snippet_for(haystack, terms),
                metadata={"entry": source},
            )
        )
    return hits


def markdown_paths_from_source_index(path: Path) -> list[Path]:
    if not path.exists():
        return []
    try:
        data = load_yaml(path)
    except Exception:
        return []
    paths: list[Path] = []
    for source in data.get("sources", []) if isinstance(data, dict) else []:
        if not isinstance(source, dict):
            continue
        single = source.get("markdown_extract_path")
        if isinstance(single, str) and single:
            paths.append(Path(single))
        many = source.get("markdown_extract_paths")
        if isinstance(many, list):
            for item in many:
                if isinstance(item, str) and item:
                    paths.append(Path(item))
    return sorted({path.resolve() for path in paths if path.exists()})


def frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    raw = text[3:end]
    try:
        metadata = yaml.safe_load(raw) or {}
    except Exception:
        metadata = {}
    return metadata if isinstance(metadata, dict) else {}, text[end + 4 :]


def search_markdown(path: Path, terms: list[str]) -> EvidenceHit | None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    metadata, body = frontmatter(text)
    haystack = "\n".join(
        [
            str(metadata.get("source_id") or ""),
            str(metadata.get("canonical_title") or ""),
            str(metadata.get("author") or ""),
            body,
        ]
    )
    score, matched = score_text(haystack, terms)
    if score <= 0:
        return None
    return EvidenceHit(
        source_type="source_markdown",
        source=str(path),
        title=str(metadata.get("canonical_title") or path.stem) or None,
        source_id=str(metadata.get("source_id") or "") or None,
        score=score,
        matched_terms=matched,
        snippet=snippet_for(haystack, terms),
        metadata={
            "author": metadata.get("author"),
            "year": metadata.get("year"),
            "local_pdf_path": metadata.get("local_pdf_path"),
        },
    )


def discover_markdown_files(source_profiles_root: Path) -> list[Path]:
    roots = [
        source_profiles_root / "active-profile",
        source_profiles_root / "named-profiles",
    ]
    files: list[Path] = []
    for root in roots:
        if root.exists():
            files.extend(path for path in root.rglob("*.md") if path.is_file())
    return sorted(files)


def search_filenames(source_profiles_root: Path, terms: list[str]) -> list[EvidenceHit]:
    hits: list[EvidenceHit] = []
    for path in (source_profiles_root / "proposed-categories").rglob("*.pdf"):
        score, matched = score_text(path.name, terms)
        if score <= 0:
            continue
        hits.append(
            EvidenceHit(
                source_type="source_filename",
                source=str(path),
                title=path.stem,
                score=score,
                matched_terms=matched,
                snippet=path.name,
                metadata={"category": path.parent.name},
            )
        )
    return hits


def default_source_index_paths(source_profiles_root: Path, volume: str | None, chapter: str | None) -> list[Path]:
    base = source_profiles_root / "volumes"
    if volume and chapter:
        return sorted((base / volume).rglob(f"{chapter}/source-index.yaml"))
    if volume:
        return sorted((base / volume).rglob("source-index.yaml"))
    return sorted(base.rglob("source-index.yaml"))


def find_evidence(
    query: str,
    *,
    knowledge_roots: Iterable[Path],
    source_profiles_root: Path | None,
    source_index_paths: Iterable[Path],
    volume: str | None,
    chapter: str | None,
    limit: int,
) -> dict[str, Any]:
    terms = query_terms(query)
    hits: list[EvidenceHit] = []

    knowledge_files = discover_knowledge_files(knowledge_roots)
    for path in knowledge_files:
        hits.extend(search_knowledge_file(path, terms))

    source_indexes = list(source_index_paths)
    source_registry = None
    markdown_files: list[Path] = []
    if source_profiles_root:
        source_indexes.extend(default_source_index_paths(source_profiles_root, volume, chapter))
        source_registry = source_profiles_root / "inventory" / "source-registry.yaml"
        hits.extend(search_source_registry(source_registry, terms))
        markdown_files = discover_markdown_files(source_profiles_root)
        hits.extend(search_filenames(source_profiles_root, terms))

    index_markdown_files: list[Path] = []
    for path in source_indexes:
        hits.extend(search_source_index(path, terms))
        index_markdown_files.extend(markdown_paths_from_source_index(path))

    markdown_files = sorted({*(path.resolve() for path in markdown_files), *(path.resolve() for path in index_markdown_files)})
    for path in markdown_files:
        hit = search_markdown(path, terms)
        if hit:
            if path in {item.resolve() for item in index_markdown_files}:
                hit.source_type = "source_index_markdown"
                hit.score += 15
            hits.append(hit)

    hits.sort(key=lambda hit: (-hit.score, hit.source_type, hit.title or "", hit.source))
    deduped: list[EvidenceHit] = []
    seen: set[tuple[str, str, str | None]] = set()
    for hit in hits:
        key = (hit.source_type, hit.source, hit.label or hit.source_id)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(hit)

    return {
        "schema_version": "lra.internal-theorem-evidence/1.0",
        "query": query,
        "terms": terms,
        "inputs": {
            "knowledge_files": [str(path) for path in knowledge_files],
            "source_profiles_root": str(source_profiles_root) if source_profiles_root else None,
            "source_registry": str(source_registry) if source_registry else None,
            "source_index_files": [str(path) for path in source_indexes],
            "markdown_files_scanned": len(markdown_files),
            "source_index_markdown_files": [str(path) for path in index_markdown_files],
        },
        "hit_count": len(deduped),
        "hits": [hit.as_json() for hit in deduped[:limit]],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True, help="The theorem/definition title or search phrase.")
    parser.add_argument("--knowledge-root", action="append", type=Path, default=[], help="Repo or directory containing .explorer/knowledge.json files. May repeat.")
    parser.add_argument("--source-profiles-root", type=Path, help="Path to lra-source-profiles.")
    parser.add_argument("--source-index", action="append", type=Path, default=[], help="Explicit source-index.yaml file. May repeat.")
    parser.add_argument("--volume", help="Optional source-profile volume key, e.g. volume-iii.")
    parser.add_argument("--chapter", help="Optional source-profile chapter key, e.g. differentiation.")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=("json", "yaml"), default="yaml")
    args = parser.parse_args()

    try:
        payload = find_evidence(
            args.query,
            knowledge_roots=[path.resolve() for path in args.knowledge_root],
            source_profiles_root=args.source_profiles_root.resolve() if args.source_profiles_root else None,
            source_index_paths=[path.resolve() for path in args.source_index],
            volume=args.volume,
            chapter=args.chapter,
            limit=args.limit,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    else:
        text = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
