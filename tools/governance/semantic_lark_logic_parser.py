#!/usr/bin/env python3
"""Lark-backed parser for governed logical LaTeX fragments.

This parser is an independent AST witness for controlled formal-support
fragments.  It preserves the original LaTeX and parses a normalized token
language with Lark, then emits the same semantic AST schema used by the
hand-rolled parser.
"""

from __future__ import annotations

import re
from typing import Any

from lark import Lark, Transformer, v_args

from semantic_latex_ast import negate_ast


GRAMMAR = r"""
?start: expr
?expr: iff
?iff: implies (IFF implies)*
?implies: disjunction (IMPLIES implies)?
?disjunction: conjunction (OR conjunction)*
?conjunction: unary (AND unary)*
?unary: NEG unary                 -> neg
      | quantifier
      | predicate
      | relation
      | "(" expr ")"

quantifier: quantifier_kind var_list bound term separator? expr     -> bounded_quantifier
          | quantifier_kind NAME expr                               -> unbounded_quantifier
quantifier_kind: FORALL | EXISTS
var_list: NAME ("," NAME)*
bound: IN | SUBSETEQ | SUBSET
separator: "," | ";"

predicate: OPERATOR "(" [term_list] ")"
relation: term relation_op term
relation_op: NOTIN | NEQ | IN | SUBSETEQ | SUBSET | EQUALS
?term: application
     | tuple
     | NUMBER                     -> number
     | NAME                       -> variable
application: NAME "(" [term_list] ")"
tuple: "(" term_list ")"
term_list: term ("," term)*

FORALL: "FORALL"
EXISTS: "EXISTS"
IFF: "IFF"
IMPLIES: "IMPLIES"
OR: "OR"
AND: "AND"
NEG: "NEG"
IN: "IN"
NOTIN: "NOTIN"
SUBSETEQ: "SUBSETEQ"
SUBSET: "SUBSET"
NEQ: "NEQ"
EQUALS: "="
OPERATOR: /OP_[A-Za-z][A-Za-z0-9]*/
NAME: /(?!FORALL\b|EXISTS\b|IFF\b|IMPLIES\b|OR\b|AND\b|NEG\b|IN\b|SUBSETEQ\b|SUBSET\b|NOTIN\b|NEQ\b)[A-Za-z][A-Za-z0-9_]*/
NUMBER: /\d+/

%import common.WS
%ignore WS
"""


PARSER = Lark(GRAMMAR, parser="earley")
DISPLAY_RE = re.compile(r"^\\\[(?P<body>.*)\\\]$", re.S)


class SemanticLarkParseError(ValueError):
    """Raised when Lark cannot parse the controlled formula."""


def normalize_latex(latex: str) -> str:
    text = latex.strip()
    display = DISPLAY_RE.match(text)
    if display:
        text = display.group("body").strip()
    while text.endswith("."):
        text = text[:-1].strip()
    text = re.sub(r"\\label\{[^{}]*\}", "", text)
    text = re.sub(r"\\operatorname\{([A-Za-z][A-Za-z0-9]*)\}", r"OP_\1", text)
    replacements = [
        (r"\\Longleftrightarrow|\\Leftrightarrow|\\iff", " IFF "),
        (r"\\Longrightarrow|\\Rightarrow|\\implies", " IMPLIES "),
        (r"\\forall", " FORALL "),
        (r"\\exists", " EXISTS "),
        (r"\\notin", " NOTIN "),
        (r"\\subseteq", " SUBSETEQ "),
        (r"\\subset", " SUBSET "),
        (r"\\neq|\\ne", " NEQ "),
        (r"\\in", " IN "),
        (r"\\land", " AND "),
        (r"\\lor", " OR "),
        (r"\\neg", " NEG "),
        (r"\\(?:Bigl|Bigr|bigl|bigr|left|right)", ""),
        (r"\\(?:qquad|quad|,|;|!)", " "),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)
    text = re.sub(r"\\(?=\s)", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def binder_id(symbol: str) -> str:
    return symbol.strip()


def relation_symbol(value: str) -> str:
    return {
        "IN": r"\in",
        "NOTIN": r"\notin",
        "NEQ": r"\neq",
        "SUBSETEQ": r"\subseteq",
        "SUBSET": r"\subset",
        "=": "=",
    }[value]


def predicate_id(name: str) -> str:
    surface = name.removeprefix("OP_")
    return "pred:" + re.sub(r"(?<!^)([A-Z])", r"-\1", surface).lower()


@v_args(inline=True)
class AstTransformer(Transformer):
    def number(self, token):
        return {"kind": "constant", "name": str(token)}

    def variable(self, token):
        return {"kind": "variable", "binder_id": binder_id(str(token))}

    def application(self, name, terms=None):
        return {
            "kind": "application",
            "function": str(name),
            "arguments": terms or [],
        }

    def tuple(self, terms):
        return {"kind": "tuple", "elements": terms}

    def term_list(self, *terms):
        return list(terms)

    def relation_op(self, token):
        return str(token)

    def relation(self, left, rel, right):
        return {
            "kind": "relation",
            "relation": relation_symbol(str(rel)),
            "left": left,
            "right": right,
        }

    def predicate(self, operator, terms=None):
        name = str(operator).removeprefix("OP_")
        return {
            "kind": "predicate",
            "predicate_id": predicate_id(str(operator)),
            "name": name,
            "arguments": terms or [],
        }

    def var_list(self, *tokens):
        return [str(token) for token in tokens]

    def bound(self, token):
        return str(token)

    def quantifier_kind(self, token):
        return str(token)

    def bounded_quantifier(self, quantifier, variables, bound, domain, *tail):
        body = tail[-1]
        if bound in {"SUBSETEQ", "SUBSET"}:
            domain = {
                "kind": "application",
                "function": "subset_of",
                "arguments": [domain],
            }
        kind = "forall" if str(quantifier) == "FORALL" else "exists"
        ast = body
        for symbol in reversed(variables):
            ast = {
                "kind": kind,
                "binder": {
                    "binder_id": binder_id(symbol),
                    "symbol": symbol,
                    "domain": domain,
                },
                "restriction": None,
                "body": ast,
            }
        return ast

    def unbounded_quantifier(self, quantifier, symbol, body):
        return {
            "kind": "forall" if str(quantifier) == "FORALL" else "exists",
            "binder": {
                "binder_id": binder_id(str(symbol)),
                "symbol": str(symbol),
                "domain": None,
            },
            "restriction": None,
            "body": body,
        }

    def neg(self, operand):
        return {"kind": "not", "operand": operand}

    def conjunction(self, first, *rest):
        ast = first
        for item in rest:
            if str(item) == "AND":
                continue
            ast = {"kind": "and", "left": ast, "right": item}
        return ast

    def disjunction(self, first, *rest):
        ast = first
        for item in rest:
            if str(item) == "OR":
                continue
            ast = {"kind": "or", "left": ast, "right": item}
        return ast

    def implies(self, left, *rest):
        if not rest:
            return left
        right = rest[-1]
        return {"kind": "implies", "left": left, "right": right}

    def iff(self, first, *rest):
        ast = first
        for item in rest:
            if str(item) == "IFF":
                continue
            ast = {"kind": "iff", "left": ast, "right": item}
        return ast


def parse_formula(latex: str) -> dict[str, Any]:
    normalized = normalize_latex(latex)
    try:
        tree = PARSER.parse(normalized)
    except Exception as exc:  # pragma: no cover - Lark exception hierarchy is broad.
        raise SemanticLarkParseError(f"could not parse controlled formula: {latex!r}") from exc
    return AstTransformer().transform(tree)


def parse_support_formula(latex: str) -> dict[str, Any]:
    ast = parse_formula(latex)
    return {
        "original_latex": latex,
        "normalized_formula": normalize_latex(latex),
        "ast": ast,
        "mechanical_negation_ast": negate_ast(ast),
    }
