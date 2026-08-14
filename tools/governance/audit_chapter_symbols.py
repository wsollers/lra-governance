#!/usr/bin/env python3
"""Deterministically audit chapter symbols against canonical registries."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.finding import Finding, finding
from core.tex import line_at, read_stripped_text
from core.volume import VOLUME_RE
from validators import (
    formal_predicate_leakage,
    operator_metadata,
    predicate_reading_constructions,
    predicate_reading_signatures,
)


GOVERNANCE_ROOT = Path(__file__).resolve().parents[2]
OPERATOR_RE = re.compile(r"\\(?P<command>operatorname|mathsf)\{(?P<name>[^}]+)\}")


@dataclass(frozen=True)
class RegistryEntry:
    identifier: str
    name: str
    symbol: str = ""


@dataclass
class SymbolAuditResult:
    chapter: Path
    volume_root: Path
    files: list[Path]
    findings: list[Finding] = field(default_factory=list)
    used_predicates: set[str] = field(default_factory=set)
    used_structures: set[str] = field(default_factory=set)
    used_notation: set[str] = field(default_factory=set)
    unused_predicates: list[str] = field(default_factory=list)
    unused_structures: list[str] = field(default_factory=list)
    unused_notation: list[str] = field(default_factory=list)
    relation_edge_count: int = 0

    @property
    def violation_count(self) -> int:
        return len(self.findings)


def chapter_tex_files(chapter: Path) -> list[Path]:
    """Return current non-router chapter content in deterministic order."""
    chapter = chapter.resolve()
    files: list[Path] = []
    for subtree in ("notes", "proofs"):
        root = chapter / subtree
        if not root.is_dir():
            continue
        files.extend(path.resolve() for path in root.rglob("*.tex") if path.name != "index.tex")
    return sorted(set(files))


def collect_chapter_tex(chapter: Path) -> str:
    """Return the legacy concatenated view used by compatibility callers."""
    chapter = chapter.resolve()
    parts = []
    for path in chapter_tex_files(chapter):
        relative = path.relative_to(chapter)
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            parts.append(f"%% WARNING: Could not read {relative}: {exc}")
        else:
            parts.append(f"%% === FILE: {relative} ===\n{content}")
    return "\n\n".join(parts)


def _volume_root(chapter: Path) -> Path:
    for parent in chapter.resolve().parents:
        if VOLUME_RE.fullmatch(parent.name):
            return parent
    return chapter.resolve().parent


def _registry(path: Path, key: str, name_field: str) -> list[RegistryEntry]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get(key), list):
        raise ValueError(f"{path}: {key} must be a list")
    entries: list[RegistryEntry] = []
    for position, item in enumerate(data[key], 1):
        if not isinstance(item, dict):
            raise ValueError(f"{path}: {key}[{position}] must be a mapping")
        identifier = str(item.get("id") or "")
        name = str(item.get(name_field) or "")
        if not identifier or not name:
            raise ValueError(f"{path}: {key}[{position}] requires id and {name_field}")
        entries.append(RegistryEntry(identifier, name, str(item.get("symbol") or "")))
    return entries


def _relations(path: Path) -> int:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("relations"), list):
        raise ValueError(f"{path}: relations must be a list")
    return len(data["relations"])


def _deduplicate(findings: list[Finding]) -> list[Finding]:
    seen: set[tuple[str, str, int]] = set()
    result: list[Finding] = []
    for item in findings:
        key = (item.code, item.path, item.line)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return sorted(result, key=lambda item: (item.path, item.line, item.code))


def _command_usage(
    result: SymbolAuditResult,
    predicates: list[RegistryEntry],
    structures: list[RegistryEntry],
    notation: list[RegistryEntry],
) -> None:
    predicate_names = {entry.name for entry in predicates}
    structure_names = {entry.name for entry in structures}
    notation_operator_names = {
        match.group("name").strip()
        for entry in notation
        for match in OPERATOR_RE.finditer(entry.symbol)
        if match.group("command") == "operatorname"
    }
    known_operator_names = predicate_names | structure_names | notation_operator_names

    for path in result.files:
        text = read_stripped_text(path)
        for match in OPERATOR_RE.finditer(text):
            command = match.group("command")
            name = match.group("name").strip()
            line = line_at(text, match.start())
            if command == "operatorname":
                if name in predicate_names:
                    result.used_predicates.add(name)
                if name in notation_operator_names:
                    result.used_notation.add(rf"\operatorname{{{name}}}")
                if name in structure_names:
                    result.used_structures.add(name)
                    result.findings.append(
                        finding(
                            "structure_constructor_operatorname",
                            rf"\operatorname{{{name}}} is registered as a structure constructor; use \mathsf{{{name}}}.",
                            path,
                            result.volume_root,
                            line,
                            "error",
                        )
                    )
            else:
                if name in structure_names:
                    result.used_structures.add(name)
                elif name in predicate_names:
                    result.used_predicates.add(name)
                    result.findings.append(
                        finding(
                            "predicate_constructor_mathsf",
                            rf"\mathsf{{{name}}} is registered as a predicate; use \operatorname{{{name}}}.",
                            path,
                            result.volume_root,
                            line,
                            "error",
                        )
                    )
                elif name not in known_operator_names:
                    result.findings.append(
                        finding(
                            "unregistered_structure_constructor",
                            rf"\mathsf{{{name}}} is not registered in structures.yaml.",
                            path,
                            result.volume_root,
                            line,
                            "error",
                        )
                    )

        for entry in notation:
            if entry.symbol and entry.symbol in text:
                result.used_notation.add(entry.symbol)


def audit_chapter_symbols(
    chapter: Path,
    *,
    governance_root: Path = GOVERNANCE_ROOT,
) -> SymbolAuditResult:
    """Run exact registry and validator checks for a chapter."""
    chapter = Path(chapter).resolve()
    if not chapter.is_dir():
        raise FileNotFoundError(chapter)
    governance_root = Path(governance_root).resolve()
    predicates = _registry(governance_root / "predicates.yaml", "predicates", "name")
    structures = _registry(governance_root / "structures.yaml", "structures", "name")
    notation = _registry(governance_root / "notation.yaml", "notation", "symbol")

    result = SymbolAuditResult(
        chapter=chapter,
        volume_root=_volume_root(chapter),
        files=chapter_tex_files(chapter),
        relation_edge_count=_relations(governance_root / "relations.yaml"),
    )
    for validator in (
        operator_metadata,
        formal_predicate_leakage,
        predicate_reading_signatures,
        predicate_reading_constructions,
    ):
        result.findings.extend(validator.validate(result.volume_root, result.files))
    _command_usage(result, predicates, structures, notation)
    result.findings = _deduplicate(result.findings)

    result.unused_predicates = sorted({entry.name for entry in predicates} - result.used_predicates)
    result.unused_structures = sorted({entry.name for entry in structures} - result.used_structures)
    result.unused_notation = sorted({entry.name for entry in notation} - result.used_notation)
    return result


def _cell(value: str) -> str:
    return value.replace("|", r"\|").replace("\n", " ")


def _inline_list(values: list[str] | set[str]) -> str:
    ordered = sorted(values)
    return ", ".join(f"`{value}`" for value in ordered) if ordered else "_None._"


def format_symbol_audit_markdown(
    result: SymbolAuditResult,
    *,
    include_unused_entries: bool = False,
) -> str:
    """Format a transparent deterministic symbol-audit report."""
    lines = [
        "# Deterministic Symbol Audit",
        f"## Chapter: {result.chapter.name}",
        "",
        "## Coverage",
        "",
        "This report checks exact registered TeX spellings, predicate and structure command forms,",
        "predicate-reading signatures and constructions, predicate leakage, and unknown",
        "`\\operatorname{...}` / `\\mathsf{...}` names.",
        "",
        "It does not infer mathematical meaning from prose, decide whether arbitrary unregistered",
        "notation is semantically equivalent, or treat ontology edges as TeX relation symbols.",
        "",
        "## Findings",
        "",
    ]
    if result.findings:
        lines += [
            "| Code | Severity | Location | Finding |",
            "|---|---|---|---|",
        ]
        for item in result.findings:
            location = item.path + (f":{item.line}" if item.line else "")
            lines.append(
                f"| `{_cell(item.code)}` | {_cell(item.severity)} | `{_cell(location)}` | {_cell(item.message)} |"
            )
    else:
        lines.append("_None._")

    lines += [
        "",
        "## Registered Uses",
        "",
        f"- Predicates: {_inline_list(result.used_predicates)}",
        f"- Structures: {_inline_list(result.used_structures)}",
        f"- Notation (exact registry spellings): {_inline_list(result.used_notation)}",
        "",
        "## Relations Registry",
        "",
        f"`relations.yaml` contains {result.relation_edge_count} ontology edge(s). It does not define TeX relation spellings, so chapter relation-symbol usage is not audited from that file.",
        "",
        "## Unused Registry Entries (Informational)",
        "",
        f"- Predicates: {len(result.unused_predicates)} unused",
        f"- Structures: {len(result.unused_structures)} unused",
        f"- Notation: {len(result.unused_notation)} unused",
        "",
    ]
    if include_unused_entries:
        lines += [
            "### Unused Predicates",
            "",
            _inline_list(result.unused_predicates),
            "",
            "### Unused Structures",
            "",
            _inline_list(result.unused_structures),
            "",
            "### Unused Notation",
            "",
            _inline_list(result.unused_notation),
            "",
        ]
    else:
        lines += [
            "Pass `--include-unused` to the standalone tool to expand these informational lists.",
            "",
        ]
    lines += [
        "## Summary",
        "",
        f"- Files scanned: {len(result.files)}",
        f"- Deterministic findings: {result.violation_count}",
        f"- Registered predicates used: {len(result.used_predicates)}",
        f"- Registered structures used: {len(result.used_structures)}",
        f"- Registered notation spellings used: {len(result.used_notation)}",
        "",
    ]
    return "\n".join(lines)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chapter", type=Path, required=True)
    parser.add_argument("--governance-root", type=Path, default=GOVERNANCE_ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--include-unused", action="store_true")
    parser.add_argument("--fail-on-findings", action="store_true")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    result = audit_chapter_symbols(args.chapter, governance_root=args.governance_root)
    markdown = format_symbol_audit_markdown(
        result,
        include_unused_entries=args.include_unused,
    )
    print(markdown)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")
    return 2 if args.fail_on_findings and result.findings else 0


if __name__ == "__main__":
    sys.exit(main())
