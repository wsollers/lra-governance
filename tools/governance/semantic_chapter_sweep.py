#!/usr/bin/env python3
"""Rank likely semantic-governance problems in TeX chapters or sections.

This is a source-level smoke detector.  It does not validate a completed
semantic artifact and it does not certify mathematics.  Instead, it scans
formal LaTeX blocks, runs the lightweight independent source extractors, and
scores cues that have repeatedly predicted bad or expensive semantic audits.
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

from compare_semantic_ast_extractors import (
    ExtractedFacts,
    displayed_math_extract,
    predicate_operator_names,
    pylatexenc_extract,
    strip_comments,
    surface_regex_extract,
    tree_sitter_extract,
)
from validate_semantic_logic import latex_quantified_variable_counts, latex_quantifier_counts


FORMAL_ENV_RE = re.compile(
    r"\\begin\{(?P<env>definition|axiom|theorem|lemma|proposition|corollary)\}"
    r"(?:\[(?P<title>[^\]]+)\])?",
    re.IGNORECASE,
)
FORMAL_BEGIN_OR_BOX_RE = re.compile(
    r"\\begin\{(?:definition|axiom|theorem|lemma|proposition|corollary)(?:box)?\}",
    re.IGNORECASE,
)
LABEL_RE = re.compile(r"\\label\{(?P<label>[^{}]+)\}")
HYPERREF_RE = re.compile(r"\\hyperref\[(?P<label>[^\]]+)\]")
REMARK_RE = re.compile(
    r"\\begin\{remark\*\}\[(?P<title>[^\]]+)\](?P<body>.*?)\\end\{remark\*\}",
    re.IGNORECASE | re.S,
)

SEVERITY_WEIGHT = {
    "critical": 40,
    "error": 25,
    "warning": 10,
    "info": 3,
}


@dataclass
class SweepFinding:
    code: str
    severity: str
    message: str

    def as_json(self) -> dict[str, str]:
        return {"code": self.code, "severity": self.severity, "message": self.message}


@dataclass
class FormalBlock:
    path: Path
    repo_relative_path: str
    line_start: int
    line_end: int
    env: str
    label: str
    title: str | None
    text: str


@dataclass
class SweepItem:
    label: str
    environment: str
    title: str | None
    path: str
    line_start: int
    line_end: int
    score: int = 0
    findings: list[SweepFinding] = field(default_factory=list)
    extractor_summary: dict[str, Any] = field(default_factory=dict)

    def add(self, code: str, severity: str, message: str) -> None:
        self.findings.append(SweepFinding(code, severity, message))
        self.score += SEVERITY_WEIGHT[severity]

    def as_json(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "environment": self.environment,
            "title": self.title,
            "path": self.path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "score": self.score,
            "findings": [finding.as_json() for finding in self.findings],
            "extractor_summary": self.extractor_summary,
        }


def tex_files(target: Path) -> Iterable[Path]:
    if target.is_file():
        if target.suffix == ".tex":
            yield target
        return
    for path in sorted(target.rglob("*.tex")):
        parts = {part.lower() for part in path.parts}
        if "build" in parts or ".external-review-diagnostics" in parts:
            continue
        yield path


def repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root)).replace("\\", "/")
    except ValueError:
        return str(path)


def line_for_offset(text: str, offset: int) -> int:
    return text[:offset].count("\n") + 1


def collect_known_labels(repo_root: Path) -> set[str]:
    labels: set[str] = set()
    for path in tex_files(repo_root):
        try:
            labels.update(LABEL_RE.findall(path.read_text(encoding="utf-8", errors="ignore")))
        except OSError:
            continue
    return labels


def explorer_labels_from_file(path: Path) -> set[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    labels: set[str] = set()
    nodes = data.get("nodes") if isinstance(data, dict) else None
    if isinstance(nodes, list):
        for node in nodes:
            if isinstance(node, dict) and isinstance(node.get("id"), str):
                labels.add(node["id"])
    return labels


def discover_explorer_files(repo_root: Path, target: Path) -> list[Path]:
    candidates: list[Path] = []
    for base in [target if target.is_dir() else target.parent, repo_root]:
        for path in base.rglob(".explorer/knowledge.json"):
            candidates.append(path)
    unique = sorted({path.resolve() for path in candidates})
    return unique


def collect_explorer_labels(paths: Iterable[Path]) -> tuple[set[str], list[str]]:
    labels: set[str] = set()
    used: list[str] = []
    for path in paths:
        found = explorer_labels_from_file(path)
        if found:
            labels.update(found)
            used.append(str(path))
    return labels, used


def formal_blocks(target: Path, repo_root: Path) -> list[FormalBlock]:
    blocks: list[FormalBlock] = []
    for path in tex_files(target):
        text = path.read_text(encoding="utf-8", errors="ignore")
        starts = list(FORMAL_BEGIN_OR_BOX_RE.finditer(text))
        for index, start in enumerate(starts):
            next_start = starts[index + 1].start() if index + 1 < len(starts) else len(text)
            block_text = text[start.start() : next_start]
            env_match = FORMAL_ENV_RE.search(block_text)
            label_match = LABEL_RE.search(block_text)
            if not env_match or not label_match:
                continue
            env = env_match.group("env").lower()
            label = label_match.group("label")
            if not re.match(r"^(def|thm|lem|prop|cor):", label):
                continue
            offset = start.start()
            end_offset = next_start
            blocks.append(
                FormalBlock(
                    path=path,
                    repo_relative_path=repo_relative(path, repo_root),
                    line_start=line_for_offset(text, offset),
                    line_end=line_for_offset(text, end_offset),
                    env=env,
                    label=label,
                    title=env_match.group("title"),
                    text=block_text,
                )
            )
    return blocks


def remark_bodies(block_text: str) -> dict[str, list[str]]:
    bodies: dict[str, list[str]] = {}
    for match in REMARK_RE.finditer(block_text):
        key = match.group("title").strip().lower()
        bodies.setdefault(key, []).append(match.group("body"))
    return bodies


def extractors(block_text: str) -> list[ExtractedFacts]:
    return [
        surface_regex_extract(block_text),
        displayed_math_extract(block_text),
        pylatexenc_extract(block_text),
        tree_sitter_extract(block_text),
    ]


def available_extractors(facts: list[ExtractedFacts]) -> list[ExtractedFacts]:
    return [item for item in facts if item.available]


def flag_disagreements(item: SweepItem, facts: list[ExtractedFacts]) -> None:
    available = available_extractors(facts)
    if len(available) < 2:
        item.add("INSUFFICIENT_EXTRACTORS", "warning", "Fewer than two independent LaTeX extractors were available.")
        return
    for field_name in ("has_iff", "has_implies", "has_forall", "has_exists", "has_negation"):
        values = {getattr(fact, field_name) for fact in available}
        if len(values) > 1 and any(values):
            names = [fact.extractor for fact in available if getattr(fact, field_name)]
            item.add(
                "EXTRACTOR_LOGICAL_CUE_DISAGREEMENT",
                "warning",
                f"Independent extractors disagree on {field_name}; positive readers: {', '.join(names)}.",
            )
    predicate_sets = [fact.predicates for fact in available if fact.predicates]
    if len(predicate_sets) >= 2 and len({tuple(sorted(items)) for items in predicate_sets}) > 1:
        item.add("EXTRACTOR_PREDICATE_DISAGREEMENT", "warning", "Independent extractors saw different governed predicate names.")


def flag_quantifier_shape(item: SweepItem, bodies: dict[str, list[str]], block_text: str) -> None:
    standard_blocks = [
        body
        for title, body_list in bodies.items()
        if "standard quantified" in title
        for body in body_list
    ]
    if not standard_blocks:
        if re.search(r"\\forall|\\exists|\bfor all\b|\bfor every\b|\bthere exists\b", block_text, re.I):
            item.add(
                "NO_STANDARD_QUANTIFIED_BLOCK",
                "warning",
                "The source has quantifier cues, but no named Standard quantified statement block.",
            )
        return
    for body in standard_blocks:
        counts = latex_quantifier_counts(body)
        variable_counts = latex_quantified_variable_counts(body)
        for quantifier in ("forall", "exists"):
            if counts[quantifier] and counts[quantifier] != variable_counts[quantifier]:
                item.add(
                    "QUANTIFIER_VARIABLE_COUNT_MISMATCH",
                    "error",
                    f"Standard quantified block has {counts[quantifier]} \\{quantifier} macro(s) but appears to bind {variable_counts[quantifier]} {quantifier} variable(s).",
                )
        if (counts["forall"] or counts["exists"]) and not re.search(r"\\Rightarrow|\\implies|\\iff|\\Longleftrightarrow", body):
            item.add(
                "QUANTIFIED_BLOCK_WITHOUT_CONNECTIVE",
                "warning",
                "Standard quantified block has quantifiers but no obvious implication/equivalence connective.",
            )


def flag_predicate_reading(item: SweepItem, bodies: dict[str, list[str]]) -> None:
    predicate_blocks = [
        body
        for title, body_list in bodies.items()
        if "predicate reading" in title
        for body in body_list
    ]
    if not predicate_blocks:
        item.add("NO_PREDICATE_READING", "info", "No Predicate reading block was found.")
        return
    for body in predicate_blocks:
        if "$label" in body or "label:" in body or "predicate-level form" in body:
            item.add(
                "PLACEHOLDER_PREDICATE_READING",
                "critical",
                "Predicate reading still contains generated placeholder language.",
            )
        if re.search(r"\\operatorname\{Derivative\}\((?:[^()]|\([^()]*\))*?,(?:[^()]|\([^()]*\))*?,\s*[a-zA-Z](?:\s*,|\))", body):
            item.add(
                "BARE_DERIVATIVE_LOCUS",
                "error",
                "Derivative predicate appears to receive a bare point instead of a governed Point(...) locus.",
            )
        predicates = predicate_operator_names(body)
        if not predicates and re.search(r"\\operatorname\{", body):
            item.add(
                "ONLY_TERM_OPERATORS_IN_PREDICATE_READING",
                "warning",
                "Predicate reading uses operatorname macros, but none look like governed UpperCamel predicates.",
            )


def flag_dependency_shape(item: SweepItem, block: FormalBlock, known_labels: set[str]) -> None:
    dependencies = set(HYPERREF_RE.findall(block.text))
    unresolved = sorted(label for label in dependencies if label not in known_labels)
    for label in unresolved:
        severity = "error" if label.startswith(("def:", "thm:", "lem:", "prop:", "cor:", "prf:")) else "warning"
        item.add("UNRESOLVED_REFERENCE_LABEL", severity, f"Referenced label {label!r} does not resolve in the visible TeX label index.")
    if block.label == "thm:darboux" and "thm:darboux-property" in dependencies:
        item.add(
            "KNOWN_BAD_DARBOUX_DEPENDENCY",
            "critical",
            "Darboux's theorem for derivatives should not depend on the continuous-function Darboux property.",
        )


def flag_known_semantic_traps(item: SweepItem, block: FormalBlock, bodies: dict[str, list[str]]) -> None:
    lower = block.text.lower()
    if len([title for title in bodies if "failure modes" in title]) > 1:
        item.add("DUPLICATE_FAILURE_MODE_BLOCKS", "warning", "Multiple Failure modes blocks are attached to one formal item.")
    if block.label == "thm:darboux":
        if re.search(r"I\s*:=\s*\[a,b\]", block.text) or re.search(r"f'\(a\).*f'\(b\)|f'\(b\).*f'\(a\)", block.text, re.S):
            item.add(
                "DARBOUX_ENDPOINT_FORMULATION",
                "critical",
                "Darboux source appears to use closed-interval endpoint derivatives; the safer theorem quantifies x,y in an open interval.",
            )
    if block.label == "thm:derivative-equivalence" and re.search(r"epsilon|topological|sequential", lower):
        if len(re.findall(r"\\Longleftrightarrow|\\iff", block.text)) < 2:
            item.add(
                "POSSIBLE_MALFORMED_MULTI_EQUIVALENCE",
                "warning",
                "Derivative-equivalence theorem mentions three formulations but does not expose an obvious three-way equivalence chain.",
            )
    if re.search(r"\bcontrapositive\b", lower) and re.search(r"\bnegation\b", lower):
        item.add(
            "NEGATION_CONTRAPOSITIVE_COLOCATED",
            "warning",
            "Source discusses negation and contrapositive together; verify these are separated in semantic forms.",
        )


def summarize_extractors(facts: list[ExtractedFacts]) -> dict[str, Any]:
    available = available_extractors(facts)
    return {
        "available": [fact.extractor for fact in available],
        "logical_cues": {
            field_name: [fact.extractor for fact in available if getattr(fact, field_name)]
            for field_name in ("has_iff", "has_implies", "has_forall", "has_exists", "has_negation")
        },
        "predicates": sorted({predicate for fact in available for predicate in fact.predicates}),
    }


def sweep(target: Path, repo_root: Path, explorer_files: Iterable[Path] = ()) -> dict[str, Any]:
    tex_labels = collect_known_labels(repo_root)
    explorer_labels, used_explorer_files = collect_explorer_labels(explorer_files)
    known_labels = tex_labels | explorer_labels
    blocks = formal_blocks(target, repo_root)
    items: list[SweepItem] = []
    for block in blocks:
        item = SweepItem(
            label=block.label,
            environment=block.env,
            title=block.title,
            path=block.repo_relative_path,
            line_start=block.line_start,
            line_end=block.line_end,
        )
        bodies = remark_bodies(block.text)
        facts = extractors(block.text)
        item.extractor_summary = summarize_extractors(facts)
        flag_disagreements(item, facts)
        flag_quantifier_shape(item, bodies, block.text)
        flag_predicate_reading(item, bodies)
        flag_dependency_shape(item, block, known_labels)
        flag_known_semantic_traps(item, block, bodies)
        if item.findings:
            items.append(item)

    items.sort(key=lambda entry: (-entry.score, entry.path, entry.line_start, entry.label))
    return {
        "schema_version": "lra.semantic-chapter-sweep/1.0",
        "target": str(target),
        "repo_root": str(repo_root),
        "knowledge_explorer_files": used_explorer_files,
        "known_label_counts": {
            "tex": len(tex_labels),
            "knowledge_explorer": len(explorer_labels),
            "combined": len(known_labels),
        },
        "formal_blocks_scanned": len(blocks),
        "items_with_findings": len(items),
        "items": [item.as_json() for item in items],
    }


def markdown_report(payload: dict[str, Any], *, limit: int | None = None) -> str:
    items = payload["items"][:limit] if limit else payload["items"]
    lines = [
        "# Semantic chapter sweep",
        "",
        f"- Target: `{payload['target']}`",
        f"- Knowledge Explorer files: {len(payload.get('knowledge_explorer_files') or [])}",
        f"- Known labels: {payload.get('known_label_counts', {}).get('combined', 0)}",
        f"- Formal blocks scanned: {payload['formal_blocks_scanned']}",
        f"- Items with findings: {payload['items_with_findings']}",
        "",
        "| Rank | Score | Label | Location | Worst findings |",
        "|---:|---:|---|---|---|",
    ]
    for rank, item in enumerate(items, start=1):
        worst = "; ".join(f"{finding['severity']}:{finding['code']}" for finding in item["findings"][:3])
        location = f"{item['path']}:{item['line_start']}"
        lines.append(f"| {rank} | {item['score']} | `{item['label']}` | `{location}` | {worst} |")
    lines.append("")
    for rank, item in enumerate(items, start=1):
        lines.extend([f"## {rank}. `{item['label']}` — score {item['score']}", ""])
        lines.append(f"Location: `{item['path']}:{item['line_start']}`")
        lines.append("")
        for finding in item["findings"]:
            lines.append(f"- `{finding['severity']}` `{finding['code']}`: {finding['message']}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, type=Path, help="A .tex file or directory to sweep.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repository root used for label indexing and relative paths.")
    parser.add_argument(
        "--knowledge-json",
        action="append",
        type=Path,
        default=[],
        help="Knowledge Explorer knowledge.json file to use as an additional strict label index. May be repeated.",
    )
    parser.add_argument(
        "--no-discover-knowledge",
        action="store_true",
        help="Do not automatically discover .explorer/knowledge.json files under the target/repo root.",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=("yaml", "json", "markdown"), default="yaml")
    parser.add_argument("--limit", type=int, help="Limit markdown output to the top N findings.")
    args = parser.parse_args()

    try:
        target = args.target.resolve()
        repo_root = args.repo_root.resolve()
        explorer_files = [path.resolve() for path in args.knowledge_json]
        if not args.no_discover_knowledge:
            explorer_files.extend(discover_explorer_files(repo_root, target))
        payload = sweep(target, repo_root, explorer_files)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    elif args.format == "markdown":
        text = markdown_report(payload, limit=args.limit) + "\n"
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
