#!/usr/bin/env python3
"""Small deterministic parser for governed semantic-support LaTeX fragments.

The parser is intentionally conservative.  It preserves the original LaTeX in
the result and only emits structured AST for grammar fragments it understands.
Unsupported fragments remain explicit failures for callers rather than being
papered over with placeholder binders.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]

DISPLAY_RE = re.compile(r"^\\\[(?P<body>.*)\\\]$", re.S)
PREDICATE_RE = re.compile(
    r"^\\operatorname\{(?P<name>[A-Za-z][A-Za-z0-9]*)\}\s*\((?P<args>.*)\)$",
    re.S,
)
REGISTRY_CALL_RE = re.compile(
    r"^(?P<name>[A-Za-z](?:_\{?\d+\}?|[A-Za-z0-9]*))\s*\((?P<args>.*)\)$",
    re.S,
)
TERM_APPLICATION_RE = re.compile(
    r"^(?P<name>"
    r"[A-Za-z][A-Za-z0-9]*(?:_\{?\\?[A-Za-z][A-Za-z0-9]*\}?)*(?:\^\{?\\?[A-Za-z][A-Za-z0-9]*\}?)?"
    r"|\\mathrm\{[A-Za-z][A-Za-z0-9]*\}"
    r"|\\mathcal\{[A-Za-z]\}"
    r"|\\[A-Za-z]+"
    r")\s*\((?P<args>.*)\)$",
    re.S,
)
CUSTOM_INFIX_RE = re.compile(r"\\(?:sim|succsim|succ)\b|\\mathbin\{")
QUANTIFIER_RE = re.compile(
    r"^\\(?P<kind>forall|exists!|exists)\s+(?P<vars>.+?)\s*(?P<bound>\\in|\\subseteq|\\subset)\s*(?P<domain>.+?)\s*(?P<body>\\;|,|\(|$)(?P<tail>.*)$",
    re.S,
)
TYPED_QUANTIFIER_RE = re.compile(
    r"^\\(?P<kind>forall|exists!|exists)\s+(?P<vars>.+?)\s*(?P<bound>\\colon|:)\s*(?P<domain>.+?\\to\s*.+?)\s*(?P<body>\\;|,|\(|$)(?P<tail>.*)$",
    re.S,
)
UNBOUNDED_QUANTIFIER_RE = re.compile(
    r"^\\(?P<kind>forall|exists)\s+(?P<var>[A-Za-z][A-Za-z0-9_]*|\\[A-Za-z]+)\s*(?:\\;|,)?\s*(?P<tail>.+)$",
    re.S,
)
EXPANDED_QUANTIFIER_RE = re.compile(
    r"^\\(?P<kind>forall|exists!|exists)\s+(?P<var>[A-Za-z][A-Za-z0-9_]*(?:_\{?\d+\}?)?|\\[A-Za-z]+)\((?P<body>.*)\)$",
    re.S,
)
PREFIX_QUANTIFIER_RE = re.compile(
    r"^\\p(?P<kind>forall|exists!|exists)\s+(?P<vars>.+?)\s*(?P<bound>\\in|\\subseteq|\\subset)\s*(?P<domain>.+?)\s*(?P<body>\\;|,|\(|$)(?P<tail>.*)$",
    re.S,
)
PREFIX_TYPED_QUANTIFIER_RE = re.compile(
    r"^\\p(?P<kind>forall|exists!|exists)\s+(?P<vars>.+?)\s*(?P<bound>\\colon|:)\s*(?P<domain>.+?\\to\s*.+?)\s*(?P<body>\\;|,|\(|$)(?P<tail>.*)$",
    re.S,
)


class SemanticLatexParseError(ValueError):
    """Raised when a formula is outside the deterministic parser grammar."""


def strip_outer_latex(latex: str) -> str:
    text = latex.strip()
    display = DISPLAY_RE.match(text)
    if display:
        text = display.group("body").strip()
    text = re.sub(r"\\label\{[^{}]*\}", "", text).strip()
    text = re.sub(r"\\begin\{(?:aligned|align\*?|split|gathered)\}", "", text)
    text = re.sub(r"\\end\{(?:aligned|align\*?|split|gathered)\}", "", text)
    text = re.sub(r"\\\\(?:\[[^\]]*\])?", " ", text)
    text = text.replace("&", " ")
    text = re.sub(r"\\(?:Bigl|Bigr|bigl|bigr|left|right)(?![A-Za-z])", "", text)
    text = re.sub(r"\\text\{\s*and\s*\}", r" \\land ", text, flags=re.I)
    text = re.sub(r"\\text\{\s*or\s*\}", r" \\lor ", text, flags=re.I)
    text = re.sub(r"\\text\{\s*implies\s*\}", r" \\rightarrow ", text, flags=re.I)
    text = re.sub(r"\\text\{\s*if\s+and\s+only\s+if\s*\}", r" \\leftrightarrow ", text, flags=re.I)
    text = re.sub(
        r"\((\\(?:forall|exists!|exists)\s+[^()]*?(?:\\in|\\subseteq|\\subset|\\colon|:)[^()]*)\)\s*(?:\\[,;!]\s*)?",
        parenthesized_quantifier_prefix,
        text,
    )
    text = re.sub(r"\((\\(?:forall|exists!|exists)\s+[^()]*)\)\s*\(", r"\1(", text)
    text = re.sub(r"\\(?:qquad|quad|,|!)", " ", text)
    text = re.sub(r"\\(?=\s)", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    while text.endswith("."):
        text = text[:-1].strip()
    while text.endswith(","):
        text = text[:-1].strip()
    return text


def parenthesized_quantifier_prefix(match: re.Match[str]) -> str:
    inner = match.group(1)
    return "\\p" + inner.removeprefix("\\") + r"\; "


def strip_outer_parens(text: str) -> str:
    text = text.strip()
    while text.startswith("(") and text.endswith(")") and balanced(text[1:-1]):
        text = text[1:-1].strip()
    while text.startswith("[") and text.endswith("]") and balanced(text[1:-1]):
        text = text[1:-1].strip()
    return text


def balanced(text: str) -> bool:
    depth = 0
    i = 0
    while i < len(text):
        if text.startswith(r"\{", i):
            depth += 1
            i += 2
            continue
        if text.startswith(r"\}", i):
            depth -= 1
            if depth < 0:
                return False
            i += 2
            continue
        char = text[i]
        if char == "\\":
            i += 2
            continue
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
            if depth < 0:
                return False
        i += 1
    return depth == 0


def split_top_level(text: str, operators: list[str]) -> tuple[str, str, str] | None:
    depth = 0
    i = 0
    while i < len(text):
        if text.startswith(r"\{", i):
            depth += 1
            i += 2
            continue
        if text.startswith(r"\}", i):
            depth -= 1
            i += 2
            continue
        char = text[i]
        if char in "([{":
            depth += 1
            i += 1
            continue
        if char in ")]}":
            depth -= 1
            i += 1
            continue
        if depth == 0:
            for operator in operators:
                if text.startswith(operator, i):
                    if (
                        operator.startswith("\\")
                        and operator[1:].isalpha()
                        and i + len(operator) < len(text)
                        and text[i + len(operator)].isalpha()
                    ):
                        continue
                    return text[:i].strip(), operator, text[i + len(operator) :].strip()
        i += 1
    return None


def split_top_level_equal_chain(text: str) -> list[str] | None:
    parts: list[str] = []
    depth = 0
    start = 0
    i = 0
    while i < len(text):
        if text.startswith(r"\{", i):
            depth += 1
            i += 2
            continue
        if text.startswith(r"\}", i):
            depth -= 1
            i += 2
            continue
        char = text[i]
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == "=" and depth == 0:
            previous = text[:i].rstrip()
            if previous.endswith(":"):
                i += 1
                continue
            parts.append(text[start:i].strip())
            start = i + 1
        i += 1
    if not parts:
        return None
    parts.append(text[start:].strip())
    if len(parts) < 3 or any(not part for part in parts):
        return None
    return parts


def equality_chain_sequence(parts: list[str]) -> dict[str, Any]:
    relations = [
        {"kind": "relation", "relation": "=", "left": term(left), "right": term(right)}
        for left, right in zip(parts, parts[1:])
    ]
    ast = relations[-1]
    for relation in reversed(relations[:-1]):
        ast = {"kind": "formula_sequence", "left": relation, "right": ast}
    return ast


def binder_id(symbol: str) -> str:
    cleaned = symbol.strip().replace("\\", "").replace("{", "").replace("}", "")
    cleaned = re.sub(r"(?<=[A-Za-z0-9])circ_", "_circ_", cleaned)
    cleaned = re.sub(r"(?<=[A-Za-z0-9])circ(?=\s+)", "_circ", cleaned)
    return re.sub(r"\s+", "_", cleaned)


def surface_key(symbol: str) -> str:
    return re.sub(r"\s+", "", symbol.strip())


def symbol_aliases(symbol: str) -> set[str]:
    """Return equivalent TeX/plain spellings for a governed symbol."""
    raw = symbol.strip()
    normalized = binder_id(raw)
    aliases = {item for item in {raw, normalized} if item}
    if normalized and re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", normalized):
        aliases.add("\\" + normalized)
        if normalized.startswith("var") and len(normalized) > 3 and normalized[3].islower():
            base = normalized[3:]
            aliases.update({base, "\\" + base})
        elif normalized[0].islower():
            aliases.update({"var" + normalized, "\\var" + normalized})
    return aliases


def quantifier_kind(kind: str) -> str:
    return "exists_unique" if kind == "exists!" else kind


def variable(symbol: str) -> dict[str, Any]:
    cleaned = re.sub(r"\\(?:;|,|!|:)", "", symbol).strip()
    if cleaned == "1" or re.fullmatch(r"\d+", cleaned):
        return {"kind": "constant", "name": cleaned}
    return {"kind": "variable", "binder_id": binder_id(cleaned)}


def raw_atom(text: str) -> dict[str, Any]:
    return {"kind": "raw_latex", "latex": canonical_raw_latex(text)}


def canonical_raw_latex(text: str) -> str:
    text = strip_outer_parens(text.strip())
    if (text.startswith("{") and text.endswith("}") and "mid" in text) or (
        text.startswith(r"\{") and text.endswith(r"\}") and "mid" in text
    ):
        return canonical_raw_set_builder(text)
    text = re.sub(r"\\widehat\s*([A-Za-z])", r"widehat_\1", text)
    text = re.sub(r"\\mathbb\{([^{}]+)\}", r"mathbb\1", text)
    text = re.sub(r"mathbb_([A-Za-z])", r"mathbb\1", text)
    text = re.sub(r"\\mathcal\{([^{}]+)\}", r"mathcal_\1", text)
    text = re.sub(r"\\mathsf\{([^{}]+)\}", r"mathsf\1", text)
    text = re.sub(r"\\mathrm\{([^{}]+)\}", r"mathrm_\1", text)
    text = re.sub(r"\bmathrm\{([^{}]+)\}", r"mathrm_\1", text)
    text = re.sub(r"\bmathrm_([A-Za-z]+)\b", r"mathrm_\1", text)
    text = re.sub(r"\\(?:;|,|!|quad|qquad)", " ", text)
    text = re.sub(r"\\coloneqq", " COLON = ", text)
    text = re.sub(r"\\colon|:", " COLON ", text)
    text = re.sub(r"\s*COLON\s*=\s*", " COLON = ", text)
    text = re.sub(r"\\(?:to|rightarrow)", "to", text)
    text = re.sub(r"\\times", "times", text)
    text = re.sub(r"\\setminus", "setminus", text)
    text = re.sub(r"\\(?!text\b)([A-Za-z]+)(?=\s*\()", r"\1", text)
    text = re.sub(r"\\(?!text\b)([A-Za-z]+)", r"\1", text)
    text = re.sub(r"\b([A-Za-z]+)_\{(\d+)\}", r"\1_\2", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"_?TIMES_?", "times", text)
    text = re.sub(r"_times_", "times", text)
    text = re.sub(r"\b([A-Za-z][A-Za-z0-9_']*)\s+in\s+([A-Za-z][A-Za-z0-9_]*)", r"\1in\2", text)
    text = re.sub(r"\b([A-Za-z][A-Za-z0-9_']*)\s+subseteq\s+([A-Za-z][A-Za-z0-9_]*)", r"\1subseteq\2", text)
    text = re.sub(r"\s*(to|times|setminus)\s*", r"\1", text)
    return text


def is_finite_set_literal(text: str) -> bool:
    text = text.strip()
    if not (
        (text.startswith(r"\{") and text.endswith(r"\}"))
        or (text.startswith("{") and text.endswith("}"))
    ):
        return False
    inner = text[2:-2] if text.startswith(r"\{") else text[1:-1]
    if not inner.strip():
        return False
    return not re.search(r"\\(?:mid|text)\b|(?<!\\)[:|]", inner)


def canonical_finite_set_literal(text: str) -> str:
    text = text.strip()
    inner = text[2:-2] if text.startswith(r"\{") else text[1:-1]
    inner = canonical_raw_latex(inner)
    inner = re.sub(r"\s*,\s*", ",", inner)
    return "{" + inner + "}"


def canonical_raw_set_builder(text: str) -> str:
    text = strip_edge_spacing_macros(text.strip())
    if text.startswith("{") and text.endswith("}"):
        text = r"\{" + text[1:-1] + r"\}"
    text = re.sub(r"\\mathcal\{([^{}]+)\}", r"mathcal_\1", text)
    text = re.sub(r"\\mathcal\s+([A-Za-z])", r"mathcal_\1", text)
    text = re.sub(r"\\mathrm\{([^{}]+)\}", r"mathrm_\1", text)
    text = re.sub(r"\\mathbb\{([^{}]+)\}", r"mathbb\1", text)
    text = re.sub(r"\bmathbb_([A-Za-z])\b", r"mathbb\1", text)
    text = re.sub(r"\\mid", " mid ", text)
    text = re.sub(r"\\Bigm\|", " Bigm| ", text)
    text = re.sub(r"\\vdash", "vdash", text)
    text = re.sub(r"\\models", "models", text)
    text = re.sub(r"\\colon|:", " COLON ", text)
    text = re.sub(r"\\(?:,|;|!|quad|qquad)", " ", text)
    text = re.sub(r"\\times", " times ", text)
    text = re.sub(r"\\(?:land|lor)", lambda match: " " + match.group(0).removeprefix("\\") + " ", text)
    text = re.sub(r"\\(?!text\b)([A-Za-z]+)(?=\s*\()", r"\1", text)
    text = re.sub(r"\\(?!text\b)([A-Za-z]+)", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"(?<=[A-Za-z0-9_\)])mid(?=\S|\s)", " mid ", text)
    text = re.sub(r"\bmid(?=[A-Za-z0-9_\(])", "mid ", text)
    text = re.sub(r"(?<=[a-z\)])in(?=[A-Z]|mathcal|mathbb)", "in ", text)
    text = re.sub(r"(?<=[a-z\)])notin(?=[A-Z]|mathcal|mathbb)", "notin ", text)
    text = re.sub(r"(?<=[A-Za-z0-9_\)])subseteq(?=[A-Z]|mathcal|mathbb)", "subseteq ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\\\{\s*", r"\\{", text)
    text = re.sub(r"\s*\\\}", r"\\}", text)
    text = re.sub(r"([A-Za-z0-9_'\)])\s+(in|notin|subseteq|subset|models|vdash|mapsto|leq|geq|le|ge)\s+", r"\1\2 ", text)
    text = re.sub(r"\s*(to|times|setminus)\s*", r"\1", text)
    text = re.sub(r"\s*,\s*", ",", text)
    text = re.sub(r"\s+Bigm\|\s+", " Bigm| ", text)
    return text


def contains_logical_syntax(text: str) -> bool:
    return bool(
        re.search(
            r"\\(?:forall|exists|Longleftrightarrow|Leftrightarrow|iff|Longrightarrow|Rightarrow|implies|land|lor|neg|uparrow|downarrow)\b",
            text,
        )
    )


def contains_custom_infix_surface(text: str) -> bool:
    return bool(CUSTOM_INFIX_RE.search(text))


def contains_formula_object_syntax(text: str) -> bool:
    return bool(
        re.search(
            r"\\(?:forall|exists|leftrightarrow|to|rightarrow|land|lor|neg|uparrow|downarrow|circ)\b",
            text,
        )
    )


def formula_variable_name(symbol: str) -> str:
    return binder_id(symbol)


def formula_variable(symbol: str) -> dict[str, Any]:
    return {"kind": "formula_variable", "name": formula_variable_name(symbol)}


TERM_INFIX_OPERATOR_GROUPS = (
    [r"\cup"],
    [r"\setminus"],
    [r"\cap"],
    [r"\circ"],
)


def term_operation(operator: str, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {"kind": "term_operation", "operator": operator, "left": left, "right": right}


def strip_edge_spacing_macros(text: str) -> str:
    return re.sub(r"^(?:\\;|\\,|\\!|\s)+|(?:\\;|\\,|\\!|\s)+$", "", text.strip())


RELATION_OPERATORS = (
    r"\models",
    r"\vdash",
    r"\equiv",
    r"\notin",
    r"\subseteq",
    r"\subset",
    r"\neq",
    r"\ne",
    r"\leq",
    r"\geq",
    r"\in",
    r"\mapsto",
    r"\coloneqq",
    r"\colon",
    ":",
    "<",
    ">",
    "=",
)


def contains_top_level_relation(text: str) -> bool:
    if text.lstrip().startswith((r"\forall", r"\exists")):
        return False
    if re.search(
        r"\\(?:forall|exists!|exists)\s+[^,;()]*?(?:\\in|\\subseteq|\\subset|\\colon|:)\s*[^,;()]+$",
        text,
    ):
        return False
    return any(split_top_level(text, [operator]) for operator in RELATION_OPERATORS)


def looks_like_structured_formula_operand(text: str) -> bool:
    stripped = strip_outer_parens(text.strip())
    if stripped.startswith((r"\forall", r"\exists", r"\pforall", r"\pexists", r"\neg")):
        return True
    if contains_top_level_relation(stripped):
        return True
    for operators in (
        [r"\Longleftrightarrow", r"\Leftrightarrow", r"\leftrightarrow", r"\iff"],
        [r"\Longrightarrow", r"\Rightarrow", r"\rightarrow", r"\implies"],
        [r"\lor"],
        [r"\land"],
    ):
        if split_top_level(stripped, operators):
            return True
    return False


def parse_indexed_term_operation(text: str) -> dict[str, Any] | None:
    match = re.match(
        r"^(?P<operator>\\bigcup|\\bigcap)\s*_\{(?P<index>(?:[^{}]|\{[^{}]*\})+)\}(?P<body>.+)$",
        text,
        re.S,
    )
    if not match:
        return None
    index_text = match.group("index").strip()
    body_text = match.group("body").strip()
    if not body_text:
        raise SemanticLatexParseError(f"indexed term operation has no body: {text}")
    split = split_top_level(index_text, [r"\in"])
    if split:
        binder, _op, domain = split
        if not binder or not domain:
            raise SemanticLatexParseError(f"indexed term operation has malformed index: {text}")
        index = {"binder_id": binder_id(binder), "domain": term(domain)}
    else:
        index = {"binder_id": binder_id(index_text), "domain": None}
    return {
        "kind": "indexed_term_operation",
        "operator": match.group("operator"),
        "index": index,
        "body": term(body_text),
    }


def parse_formula_object(text: str) -> dict[str, Any]:
    text = strip_outer_parens(text.strip())
    if not text:
        raise SemanticLatexParseError("formula object has empty fragment")
    if re.match(r"^\\circ\s*\\in\b", text):
        return parse_formula(text)
    comma = split_top_level(text, [","])
    if comma:
        left, _op, right = comma
        if not left or not right:
            raise SemanticLatexParseError(f"formula object sequence has missing item: {text}")
        return {
            "kind": "formula_sequence",
            "left": parse_formula_object(left),
            "right": parse_formula_object(right),
        }
    for operators in (
        [r"\leftrightarrow", r"\iff"],
        [r"\to", r"\rightarrow"],
        [r"\lor"],
        [r"\land", r"\uparrow", r"\downarrow", r"\circ"],
    ):
        split = split_top_level(text, operators)
        if split:
            left, op, right = split
            if not left or not right:
                raise SemanticLatexParseError(f"formula object connective has missing operand: {text}")
            return {
                "kind": "formula_connective",
                "operator": op,
                "left": parse_formula_object(left),
                "right": parse_formula_object(right),
            }
    if text.startswith(r"\neg"):
        operand = text[4:].strip()
        if not operand:
            raise SemanticLatexParseError(f"formula object negation has no operand: {text}")
        return {"kind": "formula_not", "operand": parse_formula_object(operand)}
    quantifier = re.match(r"^\\(?P<kind>forall|exists!|exists)\s+(?P<var>[A-Za-z][A-Za-z0-9_]*|\\[A-Za-z]+)\s*(?P<body>.+)$", text, re.S)
    if quantifier:
        return {
            "kind": "formula_quantifier",
            "quantifier": "\\" + quantifier.group("kind"),
            "binder": formula_variable(quantifier.group("var")),
            "body": parse_formula_object(quantifier.group("body")),
        }
    if re.fullmatch(r"\\?[A-Za-z][A-Za-z0-9_]*(?:_\{?\\?[A-Za-z0-9]+\}?)*(?:\([^)]+\))?", text):
        return formula_variable(text)
    if contains_formula_object_syntax(text):
        raise SemanticLatexParseError(f"unsupported formula object fragment: {text}")
    return formula_variable(text)


def default_predicate_id(name: str) -> str:
    return "pred:" + re.sub(r"(?<!^)([A-Z])", r"-\1", name).lower()


@lru_cache(maxsize=1)
def predicate_surface_index() -> dict[tuple[str, int], str]:
    index: dict[tuple[str, int], str] = {}
    registry = ROOT / "predicates.yaml"
    if not registry.exists():
        return index
    for item in yaml.safe_load(registry.read_text(encoding="utf-8")).get("predicates", []) or []:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        arity = len([arg for arg in item.get("arguments", []) or [] if isinstance(arg, dict)])
        surfaces = {str(item.get("name") or "")}
        surfaces.update(str(surface) for surface in item.get("surface_forms", []) or [])
        for surface in surfaces:
            surface = surface_key(surface)
            if surface:
                index.setdefault((surface, arity), str(item["id"]))
    return index


def resolve_predicate_id(name: str, arity: int) -> str:
    return predicate_surface_index().get((surface_key(name), arity), default_predicate_id(name))


def term(text: str) -> dict[str, Any]:
    text = strip_edge_spacing_macros(text)
    text = strip_outer_parens(text)
    if r"\widehat" in text:
        text = re.sub(r"\\widehat\s*([A-Za-z])", r"widehat_\1", text)
    if "|" in text:
        return raw_atom(text)
    if re.search(r"\)\s+\([^()]*\\(?:to|rightarrow)[^()]*\)$", text):
        return raw_atom(text)
    if is_finite_set_literal(text):
        return raw_atom(canonical_finite_set_literal(text))
    function_space = split_top_level(text, [r"\to"])
    if function_space:
        left, _op, right = function_space
        return {"kind": "application", "function": "function_space", "arguments": [term(left), term(right)]}
    indexed_operation = parse_indexed_term_operation(text)
    if indexed_operation:
        return indexed_operation
    for operators in TERM_INFIX_OPERATOR_GROUPS:
        split = split_top_level(text, operators)
        if split:
            left, op, right = split
            if not left and not right and text == op:
                break
            if not left or not right:
                raise SemanticLatexParseError(f"term operation has missing operand: {text}")
            return term_operation(op, term(left), term(right))
    product = split_top_level(text, [r"\times"])
    if product:
        left, _op, right = product
        return {"kind": "application", "function": "cartesian_product", "arguments": [term(left), term(right)]}
    if text.startswith((r"\{", "{")) and re.search(
        r"\\(?:neg|land|lor|to|rightarrow|leftrightarrow|iff)\b",
        text,
    ):
        if r"\mid" in text or r"\text" in text or r"\models" in text or r"\vdash" in text or ":" in text:
            return raw_atom(canonical_raw_set_builder(text))
        return raw_atom(text)
    if (
        (r"\{" in text or text.startswith("{"))
        and (r"\text" in text or r"\mid" in text or r"\models" in text or r"\vdash" in text or ":" in text)
    ):
        return raw_atom(canonical_raw_set_builder(text))
    if contains_custom_infix_surface(text):
        return raw_atom(text)
    if contains_logical_syntax(text):
        return raw_atom(text)
    if "," in text:
        parts = split_arguments(text)
        if len(parts) > 1:
            return {"kind": "tuple", "elements": [term(item) for item in parts]}
    call = TERM_APPLICATION_RE.match(text)
    if call:
        function = binder_id(call.group("name"))
        arguments_text = call.group("args")
        nested_call_index = arguments_text.find(")(")
        if nested_call_index >= 0:
            first_arg = arguments_text[:nested_call_index].strip()
            later_args = arguments_text[nested_call_index + 2 :].strip()
            arguments = [term(first_arg), *[term(arg) for arg in split_arguments(later_args)]]
        else:
            arguments = [term(arg) for arg in split_arguments(arguments_text)]
        return {"kind": "application", "function": function, "arguments": arguments}
    return variable(text)


def split_arguments(text: str) -> list[str]:
    args: list[str] = []
    depth = 0
    start = 0
    index = 0
    while index < len(text):
        if text.startswith(r"\{", index):
            depth += 1
            index += 2
            continue
        if text.startswith(r"\}", index):
            depth -= 1
            index += 2
            continue
        char = text[index]
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == "," and depth == 0:
            args.append(text[start:index].strip())
            start = index + 1
        index += 1
    tail = text[start:].strip()
    if tail:
        args.append(tail)
    return args


def parse_predicate(text: str) -> dict[str, Any] | None:
    stripped = strip_outer_parens(text)
    match = PREDICATE_RE.match(stripped)
    registry_call = False
    if not match:
        match = REGISTRY_CALL_RE.match(stripped)
        registry_call = bool(match)
    if not match:
        return None
    name = match.group("name")
    arguments = [term(arg) for arg in split_arguments(match.group("args"))]
    predicate_id = resolve_predicate_id(name, len(arguments))
    if registry_call and predicate_id == default_predicate_id(name):
        return None
    return {
        "kind": "predicate",
        "predicate_id": predicate_id,
        "name": name,
        "arguments": arguments,
    }


def parse_zero_arity_predicate(text: str) -> dict[str, Any] | None:
    stripped = strip_outer_parens(text)
    match = re.fullmatch(r"(?P<name>[A-Za-z](?:_\{?\d+\}?|[A-Za-z0-9]*))|\\(?P<command>[A-Za-z]+)", stripped)
    if not match:
        return None
    name = match.group("name") or ("\\" + str(match.group("command")))
    predicate_id = resolve_predicate_id(name, 0)
    if predicate_id == default_predicate_id(name):
        return None
    return {
        "kind": "predicate",
        "predicate_id": predicate_id,
        "name": name,
        "arguments": [],
    }


def parse_quantifier(text: str) -> dict[str, Any] | None:
    expanded = EXPANDED_QUANTIFIER_RE.match(text)
    if expanded:
        kind = quantifier_kind(expanded.group("kind"))
        symbol = expanded.group("var")
        body = desugar_expanded_quantifier(kind, symbol, parse_formula(expanded.group("body")))
        if body:
            return body
    match, typed_match = choose_quantifier_match(
        QUANTIFIER_RE.match(text),
        TYPED_QUANTIFIER_RE.match(text),
    )
    if typed_match and match:
        kind = quantifier_kind(match.group("kind"))
        symbols = [item.strip() for item in match.group("vars").split(",") if item.strip()]
        domain_ast = term(match.group("domain").strip())
        tail = match.group("tail").strip()
        if match.group("body") == "(" and tail.endswith(")"):
            tail = tail[:-1].strip()
        if not tail:
            raise SemanticLatexParseError(f"quantifier has no body: {text}")
        body = parse_formula(tail)
        for symbol in reversed(symbols):
            body = {
                "kind": kind,
                "binder": {
                    "binder_id": binder_id(symbol),
                    "symbol": symbol,
                    "domain": domain_ast,
                },
                "restriction": None,
                "body": body,
            }
        return body
    if not match:
        unbounded = UNBOUNDED_QUANTIFIER_RE.match(text)
        if not unbounded:
            return None
        kind = quantifier_kind(unbounded.group("kind"))
        symbol = unbounded.group("var")
        return {
            "kind": kind,
            "binder": {
                "binder_id": binder_id(symbol),
                "symbol": symbol,
                "domain": None,
            },
            "restriction": None,
            "body": parse_formula(unbounded.group("tail")),
        }
    kind = quantifier_kind(match.group("kind"))
    symbols = [item.strip() for item in match.group("vars").split(",") if item.strip()]
    domain_ast = term(match.group("domain").strip())
    if match.group("bound") in {r"\subseteq", r"\subset"}:
        domain_ast = {
            "kind": "application",
            "function": "subset_of",
            "arguments": [domain_ast],
        }
    tail = match.group("tail").strip()
    if match.group("body") == "(" and tail.endswith(")"):
        tail = tail[:-1].strip()
    if not tail:
        raise SemanticLatexParseError(f"quantifier has no body: {text}")
    body = parse_formula(tail)
    for symbol in reversed(symbols):
        body = {
            "kind": kind,
            "binder": {
                "binder_id": binder_id(symbol),
                "symbol": symbol,
                "domain": domain_ast,
            },
            "restriction": None,
            "body": body,
        }
    return body


def desugar_expanded_quantifier(kind: str, symbol: str, body: dict[str, Any]) -> dict[str, Any] | None:
    connective = "implies" if kind == "forall" else "and"
    if body.get("kind") != connective:
        return None
    restriction = body.get("left")
    if not isinstance(restriction, dict) or restriction.get("kind") != "relation":
        return None
    if restriction.get("relation") != r"\in":
        return None
    left = restriction.get("left")
    if not isinstance(left, dict) or left.get("kind") != "variable":
        return None
    if left.get("binder_id") != binder_id(symbol):
        return None
    return {
        "kind": kind,
        "binder": {
            "binder_id": binder_id(symbol),
            "symbol": symbol,
            "domain": restriction["right"],
        },
        "restriction": None,
        "body": body["right"],
    }


def choose_quantifier_match(
    bounded: re.Match[str] | None,
    typed: re.Match[str] | None,
) -> tuple[re.Match[str] | None, bool]:
    if bounded and typed:
        return (typed, True) if typed.start("bound") < bounded.start("bound") else (bounded, False)
    if typed:
        return typed, True
    return bounded, False


def parse_prefix_quantifier(text: str) -> dict[str, Any] | None:
    match, typed_match = choose_quantifier_match(
        PREFIX_QUANTIFIER_RE.match(text),
        PREFIX_TYPED_QUANTIFIER_RE.match(text),
    )
    if not match:
        return None
    kind = quantifier_kind(match.group("kind"))
    symbols = [item.strip() for item in match.group("vars").split(",") if item.strip()]
    domain_ast = term(match.group("domain").strip())
    if not typed_match and match.group("bound") in {r"\subseteq", r"\subset"}:
        domain_ast = {
            "kind": "application",
            "function": "subset_of",
            "arguments": [domain_ast],
        }
    tail = match.group("tail").strip()
    if match.group("body") == "(" and tail.endswith(")"):
        tail = tail[:-1].strip()
    if not tail:
        raise SemanticLatexParseError(f"quantifier has no body: {text}")
    body = parse_formula(tail)
    for symbol in reversed(symbols):
        body = {
            "kind": kind,
            "binder": {
                "binder_id": binder_id(symbol),
                "symbol": symbol,
                "domain": domain_ast,
            },
            "restriction": None,
            "body": body,
        }
    return body


def parse_atom(text: str) -> dict[str, Any]:
    for relation in RELATION_OPERATORS:
        split = split_top_level(text, [relation])
        if split:
            left, op, right = split
            if not left or not right:
                raise SemanticLatexParseError(f"relation has missing side: {text}")
            if r"\text" in text and not right.lstrip().startswith((r"\{", "{")):
                return raw_atom(text)
            if op == r"\ne":
                op = r"\neq"
            if op == r"\coloneqq":
                op = r"\colon"
            if op == ":":
                op = r"\colon"
            if op == r"\colon" and right.lstrip().startswith("="):
                right = right.lstrip()[1:].strip()
            if op == r"\equiv":
                return {
                    "kind": "relation",
                    "relation": op,
                    "left": parse_formula_object(left),
                    "right": parse_formula_object(right),
                }
            if op == r"\colon" and re.search(
                r"\\mid|\\Bigm\||\\forall|\\exists|\\subseteq|\\in\b",
                right,
            ):
                right_ast = raw_atom(canonical_raw_set_builder(right))
            else:
                right_ast = term(right)
            return {
                "kind": "relation",
                "relation": op,
                "left": term(left),
                "right": right_ast,
            }
    predicate = parse_predicate(text)
    if predicate:
        return predicate
    zero_arity = parse_zero_arity_predicate(text)
    if zero_arity:
        return zero_arity
    if contains_custom_infix_surface(text):
        return raw_atom(text)
    call = TERM_APPLICATION_RE.match(text)
    if call:
        return term(text)
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*|\\[A-Za-z]+", text):
        return variable(text)
    if not contains_logical_syntax(text):
        return raw_atom(text)
    raise SemanticLatexParseError(f"unsupported formula fragment: {text}")


def parse_formula(latex: str) -> dict[str, Any]:
    text = strip_outer_parens(strip_outer_latex(latex))
    text = strip_edge_spacing_macros(text)
    parse_prefix_quantifier_first = text.startswith((r"\pforall", r"\pexists"))
    if parse_prefix_quantifier_first and r"\equiv" in text:
        quantified = parse_prefix_quantifier(text)
        if quantified:
            return quantified
    sequence = split_top_level(text, [","])
    if sequence:
        left, _op, right = sequence
        if contains_top_level_relation(left) and contains_top_level_relation(right):
            return {"kind": "formula_sequence", "left": parse_formula(left), "right": parse_formula(right)}
    if r"\equiv" in text:
        for operator, kind in (
            (r"\Longleftrightarrow", "iff"),
            (r"\Leftrightarrow", "iff"),
            (r"\leftrightarrow", "iff"),
            (r"\iff", "iff"),
            (r"\Longrightarrow", "implies"),
            (r"\Rightarrow", "implies"),
            (r"\rightarrow", "implies"),
            (r"\implies", "implies"),
        ):
            split = split_top_level(text, [operator])
            if split:
                left, _op, right = split
                left = left.rstrip()
                if kind == "iff" and not left.endswith(":") and not (
                    looks_like_structured_formula_operand(left) and looks_like_structured_formula_operand(right)
                ):
                    continue
                if kind == "iff" and left.endswith(":"):
                    left = left[:-1].rstrip()
                if not left or not right:
                    raise SemanticLatexParseError(f"connective has missing side: {text}")
                return {"kind": kind, "left": parse_formula(left), "right": parse_formula(right)}
        for operators, kind in (([r"\lor"], "or"), ([r"\land"], "and")):
            split = split_top_level(text, operators)
            if split:
                left, _op, right = split
                if looks_like_structured_formula_operand(left) and looks_like_structured_formula_operand(right):
                    return {"kind": kind, "left": parse_formula(left), "right": parse_formula(right)}
    if r"\equiv" in text:
        sequence = split_top_level(text, [","])
        if sequence:
            left, _op, right = sequence
            if not left or not right:
                raise SemanticLatexParseError(f"formula sequence has missing item: {text}")
            return {"kind": "formula_sequence", "left": parse_formula(left), "right": parse_formula(right)}
        return parse_atom(text)
    parse_quantifier_first = (
        not parse_prefix_quantifier_first
        and not quantifier_has_parenthesized_body_followed_by_connective(text)
        and not expanded_quantifier_has_body_followed_by_connective(text)
    )
    if parse_quantifier_first:
        quantified = parse_quantifier(text)
        if quantified:
            return quantified
    for ops, kind in (
        ([r"\Longleftrightarrow", r"\Leftrightarrow", r"\leftrightarrow", r"\iff"], "iff"),
        ([r"\Longrightarrow", r"\Rightarrow", r"\rightarrow", r"\implies"], "implies"),
        ([r"\lor"], "or"),
        ([r"\land"], "and"),
    ):
        split = split_top_level(text, ops)
        if split:
            left, _op, right = split
            return {"kind": kind, "left": parse_formula(left), "right": parse_formula(right)}
    equality_chain = split_top_level_equal_chain(text)
    if equality_chain:
        return equality_chain_sequence(equality_chain)
    if parse_prefix_quantifier_first:
        quantified = parse_prefix_quantifier(text)
        if quantified:
            return quantified
    if not parse_quantifier_first:
        quantified = parse_quantifier(text)
        if quantified:
            return quantified
    if text.startswith(r"\neg"):
        return {"kind": "not", "operand": parse_formula(text[4:].strip())}
    return parse_atom(text)


def quantifier_has_parenthesized_body_followed_by_connective(text: str) -> bool:
    match = TYPED_QUANTIFIER_RE.match(text) or QUANTIFIER_RE.match(text)
    if not match:
        return False
    if match.group("body") == "(":
        open_index = text.find("(", match.start("body"))
    else:
        tail = match.group("tail").lstrip()
        if not tail.startswith("("):
            return False
        open_index = text.find(tail, match.start("tail"))
    if open_index < 0:
        return False
    depth = 0
    i = open_index
    while i < len(text):
        char = text[i]
        if char == "\\":
            i += 2
            continue
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
            if depth == 0:
                rest = text[i + 1 :].strip()
                return any(
                    rest.startswith(operator)
                    for operator in (
                        r"\land",
                        r"\lor",
                        r"\Longrightarrow",
                        r"\Rightarrow",
                        r"\rightarrow",
                        r"\implies",
                        r"\Longleftrightarrow",
                        r"\Leftrightarrow",
                        r"\leftrightarrow",
                        r"\iff",
                    )
                )
        i += 1
    return False


def expanded_quantifier_has_body_followed_by_connective(text: str) -> bool:
    match = re.match(
        r"^\\(?:forall|exists!|exists)\s+(?:[A-Za-z][A-Za-z0-9_]*(?:_\{?\d+\}?)?|\\[A-Za-z]+)\s*\(",
        text,
    )
    if not match:
        return False
    open_index = text.find("(", match.end() - 1)
    if open_index < 0:
        return False
    depth = 0
    i = open_index
    while i < len(text):
        char = text[i]
        if char == "\\":
            i += 2
            continue
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
            if depth == 0:
                rest = text[i + 1 :].strip()
                return any(
                    rest.startswith(operator)
                    for operator in (
                        r"\land",
                        r"\lor",
                        r"\Longrightarrow",
                        r"\Rightarrow",
                        r"\rightarrow",
                        r"\implies",
                        r"\Longleftrightarrow",
                        r"\Leftrightarrow",
                        r"\leftrightarrow",
                        r"\iff",
                    )
                )
        i += 1
    return False


def negate_ast(node: dict[str, Any]) -> dict[str, Any]:
    kind = node.get("kind")
    if kind == "not":
        operand = node.get("operand")
        if isinstance(operand, dict):
            return operand
    if kind == "and":
        return {"kind": "or", "left": negate_ast(node["left"]), "right": negate_ast(node["right"])}
    if kind == "or":
        return {"kind": "and", "left": negate_ast(node["left"]), "right": negate_ast(node["right"])}
    if kind == "implies":
        return {"kind": "and", "left": node["left"], "right": negate_ast(node["right"])}
    if kind == "iff":
        left = node["left"]
        right = node["right"]
        return {
            "kind": "or",
            "left": {"kind": "and", "left": left, "right": negate_ast(right)},
            "right": {"kind": "and", "left": negate_ast(left), "right": right},
        }
    if kind == "formula_sequence":
        return {"kind": "not", "operand": node}
    if kind == "forall":
        return {
            "kind": "exists",
            "binder": node["binder"],
            "restriction": node.get("restriction"),
            "body": negate_ast(node["body"]),
        }
    if kind == "exists":
        return {
            "kind": "forall",
            "binder": node["binder"],
            "restriction": node.get("restriction"),
            "body": negate_ast(node["body"]),
        }
    if kind == "relation":
        opposite = {
            r"\in": r"\notin",
            r"\notin": r"\in",
            "=": r"\neq",
            r"\neq": "=",
            r"\leq": ">",
            "<": r"\geq",
        }.get(str(node.get("relation")))
        if opposite:
            return {**node, "relation": opposite}
    return {"kind": "not", "operand": node}


def parse_support_formula(latex: str) -> dict[str, Any]:
    ast = parse_formula(latex)
    return {
        "original_latex": latex,
        "ast": ast,
        "mechanical_negation_ast": negate_ast(ast),
    }
