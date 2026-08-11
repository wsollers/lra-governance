#!/usr/bin/env python3
"""Ranked search for the internal LRA TeX/Lean object index."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

import yaml

try:
    from internal_object_sqlite import query_candidates
except ModuleNotFoundError:
    from tools.governance.internal_object_sqlite import query_candidates


WORD_RE = re.compile(r"[A-Za-z0-9]+")
LATEX_TOKEN_REPLACEMENTS = (
    (re.compile(r"\\mathbb\s*\{?\s*Q\s*\}?"), " Q rational rationals "),
    (re.compile(r"\\mathbb\s*\{?\s*Z\s*\}?"), " Z integer integers "),
    (re.compile(r"\\mathbb\s*\{?\s*N\s*\}?"), " N natural naturals "),
    (re.compile(r"\\mathbb\s*\{?\s*R\s*\}?"), " R real reals "),
    (re.compile(r"\\(?:leq?|leqslant)\b"), " less equal at most leq "),
    (re.compile(r"\\(?:geq?|geqslant)\b"), " greater equal at least geq "),
    (re.compile(r"\\sup\b"), " sup supremum "),
    (re.compile(r"\\inf\b"), " inf infimum "),
    (re.compile(r"\\max\b"), " max maximum "),
    (re.compile(r"\\min\b"), " min minimum "),
    (re.compile(r"\+"), " plus sum add "),
    (re.compile(r"="), " equals equal "),
)
QUERY_STOP_TOKENS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "if",
    "in",
    "is",
    "it",
    "its",
    "let",
    "of",
    "on",
    "or",
    "such",
    "that",
    "the",
    "then",
    "there",
    "to",
    "with",
}
NUMBER_WORDS = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
}
DEFAULT_FIELDS = ("name", "label", "declaration", "signature", "statement", "search_text", "path")
FIELD_WEIGHTS = {
    "name": 5.0,
    "label": 4.0,
    "declaration": 4.0,
    "signature": 3.0,
    "statement": 2.0,
    "search_text": 1.5,
    "path": 1.0,
}
QUERY_EXPANSIONS = {
    "sup": {"sup", "supremum", "suprema", "least", "upper", "bound"},
    "supremum": {"supremum", "suprema", "least", "upper", "bound", "lub"},
    "suprema": {"supremum", "suprema", "least", "upper", "bound", "lub"},
    "lub": {"supremum", "suprema", "least", "upper", "bound", "lub"},
    "inf": {"inf", "infimum", "infima", "greatest", "lower", "bound"},
    "infimum": {"infimum", "infima", "greatest", "lower", "bound", "glb"},
    "infima": {"infimum", "infima", "greatest", "lower", "bound", "glb"},
    "glb": {"infimum", "infima", "greatest", "lower", "bound", "glb"},
    "max": {"max", "maximum", "maximal"},
    "maximum": {"max", "maximum", "maximal"},
    "min": {"min", "minimum", "minimal"},
    "minimum": {"min", "minimum", "minimal"},
    "add": {"add", "addition", "sum", "plus"},
    "addition": {"add", "addition", "sum", "plus"},
    "sum": {"sum", "add", "addition", "plus"},
    "sums": {"sum", "sums", "add", "addition", "plus"},
    "q": {"q", "rational", "rationals", "field", "classes"},
    "rational": {"q", "rational", "rationals", "field", "classes"},
    "rationals": {"q", "rational", "rationals", "field", "classes"},
    "z": {"z", "integer", "integers"},
    "integer": {"z", "integer", "integers"},
    "integers": {"z", "integer", "integers"},
    "coprime": {"coprime", "relatively", "prime", "gcd", "bezout"},
    "relatively": {"coprime", "relatively", "prime", "gcd", "bezout"},
    "prime": {"coprime", "relatively", "prime", "gcd", "bezout"},
    "gcd": {"gcd", "coprime", "bezout", "divisibility"},
    "bezout": {"bezout", "gcd", "coprime", "linear", "combination", "integer"},
    "reciprocal": {"reciprocal", "inverse", "nonzero"},
    "inverse": {"reciprocal", "inverse", "nonzero"},
    "unique": {"unique", "uniqueness"},
    "uniqueness": {"unique", "uniqueness"},
    "convergent": {"convergent", "converges", "convergence", "limit"},
    "converges": {"convergent", "converges", "convergence", "limit"},
    "convergence": {"convergent", "converges", "convergence", "limit"},
    "eventually": {"eventually", "tail", "constant", "comparison"},
    "constant": {"constant", "comparison", "bound", "bounded"},
    "comparison": {"constant", "comparison", "bound", "bounded"},
    "even": {"even", "odd", "parity", "subsequence", "subsequences"},
    "odd": {"even", "odd", "parity", "subsequence", "subsequences"},
    "parity": {"even", "odd", "parity", "subsequence", "subsequences"},
    "residue": {"residue", "mod", "modulo", "partition", "subsequence"},
    "modulo": {"residue", "mod", "modulo", "partition", "subsequence"},
    "partition": {"partition", "finite", "residue", "subsequence", "recombine"},
}


def load_payload(path: Path) -> dict[str, Any]:
    if path.suffix.lower() in {".yaml", ".yml"}:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("objects"), list):
        raise ValueError(f"{path} is not an internal object index payload")
    return data


def normalize_text(text: str) -> str:
    text = preprocess_text(text)
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    return " ".join(tokenize(text))


def tokenize(text: str) -> list[str]:
    text = preprocess_text(text)
    tokens = [match.group(0).lower() for match in WORD_RE.finditer(text)]
    return [NUMBER_WORDS.get(token, token) for token in tokens]


def preprocess_text(text: str) -> str:
    for pattern, replacement in LATEX_TOKEN_REPLACEMENTS:
        text = pattern.sub(replacement, text)
    text = text.replace("<=", " less equal at most leq ")
    text = text.replace(">=", " greater equal at least geq ")
    return text


def expand_tokens(tokens: list[str]) -> set[str]:
    content_tokens = [token for token in tokens if token not in QUERY_STOP_TOKENS]
    expanded = set(content_tokens)
    for token in content_tokens:
        expanded.update(QUERY_EXPANSIONS.get(token, set()))
    return expanded


def char_ngrams(text: str, n: int = 3) -> set[str]:
    compact = re.sub(r"[^a-z0-9]+", " ", normalize_text(text)).strip()
    if len(compact) <= n:
        return {compact} if compact else set()
    return {compact[index : index + n] for index in range(len(compact) - n + 1)}


def field_value(record: dict[str, Any], field: str) -> str:
    value = record.get(field)
    return "" if value is None else str(value)


def score_field(query: str, query_tokens: list[str], expanded_tokens: set[str], query_grams: set[str], value: str, weight: float) -> float:
    if not value:
        return 0.0
    normalized = normalize_text(value)
    if not normalized:
        return 0.0
    value_tokens = set(tokenize(value))
    score = 0.0
    if query and query in normalized:
        score += 12.0 * weight
    content_query_tokens = [token for token in query_tokens if token not in QUERY_STOP_TOKENS]
    if content_query_tokens and all(token in value_tokens for token in content_query_tokens):
        score += 8.0 * weight
    matched_expanded = expanded_tokens & value_tokens
    if expanded_tokens:
        score += 5.0 * weight * (len(matched_expanded) / len(expanded_tokens))
    value_grams = char_ngrams(value)
    if query_grams and value_grams:
        overlap = len(query_grams & value_grams)
        dice = (2.0 * overlap) / (len(query_grams) + len(value_grams))
        score += 6.0 * weight * dice
    return score


def record_score(record: dict[str, Any], query: str, fields: tuple[str, ...]) -> float:
    query_tokens = tokenize(query)
    normalized_query = " ".join(query_tokens)
    expanded_tokens = expand_tokens(query_tokens)
    query_grams = char_ngrams(query)
    score = 0.0
    for field in fields:
        score += score_field(
            normalized_query,
            query_tokens,
            expanded_tokens,
            query_grams,
            field_value(record, field),
            FIELD_WEIGHTS.get(field, 1.0),
        )
    content_query_tokens = [token for token in query_tokens if token not in QUERY_STOP_TOKENS]
    record_tokens = set(tokenize(" ".join(field_value(record, field) for field in fields)))
    if content_query_tokens and record_tokens:
        direct_matches = sum(1 for token in content_query_tokens if token in record_tokens)
        expanded_matches = len(expanded_tokens & record_tokens)
        score += 30.0 * (direct_matches / len(content_query_tokens))
        score += 10.0 * (expanded_matches / max(len(expanded_tokens), 1))
    if record.get("source_family") == "tex" and record.get("label"):
        score += 0.25
    if "/proofs/" in str(record.get("path") or ""):
        score *= 0.85
    return score


def search_records(
    records: list[dict[str, Any]],
    query: str,
    *,
    source_family: str | None = None,
    kind: str | None = None,
    volume: str | None = None,
    limit: int = 10,
    fields: tuple[str, ...] = DEFAULT_FIELDS,
) -> list[dict[str, Any]]:
    results = []
    for record in records:
        if source_family and record.get("source_family") != source_family:
            continue
        if kind and record.get("kind") != kind:
            continue
        if volume and str(record.get("volume") or "").lower() != volume.lower():
            continue
        score = record_score(record, query, fields)
        if score <= 0:
            continue
        item = dict(record)
        item["_score"] = round(score, 4)
        results.append(item)
    results.sort(
        key=lambda item: (
            -float(item["_score"]),
            str(item.get("source_family") or ""),
            str(item.get("path") or ""),
            int(item.get("line") or 0),
        )
    )
    return results[:limit]


def search_sqlite(
    index: Path,
    query: str,
    *,
    source_family: str | None = None,
    kind: str | None = None,
    volume: str | None = None,
    limit: int = 10,
    fields: tuple[str, ...] = DEFAULT_FIELDS,
) -> list[dict[str, Any]]:
    terms = sorted(expand_tokens(tokenize(query)))
    candidates = query_candidates(
        index,
        terms,
        source_family=source_family,
        kind=kind,
        volume=volume,
        limit=max(300, limit * 50),
    )
    results = []
    for candidate in candidates:
        score = record_score(candidate, query, fields)
        if score <= 0:
            continue
        item = dict(candidate)
        item["_score"] = round(score, 4)
        results.append(item)
    results.sort(
        key=lambda item: (
            -float(item["_score"]),
            float(item.get("_fts_rank") or 0),
            str(item.get("source_family") or ""),
            str(item.get("path") or ""),
            int(item.get("line") or 0),
        )
    )
    return results[:limit]


def output_json(results: list[dict[str, Any]]) -> None:
    print(json.dumps(results, indent=2, ensure_ascii=False))


def output_text(results: list[dict[str, Any]]) -> None:
    for rank, item in enumerate(results, start=1):
        location = f"{item.get('repo_root')}\\{str(item.get('path') or '').replace('/', '\\')}:{item.get('line')}"
        label = item.get("label") or item.get("declaration") or item.get("object_id")
        print(f"{rank}. score={item['_score']} {item.get('source_family')} {item.get('kind')} | {item.get('name')} | {label}")
        print(f"   {location}")
        statement = " ".join(str(item.get("statement") or "").split())
        if statement:
            print(f"   {statement[:240]}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True, help="Internal object SQLite, JSON, or YAML index.")
    parser.add_argument("query", help="Search query, e.g. 'suprema of a sum'.")
    parser.add_argument("--source-family", choices=["tex", "lean", "cpp"])
    parser.add_argument(
        "--kind",
        choices=[
            "definition",
            "axiom",
            "theorem",
            "lemma",
            "proposition",
            "corollary",
            "abbrev",
            "def",
            "structure",
            "class",
            "inductive",
            "namespace",
            "struct",
            "enum",
            "function",
            "method",
        ],
    )
    parser.add_argument("--volume", help="Restrict to a volume such as volume-iii or VolumeIII.")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.index.suffix.lower() in {".sqlite", ".db"}:
        results = search_sqlite(
            args.index,
            args.query,
            source_family=args.source_family,
            kind=args.kind,
            volume=args.volume,
            limit=args.limit,
        )
    else:
        payload = load_payload(args.index)
        results = search_records(
            payload["objects"],
            args.query,
            source_family=args.source_family,
            kind=args.kind,
            volume=args.volume,
            limit=args.limit,
        )
    if args.format == "json":
        output_json(results)
    else:
        output_text(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
