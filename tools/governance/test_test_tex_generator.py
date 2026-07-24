from test_tex_generator.config import GenerationConfig
from test_tex_generator.generator import UniverseTestGenerator
from test_tex_generator.models import Formula
from test_tex_generator.registry import load_testing_symbols
from test_tex_generator.state import GeneratorState
from test_tex_generator.validation import (
    expected_governed_ast,
    extract_display_formulas,
    validate_case_registry,
)
from semantic_lark_logic_parser import parse_formula as parse_lark_formula
from semantic_latex_ast import parse_formula as parse_hand_formula


def run_all_tests() -> None:
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            value()


def formula_symbol_ids(formula: dict) -> list[str]:
    ids = []
    for key in ("symbol", "binder", "domain"):
        value = formula.get(key)
        if isinstance(value, str):
            ids.append(value)
    ids.extend(value for value in formula.get("arguments") or [] if isinstance(value, str))
    for child in formula.get("children") or []:
        ids.extend(formula_symbol_ids(child))
    return ids


def test_generates_unique_syntactically_intended_cases():
    config = GenerationConfig(count=20, seed=10)
    state = GeneratorState()
    cases = UniverseTestGenerator(config, state).generate()
    assert len(cases) == 20
    assert len({case.rendering_hash for case in cases}) == 20
    assert all(case.expected["syntactically_intended_valid"] for case in cases)
    assert any("Suppose that" in case.tex or "Assume that" in case.tex for case in cases)


def test_generated_case_carries_exact_synthetic_registry():
    config = GenerationConfig(count=1, seed=10)
    state = GeneratorState()
    case = UniverseTestGenerator(config, state).generate()[0].to_dict()
    registry = case["synthetic_registry"]

    assert registry["schema_version"] == "test-tex-generator.synthetic-registry/1.0"
    assert registry["universe_version"] == case["universe_version"]
    assert registry["symbols"]["TestPredicate14"]["tex"] == "P_{14}"
    assert registry["symbols"]["TestPredicate14"]["arity"] == 4
    assert registry["symbols"]["TestRelation05"]["tex"] == "R_{5}"
    assert registry["symbols"]["TestRelation05"]["arity"] == 3


def test_testing_symbols_are_loaded_from_production_registries():
    symbols = {symbol.id: symbol.to_dict() for symbol in load_testing_symbols()}

    assert symbols["TestPredicate14"]["tex"] == "P_{14}"
    assert symbols["TestPredicate14"]["arity"] == 4
    assert symbols["TestRelation05"]["tex"] == "R_{5}"
    assert symbols["TestRelation05"]["arity"] == 3
    assert symbols["TestStructure06"]["tex"] == r"\mathcal{T}_{6}"
    assert symbols["TestNumberSystem03"]["tex"] == r"\mathbb{T}_{3}"
    assert symbols["TestAmbient06"]["metadata"]["element_type"] == "element"


def test_generator_state_is_seeded_from_production_testing_registry():
    state = GeneratorState()
    UniverseTestGenerator(GenerationConfig(count=1, seed=10), state)

    assert state.symbols["TestPredicate14"]["tex"] == "P_{14}"
    assert state.symbols["TestRelation05"]["tex"] == "R_{5}"
    assert state.symbols["TestNumberSystem03"]["tex"] == r"\mathbb{T}_{3}"
    assert state.symbols["TestAmbient06"]["metadata"]["element_type"] == "element"


def test_synthetic_registry_is_not_fixed_to_one_symbols():
    config = GenerationConfig(count=1, seed=10)
    state = GeneratorState()
    case = UniverseTestGenerator(config, state).generate()[0].to_dict()
    registry = case["synthetic_registry"]["symbols"]

    assert "TestAmbient06" in registry
    assert registry["TestAmbient06"]["tex"] == "A_{6}"
    assert "TestElement18" in registry
    assert registry["TestElement18"]["tex"] == "x_{18}"


def test_case_registry_validation_accepts_generated_case():
    config = GenerationConfig(count=1, seed=10)
    state = GeneratorState()
    case = UniverseTestGenerator(config, state).generate()[0].to_dict()

    validate_case_registry(case)


def test_case_registry_validation_rejects_missing_symbol():
    config = GenerationConfig(count=1, seed=10)
    state = GeneratorState()
    case = UniverseTestGenerator(config, state).generate()[0].to_dict()
    missing = formula_symbol_ids(case["canonical_formula"])[0]
    del case["synthetic_registry"]["symbols"][missing]

    try:
        validate_case_registry(case)
    except ValueError as exc:
        assert f"unknown symbol {missing}" in str(exc)
    else:
        raise AssertionError("missing registry symbol should fail validation")


def test_case_registry_validation_rejects_wrong_arity():
    config = GenerationConfig(count=1, seed=10)
    state = GeneratorState()
    case = UniverseTestGenerator(config, state).generate()[0].to_dict()
    formula = case["canonical_formula"]
    while formula.get("kind") not in {"predicate", "relation"}:
        children = formula.get("children") or []
        if not children:
            return
        formula = children[0]
    symbol = formula["symbol"]
    case["synthetic_registry"]["symbols"][symbol]["arity"] = 99

    try:
        validate_case_registry(case)
    except ValueError as exc:
        assert f"arity mismatch for {symbol}" in str(exc)
    else:
        raise AssertionError("wrong registry arity should fail validation")


def test_extract_display_formulas_from_generated_discourse():
    config = GenerationConfig(count=1, seed=10)
    state = GeneratorState()
    generator = UniverseTestGenerator(config, state)
    formula = Formula("membership", arguments=("TestElement01", "TestAmbient01"))
    tex_formula = generator.render_formula(formula, "symbolic")
    tex = generator.discourse(tex_formula, "let-suppose-then")

    displays = extract_display_formulas(tex)

    assert len(displays) == 2
    assert displays[0] == displays[1]


def test_symbolic_connective_renderer_separates_latex_commands_from_operands():
    config = GenerationConfig(count=1, seed=10)
    state = GeneratorState()
    generator = UniverseTestGenerator(config, state)
    formula = Formula(
        "and",
        children=(
            Formula("predicate", symbol="TestPredicate14", arguments=("TestElement01",)),
            Formula("membership", arguments=("TestElement02", "TestAmbient01")),
        ),
    )

    tex = generator.render_formula(formula, "house")

    assert r"\landx" not in tex
    assert r"\land\,x_{2}" in tex


def test_text_connective_renderer_separates_spacing_commands_from_operands():
    config = GenerationConfig(count=1, seed=10)
    state = GeneratorState()
    generator = UniverseTestGenerator(config, state)
    formula = Formula(
        "implies",
        children=(
            Formula("membership", arguments=("TestElement01", "TestAmbient01")),
            Formula("typed_signature", arguments=("TestFunction02", "TestAmbient02", "TestNumberSystem01")),
        ),
    )

    tex = generator.render_formula(formula, "text-connectives")

    assert r"\quadf" not in tex
    assert r"\quad f_{2}" in tex


def test_expanded_quantifier_renderer_separates_connective_from_body():
    config = GenerationConfig(count=1, seed=10)
    state = GeneratorState()
    generator = UniverseTestGenerator(config, state)
    formula = Formula(
        "forall",
        binder="TestElement01",
        domain="TestAmbient01",
        children=(Formula("membership", arguments=("TestElement02", "TestAmbient01")),),
    )

    tex = generator.render_formula(formula, "expanded-quantifiers")

    assert r"\rightarrowx" not in tex
    assert r"\rightarrow x_{2}" in tex


def test_builds_expected_governed_ast_from_canonical_formula():
    config = GenerationConfig(count=1, seed=10)
    state = GeneratorState()
    formula = Formula(
        "not",
        children=(
            Formula(
                "forall",
                binder="TestElement12",
                domain="TestAmbient01",
                children=(
                    Formula(
                        "and",
                        children=(
                            Formula("membership", arguments=("TestElement12", "TestAmbient01")),
                            Formula("equality", arguments=("TestElement01", "TestElement02")),
                        ),
                    ),
                ),
            ),
        ),
    )
    case = {
        "canonical_formula": formula.to_dict(),
        "synthetic_registry": UniverseTestGenerator(config, state).state.synthetic_registry(),
        "expected": {"root_kind": "not"},
    }

    ast = expected_governed_ast(case)

    assert ast["kind"] == case["expected"]["root_kind"]
    assert ast["operand"]["kind"] == "forall"
    assert ast["operand"]["binder"]["binder_id"] == "x_12"
    assert ast["operand"]["body"]["kind"] == "and"


def test_textbook_failure_atoms_render_to_expected_parser_asts():
    config = GenerationConfig(count=1, seed=10)
    state = GeneratorState()
    generator = UniverseTestGenerator(config, state)
    formulas = [
        Formula("satisfaction", arguments=("TestStructure01", "TestRelation01")),
        Formula("provability", arguments=("TestSet01", "TestPredicate01")),
        Formula("equivalence_relation", arguments=("TestRelation02", "TestPredicate02")),
        Formula("typed_signature", arguments=("TestFunction01", "TestAmbient01", "TestNumberSystem01")),
        Formula(
            "restriction_equality",
            arguments=("TestFunction02", "TestRelation03", "TestFunction03", "TestRelation04"),
        ),
        Formula("syntax_set_membership"),
    ]

    for formula in formulas:
        case = {
            "canonical_formula": formula.to_dict(),
            "synthetic_registry": state.synthetic_registry(),
        }
        expected = expected_governed_ast(case)
        tex = generator.render_formula(formula, "symbolic")

        assert parse_hand_formula(tex) == expected
        assert parse_lark_formula(tex) == expected


def test_generator_covers_textbook_failure_atom_categories():
    config = GenerationConfig(count=24, seed=12)
    state = GeneratorState()
    cases = UniverseTestGenerator(config, state).generate()
    categories = {kind for case in cases for kind in case.construction["node_kinds"]}

    assert "satisfaction" in categories
    assert "provability" in categories
    assert "equivalence_relation" in categories
    assert "typed_signature" in categories
    assert "restriction_equality" in categories
    assert "syntax_set_membership" in categories


if __name__ == "__main__":
    run_all_tests()
    print("test_test_tex_generator: OK")
