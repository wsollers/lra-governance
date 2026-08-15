#!/usr/bin/env python3
"""Query LRA primary sources, authored objects, code objects, and vocabulary.

This is a compact agent-facing facade over indexes owned by lra-source-profiles
and lra-governance. It does not copy source text or create another canonical
data store.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


GOVERNANCE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INDEX_ROOT = Path(r"D:\Readings\indexes\lra")
INTERNAL_SQLITE_DIR = Path("internal") / "sqlite"
INTERNAL_DATABASES = {
    "tex": INTERNAL_SQLITE_DIR / "tex-search.sqlite",
    "lean": INTERNAL_SQLITE_DIR / "lean-search.sqlite",
    "cpp": INTERNAL_SQLITE_DIR / "cpp-search.sqlite",
}
SCOPES = ("sources", "tex", "lean", "cpp", "vocabulary", "internal", "all")

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")


@dataclass(frozen=True)
class LookupLocations:
    catalog_root: Path | None
    source_profiles_root: Path | None
    index_root: Path | None


class LookupError(RuntimeError):
    pass


@dataclass(frozen=True)
class SourceLooseAttempt:
    query: str
    authors: tuple[str, ...] = ()


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        raise LookupError(f"failed to read {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise LookupError(f"{path}: expected a YAML mapping")
    return payload


def _resolved_existing(value: str | Path | None) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser().resolve(strict=False)
    return path if path.exists() else None


def resolve_locations(governance_root: Path = GOVERNANCE_ROOT) -> LookupLocations:
    catalog = _resolved_existing(os.environ.get("LRA_SOURCES_ROOT"))
    if catalog is None:
        catalog = _resolved_existing(governance_root.parent / "lra-sources")

    catalog_data: dict[str, Any] = {}
    if catalog is not None and (catalog / "index.yaml").exists():
        catalog_data = _load_mapping(catalog / "index.yaml")

    profiles = _resolved_existing(os.environ.get("LRA_SOURCE_PROFILES_ROOT"))
    if profiles is None:
        profiles = _resolved_existing(catalog_data.get("source_profiles_root"))
    if profiles is None:
        profiles = _resolved_existing(governance_root.parent / "lra-source-profiles")

    index_root = _resolved_existing(
        os.environ.get("LRA_SOURCE_INDEX_ROOT")
        or os.environ.get("LRA_SOURCE_ARTIFACT_ROOT")
    )
    if index_root is None:
        index_root = _resolved_existing(catalog_data.get("source_index_root"))
    if index_root is None:
        index_root = _resolved_existing(DEFAULT_INDEX_ROOT)

    return LookupLocations(catalog, profiles, index_root)


def _source_search_script(locations: LookupLocations) -> Path | None:
    if locations.source_profiles_root is None:
        return None
    candidate = locations.source_profiles_root / "scripts" / "search_omnibus.py"
    return candidate if candidate.exists() else None


def status_payload(locations: LookupLocations) -> dict[str, Any]:
    index_root = locations.index_root
    source_script = _source_search_script(locations)
    paths = {
        "source_sqlite": index_root / "omnibus" / "sqlite" / "omnibus-search.sqlite"
        if index_root else None,
        "source_theorem_json": index_root / "omnibus" / "theorem-index.json"
        if index_root else None,
        "source_theorem_yaml": index_root / "omnibus" / "theorem-index.yaml"
        if index_root else None,
        "tex_sqlite": index_root / INTERNAL_DATABASES["tex"] if index_root else None,
        "lean_sqlite": index_root / INTERNAL_DATABASES["lean"] if index_root else None,
        "cpp_sqlite": index_root / INTERNAL_DATABASES["cpp"] if index_root else None,
    }
    source_index_available = any(
        path and path.exists()
        for path in (
            paths["source_sqlite"],
            paths["source_theorem_json"],
            paths["source_theorem_yaml"],
        )
    )
    lanes = {
        "sources": bool(source_script and source_index_available),
        "tex": bool(paths["tex_sqlite"] and paths["tex_sqlite"].exists()),
        "lean": bool(paths["lean_sqlite"] and paths["lean_sqlite"].exists()),
        "cpp": bool(paths["cpp_sqlite"] and paths["cpp_sqlite"].exists()),
        "vocabulary": all((GOVERNANCE_ROOT / name).exists() for name in (
            "predicates.yaml", "structures.yaml", "notation.yaml", "relations.yaml"
        )),
    }
    return {
        "ready": any(lanes.values()),
        "catalog_root": str(locations.catalog_root) if locations.catalog_root else None,
        "source_profiles_root": str(locations.source_profiles_root) if locations.source_profiles_root else None,
        "index_root": str(index_root) if index_root else None,
        "source_search_tool": str(source_script) if source_script else None,
        "lanes": lanes,
        "indexes": {key: str(value) if value else None for key, value in paths.items()},
    }


def _clip(value: Any, limit: int = 420) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def _compact_source(hit: dict[str, Any]) -> dict[str, Any]:
    return {
        "score": hit.get("score"),
        "kind": hit.get("kind"),
        "number": hit.get("number") or None,
        "title": hit.get("title") or None,
        "source_id": hit.get("source_id"),
        "source_title": hit.get("source_title"),
        "author": hit.get("author") or None,
        "volume": hit.get("volume") or None,
        "path": hit.get("path"),
        "line": hit.get("line"),
        "snippet": _clip(hit.get("snippet")),
    }


def search_sources(
    locations: LookupLocations,
    query: str,
    *,
    limit: int,
    args: argparse.Namespace,
) -> dict[str, Any]:
    script = _source_search_script(locations)
    if script is None or locations.index_root is None:
        raise LookupError("source search requires lra-source-profiles and an LRA index root")
    command = [
        sys.executable,
        str(script),
        query,
        "--index-root",
        str(locations.index_root),
        "--limit",
        str(limit),
        "--format",
        "json",
    ]
    for value in args.author:
        command.extend(("--author", value))
    for value in args.source_id:
        command.extend(("--source-id", value))
    for value in args.source_list:
        command.extend(("--source-list", str(value)))
    for option in ("profile", "volume", "book", "chapter"):
        value = getattr(args, option)
        if value:
            command.extend((f"--{option.replace('_', '-')}", value))
    if args.include_disabled:
        command.append("--include-disabled")

    completed = subprocess.run(
        command,
        cwd=locations.source_profiles_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    if completed.returncode != 0:
        raise LookupError(_clip(completed.stderr or completed.stdout, 800))
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise LookupError(f"source search returned invalid JSON: {exc}") from exc
    return {
        "hits": [_compact_source(hit) for hit in (payload.get("hits") or [])[:limit]],
        "codesearch": (payload.get("codesearch") or [])[:limit],
        "filters": payload.get("filters") or {},
    }


_COMMON_SOURCE_AUTHOR_HINTS = {
    "abbot",
    "abbott",
    "apostol",
    "bartle",
    "bruckner",
    "bruckners",
    "folland",
    "lebl",
    "munkres",
    "pugh",
    "royden",
    "rudin",
    "searcoid",
    "spivak",
    "tao",
    "zorich",
}
_AUTHOR_ALIASES = {
    "abbot": ("abbot", "abbott"),
    "bruckners": ("bruckners", "bruckner"),
}
_SPELLING_VARIANTS = {
    "def": "definition",
    "defs": "definition",
    "definitions": "definition",
    "guage": "gauge",
}
_INTENT_PHRASES = (
    "which authors have",
    "which author has",
    "definitions of",
    "definition of",
    "compare",
    "related to",
    "information about",
    "info about",
    "info for",
)
_FILLER_TOKENS = {"a", "an", "and", "for", "from", "in", "of", "on", "the", "with"}


def _source_explicit_constraints(args: argparse.Namespace) -> bool:
    return any(
        (
            args.source_id,
            args.source_list,
            args.profile,
            args.book,
            args.chapter,
        )
    )


def _tokenize_query(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z0-9'’-]*", text.lower())


def _clean_author_hint(value: str) -> str:
    value = value.lower().strip("'’")
    if value.endswith("'s") or value.endswith("’s"):
        value = value[:-2]
    if value.endswith("s") and value in _AUTHOR_ALIASES:
        return _AUTHOR_ALIASES[value][-1]
    return value


def _expand_author_hint(value: str) -> tuple[str, ...]:
    value = _clean_author_hint(value)
    return _AUTHOR_ALIASES.get(value, (value,))


def _extract_author_hints(query: str) -> list[str]:
    hints: list[str] = []
    for match in re.finditer(r"\b(?:from|by|with)\s+([A-Za-z][A-Za-z0-9'’-]*)", query, re.IGNORECASE):
        hints.extend(_expand_author_hint(match.group(1)))
    for match in re.finditer(r"\b([A-Za-z][A-Za-z0-9'’-]*)(?:'s|’s)\b", query, re.IGNORECASE):
        hints.extend(_expand_author_hint(match.group(1)))

    tokens = _tokenize_query(query)
    if tokens and tokens[0] in _COMMON_SOURCE_AUTHOR_HINTS:
        hints.extend(_expand_author_hint(tokens[0]))

    seen: set[str] = set()
    unique: list[str] = []
    for hint in hints:
        if hint and hint not in seen:
            seen.add(hint)
            unique.append(hint)
    return unique


def _clean_loose_query(query: str) -> str:
    text = query.lower()
    text = re.sub(r"\b([A-Za-z][A-Za-z0-9'’-]*)(?:'s|’s)\b", " ", text)
    text = re.sub(r"\b(?:from|by|with)\s+[A-Za-z][A-Za-z0-9'’-]*\b", " ", text)
    for phrase in _INTENT_PHRASES:
        text = text.replace(phrase, " ")
    tokens = []
    for token in _tokenize_query(text):
        token = _SPELLING_VARIANTS.get(token, token)
        if token not in _FILLER_TOKENS:
            tokens.append(token)
    if len(tokens) > 1 and tokens[0] in _COMMON_SOURCE_AUTHOR_HINTS:
        tokens = tokens[1:]
    return " ".join(tokens)


def _dedupe_attempts(attempts: list[SourceLooseAttempt]) -> list[SourceLooseAttempt]:
    deduped: list[SourceLooseAttempt] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for attempt in attempts:
        key = (attempt.query, attempt.authors)
        if attempt.query and key not in seen:
            seen.add(key)
            deduped.append(attempt)
    return deduped


def plan_loose_source_attempts(
    query: str, args: argparse.Namespace
) -> list[SourceLooseAttempt]:
    if _source_explicit_constraints(args):
        return []

    cleaned = _clean_loose_query(query)
    if not cleaned or cleaned == query.lower().strip():
        return []

    authors = list(args.author) or _extract_author_hints(query)
    attempts: list[SourceLooseAttempt] = []
    for author in authors:
        attempts.append(SourceLooseAttempt(cleaned, (author,)))
    attempts.append(SourceLooseAttempt(cleaned))
    return _dedupe_attempts(attempts)[:6]


def _clone_source_args(
    args: argparse.Namespace, *, authors: tuple[str, ...]
) -> argparse.Namespace:
    cloned = argparse.Namespace(**vars(args))
    cloned.author = list(authors)
    return cloned


def _source_hit_key(hit: dict[str, Any]) -> tuple[Any, ...]:
    return (
        hit.get("source_id"),
        hit.get("kind"),
        hit.get("number"),
        hit.get("title"),
        hit.get("path"),
        hit.get("line"),
    )


def enrich_with_loose_source_results(
    locations: LookupLocations,
    source_results: dict[str, Any],
    args: argparse.Namespace,
    *,
    limit: int,
) -> list[str]:
    if source_results.get("hits") or not getattr(args, "loose_sources", True):
        return []

    warnings: list[str] = []
    attempts_summary: list[dict[str, Any]] = []
    merged_hits: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()

    for attempt in plan_loose_source_attempts(args.query, args):
        attempt_args = _clone_source_args(args, authors=attempt.authors)
        try:
            attempt_results = search_sources(
                locations, attempt.query, limit=limit, args=attempt_args
            )
        except (LookupError, OSError, subprocess.SubprocessError) as exc:
            warnings.append(f"sources loose retry {attempt.query!r}: {exc}")
            continue
        hits = attempt_results.get("hits") or []
        attempts_summary.append(
            {
                "query": attempt.query,
                "authors": list(attempt.authors),
                "hit_count": len(hits),
            }
        )
        for hit in hits:
            key = _source_hit_key(hit)
            if key in seen:
                continue
            seen.add(key)
            annotated = dict(hit)
            annotated["matched_query"] = attempt.query
            if attempt.authors:
                annotated["matched_author_filter"] = list(attempt.authors)
            merged_hits.append(annotated)
            if len(merged_hits) >= limit:
                break
        if len(merged_hits) >= limit:
            break

    if attempts_summary:
        source_results["loose_attempts"] = attempts_summary
    if merged_hits:
        source_results["hits"] = merged_hits
        warnings.append(
            "sources: strict query returned 0 hits; loose retry returned "
            f"{len(merged_hits)} hit(s)"
        )
    return warnings


def _internal_module():
    try:
        import search_internal_object_index as module
    except ModuleNotFoundError:
        from tools.governance import search_internal_object_index as module
    return module


def _compact_internal(hit: dict[str, Any]) -> dict[str, Any]:
    metadata = hit.get("metadata") if isinstance(hit.get("metadata"), dict) else {}
    return {
        "score": hit.get("_score"),
        "object_id": hit.get("object_id"),
        "family": hit.get("source_family"),
        "kind": hit.get("kind"),
        "name": hit.get("name"),
        "label": hit.get("label") or None,
        "declaration": hit.get("declaration") or None,
        "repo_root": hit.get("repo_root"),
        "path": hit.get("path"),
        "line": hit.get("line"),
        "statement": _clip(hit.get("statement") or hit.get("signature"), 360),
        "verification_status": metadata.get("verification_status"),
    }


def search_internal(
    locations: LookupLocations,
    query: str,
    families: set[str],
    *,
    limit: int,
    volume: str | None,
) -> dict[str, list[dict[str, Any]]]:
    if locations.index_root is None:
        raise LookupError("internal search requires an LRA index root")
    module = _internal_module()
    results: dict[str, list[dict[str, Any]]] = {}

    for family in sorted(families):
        path = locations.index_root / INTERNAL_DATABASES[family]
        if not path.exists():
            raise LookupError(f"internal {family} SQLite index is missing: {path}")
        hits = module.search_sqlite(
            path,
            query,
            source_family=family,
            volume=volume if family in {"tex", "lean"} else None,
            limit=limit,
        )
        results[family] = [_compact_internal(hit) for hit in hits]
    return results


def search_vocabulary(query: str, *, limit: int) -> list[dict[str, Any]]:
    try:
        import vocabulary
    except ModuleNotFoundError:
        from tools.governance import vocabulary
    root = vocabulary.governance_root(GOVERNANCE_ROOT)
    index = vocabulary.default_index_path(root)
    vocabulary.ensure_index(root, index, refresh=True)
    return vocabulary.search_entries(
        index, query, kind=None, include_testing=False, limit=limit
    )


def expand_scopes(raw_scopes: list[str] | None) -> set[str]:
    scopes = set(raw_scopes or ["all"])
    if "all" in scopes:
        return {"sources", "tex", "lean", "cpp", "vocabulary"}
    if "internal" in scopes:
        scopes.remove("internal")
        scopes.update(("tex", "lean", "cpp"))
    return scopes


def lookup(args: argparse.Namespace, locations: LookupLocations) -> dict[str, Any]:
    scopes = expand_scopes(args.scope)
    payload: dict[str, Any] = {"query": args.query, "results": {}, "warnings": []}
    if "sources" in scopes:
        try:
            source_results = search_sources(
                locations, args.query, limit=args.limit, args=args
            )
            payload["results"]["sources"] = source_results
            payload["warnings"].extend(
                enrich_with_loose_source_results(
                    locations, source_results, args, limit=args.limit
                )
            )
            if args.author and not source_results.get("hits"):
                authors = ", ".join(args.author)
                payload["warnings"].append(
                    "sources: 0 hits with --author filter(s) "
                    f"{authors!r}; retry sources without --author, then constrain by "
                    "--source-id or a reviewed source list if needed"
                )
        except (LookupError, OSError, subprocess.SubprocessError) as exc:
            payload["warnings"].append(f"sources: {exc}")

    families = scopes & {"tex", "lean", "cpp"}
    for family in sorted(families):
        try:
            payload["results"].update(
                search_internal(
                    locations,
                    args.query,
                    {family},
                    limit=args.limit,
                    volume=args.volume,
                )
            )
        except (LookupError, OSError, ValueError, yaml.YAMLError) as exc:
            payload["warnings"].append(f"{family}: {exc}")

    if "vocabulary" in scopes:
        try:
            payload["results"]["vocabulary"] = search_vocabulary(
                args.query, limit=args.limit
            )
        except Exception as exc:
            payload["warnings"].append(f"vocabulary: {exc}")
    return payload


def print_text(payload: dict[str, Any]) -> None:
    print(f"query: {payload['query']}")
    for lane, value in payload["results"].items():
        hits = value.get("hits", []) if lane == "sources" else value
        print(f"\n{lane}: {len(hits)} hit(s)")
        for index, hit in enumerate(hits, start=1):
            title = hit.get("title") or hit.get("name") or hit.get("id") or ""
            identity = hit.get("source_id") or hit.get("label") or hit.get("declaration") or hit.get("object_id") or hit.get("id")
            print(f"  {index}. {hit.get('kind', '')} {title} [{identity}]")
            path = hit.get("path")
            if path:
                print(f"     {path}:{hit.get('line') or ''}")
            detail = hit.get("snippet") or hit.get("statement") or hit.get("description")
            if detail:
                print(f"     {detail}")
    for warning in payload.get("warnings") or []:
        print(f"\nwarning: {warning}", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", help="Theorem, definition, concept, label, or code phrase.")
    parser.add_argument("--status", action="store_true", help="Show resolved engines and index availability.")
    parser.add_argument(
        "--candidate-discovery-config",
        type=Path,
        help="Build a source-grounded concept discovery receipt from a reviewed source-index config.",
    )
    parser.add_argument("--output", type=Path, help="Write candidate-discovery JSON to this path.")
    parser.add_argument("--scope", action="append", choices=SCOPES, help="Search lane; repeat to combine. Default: all.")
    parser.add_argument("--limit", type=int, default=5, help="Maximum results per search lane.")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--author", action="append", default=[])
    parser.add_argument("--source-id", action="append", default=[])
    parser.add_argument("--source-list", action="append", type=Path, default=[])
    parser.add_argument("--profile")
    parser.add_argument("--volume")
    parser.add_argument("--book")
    parser.add_argument("--chapter")
    parser.add_argument("--include-disabled", action="store_true")
    parser.add_argument(
        "--no-loose-sources",
        dest="loose_sources",
        action="store_false",
        default=True,
        help="Disable automatic loose source retries after a zero-hit strict source query.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.candidate_discovery_config:
        try:
            from tools.governance import concept_candidate_discovery as discovery
        except ModuleNotFoundError:
            import concept_candidate_discovery as discovery
        receipt = discovery.build_receipt(discovery.load_mapping(args.candidate_discovery_config))
        errors = discovery.validate_receipt(receipt)
        if errors:
            print("candidate discovery: FAIL", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        text = json.dumps(receipt, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            args.output.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0
    locations = resolve_locations()
    if args.status:
        status = status_payload(locations)
        print(json.dumps(status, indent=2, ensure_ascii=False))
        return 0 if status["ready"] else 1
    if not args.query:
        print("error: query is required unless --status is used", file=sys.stderr)
        return 2
    payload = lookup(args, locations)
    if args.format == "text":
        print_text(payload)
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["results"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
