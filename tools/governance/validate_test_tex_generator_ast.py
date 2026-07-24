from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

import yaml

from semantic_lark_logic_parser import parse_formula as parse_lark_formula
from semantic_latex_ast import parse_formula as parse_hand_formula
from test_tex_generator.validation import expected_governed_ast, extract_display_formulas


Parser = Callable[[str], dict[str, Any]]


def load_cases(path: Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    if not isinstance(data, list):
        raise ValueError(f"expected a YAML list of generated cases in {path}")
    return data


def ast_equal(left: Any, right: Any) -> bool:
    return left == right


def parse_with(name: str, parser: Parser, formula: str, expected: dict[str, Any]) -> dict[str, Any]:
    try:
        actual = parser(formula)
    except Exception as exc:  # noqa: BLE001 - report parser failures as test data.
        return {
            "parser": name,
            "status": "parse_error",
            "error": f"{type(exc).__name__}: {exc}",
        }
    if ast_equal(actual, expected):
        return {"parser": name, "status": "pass", "actual": actual}
    return {
        "parser": name,
        "status": "ast_mismatch",
        "expected": expected,
        "actual": actual,
    }


def compare_parser_results(hand: dict[str, Any], lark: dict[str, Any]) -> dict[str, Any]:
    hand_correct = hand.get("status") == "pass"
    lark_correct = lark.get("status") == "pass"
    hand_parsed = hand.get("status") != "parse_error"
    lark_parsed = lark.get("status") != "parse_error"

    if hand_parsed and lark_parsed:
        same_ast = hand.get("actual") == lark.get("actual")
        agreement_class = "same_ast" if same_ast else "different_ast"
    elif not hand_parsed and not lark_parsed:
        same_ast = False
        agreement_class = "both_parse_error"
    elif not hand_parsed:
        same_ast = False
        agreement_class = "hand_parse_error"
    else:
        same_ast = False
        agreement_class = "lark_parse_error"

    if hand_correct and lark_correct:
        truth_class = "both_correct"
    elif not hand_parsed and not lark_parsed:
        truth_class = "both_parse_error"
    elif not hand_parsed:
        truth_class = "hand_parse_error_lark_wrong"
        if lark_correct:
            truth_class = "hand_parse_error_lark_correct"
    elif not lark_parsed:
        truth_class = "hand_wrong_lark_parse_error"
        if hand_correct:
            truth_class = "hand_correct_lark_parse_error"
    elif hand_correct:
        truth_class = "hand_only_correct"
    elif lark_correct:
        truth_class = "lark_only_correct"
    elif same_ast:
        truth_class = "both_wrong_same_ast"
    else:
        truth_class = "both_wrong_different_ast"

    return {
        "truth_class": truth_class,
        "agreement_class": agreement_class,
        "hand_correct": hand_correct,
        "lark_correct": lark_correct,
        "hand_parsed": hand_parsed,
        "lark_parsed": lark_parsed,
        "same_ast": same_ast,
    }


def increment(counter: dict[str, int], key: str) -> None:
    counter[key] = counter.get(key, 0) + 1


def validate_cases(cases: list[dict[str, Any]], limit: int | None = None) -> dict[str, Any]:
    selected = cases[:limit] if limit is not None else cases
    summary: dict[str, int] = {}
    truth_matrix: dict[str, int] = {}
    agreement_matrix: dict[str, int] = {}
    validator_accuracy = {
        "hand": {"correct": 0, "total": 0},
        "lark": {"correct": 0, "total": 0},
    }
    failures: list[dict[str, Any]] = []
    display_count = 0
    pass_count = 0

    for case in selected:
        expected = expected_governed_ast(case)
        displays = extract_display_formulas(str(case.get("tex", "")))
        if not displays:
            key = "display_missing"
            summary[key] = summary.get(key, 0) + 1
            failures.append({"case_id": case.get("id"), "status": key})
            continue
        for index, formula in enumerate(displays):
            display_count += 1
            hand = parse_with("hand", parse_hand_formula, formula, expected)
            lark = parse_with("lark", parse_lark_formula, formula, expected)
            comparison = compare_parser_results(hand, lark)
            increment(truth_matrix, comparison["truth_class"])
            increment(agreement_matrix, comparison["agreement_class"])
            for parser_name in ("hand", "lark"):
                validator_accuracy[parser_name]["total"] += 1
                if comparison[f"{parser_name}_correct"]:
                    validator_accuracy[parser_name]["correct"] += 1
            parser_disagreement = comparison["agreement_class"] == "different_ast"
            statuses = [hand["status"], lark["status"]]
            if statuses == ["pass", "pass"] and not parser_disagreement:
                pass_count += 1
                increment(summary, "pass")
                continue
            for result in (hand, lark):
                key = f"{result['parser']}_{result['status']}"
                increment(summary, key)
            if parser_disagreement:
                increment(summary, "parser_disagreement")
            failures.append(
                {
                    "case_id": case.get("id"),
                    "display_index": index,
                    "formula": formula,
                    "expected": expected,
                    "hand": hand,
                    "lark": lark,
                    "comparison": comparison,
                    "parser_disagreement": parser_disagreement,
                }
            )

    return {
        "case_count": len(selected),
        "display_count": display_count,
        "pass_count": pass_count,
        "failure_count": len(failures),
        "summary": dict(sorted(summary.items())),
        "truth_matrix": dict(sorted(truth_matrix.items())),
        "agreement_matrix": dict(sorted(agreement_matrix.items())),
        "validator_accuracy": validator_accuracy,
        "failures": failures,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare generated TeX displays against known canonical ASTs using both governance parsers."
    )
    parser.add_argument("--cases", required=True, help="YAML file produced by test_tex_generator.cli")
    parser.add_argument("--output", required=True, help="JSON report path")
    parser.add_argument("--limit", type=int, help="Only validate the first N cases")
    parser.add_argument("--fail-on-mismatch", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    report = validate_cases(load_cases(Path(args.cases)), args.limit)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(
        f"Validated {report['display_count']} displays from {report['case_count']} cases: "
        f"{report['pass_count']} pass, {report['failure_count']} fail"
    )
    print(f"Report saved to {out}")
    if args.fail_on_mismatch and report["failure_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
