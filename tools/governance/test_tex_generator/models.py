from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any


@dataclass(frozen=True)
class Symbol:
    id: str
    tex: str
    category: str
    value_type: str
    arity: int | None = None
    argument_types: tuple[str, ...] = ()
    return_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["argument_types"] = list(self.argument_types)
        return data


@dataclass(frozen=True)
class Formula:
    kind: str
    children: tuple["Formula", ...] = ()
    symbol: str | None = None
    arguments: tuple[str, ...] = ()
    binder: str | None = None
    domain: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "symbol": self.symbol,
            "arguments": list(self.arguments),
            "binder": self.binder,
            "domain": self.domain,
            "children": [child.to_dict() for child in self.children],
        }


@dataclass
class GeneratedCase:
    id: str
    universe_version: int
    canonical_hash: str
    rendering_hash: str
    construction: dict[str, Any]
    tex: str
    canonical_formula: dict[str, Any]
    expected: dict[str, Any]
    synthetic_registry: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
