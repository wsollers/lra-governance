from __future__ import annotations

import re
from typing import Any


ATOMIC_ARITY_KINDS = {"predicate", "relation"}
SYMBOL_ARGUMENT_KINDS = {
    "membership",
    "equality",
    "subset",
    "satisfaction",
    "provability",
    "equivalence_relation",
    "typed_signature",
    "restriction_equality",
}
QUANTIFIER_KINDS = {"forall", "exists", "exists_unique"}


def validate_case_registry(case: dict[str, Any]) -> None:
    registry = case.get("synthetic_registry")
    if not isinstance(registry, dict):
        raise ValueError("case is missing synthetic_registry")
    symbols = registry.get("symbols")
    if not isinstance(symbols, dict):
        raise ValueError("synthetic_registry is missing symbols")
    formula = case.get("canonical_formula")
    if not isinstance(formula, dict):
        raise ValueError("case is missing canonical_formula")
    _validate_formula(formula, symbols)


def extract_display_formulas(tex: str) -> list[str]:
    return [match.strip() for match in re.findall(r"\\\[(.*?)\\\]", tex, flags=re.S)]


def expected_governed_ast(case: dict[str, Any]) -> dict[str, Any]:
    validate_case_registry(case)
    symbols = case["synthetic_registry"]["symbols"]
    return _expected_formula(case["canonical_formula"], symbols)


def _validate_formula(formula: dict[str, Any], symbols: dict[str, dict[str, Any]]) -> None:
    kind = str(formula.get("kind") or "")
    symbol = formula.get("symbol")
    if kind in ATOMIC_ARITY_KINDS:
        _require_symbol(symbol, symbols)
        expected_arity = symbols[str(symbol)].get("arity")
        actual_arity = len(formula.get("arguments") or [])
        if expected_arity != actual_arity:
            raise ValueError(f"arity mismatch for {symbol}: registry has {expected_arity}, formula has {actual_arity}")
    if kind in SYMBOL_ARGUMENT_KINDS:
        for argument in formula.get("arguments") or []:
            _require_symbol(argument, symbols)
    if kind in QUANTIFIER_KINDS:
        _require_symbol(formula.get("binder"), symbols)
        _require_symbol(formula.get("domain"), symbols)
    for child in formula.get("children") or []:
        if not isinstance(child, dict):
            raise ValueError(f"invalid child formula for {kind}")
        _validate_formula(child, symbols)


def _expected_formula(formula: dict[str, Any], symbols: dict[str, dict[str, Any]]) -> dict[str, Any]:
    kind = str(formula.get("kind") or "")
    children = formula.get("children") or []
    if kind == "not":
        return {"kind": "not", "operand": _expected_formula(children[0], symbols)}
    if kind in {"and", "or", "implies", "iff"}:
        return {
            "kind": kind,
            "left": _expected_formula(children[0], symbols),
            "right": _expected_formula(children[1], symbols),
        }
    if kind in QUANTIFIER_KINDS:
        return {
            "kind": kind,
            "binder": {
                "binder_id": _symbol_binder_id(formula["binder"], symbols),
                "symbol": symbols[formula["binder"]]["tex"],
                "domain": _symbol_term(formula["domain"], symbols),
            },
            "restriction": None,
            "body": _expected_formula(children[0], symbols),
        }
    if kind == "membership":
        left, right = formula.get("arguments") or []
        return {"kind": "relation", "relation": r"\in", "left": _symbol_term(left, symbols), "right": _symbol_term(right, symbols)}
    if kind == "equality":
        left, right = formula.get("arguments") or []
        return {"kind": "relation", "relation": "=", "left": _symbol_term(left, symbols), "right": _symbol_term(right, symbols)}
    if kind == "subset":
        left, right = formula.get("arguments") or []
        return {"kind": "relation", "relation": r"\subseteq", "left": _symbol_term(left, symbols), "right": _symbol_term(right, symbols)}
    if kind == "satisfaction":
        left, right = formula.get("arguments") or []
        return {"kind": "relation", "relation": r"\models", "left": _symbol_term(left, symbols), "right": _symbol_term(right, symbols)}
    if kind == "provability":
        left, right = formula.get("arguments") or []
        return {"kind": "relation", "relation": r"\vdash", "left": _symbol_term(left, symbols), "right": _symbol_term(right, symbols)}
    if kind == "equivalence_relation":
        left, right = formula.get("arguments") or []
        return {
            "kind": "relation",
            "relation": r"\equiv",
            "left": {"kind": "formula_variable", "name": _symbol_term(left, symbols)["binder_id"]},
            "right": {"kind": "formula_variable", "name": _symbol_term(right, symbols)["binder_id"]},
        }
    if kind == "typed_signature":
        function, domain, codomain = formula.get("arguments") or []
        return {
            "kind": "relation",
            "relation": r"\colon",
            "left": _symbol_term(function, symbols),
            "right": {
                "kind": "application",
                "function": "function_space",
                "arguments": [_symbol_term(domain, symbols), _symbol_term(codomain, symbols)],
            },
        }
    if kind == "restriction_equality":
        left_function, left_scope, right_function, right_scope = formula.get("arguments") or []
        return {
            "kind": "relation",
            "relation": "=",
            "left": _raw_restriction_term(left_function, left_scope, symbols),
            "right": _raw_restriction_term(right_function, right_scope, symbols),
        }
    if kind == "syntax_set_membership":
        return {
            "kind": "relation",
            "relation": r"\in",
            "left": {"kind": "variable", "binder_id": "circ"},
            "right": {"kind": "raw_latex", "latex": "{neg,land,lor,to,leftrightarrow}"},
        }
    if kind in ATOMIC_ARITY_KINDS:
        symbol_id = str(formula["symbol"])
        symbol = symbols[symbol_id]
        prefix = "test-predicate" if kind == "predicate" else "test-relation"
        return {
            "kind": "predicate",
            "predicate_id": f"pred:{prefix}-{int(symbol_id[-2:])}",
            "name": symbol["tex"],
            "arguments": [_symbol_term(argument, symbols) for argument in formula.get("arguments") or []],
        }
    raise ValueError(f"unsupported canonical formula kind {kind}")


def _symbol_term(symbol_id: str, symbols: dict[str, dict[str, Any]]) -> dict[str, Any]:
    symbol = symbols[symbol_id]
    return {"kind": "variable", "binder_id": _binder_id(symbol["tex"])}


def _symbol_binder_id(symbol_id: str, symbols: dict[str, dict[str, Any]]) -> str:
    return _binder_id(symbols[symbol_id]["tex"])


def _binder_id(tex: str) -> str:
    return tex.strip().replace("\\", "").replace("{", "").replace("}", "")


def _raw_restriction_term(function_id: str, scope_id: str, symbols: dict[str, dict[str, Any]]) -> dict[str, Any]:
    function = _raw_symbol_text(symbols[function_id]["tex"])
    scope = _raw_symbol_text(symbols[scope_id]["tex"])
    return {"kind": "raw_latex", "latex": rf"{function}|_{{operatorname{{Var}}({scope})}}"}


def _raw_symbol_text(tex: str) -> str:
    return re.sub(r"\b([A-Za-z]+)_\{(\d+)\}", r"\1_\2", tex)


def _require_symbol(symbol_id: object, symbols: dict[str, dict[str, Any]]) -> None:
    if not isinstance(symbol_id, str) or symbol_id not in symbols:
        raise ValueError(f"unknown symbol {symbol_id}")
