from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import random
from typing import Any

from .config import GenerationConfig
from .models import Formula, GeneratedCase
from .state import GeneratorState
from .universe import Universe


@dataclass
class UniverseTestGenerator:
    config: GenerationConfig
    state: GeneratorState

    def __post_init__(self) -> None:
        self.rng = random.Random(self.config.seed + self.state.case_count)
        self.universe = Universe(self.state, self.rng)
        self.universe.ensure_minimum()

    def choose_least_covered(self, dimension: str, values: list[Any]) -> Any:
        if self.config.strategy == "random":
            return self.rng.choice(values)
        minimum = min(self.state.coverage_count(dimension, str(v)) for v in values)
        candidates = [v for v in values if self.state.coverage_count(dimension, str(v)) == minimum]
        return self.rng.choice(candidates)

    def symbol_for_type(self, typ: str) -> dict[str, Any]:
        map_types = {
            "element": "element", "ambient": "ambient", "number": "constant",
            "set": "set", "structure": "structure", "function": "function",
            "predicate": "predicate", "relation": "relation", "number_system": "number_system",
        }
        category = map_types[typ]
        choices = self.universe.by_category(category)
        if not choices:
            getattr(self.universe, f"create_{category}")()
            choices = self.universe.by_category(category)
        return self.rng.choice(choices)

    def atom(self) -> Formula:
        category = self.choose_least_covered(
            "atomic_category",
            [
                "predicate",
                "relation",
                "membership",
                "equality",
                "subset",
                "satisfaction",
                "provability",
                "equivalence_relation",
                "typed_signature",
                "restriction_equality",
                "syntax_set_membership",
            ],
        )
        if category in {"predicate", "relation"}:
            symbols = self.universe.by_category(category)
            symbol = self.choose_least_covered("arity", [s for s in symbols if s.get("arity") in self.config.predicate_arities])
            args = tuple(self.symbol_for_type(t)["id"] for t in symbol.get("argument_types", []))
            return Formula(category, symbol=symbol["id"], arguments=args)
        if category == "membership":
            return Formula("membership", arguments=(self.symbol_for_type("element")["id"], self.symbol_for_type("ambient")["id"]))
        if category == "equality":
            typ = self.rng.choice(["element", "set", "structure", "number"])
            return Formula("equality", arguments=(self.symbol_for_type(typ)["id"], self.symbol_for_type(typ)["id"]))
        if category == "satisfaction":
            return Formula("satisfaction", arguments=(self.symbol_for_type("structure")["id"], self.symbol_for_type("relation")["id"]))
        if category == "provability":
            return Formula("provability", arguments=(self.symbol_for_type("set")["id"], self.symbol_for_type("predicate")["id"]))
        if category == "equivalence_relation":
            return Formula("equivalence_relation", arguments=(self.symbol_for_type("relation")["id"], self.symbol_for_type("predicate")["id"]))
        if category == "typed_signature":
            return Formula(
                "typed_signature",
                arguments=(
                    self.symbol_for_type("function")["id"],
                    self.symbol_for_type("ambient")["id"],
                    self.symbol_for_type("number_system")["id"],
                ),
            )
        if category == "restriction_equality":
            return Formula(
                "restriction_equality",
                arguments=(
                    self.symbol_for_type("function")["id"],
                    self.symbol_for_type("relation")["id"],
                    self.symbol_for_type("function")["id"],
                    self.symbol_for_type("relation")["id"],
                ),
            )
        if category == "syntax_set_membership":
            return Formula("syntax_set_membership")
        return Formula("subset", arguments=(self.symbol_for_type("set")["id"], self.symbol_for_type("ambient")["id"]))

    def formula(self, depth: int = 0, qdepth: int = 0) -> Formula:
        if depth >= self.config.max_formula_depth:
            return self.atom()
        forms = ["atom"] + self.config.connectives + self.config.quantifiers
        if qdepth >= self.config.max_quantifier_depth:
            forms = [f for f in forms if f not in self.config.quantifiers]
        kind = self.choose_least_covered("formula_kind", forms)
        if kind == "atom":
            return self.atom()
        if kind == "not":
            return Formula("not", children=(self.formula(depth + 1, qdepth),))
        if kind in {"and", "or", "implies", "iff"}:
            return Formula(kind, children=(self.formula(depth + 1, qdepth), self.formula(depth + 1, qdepth)))
        binder = self.symbol_for_type("element")["id"]
        domain = self.symbol_for_type("ambient")["id"]
        return Formula(kind, children=(self.formula(depth + 1, qdepth + 1),), binder=binder, domain=domain)

    def render_symbol(self, sid: str) -> str:
        return self.state.symbols[sid]["tex"]

    def render_formula(self, f: Formula, renderer: str) -> str:
        if f.kind in {"predicate", "relation"}:
            name = self.render_symbol(f.symbol or "")
            args = ",".join(self.render_symbol(a) for a in f.arguments)
            return name if not f.arguments else rf"{name}\bigl({args}\bigr)"
        if f.kind == "membership":
            a, b = map(self.render_symbol, f.arguments)
            return rf"{a}\in {b}"
        if f.kind == "equality":
            a, b = map(self.render_symbol, f.arguments)
            return rf"{a}={b}"
        if f.kind == "subset":
            a, b = map(self.render_symbol, f.arguments)
            return rf"{a}\subseteq {b}"
        if f.kind == "satisfaction":
            a, b = map(self.render_symbol, f.arguments)
            return rf"{a}\models {b}"
        if f.kind == "provability":
            a, b = map(self.render_symbol, f.arguments)
            return rf"{a}\vdash {b}"
        if f.kind == "equivalence_relation":
            a, b = map(self.render_symbol, f.arguments)
            return rf"{a}\equiv {b}"
        if f.kind == "typed_signature":
            function, domain, codomain = map(self.render_symbol, f.arguments)
            return rf"{function}:{domain}\to {codomain}"
        if f.kind == "restriction_equality":
            left_function, left_scope, right_function, right_scope = map(self.render_symbol, f.arguments)
            return (
                rf"{left_function}|_{{\operatorname{{Var}}({left_scope})}}="
                rf"{right_function}|_{{\operatorname{{Var}}({right_scope})}}"
            )
        if f.kind == "syntax_set_membership":
            return r"\circ\in\{\neg,\land,\lor,\to,\leftrightarrow\}"
        if f.kind == "not":
            return rf"\neg\bigl({self.render_formula(f.children[0], renderer)}\bigr)"
        if f.kind in {"and", "or", "implies", "iff"}:
            left = self.render_formula(f.children[0], renderer)
            right = self.render_formula(f.children[1], renderer)
            symbolic = {"and": r"\land", "or": r"\lor", "implies": r"\rightarrow", "iff": r"\leftrightarrow"}
            text = {
                "and": r" \quad\text{and}\quad ",
                "or": r" \quad\text{or}\quad ",
                "implies": r" \quad\text{implies}\quad ",
                "iff": r" \quad\text{if and only if}\quad ",
            }
            op = text[f.kind] if renderer == "text-connectives" else rf"\,{symbolic[f.kind]}\,"
            return rf"\bigl({left}{op}{right}\bigr)"
        binder = self.render_symbol(f.binder or "")
        domain = self.render_symbol(f.domain or "")
        body = self.render_formula(f.children[0], renderer)
        q = {"forall": r"\forall", "exists": r"\exists", "exists_unique": r"\exists!"}[f.kind]
        if renderer == "expanded-quantifiers" and f.kind == "forall":
            return rf"({q} {binder})\bigl({binder}\in {domain}\rightarrow {body}\bigr)"
        if renderer == "expanded-quantifiers" and f.kind in {"exists", "exists_unique"}:
            return rf"({q} {binder})\bigl({binder}\in {domain}\land {body}\bigr)"
        return rf"({q} {binder}\in {domain})\,{body}"

    def discourse(self, formula_tex: str, form: str) -> str:
        ambient = self.rng.choice(self.universe.by_category("ambient"))["tex"]
        structure = self.rng.choice(self.universe.by_category("structure"))["tex"]
        element = self.rng.choice(self.universe.by_category("element"))["tex"]
        openings = {
            "formula": rf"\[{formula_tex}\]",
            "let-suppose-then": rf"Let \({ambient}\) be a test ambient, and let \({element}\in {ambient}\).\n\nSuppose that\n\[{formula_tex}\]\nThen\n\[{formula_tex}\]",
            "let-assume-therefore": rf"Let \({structure}\) be a test structure with ambient \({ambient}\).\n\nAssume that\n\[{formula_tex}\]\nTherefore,\n\[{formula_tex}\]",
            "given-it-follows": rf"Given a test ambient \({ambient}\), suppose\n\[{formula_tex}\]\nIt follows that\n\[{formula_tex}\]",
        }
        return openings[form]

    def features(self, f: Formula) -> dict[str, Any]:
        kinds: list[str] = []
        arities: list[int] = []
        max_qdepth = 0

        def walk(node: Formula, current_q: int = 0) -> None:
            nonlocal max_qdepth
            kinds.append(node.kind)
            if node.kind in {"predicate", "relation"} and node.symbol:
                arities.append(int(self.state.symbols[node.symbol].get("arity", 0)))
            nq = current_q + 1 if node.kind in {"forall", "exists", "exists_unique"} else current_q
            max_qdepth = max(max_qdepth, nq)
            for child in node.children:
                walk(child, nq)

        walk(f)
        return {"node_kinds": kinds, "predicate_arities": arities, "quantifier_depth": max_qdepth}

    def generate_one(self) -> GeneratedCase:
        for _ in range(1000):
            formula = self.formula()
            renderer = self.choose_least_covered("renderer", self.config.renderers)
            discourse_form = self.choose_least_covered("discourse", self.config.discourse_forms)
            tex_formula = self.render_formula(formula, renderer)
            tex = self.discourse(tex_formula, discourse_form)
            canonical_json = json.dumps(formula.to_dict(), sort_keys=True)
            canonical_hash = hashlib.sha256(canonical_json.encode()).hexdigest()
            rendering_hash = hashlib.sha256(tex.encode()).hexdigest()
            if rendering_hash in self.state.rendering_hashes:
                continue
            case_id = self.state.next_id("case", "TestCase")
            features = self.features(formula)
            construction = {"renderer": renderer, "discourse": discourse_form, **features}
            expected = {
                "syntactically_intended_valid": True,
                "root_kind": formula.kind,
                "quantifier_depth": features["quantifier_depth"],
                "predicate_arities": features["predicate_arities"],
                "canonical_formula_hash": canonical_hash,
            }
            self.state.canonical_hashes.add(canonical_hash)
            self.state.rendering_hashes.add(rendering_hash)
            self.state.case_count += 1
            for key, value in [("renderer", renderer), ("discourse", discourse_form), ("root_kind", formula.kind)]:
                self.state.increment_coverage(key, str(value))
            for kind in features["node_kinds"]:
                self.state.increment_coverage("node_kind", kind)
            for arity in features["predicate_arities"]:
                self.state.increment_coverage("predicate_arity", str(arity))
            self.state.increment_coverage("quantifier_depth", str(features["quantifier_depth"]))
            return GeneratedCase(
                case_id,
                self.state.universe_version,
                canonical_hash,
                rendering_hash,
                construction,
                tex,
                formula.to_dict(),
                expected,
                self.state.synthetic_registry(),
            )
        raise RuntimeError("Unable to generate a unique case after 1000 attempts")

    def generate(self) -> list[GeneratedCase]:
        return [self.generate_one() for _ in range(self.config.count)]
