from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "governance"))

import validate_test_tex_generator_ast as validator


EXPECTED = {"kind": "variable", "binder_id": "A"}
OTHER = {"kind": "variable", "binder_id": "B"}
THIRD = {"kind": "variable", "binder_id": "C"}


def run_all_tests() -> None:
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            value()


def parser_returning(ast):
    def parse(_formula: str):
        return ast

    return parse


def parser_raising(_formula: str):
    raise ValueError("bad syntax")


def compare(hand_parser, lark_parser):
    hand = validator.parse_with("hand", hand_parser, "A", EXPECTED)
    lark = validator.parse_with("lark", lark_parser, "A", EXPECTED)
    return validator.compare_parser_results(hand, lark)


def test_compare_parser_results_classifies_both_correct():
    result = compare(parser_returning(EXPECTED), parser_returning(EXPECTED))

    assert result["truth_class"] == "both_correct"
    assert result["agreement_class"] == "same_ast"
    assert result["hand_correct"] is True
    assert result["lark_correct"] is True


def test_compare_parser_results_classifies_one_validator_correct():
    result = compare(parser_returning(EXPECTED), parser_returning(OTHER))

    assert result["truth_class"] == "hand_only_correct"
    assert result["agreement_class"] == "different_ast"
    assert result["hand_correct"] is True
    assert result["lark_correct"] is False


def test_compare_parser_results_classifies_shared_wrong_ast():
    result = compare(parser_returning(OTHER), parser_returning(OTHER))

    assert result["truth_class"] == "both_wrong_same_ast"
    assert result["agreement_class"] == "same_ast"


def test_compare_parser_results_classifies_different_wrong_asts():
    result = compare(parser_returning(OTHER), parser_returning(THIRD))

    assert result["truth_class"] == "both_wrong_different_ast"
    assert result["agreement_class"] == "different_ast"


def test_compare_parser_results_classifies_parse_errors():
    result = compare(parser_raising, parser_returning(EXPECTED))

    assert result["truth_class"] == "hand_parse_error_lark_correct"
    assert result["agreement_class"] == "hand_parse_error"
    assert result["hand_correct"] is False
    assert result["lark_correct"] is True


def test_validate_cases_reports_truth_and_agreement_matrices():
    case = {
        "id": "Case1",
        "tex": r"\[A\]",
        "canonical_formula": {"kind": "membership", "arguments": ["x", "A"]},
        "synthetic_registry": {
            "symbols": {
                "x": {"tex": "x"},
                "A": {"tex": "A"},
            }
        },
    }

    with (
        patch.object(validator, "expected_governed_ast", return_value=EXPECTED),
        patch.object(validator, "parse_hand_formula", parser_returning(EXPECTED)),
        patch.object(validator, "parse_lark_formula", parser_returning(OTHER)),
    ):
        report = validator.validate_cases([case])

    assert report["truth_matrix"] == {"hand_only_correct": 1}
    assert report["agreement_matrix"] == {"different_ast": 1}
    assert report["validator_accuracy"] == {"hand": {"correct": 1, "total": 1}, "lark": {"correct": 0, "total": 1}}
    assert report["failures"][0]["comparison"]["truth_class"] == "hand_only_correct"


if __name__ == "__main__":
    run_all_tests()
    print("test_validate_test_tex_generator_ast: OK")
