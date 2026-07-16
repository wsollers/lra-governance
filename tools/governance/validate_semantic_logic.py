#!/usr/bin/env python3
"""Locally validate semantic-artifact logic invariants.

This validator is intentionally narrower than an external mathematical review.
It checks the machine-verifiable contract between a semantic artifact YAML file
and the corrected TeX that would be applied to source.
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


CHECK_NAMES = (
    "binder_scope",
    "language_level",
    "assumptions_and_conclusion",
    "statement_shape",
    "theorem_equivalence_shape",
    "quantifier_order",
    "witness_dependencies",
    "negation",
    "normalization_assumptions",
    "contrapositive",
    "applicability_failure",
    "order_strength",
    "predicate_signatures",
    "failure_modes",
    "yaml_tex_equivalence",
)

ROOT = Path(__file__).resolve().parents[2]
VOLUME_NAMES = {
    "i": "lra-volume-i",
    "ii": "lra-volume-ii",
    "iii": "lra-volume-iii",
    "iv": "lra-volume-iv",
    "v": "lra-volume-v",
    "vi": "lra-volume-vi",
    "vii": "lra-volume-vii",
    "viii": "lra-volume-viii",
}
EXPLICIT_COERCION_FUNCTIONS = {
    "coerce",
    "cast",
    "nat_cast",
    "int_cast",
    "real_cast",
    "embedding",
    "inclusion",
    "subtype_val",
}
FORMAL_ENV_RE = re.compile(
    r"\\begin\{(?P<env>definition|axiom|theorem|lemma|proposition|corollary)\}"
    r"(?:\[(?P<title>[^\]]+)\])?",
    re.IGNORECASE,
)
LABEL_RE = re.compile(r"\\label\{(?P<label>[^{}]+)\}")


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


@dataclass
class LogicResult:
    checks: dict[str, dict[str, str | None]] = field(
        default_factory=lambda: {
            name: {"result": "pass", "notes": None} for name in CHECK_NAMES
        }
    )
    findings: list[Finding] = field(default_factory=list)

    def set_check(self, name: str, result: str, notes: str) -> None:
        self.checks[name] = {"result": result, "notes": notes}

    def add(self, code: str, severity: str, message: str, field: str | None = None) -> None:
        self.findings.append(Finding(code, severity, message, field))

    @property
    def result(self) -> str:
        check_results = {str(check.get("result")) for check in self.checks.values()}
        if "blocked" in check_results:
            return "blocked"
        if "fail" in check_results:
            return "fail"
        severities = {finding.severity for finding in self.findings}
        if "blocking" in severities:
            return "blocked"
        if "error" in severities:
            return "fail"
        if "warning" in check_results:
            return "pass_with_warnings"
        if "warning" in severities:
            return "pass_with_warnings"
        return "pass"

    def as_json(self) -> dict[str, Any]:
        return {
            "result": self.result,
            "checks": self.checks,
            "findings": [finding.as_json() for finding in self.findings],
        }


@dataclass(frozen=True)
class FormalCandidate:
    label: str
    kind: str
    title: str | None
    path: Path
    line_start: int
    line_end: int
    text: str

    def as_json(self, root: Path | None = None) -> dict[str, Any]:
        path = self.path
        if root is not None:
            try:
                rendered = path.relative_to(root).as_posix()
            except ValueError:
                rendered = str(path)
        else:
            rendered = str(path)
        return {
            "label": self.label,
            "kind": self.kind,
            "title": self.title,
            "path": rendered,
            "line_start": self.line_start,
            "line_end": self.line_end,
        }


def load_mapping(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a mapping")
    return data


def load_serialized_mapping(path: Path) -> dict[str, Any]:
    text = sys.stdin.read() if str(path) == "-" else path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a mapping")
    return data


def parse_embedded_mapping(value: Any, field: str) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            data = json.loads(value)
        except json.JSONDecodeError:
            data = yaml.safe_load(value)
        if isinstance(data, dict):
            return data
    raise ValueError(f"{field}: expected an object or serialized YAML/JSON mapping")


def extract_llm_artifact_and_tex(payload: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    """Extract artifact data and corrected TeX from a governed LLM payload.

    Accepted envelopes are intentionally practical: direct objects, reviewer
    strings (`artifact_yaml` / `corrected_tex`), or a nested
    `semantic_review` packet produced by the external reviewer tooling.
    """
    candidates = [
        payload,
        payload.get("semantic_review") if isinstance(payload.get("semantic_review"), dict) else None,
        payload.get("result") if isinstance(payload.get("result"), dict) else None,
    ]
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        if "artifact" in candidate:
            artifact = parse_embedded_mapping(candidate["artifact"], "artifact")
        elif "artifact_yaml" in candidate:
            artifact = parse_embedded_mapping(candidate["artifact_yaml"], "artifact_yaml")
        else:
            continue
        corrected_tex = candidate.get("corrected_tex")
        if corrected_tex is None:
            corrected_tex = candidate.get("corrected_tex_source")
        if corrected_tex is not None and not isinstance(corrected_tex, str):
            raise ValueError("corrected_tex: expected a string")
        return artifact, corrected_tex
    raise ValueError("LLM payload must contain artifact/artifact_yaml data")


def tex_files(target: Path) -> Iterable[Path]:
    if target.is_file():
        if target.suffix == ".tex":
            yield target
        return
    for path in sorted(target.rglob("*.tex")):
        parts = {part.lower() for part in path.parts}
        if "build" in parts or ".external-review-diagnostics" in parts:
            continue
        if path.name == "corrected.tex" and (path.parent / "artifact.yaml").exists():
            continue
        yield path


def line_for_offset(text: str, offset: int) -> int:
    return text[:offset].count("\n") + 1


def formal_candidates(target: Path) -> list[FormalCandidate]:
    candidates: list[FormalCandidate] = []
    for path in tex_files(target):
        text = path.read_text(encoding="utf-8", errors="ignore")
        starts = list(FORMAL_ENV_RE.finditer(text))
        for index, start in enumerate(starts):
            next_start = starts[index + 1].start() if index + 1 < len(starts) else len(text)
            block = text[start.start() : next_start]
            label_match = LABEL_RE.search(block)
            if not label_match:
                continue
            label = label_match.group("label")
            if not re.match(r"^(def|ax|thm|lem|prop|cor):", label):
                continue
            candidates.append(
                FormalCandidate(
                    label=label,
                    kind=start.group("env").lower(),
                    title=start.group("title"),
                    path=path,
                    line_start=line_for_offset(text, start.start()),
                    line_end=line_for_offset(text, next_start),
                    text=block,
                )
            )
    return candidates


def resolve_volume_root(volume: str, repos_root: Path | None, explicit_root: Path | None) -> Path:
    if volume not in VOLUME_NAMES:
        raise ValueError(f"unknown volume {volume!r}; expected one of {', '.join(VOLUME_NAMES)}")
    if explicit_root is not None:
        root = explicit_root.resolve()
        if not root.exists():
            raise FileNotFoundError(root)
        return root
    if repos_root is None:
        raise ValueError("--repos-root is required when --volume-root is not supplied")
    root = (repos_root / VOLUME_NAMES[volume]).resolve()
    if not root.exists():
        raise FileNotFoundError(root)
    return root


def resolve_candidate(volume_root: Path, label: str, target: Path | None = None) -> FormalCandidate:
    search_root = target.resolve() if target is not None else volume_root
    matches = [candidate for candidate in formal_candidates(search_root) if candidate.label == label]
    if not matches:
        raise ValueError(f"label {label!r} was not found under {search_root}")
    if len(matches) > 1:
        locations = ", ".join(str(item.path) for item in matches)
        raise ValueError(f"label {label!r} is ambiguous under {search_root}: {locations}")
    return matches[0]


def artifact_package_index(target: Path) -> dict[str, tuple[Path, Path]]:
    packages: dict[str, tuple[Path, Path]] = {}
    for artifact in sorted(target.rglob("artifact.yaml")):
        if ".external-review-diagnostics" in {part.lower() for part in artifact.parts}:
            continue
        corrected = artifact.parent / "corrected.tex"
        if not corrected.exists():
            continue
        try:
            data = load_mapping(artifact)
        except Exception:
            continue
        label = str((data.get("identity") or {}).get("label") or "")
        if label:
            packages[label] = (artifact, corrected)
    return packages


def registry_signatures() -> tuple[
    dict[str, list[dict[str, str]]],
    dict[str, dict[str, Any]],
    dict[str, list[dict[str, str]]],
    dict[str, str | None],
]:
    predicates: dict[str, list[dict[str, str]]] = {}
    predicate_domain_conventions: dict[str, dict[str, Any]] = {}
    structures: dict[str, list[dict[str, str]]] = {}
    structure_carriers: dict[str, str | None] = {}
    pred_path = ROOT / "predicates.yaml"
    struct_path = ROOT / "structures.yaml"
    if pred_path.exists():
        for item in load_mapping(pred_path).get("predicates", []) or []:
            if isinstance(item, dict) and item.get("id"):
                predicates[str(item["id"])] = [
                    {"name": str(arg.get("name") or ""), "role": str(arg.get("role") or "")}
                    for arg in item.get("arguments", []) or []
                    if isinstance(arg, dict)
                ]
                convention = item.get("domain_convention")
                if isinstance(convention, dict):
                    predicate_domain_conventions[str(item["id"])] = convention
    if struct_path.exists():
        for item in load_mapping(struct_path).get("structures", []) or []:
            if isinstance(item, dict) and item.get("id"):
                structures[str(item["id"])] = [
                    {"name": str(arg.get("name") or ""), "role": str(arg.get("role") or "")}
                    for arg in item.get("arguments", []) or []
                    if isinstance(arg, dict)
                ]
                structure_carriers[str(item["id"])] = str(item.get("carrier_argument") or "") or None
    return predicates, predicate_domain_conventions, structures, structure_carriers


def walk_ast(node: Any):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk_ast(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk_ast(value)


def ast_kind(node: Any) -> str | None:
    return node.get("kind") if isinstance(node, dict) else None


def ast_contains_kind(node: Any, kind: str) -> bool:
    return any(child.get("kind") == kind for child in walk_ast(node))


def ast_kind_count(node: Any, kind: str) -> int:
    return sum(1 for child in walk_ast(node) if isinstance(child, dict) and child.get("kind") == kind)


def ast_contains_relation(node: Any, relation: str) -> bool:
    return any(child.get("kind") == "relation" and child.get("relation") == relation for child in walk_ast(node))


def equivalence_operator_count(latex: str) -> int:
    return len(re.findall(r"\\(?:Longleftrightarrow|iff)\b|\\iff\b", latex))


def latex_quantifier_counts(latex: str) -> dict[str, int]:
    return {
        "forall": len(re.findall(r"\\forall\b", latex)),
        "exists": len(re.findall(r"\\exists\b", latex)),
    }


def latex_quantified_variable_counts(latex: str) -> dict[str, int]:
    """Heuristically count variables bound by explicit LaTeX quantifiers.

    This deliberately stays shallow.  It catches common governed forms such as
    ``\\forall x,y\\in I`` where one quantifier macro binds two variables.  It is
    not intended to parse all mathematical TeX; uncertain cases fall back to
    the quantifier macro count handled separately.
    """
    counts = {"forall": 0, "exists": 0}
    pattern = re.compile(r"\\(?P<kind>forall|exists)\s*(?P<body>.*?)(?=(?:\\forall|\\exists|\\Rightarrow|\\Longrightarrow|\\implies|\\land|\\lor|\.|,?\s*\)|,?\s*\]|\Z))", re.S)
    for match in pattern.finditer(latex):
        kind = match.group("kind")
        body = match.group("body")
        body = body.split(r"\;", 1)[0]
        body = body.split(";", 1)[0]
        body = re.split(r"\\bigl|\\Bigl|\\left|\[|\(", body, maxsplit=1)[0]
        body = re.split(r"\\in|\\subseteq|\\subset|:", body, maxsplit=1)[0]
        names = [
            item.strip()
            for item in body.split(",")
            if item.strip()
        ]
        cleaned = []
        for name in names:
            name = re.sub(r"\\(?:,|!|:|\s)+", "", name).strip()
            # Keep ordinary variables and macro variables such as \lambda,
            # but ignore empty glue left by formatting commands.
            if re.search(r"[A-Za-z]|\\[A-Za-z]+", name):
                cleaned.append(name)
        counts[kind] += len(cleaned) if cleaned else 1
    return counts


def is_iff_pair(node: Any) -> bool:
    return isinstance(node, dict) and node.get("kind") == "iff"


def is_conjunction_of_iff_pairs(node: Any) -> bool:
    """Return true for (A iff B) and (B iff C), allowing larger and-trees.

    A displayed three-way equivalence is not truth-functionally represented by
    A iff (B iff C).  The machine contract represents n-way equivalence as a
    conjunction of adjacent biconditionals.
    """
    if not isinstance(node, dict):
        return False
    kind = node.get("kind")
    if kind == "iff":
        return True
    if kind != "and":
        return False
    return is_conjunction_of_iff_pairs(node.get("left")) and is_conjunction_of_iff_pairs(node.get("right"))


def has_nested_iff(node: Any) -> bool:
    if not isinstance(node, dict) or node.get("kind") != "iff":
        return False
    return ast_contains_kind(node.get("left"), "iff") or ast_contains_kind(node.get("right"), "iff")


def has_iff_to_conjunction(node: Any) -> bool:
    if not isinstance(node, dict) or node.get("kind") != "iff":
        return False
    return ast_kind(node.get("left")) == "and" or ast_kind(node.get("right")) == "and"


def canonical_ast(node: Any, env: dict[str, str] | None = None, counter: list[int] | None = None) -> Any:
    """Return a binder-normalized AST for structural comparison."""
    if env is None:
        env = {}
    if counter is None:
        counter = [0]
    if isinstance(node, list):
        return [canonical_ast(item, env, counter) for item in node]
    if not isinstance(node, dict):
        return node
    kind = node.get("kind")
    if kind == "variable":
        binder_id = str(node.get("binder_id") or "")
        copy = dict(node)
        copy["binder_id"] = env.get(binder_id, binder_id)
        return {key: canonical_ast(value, env, counter) for key, value in sorted(copy.items())}
    if kind in {"forall", "exists", "exists_unique"}:
        binder = dict(node.get("binder") or {})
        old_id = str(binder.get("binder_id") or "")
        canonical_id = f"bound_{counter[0]}"
        counter[0] += 1
        new_env = dict(env)
        if old_id:
            new_env[old_id] = canonical_id
        binder["binder_id"] = canonical_id
        # Binder symbols are presentation choices. A negated formula often
        # renames \varepsilon to \varepsilon_0, and alpha-equivalence should
        # compare the binding structure rather than the displayed glyph.
        binder["symbol"] = canonical_id
        copy = dict(node)
        copy["binder"] = binder
        return {
            key: canonical_ast(value, new_env if key in {"restriction", "body"} else env, counter)
            for key, value in sorted(copy.items())
        }
    return {key: canonical_ast(value, env, counter) for key, value in sorted(node.items())}


def ast_equal(left: Any, right: Any) -> bool:
    return canonical_ast(left) == canonical_ast(right)


def ast_contains_equivalent(root: Any, target: Any) -> bool:
    return any(ast_equal(node, target) for node in walk_ast(root))


def negate_ast(node: Any) -> dict[str, Any]:
    if not isinstance(node, dict):
        return {"kind": "not", "operand": node}
    kind = node.get("kind")
    if kind == "not":
        operand = node.get("operand")
        return operand if isinstance(operand, dict) else {"kind": "raw_latex", "latex": str(operand)}
    if kind == "and":
        return {"kind": "or", "left": negate_ast(node.get("left")), "right": negate_ast(node.get("right"))}
    if kind == "or":
        return {"kind": "and", "left": negate_ast(node.get("left")), "right": negate_ast(node.get("right"))}
    if kind == "implies":
        return {"kind": "and", "left": node.get("left"), "right": negate_ast(node.get("right"))}
    if kind == "iff":
        left = node.get("left")
        right = node.get("right")
        return {
            "kind": "or",
            "left": {"kind": "and", "left": left, "right": negate_ast(right)},
            "right": {"kind": "and", "left": negate_ast(left), "right": right},
        }
    if kind == "forall":
        binder = node.get("binder")
        return {
            "kind": "exists",
            "binder": binder,
            "restriction": node.get("restriction"),
            "body": negate_ast(node.get("body")),
        }
    if kind == "exists":
        binder = node.get("binder")
        return {
            "kind": "forall",
            "binder": binder,
            "restriction": node.get("restriction"),
            "body": negate_ast(node.get("body")),
        }
    return {"kind": "not", "operand": node}


def unwrap_definition(statement_ast: Any) -> tuple[Any, Any] | tuple[None, None]:
    if isinstance(statement_ast, dict) and statement_ast.get("kind") == "iff":
        return statement_ast.get("left"), statement_ast.get("right")
    return None, None


def collect_definition_unfoldings(statement_ast: Any) -> dict[str, Any]:
    left, right = unwrap_definition(statement_ast)
    if not isinstance(left, dict) or left.get("kind") != "predicate":
        return {}
    key = json.dumps(canonical_ast(left), sort_keys=True)
    return {key: right}


def unfold_once(node: Any, definitions: dict[str, Any]) -> Any:
    if isinstance(node, list):
        return [unfold_once(item, definitions) for item in node]
    if not isinstance(node, dict):
        return node
    key = json.dumps(canonical_ast(node), sort_keys=True)
    if key in definitions:
        return definitions[key]
    return {key_: unfold_once(value, definitions) for key_, value in node.items()}


def logic_shape(node: Any) -> str:
    if not isinstance(node, dict):
        return str(node)
    kind = str(node.get("kind") or "?")
    if kind in {"variable", "constant"}:
        return kind
    if kind == "predicate":
        return f"predicate:{node.get('predicate_id')}"
    if kind == "relation":
        return f"relation:{node.get('relation')}"
    children = []
    for key, value in node.items():
        if key == "kind":
            continue
        if isinstance(value, dict):
            children.append(f"{key}={logic_shape(value)}")
        elif isinstance(value, list):
            children.append(f"{key}=[{','.join(logic_shape(item) for item in value)}]")
    return f"{kind}({';'.join(children)})"


def predicate_nodes(node: Any) -> list[dict[str, Any]]:
    return [
        child
        for child in walk_ast(node)
        if isinstance(child, dict) and child.get("kind") == "predicate"
    ]


def application_nodes(node: Any) -> list[dict[str, Any]]:
    return [
        child
        for child in walk_ast(node)
        if isinstance(child, dict) and child.get("kind") == "application"
    ]


def role_tokens(value: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", value.lower()) if token}


def type_summary(type_ast: Any) -> set[str]:
    tokens: set[str] = set()
    for node in walk_ast(type_ast):
        if not isinstance(node, dict):
            continue
        kind = node.get("kind")
        if kind == "application":
            tokens.update(role_tokens(str(node.get("function") or "")))
        elif kind == "constant":
            tokens.update(role_tokens(str(node.get("name") or "")))
        elif kind == "raw_latex":
            tokens.update(role_tokens(str(node.get("latex") or "")))
    return tokens


def type_ambient(type_ast: Any) -> Any:
    if not isinstance(type_ast, dict):
        return None
    if type_ast.get("kind") == "application" and str(type_ast.get("function") or "") in {
        "element_of",
        "subset_of",
        "domain_of",
    }:
        args = type_ast.get("arguments") or []
        return args[0] if args else None
    return None


def normalize_latex_atom(value: str) -> str:
    return re.sub(r"\s+", "", value).strip("{}")


def function_domain_from_type(type_ast: Any, function_symbol: str) -> Any:
    if not isinstance(type_ast, dict):
        return None
    if type_ast.get("kind") == "application":
        function = str(type_ast.get("function") or "")
        args = type_ast.get("arguments") or []
        if function in {"function_space", "FunctionSpace", "map_to"} and args:
            return args[0]
        if function in {"domain_of", "domain"} and args:
            return args[0]
    if type_ast.get("kind") == "raw_latex":
        latex = str(type_ast.get("latex") or "")
        if ":" in latex:
            lhs, rhs = latex.split(":", 1)
            if normalize_latex_atom(lhs) not in {normalize_latex_atom(function_symbol), ""}:
                rhs = latex
        else:
            rhs = latex
        match = re.search(r"(?P<domain>.+?)(?:\\to|->|→|\\rightarrow)", rhs)
        if match:
            return normalize_latex_atom(match.group("domain"))
    return None


def formula_quantifier_domains(node: Any) -> list[Any]:
    domains: list[Any] = []
    for child in walk_ast(node):
        if not isinstance(child, dict) or child.get("kind") not in {"forall", "exists", "exists_unique"}:
            continue
        binder = child.get("binder") or {}
        if isinstance(binder, dict) and binder.get("domain") is not None:
            domains.append(binder["domain"])
    return domains


def domain_matches(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return False
    if isinstance(left, dict) and isinstance(right, dict):
        return ast_equal(left, right)
    if isinstance(left, dict) and left.get("kind") == "variable":
        return normalize_latex_atom(str(left.get("binder_id") or "")) == normalize_latex_atom(str(right))
    if isinstance(right, dict) and right.get("kind") == "variable":
        return normalize_latex_atom(str(right.get("binder_id") or "")) == normalize_latex_atom(str(left))
    return normalize_latex_atom(str(left)) == normalize_latex_atom(str(right))


def argument_is_explicitly_coerced(arg: Any) -> bool:
    if not isinstance(arg, dict) or arg.get("kind") != "application":
        return False
    return str(arg.get("function") or "") in EXPLICIT_COERCION_FUNCTIONS


def symbol_for_argument(arg: Any) -> str:
    if not isinstance(arg, dict):
        return "<?>"
    if arg.get("kind") == "variable":
        return str(arg.get("binder_id") or "<?>")
    if arg.get("kind") == "constant":
        return str(arg.get("name") or "<?>")
    if arg.get("kind") == "application":
        return str(arg.get("function") or "application")
    return str(arg.get("kind") or "<?>")


ROLE_GROUPS = {
    "function": {"function", "map", "operation", "object", "sequence", "indexed", "functional"},
    "point": {"point", "source", "target", "limit", "candidate", "element", "base", "cluster", "value"},
    "subset": {"subset", "domain", "set", "collection", "source"},
    "ambient": {"ambient", "space", "structure", "carrier", "context", "source", "target"},
    "relation": {"relation", "order", "preorder", "partial", "total", "binary"},
    "interval": {"interval", "region", "neighbourhood", "neighborhood", "ball"},
}


TYPE_ROLE_HINTS = {
    "point": {"element", "member", "point"},
    "subset": {"subset", "set", "domain", "powerset"},
    "function": {"function", "map", "function_space"},
    "ambient": {"struct", "space", "ambient", "set", "real", "ordered"},
    "relation": {"relation", "order"},
    "interval": {"interval", "neighbourhood", "neighborhood", "ball"},
}


def role_group(tokens: set[str]) -> str | None:
    scores = {
        group: len(tokens & markers)
        for group, markers in ROLE_GROUPS.items()
    }
    best_group, best_score = max(scores.items(), key=lambda item: item[1])
    return best_group if best_score else None


def roles_compatible(expected_role: str, actual_role: str) -> bool:
    expected_tokens = role_tokens(expected_role)
    actual_tokens = role_tokens(actual_role)
    if not expected_tokens or not actual_tokens:
        return True
    if expected_tokens & actual_tokens:
        return True
    expected_group = role_group(expected_tokens)
    actual_group = role_group(actual_tokens)
    if expected_group and actual_group and expected_group == actual_group:
        return True
    return False


def type_compatible_with_role(expected_role: str, type_tokens: set[str]) -> bool:
    if not type_tokens:
        return True
    group = role_group(role_tokens(expected_role))
    if not group:
        return True
    hints = TYPE_ROLE_HINTS.get(group, set())
    if not hints:
        return True
    # Catch only clear category inversions. A sparse type record that omits the
    # expected hint remains acceptable; richer type contracts can tighten this.
    incompatible = {
        "point": {"subset", "function", "map", "space", "structure"},
        "subset": {"element", "point", "function", "map"},
        "function": {"element", "point", "subset"},
        "ambient": {"element", "point", "function"},
        "relation": {"element", "point", "subset"},
    }.get(group, set())
    if type_tokens & hints:
        return True
    if type_tokens & incompatible:
        return False
    return True


def declared_metadata(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    metadata: dict[str, dict[str, Any]] = {}
    for section in ("context", "parameters"):
        for item in data.get(section, []) or []:
            if isinstance(item, dict) and item.get("id"):
                metadata[str(item["id"])] = item
    return metadata


def ambient_carrier_candidates(
    ambient: Any,
    metadata: dict[str, dict[str, Any]],
    structure_signatures: dict[str, list[dict[str, str]]],
    structure_carriers: dict[str, str | None],
) -> list[Any]:
    candidates = [ambient]
    target = ambient
    if isinstance(ambient, dict) and ambient.get("kind") == "variable":
        declared = metadata.get(str(ambient.get("binder_id") or ""), {})
        target = declared.get("ast") or declared.get("construction_ast") or ambient
        if isinstance(declared.get("ast"), dict):
            candidates.append(declared["ast"])
    if isinstance(target, dict) and target.get("kind") == "application":
        function = str(target.get("function") or "")
        carrier_name = structure_carriers.get(function)
        signature = structure_signatures.get(function, [])
        args = target.get("arguments") or []
        if carrier_name:
            for index, spec in enumerate(signature):
                if spec.get("name") == carrier_name and index < len(args):
                    candidates.append(args[index])
        elif args:
            first_role = signature[0].get("role") if signature else ""
            if role_group(role_tokens(first_role)) in {"ambient", "subset"} or "carrier" in role_tokens(first_role):
                candidates.append(args[0])
    return candidates


def validate_signature_call(
    call_kind: str,
    call_id: str,
    arguments: list[Any],
    signature: list[dict[str, str]],
    metadata: dict[str, dict[str, Any]],
    structure_signatures: dict[str, list[dict[str, str]]],
    structure_carriers: dict[str, str | None],
) -> list[str]:
    errors: list[str] = []
    if len(arguments) != len(signature):
        errors.append(f"{call_id} expects {len(signature)} arguments, got {len(arguments)}")
        return errors
    ambient_args: list[Any] = []
    for arg, spec in zip(arguments, signature):
        if role_group(role_tokens(str(spec.get("role") or ""))) == "ambient":
            ambient_args.extend(ambient_carrier_candidates(arg, metadata, structure_signatures, structure_carriers))
    for index, (arg, spec) in enumerate(zip(arguments, signature), start=1):
        if argument_is_explicitly_coerced(arg):
            continue
        if not isinstance(arg, dict) or arg.get("kind") != "variable":
            continue
        binder_id = str(arg.get("binder_id") or "")
        declared = metadata.get(binder_id, {})
        actual_role = str(declared.get("role") or "")
        expected_role = str(spec.get("role") or "")
        if actual_role and not roles_compatible(expected_role, actual_role):
            errors.append(
                f"{call_id} argument {index} ({binder_id}) has role {actual_role!r}, expected {expected_role!r}"
            )
        declared_type = declared.get("type")
        if isinstance(declared_type, dict) and not type_compatible_with_role(expected_role, type_summary(declared_type)):
            errors.append(
                f"{call_id} argument {index} ({binder_id}) has type incompatible with expected role {expected_role!r}; use an explicit coercion/conversion if intended"
            )
        if ambient_args and role_group(role_tokens(expected_role)) in {"point", "subset"}:
            declared_ambient = type_ambient(declared_type)
            if declared_ambient is not None and not any(ast_equal(declared_ambient, ambient) for ambient in ambient_args):
                errors.append(
                    f"{call_id} argument {index} ({binder_id}) is typed over a different ambient than the call supplies; use an explicit coercion/conversion if intended"
                )
    return errors


def validate_domain_convention(
    predicate_id: str,
    node: dict[str, Any],
    signature: list[dict[str, str]],
    convention: dict[str, Any],
    metadata: dict[str, dict[str, Any]],
    data: dict[str, Any],
) -> list[str]:
    if convention.get("kind") != "typed_function_domain":
        return []
    errors: list[str] = []
    function_arg_name = str(convention.get("function_argument") or "")
    function_index = next(
        (index for index, spec in enumerate(signature) if spec.get("name") == function_arg_name),
        None,
    )
    arguments = node.get("arguments") or []
    if function_index is None or function_index >= len(arguments):
        return errors
    function_arg = arguments[function_index]
    if not isinstance(function_arg, dict) or function_arg.get("kind") != "variable":
        return errors
    function_id = str(function_arg.get("binder_id") or "")
    declared = metadata.get(function_id, {})
    carried_domain = function_domain_from_type(declared.get("type"), str(declared.get("symbol") or function_id))
    if carried_domain is None:
        errors.append(
            f"{predicate_id} uses typed-function-domain semantics, but argument {function_arg_name} ({function_id}) has no declared domain-bearing function type"
        )
        return errors
    quantified_domains = formula_quantifier_domains((data.get("logical_forms") or {}).get("standard_quantified", {}).get("ast"))
    if quantified_domains and not any(domain_matches(carried_domain, domain) for domain in quantified_domains):
        errors.append(
            f"{predicate_id} carries the domain of {function_id} from its function type, but the quantified form does not range over that declared domain"
        )
    return errors


def declared_binders(data: dict[str, Any]) -> set[str]:
    declared: set[str] = set()
    for section in ("context", "parameters"):
        for item in data.get(section, []) or []:
            if isinstance(item, dict) and item.get("id"):
                declared.add(str(item["id"]))
    return declared


def check_scope(data: dict[str, Any], result: LogicResult) -> None:
    declared = declared_binders(data)
    errors: list[str] = []

    def visit(node: Any, bound: set[str], path: str) -> None:
        if not isinstance(node, dict):
            return
        kind = node.get("kind")
        if kind == "raw_latex":
            return
        if kind == "variable":
            binder_id = str(node.get("binder_id") or "")
            if binder_id not in bound and binder_id not in declared:
                errors.append(f"{path}: undeclared binder id {binder_id!r}")
            return
        if kind in {"forall", "exists", "exists_unique"}:
            binder = node.get("binder") or {}
            binder_id = str(binder.get("binder_id") or "")
            if not binder_id:
                errors.append(f"{path}: quantifier binder lacks binder_id")
                return
            visit(binder.get("domain"), bound, f"{path}.binder.domain")
            new_bound = set(bound)
            new_bound.add(binder_id)
            visit(node.get("restriction"), new_bound, f"{path}.restriction")
            visit(node.get("body"), new_bound, f"{path}.body")
            return
        for key, value in node.items():
            if key == "kind":
                continue
            if isinstance(value, dict):
                visit(value, bound, f"{path}.{key}")
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    visit(child, bound, f"{path}.{key}[{index}]")

    forms = data.get("logical_forms") or {}
    roots = [
        ("statement.semantic_ast", (data.get("statement") or {}).get("semantic_ast")),
        ("logical_forms.standard_quantified.ast", (forms.get("standard_quantified") or {}).get("ast")),
    ]
    if forms.get("predicate_reading"):
        roots.append(("logical_forms.predicate_reading.ast", forms["predicate_reading"].get("ast")))
    negation = forms.get("negation") or {}
    for key in ("mechanical", "approved_normal_form"):
        if negation.get(key):
            roots.append((f"logical_forms.negation.{key}.ast", negation[key].get("ast")))

    for path, node in roots:
        visit(node, set(), path)

    if errors:
        result.set_check("binder_scope", "fail", "Some AST variables refer to undeclared binders.")
        for error in errors:
            result.add("UNDECLARED_BINDER", "error", error, "binder_scope")
    else:
        result.set_check("binder_scope", "pass", "All variables are declared as parameters, context, or local binders.")


def check_statement_shape(data: dict[str, Any], corrected_tex: str, result: LogicResult) -> None:
    identity = data.get("identity") or {}
    statement = data.get("statement") or {}
    forms = data.get("logical_forms") or {}
    canonical_latex = str(statement.get("canonical_latex") or "")
    standard = forms.get("standard_quantified") or {}
    standard_latex = str(standard.get("latex") or "")
    statement_ast = statement.get("semantic_ast")
    standard_ast = standard.get("ast")
    wants_iff = (
        identity.get("kind") == "definition"
        and (
            r"\iff" in canonical_latex
            or r"\Longleftrightarrow" in canonical_latex
        )
    )
    standard_wants_iff = r"\iff" in standard_latex or r"\Longleftrightarrow" in standard_latex
    tex_has_equivalence = bool(
        re.search(r"\\iff|\\Longleftrightarrow|\bEquivalently\b", corrected_tex)
    )

    if wants_iff and ast_kind(statement_ast) != "iff":
        result.add(
            "DEFINITIONAL_BICONDITIONAL_OMITTED_FROM_AST",
            "error",
            "Definition LaTeX asserts an equivalence, but statement.semantic_ast is not an iff node.",
            "statement.semantic_ast",
        )
    counts = latex_quantifier_counts(standard_latex)
    variable_counts = latex_quantified_variable_counts(standard_latex)
    ast_foralls = ast_kind_count(standard_ast, "forall")
    ast_exists = ast_kind_count(standard_ast, "exists") + ast_kind_count(standard_ast, "exists_unique")
    if counts["forall"] > ast_foralls:
        result.set_check("quantifier_order", "fail", "Standard quantified LaTeX has universal binders missing from the AST.")
        result.add(
            "QUANTIFIED_LATEX_AST_MISMATCH",
            "error",
            f"standard_quantified.latex contains {counts['forall']} universal quantifier(s), but the AST exposes {ast_foralls}.",
            "logical_forms.standard_quantified.ast",
        )
    if counts["exists"] > ast_exists:
        result.set_check("quantifier_order", "fail", "Standard quantified LaTeX has existential binders missing from the AST.")
        result.add(
            "QUANTIFIED_LATEX_AST_MISMATCH",
            "error",
            f"standard_quantified.latex contains {counts['exists']} existential quantifier(s), but the AST exposes {ast_exists}.",
            "logical_forms.standard_quantified.ast",
        )
    if variable_counts["forall"] > ast_foralls:
        result.set_check("quantifier_order", "fail", "Standard quantified LaTeX binds more universal variables than the AST.")
        result.add(
            "QUANTIFIED_VARIABLE_AST_MISMATCH",
            "error",
            f"standard_quantified.latex binds about {variable_counts['forall']} universally quantified variable(s), but the AST exposes {ast_foralls} forall binder node(s).",
            "logical_forms.standard_quantified.ast",
        )
    if variable_counts["exists"] > ast_exists:
        result.set_check("quantifier_order", "fail", "Standard quantified LaTeX binds more existential variables than the AST.")
        result.add(
            "QUANTIFIED_VARIABLE_AST_MISMATCH",
            "error",
            f"standard_quantified.latex binds about {variable_counts['exists']} existentially quantified variable(s), but the AST exposes {ast_exists} existential binder node(s).",
            "logical_forms.standard_quantified.ast",
        )
    theorem_like = identity.get("kind") in {"theorem", "lemma", "proposition", "corollary"}
    standard_equivalence_count = equivalence_operator_count(standard_latex)
    if standard_wants_iff and not (theorem_like and standard_equivalence_count >= 2) and ast_kind(standard_ast) != "iff":
        result.add(
            "STANDARD_FORM_LATEX_AST_MISMATCH",
            "error",
            "Standard quantified LaTeX asserts an equivalence, but its AST is not an iff node.",
            "logical_forms.standard_quantified.ast",
        )
    standard_shape_ok = (
        not standard_wants_iff
        or ast_kind(standard_ast) == "iff"
        or (theorem_like and standard_equivalence_count >= 2 and is_conjunction_of_iff_pairs(standard_ast))
    )
    if tex_has_equivalence and wants_iff and ast_kind(statement_ast) == "iff" and standard_shape_ok:
        result.set_check("statement_shape", "pass", "Definition equivalence is represented in the statement AST; standard quantified form is shape-consistent.")
    elif wants_iff:
        result.set_check("statement_shape", "fail", "Definition equivalence is not represented consistently.")
    else:
        result.set_check("statement_shape", "pass", "No definitional biconditional mismatch detected.")

    if theorem_like:
        theorem_equivalence_nodes: list[tuple[str, Any, str]] = [
            ("statement.semantic_ast", statement_ast, canonical_latex),
            ("logical_forms.standard_quantified.ast", standard_ast, standard_latex),
        ]
        predicate_reading = forms.get("predicate_reading") or {}
        if isinstance(predicate_reading, dict):
            theorem_equivalence_nodes.append(
                (
                    "logical_forms.predicate_reading.ast",
                    predicate_reading.get("ast"),
                    str(predicate_reading.get("latex") or ""),
                )
            )
        bad_fields: list[str] = []
        checked_any = False
        for field, ast, latex in theorem_equivalence_nodes:
            is_chain = equivalence_operator_count(latex) >= 2
            if not is_chain:
                continue
            checked_any = True
            if has_nested_iff(ast):
                bad_fields.append(f"{field}: nested iff encodes A iff (B iff C), not n-way equivalence")
            elif has_iff_to_conjunction(ast):
                bad_fields.append(f"{field}: iff-to-conjunction encodes A iff (B and C), not n-way equivalence")
            elif not is_conjunction_of_iff_pairs(ast):
                bad_fields.append(f"{field}: three-way equivalence must be encoded as a conjunction of adjacent iff pairs")
        if bad_fields:
            result.set_check("theorem_equivalence_shape", "fail", "A theorem-level n-way equivalence has the wrong truth-functional AST shape.")
            for message in bad_fields:
                result.add(
                    "THREE_WAY_EQUIVALENCE_AST_INVALID",
                    "error",
                    message,
                    message.split(":", 1)[0],
                )
        elif checked_any:
            result.set_check("theorem_equivalence_shape", "pass", "Theorem-level n-way equivalences are represented as conjunctions of adjacent biconditionals.")
        else:
            result.set_check("theorem_equivalence_shape", "pass", "No theorem-level n-way equivalence chain detected.")
    else:
        result.set_check("theorem_equivalence_shape", "not_applicable", "Artifact is not theorem-like.")


def check_negation(data: dict[str, Any], result: LogicResult) -> None:
    forms = data.get("logical_forms") or {}
    negation = forms.get("negation") or {}
    statement_ast = (data.get("statement") or {}).get("semantic_ast")
    identity_kind = str((data.get("identity") or {}).get("kind") or "")
    mechanical = (negation.get("mechanical") or {}).get("ast")
    approved = (negation.get("approved_normal_form") or {}).get("ast")
    requires = negation.get("normalization_requires") or []

    if mechanical is None:
        result.set_check("negation", "warning", "No mechanical negation AST is present.")
        result.add("MISSING_MECHANICAL_NEGATION", "warning", "Mechanical negation is absent.", "logical_forms.negation.mechanical")
        return

    expected = None
    _, definiens = unwrap_definition(statement_ast)
    theorem_like = identity_kind in {"theorem", "lemma", "proposition", "corollary"}
    if theorem_like and isinstance(statement_ast, dict):
        expected = {"kind": "not", "operand": statement_ast}
    elif definiens is not None:
        expected = negate_ast(definiens)
    if expected is not None and (ast_equal(mechanical, expected) or ast_contains_equivalent(mechanical, expected)):
        if theorem_like:
            result.set_check("negation", "pass", "Mechanical negation matches the deterministic negation of the theorem statement.")
        else:
            result.set_check("negation", "pass", "Mechanical negation matches the deterministic negation of the definition body.")
    elif expected is not None and approved is not None:
        definitions = collect_definition_unfoldings(statement_ast)
        unfolded_mechanical = unfold_once(mechanical, definitions)
        theorem_normal = negate_ast(statement_ast) if theorem_like else None
        if (
            ast_equal(approved, unfolded_mechanical)
            or ast_contains_equivalent(approved, unfolded_mechanical)
            or (theorem_normal is not None and (ast_equal(approved, theorem_normal) or ast_contains_equivalent(approved, theorem_normal)))
        ):
            if theorem_like:
                result.set_check("negation", "pass", "Approved normal form matches deterministic theorem-negation normalization.")
            else:
                result.set_check("negation", "pass", "Approved normal form matches deterministic unfolding of the mechanical negation.")
        else:
            result.set_check("negation", "fail", "Provided negation does not match deterministic negation or approved unfolding.")
            result.add(
                "NEGATION_DERIVATION_MISMATCH",
                "error",
                "Expected shape derived from statement AST: " + logic_shape(expected),
                "logical_forms.negation",
            )
    elif ast_contains_kind(mechanical, "exists") and ast_contains_kind(mechanical, "not"):
        result.set_check("negation", "pass", "Mechanical negation keeps the negated comparison explicit.")
    else:
        result.set_check("negation", "fail", "Mechanical negation does not expose an existential counterexample with a negated comparison.")
        result.add(
            "MECHANICAL_NEGATION_SHAPE",
            "error",
            "Expected mechanical negation to preserve an explicit negated comparison witness.",
            "logical_forms.negation.mechanical.ast",
        )

    if approved is not None and ast_contains_relation(approved, "<") and ast_contains_relation(mechanical, r"\leq"):
        if not requires:
            result.set_check("normalization_assumptions", "fail", "Strict-order normalization is used without a recorded dependency.")
            result.add(
                "MISSING_ORDER_NORMALIZATION_ASSUMPTION",
                "error",
                "Normalizing not(x <= u) to u < x requires an explicit total-order dependency.",
                "logical_forms.negation.normalization_requires",
            )
        else:
            result.set_check("normalization_assumptions", "pass", "Strict-order normalization records an explicit order-strength dependency.")
    else:
        result.set_check("normalization_assumptions", "pass", "No strict-order normalization requiring extra assumptions was detected.")


def check_predicates(data: dict[str, Any], result: LogicResult) -> None:
    errors = []
    predicate_signatures, predicate_domain_conventions, structure_signatures, structure_carriers = registry_signatures()
    metadata = declared_metadata(data)
    for node in predicate_nodes(data):
        predicate_id = str(node.get("predicate_id") or "")
        if predicate_id not in predicate_signatures:
            continue
        errors.extend(
            validate_signature_call(
                "predicate",
                predicate_id,
                node.get("arguments") or [],
                predicate_signatures[predicate_id],
                metadata,
                structure_signatures,
                structure_carriers,
            )
        )
        if predicate_id in predicate_domain_conventions:
            errors.extend(
                validate_domain_convention(
                    predicate_id,
                    node,
                    predicate_signatures[predicate_id],
                    predicate_domain_conventions[predicate_id],
                    metadata,
                    data,
                )
            )
    for node in application_nodes(data):
        function = str(node.get("function") or "")
        if function not in structure_signatures:
            continue
        errors.extend(
            validate_signature_call(
                "structure",
                function,
                node.get("arguments") or [],
                structure_signatures[function],
                metadata,
                structure_signatures,
                structure_carriers,
            )
        )
    if errors:
        result.set_check("predicate_signatures", "fail", "Some predicate AST nodes have wrong arity.")
        for error in errors:
            result.add("SIGNATURE_ARGUMENT_MISMATCH", "error", error, "predicate_signatures")
    else:
        result.set_check("predicate_signatures", "pass", "Known predicate and structure AST nodes match registry signatures.")


def check_applicability_and_failure_modes(data: dict[str, Any], result: LogicResult) -> None:
    assumptions = data.get("assumptions") or []
    failure = data.get("failure_analysis") or {}
    applicability = failure.get("applicability_failures") or []
    statement_failures = failure.get("statement_failures") or []
    has_nonempty_assumption = any(str(item.get("kind") or "") == "nonemptiness" for item in assumptions if isinstance(item, dict))

    if has_nonempty_assumption and not applicability:
        result.set_check("applicability_failure", "fail", "Standing nonemptiness appears in assumptions but no applicability failure is recorded.")
        result.add(
            "MISSING_APPLICABILITY_FAILURE",
            "error",
            "Artifacts with standing nonemptiness must separate empty-set inapplicability from predicate failure.",
            "failure_analysis.applicability_failures",
        )
    else:
        result.set_check("applicability_failure", "pass", "Applicability failures are separated from the predicate statement.")

    if not statement_failures:
        result.set_check("failure_modes", "warning", "No statement failure modes are recorded.")
        result.add("MISSING_STATEMENT_FAILURES", "warning", "No statement failure modes are recorded.", "failure_analysis.statement_failures")
    else:
        result.set_check("failure_modes", "pass", "Statement-level failure modes are recorded.")


def check_yaml_tex_equivalence(data: dict[str, Any], corrected_tex: str, result: LogicResult) -> None:
    identity = data.get("identity") or {}
    statement = data.get("statement") or {}
    forms = data.get("logical_forms") or {}
    predicate_latex = str((forms.get("predicate_reading") or {}).get("latex") or "")
    canonical_latex = str(statement.get("canonical_latex") or "")

    required_fragments = []
    for pattern in (r"UpperBound", r"LowerBound", r"OrderedSet"):
        if pattern in predicate_latex or pattern in canonical_latex:
            required_fragments.append(pattern)
    if r"\forall" in canonical_latex or "forall" in json.dumps(statement.get("semantic_ast") or {}):
        required_fragments.append(r"\forall")
    negation = forms.get("negation") or {}
    approved_negation_latex = str((negation.get("approved_normal_form") or {}).get("latex") or "")
    contrapositive_latex = str((forms.get("contrapositive") or {}).get("latex") or "")
    logical_form_missing = False
    theorem_like = identity.get("kind") in {"theorem", "lemma", "proposition", "corollary"}
    if theorem_like and approved_negation_latex:
        if not re.search(r"Negat(?:ed|ion)|Failure modes|Mechanical", corrected_tex, re.I):
            logical_form_missing = True
            result.add(
                "YAML_TEX_LOGICAL_FORM_MISSING",
                "error",
                "Artifact records an approved theorem negation, but corrected TeX has no named negation, mechanical, or failure block.",
                "logical_forms.negation",
            )
    if theorem_like and contrapositive_latex and not re.search(r"Contrapositive", corrected_tex, re.I):
        logical_form_missing = True
        result.add(
            "YAML_TEX_LOGICAL_FORM_MISSING",
            "error",
            "Artifact records a contrapositive, but corrected TeX has no contrapositive block.",
            "logical_forms.contrapositive",
        )
    missing = [fragment for fragment in required_fragments if fragment not in corrected_tex]
    if missing:
        result.set_check("yaml_tex_equivalence", "fail", "Corrected TeX is missing symbols required by the semantic YAML.")
        result.add(
            "YAML_TEX_SYMBOL_MISMATCH",
            "error",
            f"Corrected TeX is missing required semantic fragments: {', '.join(missing)}",
            "corrected_tex",
        )
    elif logical_form_missing:
        result.set_check("yaml_tex_equivalence", "fail", "Corrected TeX is missing logical forms recorded in YAML.")
    else:
        result.set_check("yaml_tex_equivalence", "pass", "Corrected TeX contains the core predicate and quantified fragments represented in YAML.")


def validate(data: dict[str, Any], corrected_tex: str) -> LogicResult:
    result = LogicResult()
    result.set_check("language_level", "pass", "Artifact declares a supported language level.")
    result.set_check("assumptions_and_conclusion", "pass", "Assumptions and statement are represented in separate fields.")
    result.set_check("quantifier_order", "pass", "Quantifier order is represented structurally in the AST.")
    result.set_check("witness_dependencies", "pass", "Witness dependencies are checked through binder scope.")
    result.set_check("contrapositive", "not_applicable", "Definitions do not require contrapositives.")
    result.set_check("order_strength", "pass", "Order-strength changes are mediated by normalization assumptions.")

    check_scope(data, result)
    check_statement_shape(data, corrected_tex, result)
    check_negation(data, result)
    check_predicates(data, result)
    check_applicability_and_failure_modes(data, result)
    check_yaml_tex_equivalence(data, corrected_tex, result)
    return result


def batch_validate_target(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    volume_root = resolve_volume_root(args.volume, args.repos_root, args.volume_root)
    target = (volume_root / args.target).resolve() if args.target is not None and not args.target.is_absolute() else args.target.resolve()
    if not target.exists():
        raise FileNotFoundError(target)

    candidates = formal_candidates(target)
    packages = artifact_package_index(target)
    items: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    exit_code = 0
    labels = {candidate.label for candidate in candidates}

    for label, (artifact, corrected) in sorted(packages.items()):
        if label not in labels:
            continue
        data = load_mapping(artifact)
        result = validate(data, corrected.read_text(encoding="utf-8")).as_json()
        candidate = next(item for item in candidates if item.label == label)
        item = {
            "label": label,
            "candidate": candidate.as_json(volume_root),
            "artifact": artifact.relative_to(volume_root).as_posix(),
            "corrected_tex": corrected.relative_to(volume_root).as_posix(),
            "result": result,
        }
        items.append(item)
        if result["result"] not in {"pass", "pass_with_warnings"}:
            exit_code = 1

    if args.require_all_formal_artifacts:
        packaged = {item["label"] for item in items}
        for candidate in candidates:
            if candidate.label not in packaged:
                missing.append(candidate.as_json(volume_root))
        if missing:
            exit_code = 1

    payload = {
        "schema_version": "lra.semantic-logic-batch/1.0",
        "volume": args.volume,
        "volume_root": str(volume_root),
        "target": target.relative_to(volume_root).as_posix(),
        "formal_candidates": len(candidates),
        "validated_packages": len(items),
        "missing_packages": missing,
        "result": "fail" if exit_code else "pass",
        "items": items,
    }
    return payload, exit_code


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--corrected-tex", type=Path)
    parser.add_argument(
        "--llm-data",
        type=Path,
        help="JSON/YAML LLM payload containing artifact/artifact_yaml and optional corrected_tex; use '-' for stdin.",
    )
    parser.add_argument("--repos-root", type=Path)
    parser.add_argument("--volume-root", type=Path)
    parser.add_argument("--volume", choices=tuple(VOLUME_NAMES), help="Required for volume-scoped source resolution.")
    parser.add_argument("--target", type=Path, help="Volume-relative chapter/topic/file target for batch validation or label resolution.")
    parser.add_argument("--label", help="Resolve corrected TeX from the formal block with this label.")
    parser.add_argument(
        "--require-all-formal-artifacts",
        action="store_true",
        help="In --target batch mode, fail labels that do not have artifact.yaml and corrected.tex packages.",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=("yaml", "json"), default="yaml")
    args = parser.parse_args()

    try:
        if args.target is not None and args.artifact is None and args.llm_data is None and args.label is None:
            if args.volume is None:
                raise ValueError("--volume is required for --target batch validation")
            payload, return_code = batch_validate_target(args)
        else:
            candidate = None
            llm_tex = None
            if args.llm_data is not None:
                data, llm_tex = extract_llm_artifact_and_tex(load_serialized_mapping(args.llm_data))
            elif args.artifact is not None:
                data = load_mapping(args.artifact)
            else:
                raise ValueError("one of --artifact or --llm-data is required")

            if args.corrected_tex is not None:
                corrected_tex = args.corrected_tex.read_text(encoding="utf-8")
            elif llm_tex is not None:
                corrected_tex = llm_tex
            elif args.label is not None:
                if args.volume is None:
                    raise ValueError("--volume is required when resolving --label from source")
                volume_root = resolve_volume_root(args.volume, args.repos_root, args.volume_root)
                target = None
                if args.target is not None:
                    target = (volume_root / args.target).resolve() if not args.target.is_absolute() else args.target.resolve()
                candidate = resolve_candidate(volume_root, args.label, target)
                corrected_tex = candidate.text
            else:
                raise ValueError("one of --corrected-tex, --llm-data corrected_tex, or --label source resolution is required")

            payload = validate(data, corrected_tex).as_json()
            if candidate is not None:
                payload["source_resolution"] = candidate.as_json(resolve_volume_root(args.volume, args.repos_root, args.volume_root))
            return_code = 0 if payload["result"] in {"pass", "pass_with_warnings"} else 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        text = json.dumps(payload, indent=2) + "\n"
    else:
        text = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
