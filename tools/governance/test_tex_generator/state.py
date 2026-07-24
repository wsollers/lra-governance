from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json


DEFAULT_COUNTERS = {
    "type": 1,
    "ambient": 1,
    "number_system": 1,
    "structure": 1,
    "element": 1,
    "set": 1,
    "predicate": 1,
    "relation": 1,
    "function": 1,
    "operation": 1,
    "constant": 1,
    "case": 1,
}


@dataclass
class GeneratorState:
    universe_version: int = 1
    counters: dict[str, int] = field(default_factory=lambda: dict(DEFAULT_COUNTERS))
    symbols: dict[str, dict[str, Any]] = field(default_factory=dict)
    coverage: dict[str, dict[str, int]] = field(default_factory=dict)
    canonical_hashes: set[str] = field(default_factory=set)
    rendering_hashes: set[str] = field(default_factory=set)
    case_count: int = 0

    @classmethod
    def load(cls, path: str | Path) -> "GeneratorState":
        path = Path(path)
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        data["canonical_hashes"] = set(data.get("canonical_hashes", []))
        data["rendering_hashes"] = set(data.get("rendering_hashes", []))
        return cls(**data)

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "universe_version": self.universe_version,
            "counters": self.counters,
            "symbols": self.symbols,
            "coverage": self.coverage,
            "canonical_hashes": sorted(self.canonical_hashes),
            "rendering_hashes": sorted(self.rendering_hashes),
            "case_count": self.case_count,
        }
        path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    def next_id(self, category: str, prefix: str) -> str:
        value = self.counters.setdefault(category, 1)
        self.counters[category] = value + 1
        return f"{prefix}{value:02d}"

    def increment_coverage(self, dimension: str, value: str) -> None:
        bucket = self.coverage.setdefault(dimension, {})
        bucket[value] = bucket.get(value, 0) + 1

    def coverage_count(self, dimension: str, value: str) -> int:
        return self.coverage.get(dimension, {}).get(value, 0)

    def synthetic_registry(self) -> dict[str, Any]:
        return {
            "schema_version": "test-tex-generator.synthetic-registry/1.0",
            "universe_version": self.universe_version,
            "symbols": {
                symbol_id: self.symbols[symbol_id]
                for symbol_id in sorted(self.symbols)
            },
        }
