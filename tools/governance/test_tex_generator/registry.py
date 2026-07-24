from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import Symbol


ROOT = Path(__file__).resolve().parents[3]


def load_testing_symbols(root: Path = ROOT) -> list[Symbol]:
    """Load production-registered synthetic test symbols.

    These entries deliberately live in the canonical registries with
    ``testing: true`` so generated TeX exercises the same registry-backed call
    path as ordinary governed TeX. Downstream extraction can filter them by the
    same flag.
    """

    symbols: list[Symbol] = []
    symbols.extend(_load_testing_notation(root / "notation.yaml"))
    symbols.extend(_load_testing_structures(root / "structures.yaml"))
    symbols.extend(_load_testing_predicates(root / "predicates.yaml"))
    return symbols


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _load_testing_notation(path: Path) -> list[Symbol]:
    symbols: list[Symbol] = []
    for item in _load_yaml(path).get("notation", []) or []:
        if not isinstance(item, dict) or item.get("testing") is not True:
            continue
        spec = item.get("test_symbol")
        if not isinstance(spec, dict):
            continue
        symbol_id = str(spec.get("id") or item.get("name") or item.get("id") or "")
        category = str(spec.get("category") or "")
        value_type = str(spec.get("value_type") or category)
        tex = str(item.get("symbol") or "")
        if not symbol_id or not category or not tex:
            continue
        symbols.append(
            Symbol(
                symbol_id,
                tex,
                category,
                value_type,
                _optional_int(spec.get("arity")),
                tuple(str(value) for value in spec.get("argument_types") or ()),
                str(spec["return_type"]) if spec.get("return_type") is not None else None,
                dict(spec.get("metadata") or {}),
            )
        )
    return symbols


def _load_testing_structures(path: Path) -> list[Symbol]:
    symbols: list[Symbol] = []
    for item in _load_yaml(path).get("structures", []) or []:
        if not isinstance(item, dict) or item.get("testing") is not True:
            continue
        if str(item.get("category") or "") != "synthetic_test_structure":
            continue
        symbol_id = str(item.get("name") or "")
        tex = str(item.get("constructor") or "")
        if symbol_id and tex:
            symbols.append(Symbol(symbol_id, tex, "structure", "structure"))
    return symbols


def _load_testing_predicates(path: Path) -> list[Symbol]:
    symbols: list[Symbol] = []
    for item in _load_yaml(path).get("predicates", []) or []:
        if not isinstance(item, dict) or item.get("testing") is not True:
            continue
        category = str(item.get("category") or "")
        if category not in {"synthetic_test_predicate", "synthetic_test_relation"}:
            continue
        symbol_id = str(item.get("name") or "")
        tex = _predicate_tex(item)
        symbol_category = "relation" if category == "synthetic_test_relation" else "predicate"
        argument_types = tuple(str(arg.get("role") or "element") for arg in item.get("arguments") or [] if isinstance(arg, dict))
        if symbol_id and tex:
            symbols.append(Symbol(symbol_id, tex, symbol_category, "truth", len(argument_types), argument_types))
    return symbols


def _predicate_tex(item: dict[str, Any]) -> str:
    for surface in item.get("surface_forms") or []:
        text = str(surface)
        if "_{" in text:
            return text
    return str(item.get("name") or "")


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)
