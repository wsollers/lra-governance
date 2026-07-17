#!/usr/bin/env python3
"""Small deterministic parser for governed semantic-support LaTeX fragments.

The parser is intentionally conservative.  It preserves the original LaTeX in
the result and only emits structured AST for grammar fragments it understands.
Unsupported fragments remain explicit failures for callers rather than being
papered over with placeholder binders.
"""

from __future__ import annotations

import re
from typing import Any


DISPLAY_RE = re.compile(r"^\\\[(?P<body>.*)\\\]$", re.S)
PREDICATE_RE = re.compile(
    r"^\\operatorname\{(?P<name>[A-Za-z][A-Za-z0-9]*)\}\s*\((?P<args>.*)\)$",
    re.S,
)
QUANTIFIER_RE = re.compile(
    r"^\\(?P<kind>forall|exists)\s+(?P<vars>.+?)\s*(?P<bound>\\in|\\subseteq|\\subset)\s*(?P<domain>.+?)\s*(?P<body>\\;|,|\(|$)(?P<tail>.*)$",
    re.S,
)
UNBOUNDED_QUANTIFIER_RE = re.compile(
    r"^\\(?P<kind>forall|exists)\s+(?P<var>[A-Za-z][A-Za-z0-9_]*|\\[A-Za-z]+)\s+(?P<tail>.+)$",
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
    text = re.sub(r"\\(?:Bigl|Bigr|bigl|bigr|left|right)", "", text)
    text = re.sub(r"\\(?:qquad|quad|,|;|!)", " ", text)
    text = re.sub(r"\\(?=\s)", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    while text.endswith("."):
        text = text[:-1].strip()
    return text


def strip_outer_parens(text: str) -> str:
    text = text.strip()
    while text.startswith("(") and text.endswith(")") and balanced(text[1:-1]):
        text = text[1:-1].strip()
    return text


def balanced(text: str) -> bool:
    depth = 0
    i = 0
    while i < len(text):
        char = text[i]
        if char == "\\":
            i += 2
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                return False
        i += 1
    return depth == 0


def split_top_level(text: str, operators: list[str]) -> tuple[str, str, str] | None:
    depth = 0
    i = 0
    while i < len(text):
        char = text[i]
        if char == "(":
            depth += 1
            i += 1
            continue
        if char == ")":
            depth -= 1
            i += 1
            continue
        if depth == 0:
            for operator in operators:
                if text.startswith(operator, i):
                    return text[:i].strip(), operator, text[i + len(operator) :].strip()
        i += 1
    return None


def binder_id(symbol: str) -> str:
    return symbol.strip().replace("\\", "").replace("{", "").replace("}", "")


def variable(symbol: str) -> dict[str, Any]:
    cleaned = symbol.strip()
    if cleaned == "1" or re.fullmatch(r"\d+", cleaned):
        return {"kind": "constant", "name": cleaned}
    return {"kind": "variable", "binder_id": binder_id(cleaned)}


def term(text: str) -> dict[str, Any]:
    text = strip_outer_parens(text.strip())
    if "," in text and not re.match(r"^[A-Za-z][A-Za-z0-9]*\s*\(", text):
        parts = split_arguments(text)
        if len(parts) > 1:
            return {"kind": "tuple", "elements": [term(item) for item in parts]}
    call = re.match(r"^(?P<name>[A-Za-z][A-Za-z0-9]*)\s*\((?P<args>.*)\)$", text, re.S)
    if call:
        return {
            "kind": "application",
            "function": call.group("name"),
            "arguments": [term(arg) for arg in split_arguments(call.group("args"))],
        }
    return variable(text)


def split_arguments(text: str) -> list[str]:
    args: list[str] = []
    depth = 0
    start = 0
    for index, char in enumerate(text):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "," and depth == 0:
            args.append(text[start:index].strip())
            start = index + 1
    tail = text[start:].strip()
    if tail:
        args.append(tail)
    return args


def parse_predicate(text: str) -> dict[str, Any] | None:
    match = PREDICATE_RE.match(strip_outer_parens(text))
    if not match:
        return None
    name = match.group("name")
    return {
        "kind": "predicate",
        "predicate_id": "pred:" + re.sub(r"(?<!^)([A-Z])", r"-\1", name).lower(),
        "name": name,
        "arguments": [term(arg) for arg in split_arguments(match.group("args"))],
    }


def parse_quantifier(text: str) -> dict[str, Any] | None:
    match = QUANTIFIER_RE.match(text)
    if not match:
        unbounded = UNBOUNDED_QUANTIFIER_RE.match(text)
        if not unbounded:
            return None
        kind = unbounded.group("kind")
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
    kind = match.group("kind")
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


def parse_atom(text: str) -> dict[str, Any]:
    for relation in (r"\notin", r"\subseteq", r"\subset", r"\neq", r"\ne", r"\in", "="):
        split = split_top_level(text, [relation])
        if split:
            left, op, right = split
            if op == r"\ne":
                op = r"\neq"
            return {
                "kind": "relation",
                "relation": op,
                "left": term(left),
                "right": term(right),
            }
    predicate = parse_predicate(text)
    if predicate:
        return predicate
    raise SemanticLatexParseError(f"unsupported formula fragment: {text}")


def parse_formula(latex: str) -> dict[str, Any]:
    text = strip_outer_parens(strip_outer_latex(latex))
    quantified = parse_quantifier(text)
    if quantified:
        return quantified
    for ops, kind in (
        ([r"\Longleftrightarrow", r"\iff"], "iff"),
        ([r"\Longrightarrow", r"\Rightarrow", r"\implies"], "implies"),
        ([r"\lor"], "or"),
        ([r"\land"], "and"),
    ):
        split = split_top_level(text, ops)
        if split:
            left, _op, right = split
            return {"kind": kind, "left": parse_formula(left), "right": parse_formula(right)}
    if text.startswith(r"\neg"):
        return {"kind": "not", "operand": parse_formula(text[4:].strip())}
    return parse_atom(text)


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
