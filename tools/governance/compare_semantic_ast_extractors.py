#!/usr/bin/env python3
"""Compare semantic AST metadata with independently extracted source facts.

This tool is deliberately shallow: it does not prove mathematics. It asks
several independent source readers to extract logical-shape cues, then checks
whether the semantic artifact records the same cues in its structured AST.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


FORMAL_ENVIRONMENTS = {
    "definition",
    "axiom",
    "theorem",
    "lemma",
    "proposition",
    "corollary",
}

MAJOR_BOX_RE = re.compile(
    r"\\begin\{(?:definition|axiom|theorem|lemma|proposition|corollary)box\}",
    re.IGNORECASE,
)
FORMAL_BEGIN_RE = re.compile(
    r"\\begin\{(?:definition|axiom|theorem|lemma|proposition|corollary)\}",
    re.IGNORECASE,
)


@dataclass
class ExtractedFacts:
    extractor: str
    available: bool = True
    label: str | None = None
    environment_kind: str | None = None
    title: str | None = None
    has_iff: bool = False
    has_implies: bool = False
    has_forall: bool = False
    has_exists: bool = False
    has_negation: bool = False
    predicates: set[str] = field(default_factory=set)
    dependencies: set[str] = field(default_factory=set)
    support_blocks: set[str] = field(default_factory=set)
    notes: list[str] = field(default_factory=list)

    def as_json(self) -> dict[str, Any]:
        return {
            "extractor": self.extractor,
            "available": self.available,
            "label": self.label,
            "environment_kind": self.environment_kind,
            "title": self.title,
            "has_iff": self.has_iff,
            "has_implies": self.has_implies,
            "has_forall": self.has_forall,
            "has_exists": self.has_exists,
            "has_negation": self.has_negation,
            "predicates": sorted(self.predicates),
            "dependencies": sorted(self.dependencies),
            "support_blocks": sorted(self.support_blocks),
            "notes": self.notes,
        }


@dataclass
class Finding:
    code: str
    severity: str
    message: str
    field: str | None = None

    def as_json(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "field": self.field,
        }


def load_mapping(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a mapping")
    return data


def normalized_token(value: str) -> str:
    return value.replace("-", "").replace("_", "").lower()


def predicate_operator_names(text: str) -> set[str]:
    """Return operatorname entries that are predicate-shaped.

    LaTeX uses ``\\operatorname`` for both semantic predicates
    (``IsContinuous``) and ordinary term-level functions (``sgn``).  The
    extractor should not require every lowercase function symbol found in an
    example or counterexample to appear as a governed predicate in the artifact
    AST.  Registered LRA predicate surface names are UpperCamel-style, so a
    leading uppercase letter is the conservative predicate cue.
    """
    return {
        name
        for name in re.findall(r"\\operatorname\{([A-Za-z][A-Za-z0-9]*)\}", text)
        if name[:1].isupper()
    }


def load_aliases(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    data = load_mapping(path)
    aliases: dict[str, dict[str, Any]] = {}
    for item in data.get("predicate_aliases", []) or []:
        if not isinstance(item, dict):
            continue
        keys = {
            normalized_token(str(item.get("source_name") or "")),
            normalized_token(str(item.get("source_predicate") or "").split(":", 1)[-1]),
        }
        for key in keys:
            if key:
                aliases[key] = item
    return aliases


def strip_comments(text: str) -> str:
    lines = []
    for line in text.splitlines():
        escaped = False
        cut = len(line)
        for index, char in enumerate(line):
            if char == "\\":
                escaped = not escaped
                continue
            if char == "%" and not escaped:
                cut = index
                break
            escaped = False
        lines.append(line[:cut])
    return "\n".join(lines)


def scoped_source_for_label(text: str, target_label: str | None) -> tuple[str, dict[str, Any] | None]:
    if not target_label:
        return text, None
    label_re = re.compile(r"\\label\{" + re.escape(target_label) + r"\}")
    match = label_re.search(text)
    if not match:
        raise ValueError(f"target label {target_label!r} was not found in source")

    lines = text.splitlines(keepends=True)
    offset = 0
    label_line = 0
    for index, line in enumerate(lines):
        next_offset = offset + len(line)
        if offset <= match.start() < next_offset:
            label_line = index
            break
        offset = next_offset

    start_line = label_line
    for index in range(label_line, -1, -1):
        if MAJOR_BOX_RE.search(lines[index]) or FORMAL_BEGIN_RE.search(lines[index]):
            start_line = index
            break

    end_line = len(lines)
    for index in range(label_line + 1, len(lines)):
        if MAJOR_BOX_RE.search(lines[index]) or FORMAL_BEGIN_RE.search(lines[index]):
            end_line = index
            break

    return "".join(lines[start_line:end_line]), {
        "target_label": target_label,
        "source_line_start": start_line + 1,
        "source_line_end": end_line,
    }


def surface_regex_extract(text: str) -> ExtractedFacts:
    clean = strip_comments(text)
    facts = ExtractedFacts("surface_regex")
    env = re.search(
        r"\\begin\{(definition|axiom|theorem|lemma|proposition|corollary)\}(?:\[([^\]]+)\])?",
        clean,
    )
    if env:
        facts.environment_kind = env.group(1)
        facts.title = env.group(2)
    label = re.search(r"\\label\{([^}]+)\}", clean)
    if label:
        facts.label = label.group(1)
    facts.has_iff = bool(re.search(r"\\iff|\\Longleftrightarrow|\bif and only if\b|\bexactly when\b|\bequivalent(?:ly)?\b", clean, re.I))
    if facts.environment_kind == "definition" and re.search(r"\bis (?:an? )?.+?\bif\b", clean, re.I | re.S):
        facts.has_iff = True
        facts.notes.append("definition-prose rule treated 'is ... if ...' as definitional equivalence")
    facts.has_implies = bool(re.search(r"\\implies|\\Rightarrow|\bif\b.+\bthen\b", clean, re.I | re.S))
    facts.has_forall = bool(re.search(r"\\forall|\bfor all\b|\bfor every\b|\bevery\b", clean, re.I))
    facts.has_exists = bool(re.search(r"\\exists|\bthere exists\b|\bsome\b", clean, re.I))
    facts.has_negation = bool(re.search(r"\\neg|\\not|\\nleq|\\notin|\bnot\b|\bfails?\b", clean, re.I))
    facts.predicates = predicate_operator_names(clean)
    facts.dependencies = set(re.findall(r"\\hyperref\[([^\]]+)\]", clean))
    facts.support_blocks = {
        item.strip().lower()
        for item in re.findall(r"\\begin\{remark\*\}\[([^\]]+)\]", clean)
    }
    return facts


def displayed_math_extract(text: str) -> ExtractedFacts:
    clean = strip_comments(text)
    facts = ExtractedFacts("displayed_math_regex")
    displays = re.findall(r"\\\[(.*?)\\\]", clean, flags=re.S)
    math = "\n".join(displays)
    facts.has_iff = bool(re.search(r"\\iff|\\Longleftrightarrow", math))
    facts.has_implies = bool(re.search(r"\\implies|\\Rightarrow", math))
    facts.has_forall = bool(re.search(r"\\forall|\\\(forall", math))
    facts.has_exists = bool(re.search(r"\\exists|\\\(exists", math))
    facts.has_negation = bool(re.search(r"\\neg|\\not|\\nleq|\\notin", math))
    facts.predicates = predicate_operator_names(math)
    facts.notes.append(f"examined {len(displays)} displayed math block(s)")
    return facts


def pylatexenc_extract(text: str) -> ExtractedFacts:
    facts = ExtractedFacts("pylatexenc")
    if importlib.util.find_spec("pylatexenc") is None:
        facts.available = False
        facts.notes.append("pylatexenc is not installed")
        return facts
    from pylatexenc.latexwalker import LatexWalker, LatexEnvironmentNode, LatexMacroNode

    nodes, _, _ = LatexWalker(text).get_latex_nodes()

    def node_text(node: Any) -> str:
        if node is None:
            return ""
        if hasattr(node, "chars"):
            return str(node.chars)
        if hasattr(node, "nodelist"):
            return "".join(node_text(child) for child in node.nodelist or [])
        return str(node)

    def visit(node: Any) -> None:
        if isinstance(node, LatexEnvironmentNode):
            if node.environmentname in FORMAL_ENVIRONMENTS and facts.environment_kind is None:
                facts.environment_kind = node.environmentname
            if node.environmentname == "remark*":
                args = getattr(node, "nodeargd", None)
                if args is not None:
                    text_arg = "".join(str(arg) for arg in args.argnlist if arg is not None)
                    if text_arg:
                        facts.support_blocks.add(text_arg.strip("[]{}").lower())
        if isinstance(node, LatexMacroNode):
            name = node.macroname
            if name == "label":
                args = getattr(node, "nodeargd", None)
                if args is not None and args.argnlist:
                    facts.label = node_text(args.argnlist[0]).strip("{}")
            if name in {"iff", "Longleftrightarrow"}:
                facts.has_iff = True
            if name in {"implies", "Rightarrow"}:
                facts.has_implies = True
            if name == "forall":
                facts.has_forall = True
            if name == "exists":
                facts.has_exists = True
            if name in {"neg", "not", "nleq", "notin"}:
                facts.has_negation = True
        for child in getattr(node, "nodelist", []) or []:
            visit(child)

    for node in nodes:
        visit(node)
    return facts


def tree_sitter_extract(text: str) -> ExtractedFacts:
    facts = ExtractedFacts("tree_sitter_latex")
    if importlib.util.find_spec("tree_sitter") is None:
        facts.available = False
        facts.notes.append("tree_sitter is not installed")
        return facts
    if importlib.util.find_spec("tree_sitter_language_pack") is None:
        facts.available = False
        facts.notes.append("tree_sitter_language_pack is not installed")
        return facts
    from tree_sitter_language_pack import get_parser

    source = text.encode("utf-8")
    tree = get_parser("latex").parse(source)

    def text_for(node: Any) -> str:
        return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")

    def visit(node: Any) -> None:
        node_text = text_for(node)
        if node.type == "generic_environment":
            match = re.match(r"\\begin\{([^}]+)\}(?:\[([^\]]+)\])?", node_text)
            if match and match.group(1) in FORMAL_ENVIRONMENTS and facts.environment_kind is None:
                facts.environment_kind = match.group(1)
                facts.title = match.group(2)
        if node.type == "label_definition":
            match = re.search(r"\\label\{([^}]+)\}", node_text)
            if match:
                facts.label = match.group(1)
        if node.type == "displayed_equation":
            if re.search(r"\\iff|\\Longleftrightarrow", node_text):
                facts.has_iff = True
            if re.search(r"\\implies|\\Rightarrow", node_text):
                facts.has_implies = True
            if re.search(r"\\forall|\\\(forall", node_text):
                facts.has_forall = True
            if re.search(r"\\exists|\\\(exists", node_text):
                facts.has_exists = True
            if re.search(r"\\neg|\\not|\\nleq|\\notin", node_text):
                facts.has_negation = True
            facts.predicates.update(predicate_operator_names(node_text))
        for child in node.children:
            visit(child)

    visit(tree.root_node)
    return facts


def walk_ast(node: Any):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk_ast(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk_ast(value)


def artifact_facts(data: dict[str, Any]) -> ExtractedFacts:
    facts = ExtractedFacts("semantic_artifact")
    identity = data.get("identity") or {}
    facts.label = identity.get("label")
    facts.environment_kind = identity.get("kind")
    facts.title = identity.get("title")
    for node in walk_ast(data):
        if not isinstance(node, dict):
            continue
        kind = node.get("kind")
        facts.has_iff = facts.has_iff or kind == "iff"
        facts.has_implies = facts.has_implies or kind == "implies"
        facts.has_forall = facts.has_forall or kind == "forall"
        facts.has_exists = facts.has_exists or kind in {"exists", "exists_unique"}
        facts.has_negation = facts.has_negation or kind == "not"
        if kind == "predicate" and node.get("predicate_id"):
            facts.predicates.add(normalized_token(str(node["predicate_id"]).split(":", 1)[-1]))
    for section in ("failure_analysis", "semantics", "exposition"):
        text = json.dumps(data.get(section) or {})
        facts.predicates.update(
            normalized_token(item)
            for item in predicate_operator_names(text)
        )
    reading = (data.get("logical_forms") or {}).get("predicate_reading") or {}
    facts.predicates.update(
        normalized_token(str(item).split(":", 1)[-1])
        for item in reading.get("registry_predicates", []) or []
    )
    for section in ("dependency_edges", "ontology_edges", "provenance_edges", "proof_edges"):
        for edge in (data.get("relationships") or {}).get(section, []) or []:
            if isinstance(edge, dict) and edge.get("target"):
                facts.dependencies.add(str(edge["target"]))
    return facts


def normalized_predicates(predicates: set[str]) -> set[str]:
    return {normalized_token(item) for item in predicates}


def alias_satisfied(alias: dict[str, Any], artifact: ExtractedFacts, artifact_data: dict[str, Any]) -> bool:
    normalized = normalized_token(str(alias.get("normalized_name") or ""))
    normalized_id = normalized_token(str(alias.get("normalized_predicate") or "").split(":", 1)[-1])
    if normalized in artifact.predicates or normalized_id in artifact.predicates:
        return True
    text_by_field = {
        "failure_analysis": json.dumps(artifact_data.get("failure_analysis") or {}),
        "logical_forms": json.dumps(artifact_data.get("logical_forms") or {}),
        "semantics": json.dumps(artifact_data.get("semantics") or {}),
        "exposition": json.dumps(artifact_data.get("exposition") or {}),
    }
    needles = [str(alias.get("normalized_name") or ""), *(alias.get("normalized_surface_forms") or [])]
    for allowed in alias.get("allowed_fields", []) or []:
        top = str(allowed).split(".", 1)[0]
        haystack = text_by_field.get(top, "")
        if any(needle and needle in haystack for needle in needles):
            return True
    return False


def compare(
    source_facts: list[ExtractedFacts],
    artifact: ExtractedFacts,
    artifact_data: dict[str, Any],
    aliases: dict[str, dict[str, Any]],
) -> tuple[str, list[Finding]]:
    findings: list[Finding] = []
    available = [facts for facts in source_facts if facts.available]
    if len(available) < 2:
        findings.append(
            Finding(
                "INSUFFICIENT_INDEPENDENT_EXTRACTORS",
                "warning",
                "Fewer than two independent source extractors were available.",
                "extractors",
            )
        )

    for facts in available:
        for field_name in ("label", "environment_kind"):
            expected = getattr(artifact, field_name)
            actual = getattr(facts, field_name)
            if actual and expected and actual != expected:
                findings.append(
                    Finding(
                        "SOURCE_ARTIFACT_FACT_MISMATCH",
                        "error",
                        f"{facts.extractor} found {field_name}={actual!r}, but artifact has {expected!r}.",
                        field_name,
                    )
                )
        for flag in ("has_iff", "has_implies", "has_forall", "has_exists", "has_negation"):
            if getattr(facts, flag) and not getattr(artifact, flag):
                findings.append(
                    Finding(
                        "SOURCE_LOGICAL_CUE_MISSING_FROM_AST",
                        "error",
                        f"{facts.extractor} found {flag}, but artifact AST does not expose it.",
                        flag,
                    )
                )
        source_predicates = normalized_predicates(facts.predicates)
        missing_predicates = source_predicates - artifact.predicates
        unresolved_missing: set[str] = set()
        for predicate in missing_predicates:
            alias = aliases.get(predicate)
            if alias and alias_satisfied(alias, artifact, artifact_data):
                continue
            unresolved_missing.add(predicate)
        if unresolved_missing:
            findings.append(
                Finding(
                    "SOURCE_PREDICATE_MISSING_FROM_AST",
                    "error",
                    f"{facts.extractor} found predicate(s) absent from artifact AST or governed aliases: {', '.join(sorted(unresolved_missing))}.",
                    "predicates",
                )
            )

    severity = {finding.severity for finding in findings}
    if "error" in severity:
        return "fail", findings
    if "warning" in severity:
        return "pass_with_warnings", findings
    return "pass", findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-tex", required=True, type=Path)
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--target-label", help="Limit source extraction to the block containing this label.")
    parser.add_argument(
        "--alias-registry",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "semantic-aliases.yaml",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=("yaml", "json"), default="yaml")
    args = parser.parse_args()

    try:
        source_text = args.source_tex.read_text(encoding="utf-8")
        source_text, source_scope = scoped_source_for_label(source_text, args.target_label)
        artifact_data = load_mapping(args.artifact)
        aliases = load_aliases(args.alias_registry)
        source_facts = [
            surface_regex_extract(source_text),
            displayed_math_extract(source_text),
            pylatexenc_extract(source_text),
            tree_sitter_extract(source_text),
        ]
        artifact = artifact_facts(artifact_data)
        status, findings = compare(source_facts, artifact, artifact_data, aliases)
        payload = {
            "schema_version": "lra.semantic-ast-extractor-comparison/1.0",
            "result": status,
            "alias_registry": str(args.alias_registry) if args.alias_registry else None,
            "source_scope": source_scope,
            "source_extractors": [facts.as_json() for facts in source_facts],
            "artifact_facts": artifact.as_json(),
            "findings": [finding.as_json() for finding in findings],
        }
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    text = json.dumps(payload, indent=2) + "\n" if args.format == "json" else yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if status in {"pass", "pass_with_warnings"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
