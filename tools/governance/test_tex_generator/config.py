from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import yaml


@dataclass
class GenerationConfig:
    count: int = 100
    seed: int = 1
    strategy: str = "least-covered"
    max_formula_depth: int = 4
    max_quantifier_depth: int = 3
    max_discourse_steps: int = 4
    predicate_arities: list[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])
    function_arities: list[int] = field(default_factory=lambda: [0, 1, 2, 3])
    connectives: list[str] = field(default_factory=lambda: ["not", "and", "or", "implies", "iff"])
    quantifiers: list[str] = field(default_factory=lambda: ["forall", "exists", "exists_unique"])
    discourse_forms: list[str] = field(default_factory=lambda: ["formula", "let-suppose-then", "let-assume-therefore", "given-it-follows"])
    renderers: list[str] = field(default_factory=lambda: ["house", "fully-parenthesized", "text-connectives", "expanded-quantifiers"])
    argument_modes: list[str] = field(default_factory=lambda: ["homogeneous", "heterogeneous"])
    required_features: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "GenerationConfig":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "seed": self.seed,
            "strategy": self.strategy,
            "max_formula_depth": self.max_formula_depth,
            "max_quantifier_depth": self.max_quantifier_depth,
            "max_discourse_steps": self.max_discourse_steps,
            "predicate_arities": self.predicate_arities,
            "function_arities": self.function_arities,
            "connectives": self.connectives,
            "quantifiers": self.quantifiers,
            "discourse_forms": self.discourse_forms,
            "renderers": self.renderers,
            "argument_modes": self.argument_modes,
            "required_features": self.required_features,
        }
