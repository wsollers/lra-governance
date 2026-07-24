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

from semantic_latex_ast import (
    canonical_finite_set_literal,
    canonical_raw_latex,
    canonical_raw_set_builder,
    default_predicate_id,
    negate_ast,
    parse_formula_object,
    resolve_predicate_id,
)


GRAMMAR = r"""
?start: expr
?expr: quantifier
     | iff
?iff: quant_expr (IFF quant_expr)*
?quant_expr: quantifier
           | implies
?implies: disjunction ((IMPLIES | METAIMPLIES) quant_expr)?
?disjunction: conjunction (OR conjunction)*
?conjunction: unary (AND unary)*
?unary: NEG unary                 -> neg
      | prefix_quantifier
      | quantifier
      | predicate
      | relation
      | mathcal_call
      | application
      | ZERO_PREDICATE             -> zero_predicate
      | NAME                       -> variable
      | RAW_ATOM                   -> raw_atom
      | "(" expr ")"
      | "[" expr "]"

quantifier: grouped_quantifier | plain_quantifier
grouped_quantifier.2: quantifier_kind var_list bound term separator? "(" expr ")"     -> bounded_quantifier
                    | quantifier_kind var_list type_bound function_space separator? "(" expr ")" -> typed_quantifier
                    | quantifier_kind NAME "(" expr ")"                               -> unbounded_quantifier
plain_quantifier.1: quantifier_kind var_list bound term separator? expr     -> bounded_quantifier
                  | quantifier_kind var_list type_bound function_space separator? expr -> typed_quantifier
                  | quantifier_kind NAME expr                               -> unbounded_quantifier
prefix_quantifier: prefix_quantifier_kind var_list bound term separator? unary -> bounded_prefix_quantifier
                 | prefix_quantifier_kind var_list type_bound function_space separator? unary -> typed_prefix_quantifier
quantifier_kind: FORALL | EXISTS_UNIQUE | EXISTS
prefix_quantifier_kind: PFORALL | PEXISTS_UNIQUE | PEXISTS
var_list: NAME ("," NAME)*
bound: IN | SUBSETEQ | SUBSET
type_bound: COLON
separator: "," | ";"

predicate: OPERATOR "(" term_list ")"
relation: term relation_op term
relation_op: MODELS | VDASH | EQUIV | NOTIN | NEQ | IN | SUBSETEQ | SUBSET | COLON | MAPSTO | COMPOSE | LEQ | GEQ | LT | GT | EQUALS
?term: function_space
?function_space: product TO term
               | product
?product: atom TIMES product
        | atom
?atom: application
     | operator_application
     | FORMULA_OBJECT             -> raw_term
     | tuple
     | RESTRICTED_TERM            -> raw_term
     | SYNTAX_SET_LITERAL         -> raw_term
     | SET_LITERAL                -> set_literal
     | RAW_TERM                   -> raw_term
     | NUMBER                     -> number
     | LT                         -> symbol_variable
     | GT                         -> symbol_variable
     | PLUS                       -> symbol_variable
     | COMPOSE                    -> symbol_variable
     | MATHCAL_NAME               -> mathcal_variable
     | NAME                       -> variable
mathcal_call: MATHCAL_NAME "(" [term_list] ")" -> raw_mathcal_call
application: NAME "(" term_list ")"
operator_application: OPERATOR "(" term_list ")"
tuple: "(" term_list ")"
term_list: term ("," term)*

FORALL: "FORALL"
EXISTS_UNIQUE: "EXISTS_UNIQUE"
EXISTS: "EXISTS"
PFORALL: "PFORALL"
PEXISTS_UNIQUE: "PEXISTS_UNIQUE"
PEXISTS: "PEXISTS"
IFF: "IFF"
METAIMPLIES: "METAIMPLIES"
IMPLIES: "IMPLIES"
OR: "OR"
AND: "AND"
NEG: "NEG"
IN: "IN"
NOTIN: "NOTIN"
SUBSETEQ: "SUBSETEQ"
SUBSET: "SUBSET"
NEQ: "NEQ"
MODELS: "MODELS"
VDASH: "VDASH"
EQUIV: "EQUIV"
COLON: "COLON"
TO: "TO"
TIMES: "TIMES"
CUP: "CUP"
CAP: "CAP"
SETMINUS: "SETMINUS"
MAPSTO: "MAPSTO"
COMPOSE: "COMPOSE"
LEQ: "LEQ"
GEQ: "GEQ"
LT: "<"
GT: ">"
PLUS: "+"
EQUALS: "="
OPERATOR: /OP_[A-Za-z][A-Za-z0-9_]*/
MATHCAL_NAME: /mathcal_[A-Za-z]_mathrm[A-Za-z]+/
FORMULA_OBJECT: /\([^()]*\b(?:IFF|IMPLIES|OR|AND|NEG)\b[^()]*\)/
RESTRICTED_TERM: /[A-Za-z][A-Za-z0-9_]*\|_\{[^{}]+\}/
SYNTAX_SET_LITERAL: /\\\{[^{}]*\b(?:NEG|AND|OR|TO|IFF|IMPLIES)\b[^{}]*\\\}/
SET_LITERAL: /\\\{[^{}]+\\\}/
RAW_ATOM: /(?!(FORALL|EXISTS_UNIQUE|EXISTS|PFORALL|PEXISTS_UNIQUE|PEXISTS|IFF|METAIMPLIES|IMPLIES|OR|AND|NEG|IN|SUBSETEQ|SUBSET|NOTIN|NEQ|MODELS|VDASH|EQUIV|COLON|TO|TIMES|CUP|CAP|SETMINUS|MAPSTO|COMPOSE|LEQ|GEQ)\b)(?:(?!\b(?:IFF|METAIMPLIES|IMPLIES|OR|AND)\b).)+\\text\{[^{}]*\}(?:(?!\b(?:IFF|METAIMPLIES|IMPLIES|OR|AND)\b).)*/
RAW_TERM: /\\?\{(?:(?!\b(?:IFF|METAIMPLIES|IMPLIES|OR|AND)\b).)+\\text\{[^{}]*\}(?:(?!\b(?:IFF|METAIMPLIES|IMPLIES|OR|AND)\b).)+\\?\}/
ZERO_PREDICATE: /[PR]_\d+/
NAME: /(?!OP_[A-Za-z])(?!FORALL\b|EXISTS_UNIQUE\b|EXISTS\b|PFORALL\b|PEXISTS_UNIQUE\b|PEXISTS\b|IFF\b|METAIMPLIES\b|IMPLIES\b|OR\b|AND\b|NEG\b|IN\b|SUBSETEQ\b|SUBSET\b|NOTIN\b|NEQ\b|MODELS\b|VDASH\b|EQUIV\b|COLON\b|TO\b|TIMES\b|CUP\b|CAP\b|SETMINUS\b|MAPSTO\b|COMPOSE\b|LEQ\b|GEQ\b)(?:[A-Za-z][A-Za-z0-9_]*|\d+_[A-Za-z][A-Za-z0-9_]*)(?:\^\*)?/
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
    text = re.sub(r"\\begin\{(?:aligned|align\*?|split|gathered)\}", "", text)
    text = re.sub(r"\\end\{(?:aligned|align\*?|split|gathered)\}", "", text)
    text = re.sub(r"\\\\(?:\[[^\]]*\])?", " ", text)
    text = text.replace("&", " ")
    text = re.sub(r"\\mathbb\{([^{}]+)\}", r"mathbb_\1", text)
    text = re.sub(r"\\mathcal\{([^{}]+)\}", r"mathcal_\1", text)
    text = re.sub(r"\\mathsf\{([^{}]+)\}", r"mathsf_\1", text)
    text = re.sub(r"\\mathcal\s+([A-Za-z])(?!_\{)", r"mathcalspace_\1", text)
    text = re.sub(r"\\mathcal\s+([A-Za-z])", r"mathcal_\1", text)
    text = re.sub(r"\\mathrm\{([^{}]+)\}", r"mathrm_\1", text)
    text = re.sub(r"(mathcal_[A-Za-z])_\{mathrm_([a-z]+)\}", r"\1_mathrm\2", text)
    text = re.sub(r"\\operatorname\{([A-Za-z][A-Za-z0-9]*)\}", r"OP_\1", text)
    text = re.sub(r"\\widehat\s*([A-Za-z])", r"widehat_\1", text)
    text = re.sub(r"\\infty\b", "infty", text)
    text = re.sub(r"_\{([^{}\s]+)\\in\s*([^{}]+)\}", r"_{\1COMPACTIN_\2}", text)
    text = re.sub(r"\\(?:Bigl|Bigr|bigl|bigr|left|right)(?![A-Za-z])", "", text)
    text = re.sub(r"\b([A-Za-z][A-Za-z0-9_]*|mathcal_[A-Za-z]|mathbb_[A-Za-z])_\{(\d+)\}", r"\1_\2", text)
    text = re.sub(r"\b([PR]_\d+)\s*\(", r"OP_\1(", text)
    text = re.sub(r"\\text\{\s*and\s*\}", " AND ", text, flags=re.I)
    text = re.sub(r"\\text\{\s*or\s*\}", " OR ", text, flags=re.I)
    text = re.sub(r"\\text\{\s*implies\s*\}", " IMPLIES ", text, flags=re.I)
    text = re.sub(r"\\text\{\s*if\s+and\s+only\s+if\s*\}", " IFF ", text, flags=re.I)
    text = re.sub(
        r"\((\\(?:forall|exists!|exists)\s+[^()]*?(?:\\in|\\subseteq|\\subset|\\colon|:)[^()]*)\)\s*(?:\\[,;!]\s*)?",
        parenthesized_quantifier_prefix,
        text,
    )
    text = re.sub(r"\((\\(?:forall|exists!|exists)\s+[^()]*)\)\s*\(", r"\1(", text)
    replacements = [
        (r"\\Longleftrightarrow|\\Leftrightarrow|\\leftrightarrow|\\iff", " IFF "),
        (r"\\Longrightarrow|\\Rightarrow|\\implies", " METAIMPLIES "),
        (r"\\rightarrow", " IMPLIES "),
        (r"\\forall", " FORALL "),
        (r"\\exists!", " EXISTS_UNIQUE "),
        (r"\\exists", " EXISTS "),
        (r"\\notin", " NOTIN "),
        (r"\\subseteq", " SUBSETEQ "),
        (r"\\subset", " SUBSET "),
        (r"\\neg", " NEG "),
        (r"\\neq|\\ne(?![A-Za-z])", " NEQ "),
        (r"\\models", " MODELS "),
        (r"\\vdash", " VDASH "),
        (r"\\equiv", " EQUIV "),
        (r"\\uparrow", " UPARROW "),
        (r"\\downarrow", " DOWNARROW "),
        (r"\\leq", " LEQ "),
        (r"\\geq|\\ge", " GEQ "),
        (r"\\in", " IN "),
        (r"\\mapsto", " MAPSTO "),
        (r"\\circ", " COMPOSE "),
        (r"\\coloneqq", " COLON = "),
        (r"\\colon|:", " COLON "),
        (r"\\to(?=(?:mathbb_|mathcal_|mathrm_|[A-Z]))", " TO "),
        (r"\\to(?![A-Za-z])", " TO "),
        (r"\\times", " TIMES "),
        (r"\\cup", " CUP "),
        (r"\\cap", " CAP "),
        (r"\\setminus", " SETMINUS "),
        (r"\\land", " AND "),
        (r"\\lor", " OR "),
        (r"\\(?:qquad|quad|,|;|!)", " "),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)
    text = re.sub(r"\b([PR]_\d+)\s*\(", r"OP_\1(", text)
    text = re.sub(r"\\(?!text\b)([A-Za-z]+)(?=\s*\()", r"\1", text)
    text = re.sub(r"\\(?!text\b)([A-Za-z]+)", r"\1", text)
    text = re.sub(r"\\(?=\s)", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    while text.endswith("."):
        text = text[:-1].strip()
    while text.endswith(","):
        text = text[:-1].strip()
    return text


def parenthesized_quantifier_prefix(match: re.Match[str]) -> str:
    inner = match.group(1).removeprefix("\\")
    if inner.startswith("forall"):
        return " PFORALL " + inner.removeprefix("forall") + r"\; "
    if inner.startswith("exists!"):
        return " PEXISTS_UNIQUE " + inner.removeprefix("exists!") + r"\; "
    return " PEXISTS " + inner.removeprefix("exists") + r"\; "


def binder_id(symbol: str) -> str:
    mathrm = re.fullmatch(r"mathrm_([A-Za-z]+)", symbol.strip())
    if mathrm:
        return f"mathrm{mathrm.group(1)}"
    mathbb_subscript = re.fullmatch(r"mathbb_([A-Za-z])_(\d+)", symbol.strip())
    if mathbb_subscript:
        return f"mathbb{mathbb_subscript.group(1)}_{mathbb_subscript.group(2)}"
    mathcal_subscript = re.fullmatch(r"mathcal_([A-Za-z])_(\d+)", symbol.strip())
    if mathcal_subscript:
        return f"mathcal{mathcal_subscript.group(1)}_{mathcal_subscript.group(2)}"
    mathbb = re.fullmatch(r"mathbb_([A-Za-z])", symbol.strip())
    if mathbb:
        return f"mathbb{mathbb.group(1)}"
    mathcal = re.fullmatch(r"mathcal_([A-Za-z])", symbol.strip())
    if mathcal:
        return f"mathcal{mathcal.group(1)}"
    mathsf = re.fullmatch(r"mathsf_([A-Za-z]+)", symbol.strip())
    if mathsf:
        return f"mathsf{mathsf.group(1)}"
    mathcal_space = re.fullmatch(r"mathcalspace_([A-Za-z])", symbol.strip())
    if mathcal_space:
        return f"mathcal_{mathcal_space.group(1)}"
    return symbol.strip()


def predicate_surface_name(name: str) -> str:
    match = re.fullmatch(r"([PR])_(\d+)", name)
    if match:
        return f"{match.group(1)}_{{{match.group(2)}}}"
    return name


def relation_symbol(value: str) -> str:
    return {
        "IN": r"\in",
        "NOTIN": r"\notin",
        "NEQ": r"\neq",
        "MODELS": r"\models",
        "VDASH": r"\vdash",
        "EQUIV": r"\equiv",
        "SUBSETEQ": r"\subseteq",
        "SUBSET": r"\subset",
        "COLON": r"\colon",
        "MAPSTO": r"\mapsto",
        "COMPOSE": r"\circ",
        "LEQ": r"\leq",
        "GEQ": r"\geq",
        "LT": "<",
        "GT": ">",
        "<": "<",
        ">": ">",
        "=": "=",
    }[value]


TERM_OPERATION_SYMBOLS = {
    "CUP": r"\cup",
    "SETMINUS": r"\setminus",
    "CAP": r"\cap",
    "COMPOSE": r"\circ",
}


TERM_OPERATION_PRECEDENCE = (
    ["CUP"],
    ["SETMINUS"],
    ["CAP"],
    ["COMPOSE"],
)


RELATION_TOKENS = (
    "MODELS",
    "VDASH",
    "EQUIV",
    "NOTIN",
    "SUBSETEQ",
    "SUBSET",
    "NEQ",
    "LEQ",
    "GEQ",
    "IN",
    "MAPSTO",
    "COLON",
)


def contains_top_level_normalized_relation(text: str) -> bool:
    if text.lstrip().startswith(("FORALL ", "EXISTS ", "EXISTS_UNIQUE ")):
        return False
    if re.search(
        r"\b(?:FORALL|EXISTS_UNIQUE|EXISTS)\s+[^,;()]*?\b(?:IN|SUBSETEQ|SUBSET|COLON)\b\s*[^,;()]+$",
        text,
    ):
        return False
    return any(split_top_level_token(text, [token]) for token in RELATION_TOKENS) or any(
        split_top_level_char(text, [operator]) for operator in ["=", "<", ">"]
    )


def looks_like_structured_formula_operand(text: str) -> bool:
    stripped = strip_outer_group_normalized(text.strip())
    if stripped.startswith(("FORALL ", "EXISTS ", "EXISTS_UNIQUE ", "PFORALL ", "PEXISTS ")):
        return True
    if stripped.startswith("NEG "):
        return True
    if contains_top_level_normalized_relation(stripped):
        return True
    return any(split_top_level_token(stripped, [token]) for token in ["IFF", "METAIMPLIES", "IMPLIES", "OR", "AND"])


def token_term(value):
    if isinstance(value, dict):
        return value
    text = str(value)
    if text.isdigit():
        return {"kind": "constant", "name": text}
    return {"kind": "variable", "binder_id": binder_id(text)}


def mathcal_binder_id(value: str) -> str:
    match = re.fullmatch(r"mathcal_([A-Za-z])_mathrm([A-Za-z]+)", value)
    if match:
        return f"mathcal_{match.group(1)}_mathrm{match.group(2)}"
    return binder_id(value)


def binder_symbol(value: str) -> str:
    if value in {"alpha", "beta", "gamma", "delta", "epsilon", "theta", "lambda", "mu", "phi", "varphi"}:
        return "\\" + value
    subscript = re.fullmatch(r"([A-Za-z]+)_(\d+)", value)
    if subscript:
        return f"{subscript.group(1)}_{{{subscript.group(2)}}}"
    return value


def mathcal_raw_latex(value: str) -> str:
    match = re.fullmatch(r"mathcal_([A-Za-z])_mathrm([A-Za-z]+)\((.*)\)", value)
    if match:
        return f"mathcal {match.group(1)}_{{mathrm_{match.group(2)}}}({match.group(3)})"
    return canonical_raw_latex(value)


def restore_raw_token_text(value: str, *, compact_parenthesized: bool = True) -> str:
    original = value
    text = re.sub(r"\bmathbb_([A-Za-z])\b", r"mathbb\1", value)
    text = text.replace("COMPACTIN", "in")
    text = re.sub(r"\bmathcalspace_([A-Za-z])\b", r"mathcal_\1", text)
    text = re.sub(r"\bOP_([A-Za-z][A-Za-z0-9_]*)", r"operatorname{\1}", text)
    replacements = {
        "NEG": "neg",
        "AND": "land",
        "OR": "lor",
        "TO": "to",
        "TIMES": "times",
        "IFF": "leftrightarrow",
        "IMPLIES": "rightarrow",
        "IN": "in",
        "NOTIN": "notin",
        "SUBSETEQ": "subseteq",
        "SUBSET": "subset",
        "MAPSTO": "mapsto",
        "MODELS": "models",
        "VDASH": "vdash",
        "EQUIV": "equiv",
        "COLON": "COLON",
        "FORALL": "forall",
        "EXISTS_UNIQUE": "exists!",
        "EXISTS": "exists",
        "COMPOSE": "circ",
        "LEQ": "leq",
        "GEQ": "ge",
        "CUP": "cup",
        "CAP": "cap",
        "SETMINUS": "setminus",
    }
    for token, surface in replacements.items():
        text = re.sub(rf"\b{token}\b", surface, text)
    if compact_parenthesized and original.strip().startswith("("):
        text = re.sub(r"\s+", "", text)
    if text.strip().startswith(r"\{") and r"\text" not in text:
        text = re.sub(r"\s*,\s*", ",", text)
        text = re.sub(r"\\\{\s*", r"\\{", text)
        text = re.sub(r"\s*\\\}", r"\\}", text)
    text = re.sub(r"(?<=[)\w])\s+in\s+(?=[A-Za-z])", "in ", text)
    text = re.sub(r"(?<=[A-Za-z])in\s+(?=[A-Za-z])", "in", text)
    text = re.sub(r"(?<=[)\w])\s+mapsto\s+", "mapsto ", text)
    text = re.sub(r"(?<=[)\]\w])\s+models\s+(?=[A-Za-z])", "models", text)
    text = re.sub(r"(?<=[)\w])\s+vdash\s+(?=[A-Za-z])", "vdash", text)
    return text


def term_surface(value: dict[str, Any]) -> str:
    if value.get("kind") == "constant":
        return str(value.get("name"))
    if value.get("kind") == "variable":
        return str(value.get("binder_id"))
    if value.get("kind") == "raw_latex":
        return str(value.get("latex"))
    return canonical_raw_latex(str(value))


def balanced_normalized(text: str) -> bool:
    depth = 0
    for char in text:
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def strip_outer_group_normalized(text: str) -> str:
    text = text.strip()
    while text.startswith("(") and text.endswith(")") and balanced_normalized(text[1:-1]):
        text = text[1:-1].strip()
    while text.startswith("[") and text.endswith("]") and balanced_normalized(text[1:-1]):
        text = text[1:-1].strip()
    return text


def split_top_level_char(text: str, operators: list[str]) -> tuple[str, str, str] | None:
    depth = 0
    i = 0
    while i < len(text):
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
                    return text[:i].strip(), operator, text[i + len(operator) :].strip()
        i += 1
    return None


def split_top_level_equal_chain_normalized(text: str) -> list[str] | None:
    parts: list[str] = []
    depth = 0
    start = 0
    i = 0
    while i < len(text):
        char = text[i]
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == "=" and depth == 0:
            previous = text[:i].rstrip()
            if previous.endswith("COLON"):
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


def equality_chain_sequence_normalized(parts: list[str]) -> dict[str, Any]:
    relations = [
        {"kind": "relation", "relation": "=", "left": generic_term(left), "right": generic_term(right)}
        for left, right in zip(parts, parts[1:])
    ]
    ast = relations[-1]
    for relation in reversed(relations[:-1]):
        ast = {"kind": "formula_sequence", "left": relation, "right": ast}
    return ast


def split_top_level_token(text: str, tokens: list[str]) -> tuple[str, str, str] | None:
    return split_top_level_char(text, [f" {token} " for token in tokens])


def split_normalized_arguments(text: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    start = 0
    for index, char in enumerate(text):
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(text[start:index].strip())
            start = index + 1
    tail = text[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def normalized_surface_text(text: str) -> str:
    text = text.strip()
    text = text.replace("mathcalspace_", "MATHCALSPACE_")
    text = re.sub(r"\s+\bIN\b\s+", " __IN__ ", text)
    text = re.sub(r"\s*\bMAPSTO\b\s+", "mapsto_", text)
    text = re.sub(r"\s*\bCOMPOSE\b\s*", " circ ", text)
    for token, surface in (
        ("AND", "land"),
        ("OR", "lor"),
        ("TO", "to"),
        ("IFF", "leftrightarrow"),
        ("IMPLIES", "rightarrow"),
    ):
        text = re.sub(rf"\s*\b{token}\b\s*", surface, text)
    text = restore_raw_token_text(text, compact_parenthesized=False)
    text = text.replace("__IN__", "in")
    text = re.sub(r"OP_([A-Za-z][A-Za-z0-9_]*)", r"operatorname\1", text)
    text = re.sub(r"\bmathbb_([A-Za-z])\b", r"mathbb\1", text)
    text = re.sub(r"\bmathcal_([A-Za-z])\b", r"mathcal\1", text)
    text = re.sub(r"\bmathsf_([A-Za-z]+)\b", r"mathsf\1", text)
    text = re.sub(r"mathbb_([A-Za-z])(?=[A-Za-z0-9_>/])", r"mathbb\1", text)
    text = re.sub(r"mathcal_([A-Za-z])(?=[A-Za-z])", r"mathcal\1", text)
    text = re.sub(r"\bMATHCALSPACE_([A-Za-z])\b", r"mathcal_\1", text)
    text = re.sub(r"\bmathrm_([A-Za-z]+)\b", r"mathrm\1", text)
    text = re.sub(r"\s*setminus\s+", "setminus ", text)
    text = re.sub(r"\s*circ\s+", " circ ", text)
    for word in ("land", "lor", "to", "leftrightarrow", "rightarrow"):
        text = re.sub(rf"\s*{word}\s*", word, text)
    text = text.replace(r"\{", "").replace(r"\}", "")
    text = text.replace("{", "").replace("}", "")
    text = text.replace(" ", "_")
    text = text.replace("\\", "")
    text = re.sub(r"_+", "_", text)
    text = re.sub(r"mapsto_(?=(?:llbracket|operatorname|mathcal_|mathbb))", "mapsto", text)
    text = text.replace("_)", ")").replace("(_", "(")
    return text


def normalized_finite_set_literal(text: str) -> dict[str, Any]:
    restored = restore_raw_token_text(text)
    return {"kind": "raw_latex", "latex": canonical_finite_set_literal(restored)}


def normalized_set_builder_literal(text: str) -> dict[str, Any]:
    restored = restore_raw_token_text(text)
    restored = re.sub(r"(?<=[A-Za-z])in(?=[A-Z])", "in ", restored)
    if not restored.startswith(r"\{"):
        restored = r"\{" + restored.removeprefix("{")
    if not restored.endswith(r"\}"):
        restored = restored.removesuffix("}") + r"\}"
    restored = re.sub(r"\bmid(?=\s*[^{}]*(?:vdash|models))", " mid ", restored)
    restored = re.sub(r"\bmid(?=\S)", "mid ", restored)
    return {"kind": "raw_latex", "latex": canonical_raw_set_builder(restored)}


def is_normalized_finite_set_literal(text: str) -> bool:
    return text.startswith(r"\{") and text.endswith(r"\}") and not re.search(
        r"\\text\{|\\(?:mid)\b|\bmid\b|[A-Z]mid\b|mid(?=[A-Z])|\bCOLON\b|\bVDASH\b|\bMODELS\b|(?<!\\)[:|]",
        text,
    )


def generic_term(text: str) -> dict[str, Any]:
    text = strip_outer_group_normalized(text.strip())
    if not text:
        raise SemanticLarkParseError("empty term")
    if not balanced_normalized(text):
        raise SemanticLarkParseError(f"unbalanced term: {text}")
    if (text.startswith(r"\{") and text.endswith(r"\}")) or (text.startswith("{") and text.endswith("}")):
        if is_normalized_finite_set_literal(text):
            return normalized_finite_set_literal(text)
        return normalized_set_builder_literal(text)
    if re.search(r"\bsim(?:_\{|[_\s])|[A-Za-z]sim\s|\bsuccsim\b|\bsucc\b|mathbin", text):
        return generic_raw_atom(text)
    if re.search(r"^[A-Za-z][A-Za-z0-9_']*mid\s*\(", text):
        return {"kind": "raw_latex", "latex": canonical_raw_latex(restore_raw_token_text(text, compact_parenthesized=False))}
    if re.search(r"\b(?:IFF|IMPLIES|AND|OR)\b", text):
        return generic_raw_atom(text)
    if re.search(r"\)\s+\([^()]*(?:\bTO\b|toinfty)[^()]*\)$", text):
        return {"kind": "raw_latex", "latex": canonical_raw_latex(restore_raw_token_text(text, compact_parenthesized=False))}
    if text.isdigit():
        return {"kind": "constant", "name": text}
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*\[[^\]]*/[^\]]*\]", text):
        return generic_raw_atom(text)
    function_space = split_top_level_token(text, ["TO"])
    if function_space:
        left, _op, right = function_space
        return {
            "kind": "application",
            "function": "function_space",
            "arguments": [generic_term(left), generic_term(right)],
        }
    indexed = re.match(r"^(?P<operator>bigcup|bigcap)_\{(?P<index>[^{}]+)\}(?P<body>.+)$", text, re.S)
    if indexed:
        index_text = indexed.group("index").strip()
        body_text = indexed.group("body").strip()
        if not body_text:
            raise SemanticLarkParseError(f"indexed term operation has no body: {text}")
        compact_index = re.fullmatch(r"(?P<binder>\S+)COMPACTIN_(?P<domain>.+)", index_text)
        spaced_index = split_top_level_token(index_text, ["IN"])
        if compact_index:
            index = {
                "binder_id": binder_id(compact_index.group("binder")),
                "domain": generic_term(compact_index.group("domain")),
            }
        elif spaced_index:
            binder, _op, domain = spaced_index
            if not binder or not domain:
                raise SemanticLarkParseError(f"indexed term operation has malformed index: {text}")
            index = {"binder_id": binder_id(binder), "domain": generic_term(domain)}
        else:
            index = {"binder_id": binder_id(index_text), "domain": None}
        return {
            "kind": "indexed_term_operation",
            "operator": "\\" + indexed.group("operator"),
            "index": index,
            "body": generic_term(body_text),
        }
    for operators in TERM_OPERATION_PRECEDENCE:
        split = split_top_level_token(text, operators)
        if split:
            left, op, right = split
            if not left or not right:
                raise SemanticLarkParseError(f"term operation has missing operand: {text}")
            return {
                "kind": "term_operation",
                "operator": TERM_OPERATION_SYMBOLS[op.strip()],
                "left": generic_term(left),
                "right": generic_term(right),
            }
    stripped = text.strip()
    if stripped == "COMPOSE":
        return {"kind": "variable", "binder_id": "circ"}
    if stripped not in TERM_OPERATION_SYMBOLS and re.search(r"(?:^|\s)(?:CUP|SETMINUS|CAP|COMPOSE)\s*$|^(?:CUP|SETMINUS|CAP|COMPOSE)(?:\s|$)", stripped):
        raise SemanticLarkParseError(f"term operation has missing operand: {text}")
    product = split_top_level_token(text, ["TIMES"])
    if product:
        left, _op, right = product
        return {
            "kind": "application",
            "function": "cartesian_product",
            "arguments": [generic_term(left), generic_term(right)],
        }
    parts = split_normalized_arguments(text)
    if len(parts) > 1:
        return {"kind": "tuple", "elements": [generic_term(part) for part in parts]}
    call = re.fullmatch(r"(?P<name>[A-Za-z][A-Za-z0-9_]*|OP_[A-Za-z][A-Za-z0-9_]*|mathcal_[A-Za-z])\((?P<args>.*)\)", text, re.S)
    if call and (balanced_normalized(call.group("args")) or ")(" in call.group("args")):
        name = call.group("name")
        if not call.group("args").strip():
            raise SemanticLarkParseError(f"application has no arguments: {text}")
        arguments_text = call.group("args")
        nested_call_index = arguments_text.find(")(")
        if nested_call_index >= 0:
            first_arg = arguments_text[:nested_call_index].strip()
            later_args = arguments_text[nested_call_index + 2 :].strip()
            args = [generic_term(first_arg), *[generic_term(part) for part in split_normalized_arguments(later_args)]]
        else:
            args = [generic_term(part) for part in split_normalized_arguments(arguments_text)]
        if name.startswith("OP_"):
            surface_name = predicate_surface_name(name.removeprefix("OP_"))
            predicate_id = resolve_predicate_id(surface_name, len(args))
            if predicate_id != default_predicate_id(surface_name):
                return {
                    "kind": "predicate",
                    "predicate_id": predicate_id,
                    "name": surface_name,
                    "arguments": args,
                }
            surface = ",".join(term_surface(arg) for arg in args)
            return {"kind": "variable", "binder_id": f"operatorname{surface_name}({surface})"}
        return {"kind": "application", "function": binder_id(name), "arguments": args}
    return {"kind": "variable", "binder_id": normalized_surface_text(text)}


def generic_raw_atom(text: str) -> dict[str, Any]:
    if re.search(r"\bsim(?:_\{|[_\s])|[A-Za-z]sim\s|\bsuccsim\b|\bsucc\b|mathbin", text):
        return {"kind": "raw_latex", "latex": canonical_raw_latex(restore_raw_token_text(text))}
    restored = restore_raw_token_text(text, compact_parenthesized=False)
    if r"\{" in restored and re.search(r"\bmid\b|\bBigm\||\bCOLON\b|\bin\b|\bforall\b|\bexists\b", restored):
        return {"kind": "raw_latex", "latex": canonical_raw_set_builder(restored)}
    latex = normalized_surface_text(text)
    latex = latex.replace("_therefore_", " therefore ").replace("_therefore", " therefore")
    latex = latex.replace(",_", ", ")
    return {"kind": "raw_latex", "latex": canonical_raw_latex(latex)}


def normalized_formula_object_text(text: str) -> str:
    restored = text.strip()
    replacements = {
        "FORALL": r"\forall ",
        "EXISTS_UNIQUE": r"\exists! ",
        "EXISTS": r"\exists ",
        "NEG": r"\neg",
        "AND": r" \land ",
        "OR": r" \lor ",
        "TO": r" \to ",
        "IFF": r" \leftrightarrow ",
        "UPARROW": r" \uparrow ",
        "DOWNARROW": r" \downarrow ",
        "COMPOSE": r" \circ ",
    }
    for token, surface in replacements.items():
        restored = re.sub(rf"\s*\b{token}\b\s*", lambda _match, surface=surface: surface, restored)
    restored = restore_raw_token_text(restored, compact_parenthesized=False)
    restored = re.sub(
        r"\\(land|lor|to|leftrightarrow|uparrow|downarrow|circ)(?=[A-Za-z\\])",
        r"\\\1 ",
        restored,
    )
    restored = re.sub(r"(?<!\\)\buparrow\b", r"\\uparrow", restored)
    restored = re.sub(r"(?<!\\)\bdownarrow\b", r"\\downarrow", restored)
    restored = re.sub(r"(?<!\\)\bneg\b", r"\\neg", restored)
    restored = re.sub(r"(?<!\\)\bland\b", r"\\land", restored)
    restored = re.sub(r"(?<!\\)\blor\b", r"\\lor", restored)
    restored = re.sub(r"(?<!\\)\bto\b", r"\\to", restored)
    restored = re.sub(r"(?<!\\)\bleftrightarrow\b", r"\\leftrightarrow", restored)
    restored = re.sub(r"(?<!\\)\bcirc\b", r"\\circ", restored)
    return restored


def parse_normalized_formula_object(text: str) -> dict[str, Any]:
    if contains_top_level_normalized_relation(text) and not split_top_level_token(text, ["EQUIV"]):
        return parse_generic_formula(text)
    return parse_formula_object(normalized_formula_object_text(text))


def parse_generic_formula(text: str) -> dict[str, Any]:
    text = strip_outer_group_normalized(text)
    if not text:
        raise SemanticLarkParseError("empty formula")
    if not balanced_normalized(text):
        raise SemanticLarkParseError(f"unbalanced formula: {text}")
    if re.search(
        r"(?:\b(?:MODELS|VDASH|EQUIV|NOTIN|SUBSETEQ|SUBSET|NEQ|LEQ|GEQ|IN|MAPSTO|COLON|TO|TIMES)\b|[=<>])\s*$",
        text,
    ):
        raise SemanticLarkParseError(f"relation has missing side: {text}")
    if re.search(r"\b(?:IFF|METAIMPLIES|IMPLIES|OR|AND)\s*$", text):
        raise SemanticLarkParseError(f"connective has missing side: {text}")
    if " therefore " in text:
        return generic_raw_atom(text)
    sequence = split_top_level_char(text, [","])
    if sequence:
        left, _op, right = sequence
        if contains_top_level_normalized_relation(left) and contains_top_level_normalized_relation(right):
            return {"kind": "formula_sequence", "left": parse_generic_formula(left), "right": parse_generic_formula(right)}
    prefix_quantifier = re.match(
        r"^(?P<kind>PFORALL|PEXISTS_UNIQUE|PEXISTS)\s+"
        r"(?P<vars>[A-Za-z][A-Za-z0-9_']*(?:\s*,\s*[A-Za-z][A-Za-z0-9_']*)*)\s+"
        r"(?P<bound>IN|SUBSETEQ|SUBSET|COLON)\s+"
        r"(?P<domain>.+?)"
        r"(?:\s*[,;]\s*|\s+)"
        r"(?P<body>.+)$",
        text,
        re.S,
    )
    if prefix_quantifier:
        kind = {"PFORALL": "forall", "PEXISTS_UNIQUE": "exists_unique", "PEXISTS": "exists"}[
            prefix_quantifier.group("kind")
        ]
        domain = generic_term(prefix_quantifier.group("domain"))
        if prefix_quantifier.group("bound") in {"SUBSETEQ", "SUBSET"}:
            domain = {"kind": "application", "function": "subset_of", "arguments": [domain]}
        body = parse_generic_formula(prefix_quantifier.group("body"))
        for symbol in reversed([item.strip() for item in prefix_quantifier.group("vars").split(",")]):
            body = {
                "kind": kind,
                "binder": {"binder_id": binder_id(symbol), "symbol": binder_symbol(symbol), "domain": domain},
                "restriction": None,
                "body": body,
            }
        return body
    split = split_top_level_token(text, ["METAIMPLIES"])
    if split:
        left, _op, right = split
        if not left or not right:
            raise SemanticLarkParseError(f"connective has missing side: {text}")
        return {"kind": "implies", "left": parse_generic_formula(left), "right": parse_generic_formula(right)}
    split = split_top_level_token(text, ["IFF"])
    if split:
        left, _op, right = split
        left = left.rstrip()
        if not left.endswith("COLON"):
            split = None
        else:
            left = left[: -len("COLON")].rstrip()
    if split:
        if not left or not right:
            raise SemanticLarkParseError(f"connective has missing side: {text}")
        return {"kind": "iff", "left": parse_generic_formula(left), "right": parse_generic_formula(right)}
    if " EQUIV " in text:
        split = split_top_level_token(text, ["IFF"])
        if split:
            left, _op, right = split
            if not left or not right:
                raise SemanticLarkParseError(f"connective has missing side: {text}")
            if looks_like_structured_formula_operand(left) and looks_like_structured_formula_operand(right):
                return {"kind": "iff", "left": parse_generic_formula(left), "right": parse_generic_formula(right)}
        for tokens, kind in ((["METAIMPLIES", "IMPLIES"], "implies"), (["OR"], "or"), (["AND"], "and")):
            split = split_top_level_token(text, tokens)
            if split:
                left, _op, right = split
                if not left or not right:
                    raise SemanticLarkParseError(f"connective has missing side: {text}")
                if kind in {"iff", "implies"} or (
                    looks_like_structured_formula_operand(left) and looks_like_structured_formula_operand(right)
                ):
                    return {"kind": kind, "left": parse_generic_formula(left), "right": parse_generic_formula(right)}
        sequence = split_top_level_char(text, [","])
        if sequence:
            left, _op, right = sequence
            if not left or not right:
                raise SemanticLarkParseError(f"formula sequence has missing item: {text}")
            return {"kind": "formula_sequence", "left": parse_generic_formula(left), "right": parse_generic_formula(right)}
        split = split_top_level_token(text, ["EQUIV"])
        if split:
            left, _op, right = split
            if not left or not right:
                raise SemanticLarkParseError(f"relation has missing side: {text}")
            return {
                "kind": "relation",
                "relation": r"\equiv",
                "left": parse_normalized_formula_object(left),
                "right": parse_normalized_formula_object(right),
            }
    quantifier = re.match(
        r"^(?P<kind>FORALL|EXISTS_UNIQUE|EXISTS)\s+"
        r"(?P<vars>[A-Za-z][A-Za-z0-9_']*(?:\s*,\s*[A-Za-z][A-Za-z0-9_']*)*)\s+"
        r"(?P<bound>IN|SUBSETEQ|SUBSET|COLON)\s+"
        r"(?P<domain>.+?)"
        r"(?:\s*[,;]\s*|\s+)"
        r"(?P<body>.+)$",
        text,
        re.S,
    )
    if quantifier:
        kind = {"FORALL": "forall", "EXISTS_UNIQUE": "exists_unique", "EXISTS": "exists"}[quantifier.group("kind")]
        domain = generic_term(quantifier.group("domain"))
        if quantifier.group("bound") in {"SUBSETEQ", "SUBSET"}:
            domain = {"kind": "application", "function": "subset_of", "arguments": [domain]}
        body = parse_generic_formula(quantifier.group("body"))
        for symbol in reversed([item.strip() for item in quantifier.group("vars").split(",")]):
            body = {
                "kind": kind,
                "binder": {"binder_id": binder_id(symbol), "symbol": binder_symbol(symbol), "domain": domain},
                "restriction": None,
                "body": body,
            }
        return body
    unbounded_quantifier = re.match(
        r"^(?P<kind>FORALL|EXISTS_UNIQUE|EXISTS)\s+"
        r"(?P<var>[A-Za-z][A-Za-z0-9_']*)(?:\s*,\s*|\s+)"
        r"(?P<body>.+)$",
        text,
        re.S,
    )
    if unbounded_quantifier:
        kind = {"FORALL": "forall", "EXISTS_UNIQUE": "exists_unique", "EXISTS": "exists"}[
            unbounded_quantifier.group("kind")
        ]
        symbol = unbounded_quantifier.group("var")
        return {
            "kind": kind,
            "binder": {"binder_id": binder_id(symbol), "symbol": binder_symbol(symbol), "domain": None},
            "restriction": None,
            "body": parse_generic_formula(unbounded_quantifier.group("body")),
        }
    for tokens, kind in ((["IFF"], "iff"), (["METAIMPLIES", "IMPLIES"], "implies"), (["OR"], "or"), (["AND"], "and")):
        split = split_top_level_token(text, tokens)
        if split:
            left, _op, right = split
            return {"kind": kind, "left": parse_generic_formula(left), "right": parse_generic_formula(right)}
    equality_chain = split_top_level_equal_chain_normalized(text)
    if equality_chain:
        return equality_chain_sequence_normalized(equality_chain)
    if text.startswith("NEG "):
        return {"kind": "not", "operand": parse_generic_formula(text[4:].strip())}
    for token in RELATION_TOKENS:
        split = split_top_level_token(text, [token])
        if split:
            left, _op, right = split
            is_definition = token == "COLON" and right.startswith("=")
            if is_definition:
                right = right[1:].strip()
            if not left or not right or right == "=":
                raise SemanticLarkParseError(f"relation has missing side: {text}")
            if token == "EQUIV":
                return {
                    "kind": "relation",
                    "relation": relation_symbol(token),
                    "left": parse_normalized_formula_object(left),
                    "right": parse_normalized_formula_object(right),
                }
            if is_definition and re.search(
                r"\bmid\b|\bBigm\||\bFORALL\b|\bEXISTS\b|\bSUBSETEQ\b|\bIN\b|\bCOLON\b|(?<!\^)=",
                right,
            ):
                right_ast = generic_raw_atom(right)
            else:
                right_ast = generic_term(right)
            return {
                "kind": "relation",
                "relation": relation_symbol(token),
                "left": generic_term(left),
                "right": right_ast,
            }
    for operator in ["=", "<", ">"]:
        split = split_top_level_char(text, [operator])
        if split:
            left, _op, right = split
            if not left or not right:
                raise SemanticLarkParseError(f"relation has missing side: {text}")
            return {
                "kind": "relation",
                "relation": operator,
                "left": generic_term(left),
                "right": generic_term(right),
            }
    if re.search(r"\bsim(?:_\{|[_\s])|[A-Za-z]sim\s|\bsuccsim\b|\bsucc\b|mathbin", text) or re.search(
        r"\b(?:IFF|IMPLIES|AND|OR|TO)\b", text
    ):
        return generic_raw_atom(text)
    return generic_term(text)


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
            "symbol": binder_symbol(symbol),
            "domain": restriction["right"],
        },
        "restriction": None,
        "body": body["right"],
    }


@v_args(inline=True)
class AstTransformer(Transformer):
    def quantifier(self, item):
        return item

    def number(self, token):
        return {"kind": "constant", "name": str(token)}

    def variable(self, token):
        return {"kind": "variable", "binder_id": binder_id(str(token))}

    def zero_predicate(self, token):
        name = predicate_surface_name(str(token))
        predicate_id = resolve_predicate_id(name, 0)
        if predicate_id == default_predicate_id(name):
            return {"kind": "variable", "binder_id": binder_id(str(token))}
        return {
            "kind": "predicate",
            "predicate_id": predicate_id,
            "name": name,
            "arguments": [],
        }

    def symbol_variable(self, token):
        if str(token) == "COMPOSE":
            return {"kind": "variable", "binder_id": "circ"}
        return {"kind": "variable", "binder_id": str(token)}

    def mathcal_variable(self, token):
        return {"kind": "variable", "binder_id": mathcal_binder_id(str(token))}

    def set_literal(self, token):
        text = str(token)
        if is_normalized_finite_set_literal(text):
            return normalized_finite_set_literal(text)
        return normalized_set_builder_literal(text)

    def raw_term(self, token):
        text = str(token)
        if is_normalized_finite_set_literal(text):
            return normalized_finite_set_literal(text)
        if (text.startswith(r"\{") and text.endswith(r"\}")) or (text.startswith("{") and text.endswith("}")):
            return normalized_set_builder_literal(text)
        return {"kind": "raw_latex", "latex": canonical_raw_latex(restore_raw_token_text(text))}

    def application(self, name, terms=None):
        return {
            "kind": "application",
            "function": binder_id(str(name)),
            "arguments": terms or [],
        }

    def operator_application(self, operator, terms):
        name = str(operator).removeprefix("OP_")
        surface_name = predicate_surface_name(name)
        predicate_id = resolve_predicate_id(surface_name, len(terms))
        if predicate_id != default_predicate_id(surface_name):
            return {
                "kind": "predicate",
                "predicate_id": predicate_id,
                "name": surface_name,
                "arguments": terms,
            }
        surface = ",".join(term_surface(term) for term in terms)
        return {"kind": "variable", "binder_id": f"operatorname{name}({surface})"}

    def raw_mathcal_call(self, name, terms=None):
        surface = ",".join(term_surface(term) for term in (terms or []))
        return {"kind": "raw_latex", "latex": mathcal_raw_latex(f"{name}({surface})")}

    def function_space(self, left, _to, right):
        return {"kind": "application", "function": "function_space", "arguments": [token_term(left), token_term(right)]}

    def product(self, left, _times, right):
        return {"kind": "application", "function": "cartesian_product", "arguments": [token_term(left), token_term(right)]}

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
        surface_name = predicate_surface_name(name)
        arguments = terms or []
        return {
            "kind": "predicate",
            "predicate_id": resolve_predicate_id(surface_name, len(arguments)),
            "name": surface_name,
            "arguments": arguments,
        }

    def var_list(self, *tokens):
        return [str(token) for token in tokens]

    def bound(self, token):
        return str(token)

    def quantifier_kind(self, token):
        return str(token)

    def prefix_quantifier(self, item):
        return item

    def prefix_quantifier_kind(self, token):
        return str(token)

    def _quantifier_kind(self, quantifier):
        if str(quantifier) in {"FORALL", "PFORALL"}:
            return "forall"
        if str(quantifier) in {"EXISTS_UNIQUE", "PEXISTS_UNIQUE"}:
            return "exists_unique"
        return "exists"

    def bounded_quantifier(self, quantifier, variables, bound, domain, *tail):
        body = tail[-1]
        if bound in {"SUBSETEQ", "SUBSET"}:
            domain = {
                "kind": "application",
                "function": "subset_of",
                "arguments": [domain],
            }
        kind = self._quantifier_kind(quantifier)
        ast = body
        for symbol in reversed(variables):
            ast = {
                "kind": kind,
                "binder": {
                    "binder_id": binder_id(symbol),
                    "symbol": binder_symbol(symbol),
                    "domain": domain,
                },
                "restriction": None,
                "body": ast,
            }
        return ast

    def typed_quantifier(self, quantifier, variables, _bound, domain, *tail):
        body = tail[-1]
        kind = self._quantifier_kind(quantifier)
        ast = body
        for symbol in reversed(variables):
            ast = {
                "kind": kind,
                "binder": {
                    "binder_id": binder_id(symbol),
                    "symbol": binder_symbol(symbol),
                    "domain": domain,
                },
                "restriction": None,
                "body": ast,
            }
        return ast

    def bounded_prefix_quantifier(self, quantifier, variables, bound, domain, *tail):
        return self.bounded_quantifier(quantifier, variables, bound, domain, *tail)

    def typed_prefix_quantifier(self, quantifier, variables, _bound, domain, *tail):
        return self.typed_quantifier(quantifier, variables, _bound, domain, *tail)

    def unbounded_quantifier(self, quantifier, symbol, body):
        symbol = str(symbol)
        kind = self._quantifier_kind(quantifier)
        desugared = desugar_expanded_quantifier(kind, symbol, body)
        if desugared:
            return desugared
        return {
            "kind": kind,
            "binder": {
                "binder_id": binder_id(symbol),
                "symbol": binder_symbol(symbol),
                "domain": None,
            },
            "restriction": None,
            "body": body,
        }

    def neg(self, *items):
        operand = items[-1]
        return {"kind": "not", "operand": operand}

    def raw_atom(self, token):
        return {"kind": "raw_latex", "latex": canonical_raw_latex(restore_raw_token_text(str(token)))}

    def conjunction(self, first, *rest):
        terms = [first] + [item for item in rest if str(item) != "AND"]
        ast = terms[-1]
        for item in reversed(terms[:-1]):
            ast = {"kind": "and", "left": item, "right": ast}
        return ast

    def disjunction(self, first, *rest):
        terms = [first] + [item for item in rest if str(item) != "OR"]
        ast = terms[-1]
        for item in reversed(terms[:-1]):
            ast = {"kind": "or", "left": item, "right": ast}
        return ast

    def implies(self, left, *rest):
        if not rest:
            return left
        right = rest[-1]
        return {"kind": "implies", "left": left, "right": right}

    def iff(self, first, *rest):
        terms = [first] + [item for item in rest if str(item) != "IFF"]
        ast = terms[-1]
        for item in reversed(terms[:-1]):
            ast = {"kind": "iff", "left": item, "right": ast}
        return ast


def parse_formula(latex: str) -> dict[str, Any]:
    normalized = normalize_latex(latex)
    if " EQUIV " in normalized:
        if r"\text{" in normalized:
            return {"kind": "raw_latex", "latex": canonical_raw_latex(restore_raw_token_text(normalized, compact_parenthesized=False))}
        return parse_generic_formula(normalized)
    if re.search(r"\bsim(?:_\{|[_\s])|[A-Za-z]sim\s|\bsuccsim\b|\bsucc\b|mathbin", normalized):
        return parse_generic_formula(normalized)
    if re.search(
        r"\bMETAIMPLIES\s+(?:FORALL|EXISTS_UNIQUE|EXISTS)\s+[A-Za-z][A-Za-z0-9_]*\s+"
        r"(?!IN\b|SUBSETEQ\b|SUBSET\b|COLON\b)",
        normalized,
    ):
        return parse_generic_formula(normalized)
    normalized = normalized.replace(" METAIMPLIES ", " IMPLIES ")
    try:
        tree = PARSER.parse(normalized)
    except Exception as exc:  # pragma: no cover - Lark exception hierarchy is broad.
        try:
            return parse_generic_formula(normalized)
        except Exception as fallback_exc:
            raise SemanticLarkParseError(f"could not parse controlled formula: {latex!r}") from fallback_exc
    return AstTransformer().transform(tree)


def parse_support_formula(latex: str) -> dict[str, Any]:
    ast = parse_formula(latex)
    return {
        "original_latex": latex,
        "normalized_formula": normalize_latex(latex),
        "ast": ast,
        "mechanical_negation_ast": negate_ast(ast),
    }
