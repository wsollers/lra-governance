from __future__ import annotations

from dataclasses import dataclass
import random

from .models import Symbol
from .registry import load_testing_symbols
from .state import GeneratorState


TYPE_POOL = ["element", "ambient", "number", "set", "structure", "function", "relation", "number_system"]
SYNTHETIC_PREDICATE_ARITIES = {
    1: 2, 2: 0, 3: 0, 4: 4, 5: 4, 6: 0, 7: 0, 8: 3, 9: 4, 10: 4,
    11: 2, 12: 4, 13: 0, 14: 4, 15: 4, 16: 4, 17: 2, 18: 1, 19: 4,
    20: 0, 21: 4, 22: 3, 23: 4, 24: 0, 25: 0, 26: 2, 27: 2, 28: 2,
}
SYNTHETIC_RELATION_ARITIES = {
    1: 3, 2: 3, 3: 3, 4: 3, 5: 3, 6: 4, 7: 2, 8: 2, 9: 2, 10: 3, 11: 3, 12: 3,
}


@dataclass
class Universe:
    state: GeneratorState
    rng: random.Random

    def ensure_minimum(self) -> None:
        self.seed_testing_symbols()
        requirements = {
            "type": 8,
            "ambient": 6,
            "number_system": 3,
            "structure": 6,
            "element": 18,
            "set": 6,
            "predicate": 28,
            "relation": 12,
            "function": 16,
            "operation": 8,
            "constant": 8,
        }
        for category, target in requirements.items():
            while self.count(category) < target:
                getattr(self, f"create_{category}")()

    def seed_testing_symbols(self) -> None:
        for symbol in load_testing_symbols():
            self.state.symbols[symbol.id] = symbol.to_dict()

    def count(self, category: str) -> int:
        return sum(1 for symbol in self.state.symbols.values() if symbol["category"] == category)

    def add(self, symbol: Symbol) -> Symbol:
        self.state.symbols[symbol.id] = symbol.to_dict()
        self.state.universe_version += 1
        return symbol

    def by_category(self, category: str) -> list[dict]:
        return [s for s in self.state.symbols.values() if s["category"] == category]

    def create_type(self) -> Symbol:
        sid = self.state.next_id("type", "TestType")
        return self.add(Symbol(sid, sid, "type", "type"))

    def create_ambient(self) -> Symbol:
        sid = self.state.next_id("ambient", "TestAmbient")
        tex = f"A_{{{int(sid[-2:])}}}"
        return self.add(Symbol(sid, tex, "ambient", "ambient", metadata={"element_type": "element"}))

    def create_number_system(self) -> Symbol:
        sid = self.state.next_id("number_system", "TestNumberSystem")
        tex = f"\\mathbb{{T}}_{{{int(sid[-2:])}}}"
        return self.add(Symbol(sid, tex, "number_system", "number_system", metadata={"element_type": "number"}))

    def create_structure(self) -> Symbol:
        sid = self.state.next_id("structure", "TestStructure")
        tex = f"\\mathcal{{T}}_{{{int(sid[-2:])}}}"
        return self.add(Symbol(sid, tex, "structure", "structure"))

    def create_element(self) -> Symbol:
        sid = self.state.next_id("element", "TestElement")
        tex = f"x_{{{int(sid[-2:])}}}"
        return self.add(Symbol(sid, tex, "element", "element"))

    def create_set(self) -> Symbol:
        sid = self.state.next_id("set", "TestSet")
        tex = f"S_{{{int(sid[-2:])}}}"
        return self.add(Symbol(sid, tex, "set", "set"))

    def create_constant(self) -> Symbol:
        sid = self.state.next_id("constant", "TestConstant")
        tex = f"c_{{{int(sid[-2:])}}}"
        return self.add(Symbol(sid, tex, "constant", self.rng.choice(["element", "number", "structure"])))

    def _argument_types(self, arity: int) -> tuple[str, ...]:
        if arity == 0:
            return ()
        mode = self.rng.choice(["homogeneous", "heterogeneous"])
        if mode == "homogeneous":
            typ = self.rng.choice(TYPE_POOL)
            return tuple(typ for _ in range(arity))
        return tuple(self.rng.choice(TYPE_POOL) for _ in range(arity))

    def create_predicate(self, arity: int | None = None) -> Symbol:
        sid = self.state.next_id("predicate", "TestPredicate")
        index = int(sid[-2:])
        arity = SYNTHETIC_PREDICATE_ARITIES.get(index, self.rng.choice([0, 1, 2, 3, 4])) if arity is None else arity
        tex = f"P_{{{int(sid[-2:])}}}"
        return self.add(Symbol(sid, tex, "predicate", "truth", arity, self._argument_types(arity)))

    def create_relation(self, arity: int | None = None) -> Symbol:
        sid = self.state.next_id("relation", "TestRelation")
        index = int(sid[-2:])
        arity = SYNTHETIC_RELATION_ARITIES.get(index, self.rng.choice([2, 3, 4])) if arity is None else arity
        tex = f"R_{{{int(sid[-2:])}}}"
        return self.add(Symbol(sid, tex, "relation", "truth", arity, self._argument_types(arity)))

    def create_function(self, arity: int | None = None) -> Symbol:
        sid = self.state.next_id("function", "TestFunction")
        arity = self.rng.choice([0, 1, 2, 3]) if arity is None else arity
        tex = f"f_{{{int(sid[-2:])}}}"
        args = self._argument_types(arity)
        ret = self.rng.choice(TYPE_POOL[:-2])
        return self.add(Symbol(sid, tex, "function", "function", arity, args, ret))

    def create_operation(self, arity: int | None = None) -> Symbol:
        sid = self.state.next_id("operation", "TestOperation")
        arity = self.rng.choice([1, 2, 3]) if arity is None else arity
        tex = f"\\star_{{{int(sid[-2:])}}}"
        typ = self.rng.choice(["element", "number"])
        return self.add(Symbol(sid, tex, "operation", "function", arity, tuple(typ for _ in range(arity)), typ))
