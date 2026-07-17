#!/usr/bin/env python3
"""Augment semantic artifacts with deterministic support ASTs.

This module does not rewrite mathematical source text.  It preserves the
original LaTeX strings and replaces only machine AST fields that can be parsed
by the governed support-fragment grammar.
"""

from __future__ import annotations

import argparse
import copy
import re
from pathlib import Path
from typing import Any

import yaml

from semantic_latex_ast import SemanticLatexParseError, negate_ast, parse_formula
from semantic_lark_logic_parser import SemanticLarkParseError, parse_formula as parse_formula_lark


DISPLAY_RE = re.compile(r"\\\[(?P<body>.*?)\\\]", re.S)
REMARK_RE = re.compile(
    r"\\begin\{remark\*\}\[(?P<title>[^\]]+)\](?P<body>.*?)\\end\{remark\*\}",
    re.S,
)


def display_body(latex: str) -> str:
    text = latex.strip()
    match = DISPLAY_RE.search(text)
    return match.group("body").strip() if match else text


def remark_display(corrected_tex: str, title_fragment: str) -> str | None:
    target = title_fragment.lower()
    for match in REMARK_RE.finditer(corrected_tex):
        title = match.group("title").lower()
        if target not in title:
            continue
        body = match.group("body")
        display = DISPLAY_RE.search(body)
        return (display.group("body") if display else body).strip()
    return None


def parse_or_keep(latex: str) -> dict[str, Any] | None:
    try:
        return parse_formula(display_body(latex))
    except Exception:
        return None


def parser_witnesses(latex: str) -> dict[str, Any]:
    witnesses: dict[str, Any] = {"original_latex": latex}
    hand_ast = None
    lark_ast = None
    try:
        hand_ast = parse_formula(display_body(latex))
        witnesses["hand_parser"] = {"available": True, "ast": hand_ast}
    except Exception as exc:
        witnesses["hand_parser"] = {"available": False, "error": str(exc)}
    try:
        lark_ast = parse_formula_lark(display_body(latex))
        witnesses["lark_parser"] = {"available": True, "ast": lark_ast}
    except Exception as exc:
        witnesses["lark_parser"] = {"available": False, "error": str(exc)}
    witnesses["parsers_agree"] = hand_ast is not None and hand_ast == lark_ast
    return witnesses


def collect_free_symbols(node: Any, bound: set[str] | None = None) -> set[str]:
    if bound is None:
        bound = set()
    if not isinstance(node, dict):
        return set()
    kind = node.get("kind")
    if kind == "variable":
        binder_id = str(node.get("binder_id") or "")
        return set() if not binder_id or binder_id in bound else {binder_id}
    if kind in {"forall", "exists", "exists_unique"}:
        binder = node.get("binder") or {}
        binder_id = str(binder.get("binder_id") or "")
        free = collect_free_symbols(binder.get("domain"), bound)
        new_bound = set(bound)
        if binder_id:
            new_bound.add(binder_id)
        free.update(collect_free_symbols(node.get("restriction"), new_bound))
        free.update(collect_free_symbols(node.get("body"), new_bound))
        return free
    free: set[str] = set()
    if kind == "application":
        function_name = str(node.get("function") or "")
        if function_name:
            free.add(function_name)
    for key, value in node.items():
        if key in {"kind", "function"}:
            continue
        if isinstance(value, dict):
            free.update(collect_free_symbols(value, bound))
        elif isinstance(value, list):
            for item in value:
                free.update(collect_free_symbols(item, bound))
    return free


def ensure_parameters(data: dict[str, Any], asts: list[dict[str, Any]]) -> None:
    existing = {
        str(item.get("id"))
        for item in data.get("parameters", []) or []
        if isinstance(item, dict) and item.get("id")
    }
    parameters = data.setdefault("parameters", [])
    for symbol in sorted(set().union(*(collect_free_symbols(ast) for ast in asts))):
        if symbol in existing:
            continue
        parameters.append({"id": symbol, "symbol": symbol})
        existing.add(symbol)


def augment_artifact(data: dict[str, Any], corrected_tex: str) -> dict[str, Any]:
    updated = copy.deepcopy(data)
    forms = updated.setdefault("logical_forms", {})
    parsed_asts: list[dict[str, Any]] = []
    standard = forms.setdefault("standard_quantified", {})
    standard_latex = str(standard.get("latex") or "")
    standard_ast = parse_or_keep(standard_latex)

    if standard_ast is not None:
        parsed_asts.append(standard_ast)
        standard["ast"] = standard_ast
        standard["parser_witnesses"] = parser_witnesses(standard_latex)
        statement = updated.setdefault("statement", {})
        statement["semantic_ast"] = standard_ast

        negation = forms.setdefault("negation", {})
        negation["mechanical"] = {
            "latex": r"\neg\left(" + display_body(standard_latex) + r"\right)",
            "ast": {"kind": "not", "operand": standard_ast},
        }
        negation["approved_normal_form"] = {
            "latex": None,
            "ast": negate_ast(standard_ast),
        }
        negation.setdefault("normalization_requires", [])

    predicate_latex = None
    existing_predicate = forms.get("predicate_reading")
    if isinstance(existing_predicate, dict) and existing_predicate.get("latex"):
        predicate_latex = str(existing_predicate["latex"])
    if predicate_latex is None:
        predicate_latex = remark_display(corrected_tex, "predicate reading")
    if predicate_latex:
        predicate_ast = parse_or_keep(predicate_latex)
        if predicate_ast is not None:
            parsed_asts.append(predicate_ast)
            forms["predicate_reading"] = {
                "latex": predicate_latex,
                "ast": predicate_ast,
                "parser_witnesses": parser_witnesses(predicate_latex),
            }

    if parsed_asts:
        ensure_parameters(updated, parsed_asts)

    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--corrected-tex", required=True, type=Path)
    parser.add_argument("--in-place", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    data = yaml.safe_load(args.artifact.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"{args.artifact}: YAML root must be a mapping")
    updated = augment_artifact(data, args.corrected_tex.read_text(encoding="utf-8"))
    text = yaml.safe_dump(updated, sort_keys=False, allow_unicode=True)
    if args.in_place:
        args.artifact.write_text(text, encoding="utf-8")
    elif args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
