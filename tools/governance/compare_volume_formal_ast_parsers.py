#!/usr/bin/env python3
"""Extract formal-environment displays and compare AST parser outputs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "tools" / "governance") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools" / "governance"))

from core.file_inventory import input_paths  # noqa: E402
from core.tex import read_text, strip_latex_comments  # noqa: E402
from semantic_lark_logic_parser import parse_formula as parse_lark_formula  # noqa: E402
from semantic_latex_ast import parse_formula as parse_hand_formula  # noqa: E402


FORMAL_ENVIRONMENTS = {
    "definition",
    "axiom",
    "theorem",
    "lemma",
    "proposition",
    "corollary",
    "claim",
    "conjecture",
}
FORMAL_BEGIN_RE = re.compile(
    r"\\begin\{(?P<env>" + "|".join(sorted(FORMAL_ENVIRONMENTS)) + r")(?P<star>\*)?\}(?:\[(?P<title>[^\]]+)\])?",
    re.I,
)
DISPLAY_RE = re.compile(r"\\\[(?P<body>.*?)\\\]", re.S)
INPUT_RE = re.compile(r"\\(?:input|include)\{(?P<target>[^{}]+)\}")


def line_for_offset(text: str, offset: int) -> int:
    return text[:offset].count("\n") + 1


def reachable_tex_files(entry: Path, volume_source: Path) -> list[Path]:
    ordered: list[Path] = []
    seen: set[Path] = set()

    def visit(path: Path) -> None:
        resolved = path.resolve()
        if resolved in seen:
            return
        seen.add(resolved)
        if not resolved.exists() or not resolved.is_file() or resolved.suffix != ".tex":
            return
        ordered.append(resolved)
        for target in input_paths(resolved, volume_source):
            visit(target)

    visit(entry)
    return ordered


def find_matching_end(text: str, env: str, start: int) -> re.Match[str] | None:
    pattern = re.compile(r"\\(?P<kind>begin|end)\{" + re.escape(env) + r"\*?\}", re.I)
    depth = 1
    for match in pattern.finditer(text, start):
        if match.group("kind").lower() == "begin":
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return match
    return None


def formal_display_cases(book_root: Path, volume_source: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    case_number = 1
    for path in reachable_tex_files(book_root, volume_source):
        if path == book_root:
            continue
        text = strip_latex_comments(read_text(path))
        for begin in FORMAL_BEGIN_RE.finditer(text):
            env = begin.group("env")
            end = find_matching_end(text, env, begin.end())
            if not end:
                continue
            block = text[begin.start() : end.end()]
            displays = list(DISPLAY_RE.finditer(block))
            for index, display in enumerate(displays):
                formula = display.group("body").strip()
                case_id = f"VolumeFormalCase{case_number:05d}"
                case_number += 1
                cases.append(
                    {
                        "id": case_id,
                        "source": {
                            "book_root": book_root.as_posix(),
                            "source_file": path.as_posix(),
                            "source_line": line_for_offset(text, begin.start() + display.start()),
                            "environment": env.lower() + (begin.group("star") or ""),
                            "title": begin.group("title"),
                            "display_index": index,
                        },
                        "construction": {
                            "renderer": "volume-formal-display",
                            "discourse": "formal-environment-display",
                        },
                        "tex": "\\[" + formula + "\\]",
                    }
                )
    return cases


def parse_with(name: str, formula: str) -> dict[str, Any]:
    parser = parse_hand_formula if name == "hand" else parse_lark_formula
    try:
        return {"parser": name, "status": "pass", "ast": parser(formula)}
    except Exception as exc:  # noqa: BLE001 - report parser failures as data.
        return {"parser": name, "status": "parse_error", "error": f"{type(exc).__name__}: {exc}"}


def audit_surface(value: str) -> str:
    text = str(value)
    text = re.sub(r"\\(?:;|,|!|quad|qquad)", " ", text)
    text = re.sub(r"\\(?:Bigl|Bigr|bigl|bigr|left|right)", "", text)
    text = re.sub(r"\\mathbb\{([^{}]+)\}", r"mathbb\1", text)
    text = re.sub(r"mathbb_([A-Za-z])", r"mathbb\1", text)
    text = re.sub(r"\\mathcal\{([^{}]+)\}", r"mathcal\1", text)
    text = re.sub(r"mathcal_([A-Za-z])", r"mathcal\1", text)
    text = re.sub(r"\\mathrm\{([^{}]+)\}", r"mathrm\1", text)
    text = re.sub(r"mathrm_([A-Za-z]+)", r"mathrm\1", text)
    text = re.sub(r"\\operatorname\{([^{}]+)\}", r"operatorname\1", text)
    replacements = {
        "COLON": ":",
        "LEQ": "leq",
        "GEQ": "geq",
        "NEQ": "neq",
        "NOTIN": "notin",
        "SUBSETEQ": "subseteq",
        "SUBSET": "subset",
        "IN": "in",
        "TO": "to",
        "TIMES": "times",
        "COMPOSE": "circ",
        "AND": "land",
        "OR": "lor",
        "FORALL": "forall",
        "EXISTS": "exists",
    }
    for token, surface in replacements.items():
        text = re.sub(rf"\b{token}\b", surface, text)
    text = re.sub(r"\\(?:leq|le)", "leq", text)
    text = re.sub(r"\\(?:geq|ge)", "geq", text)
    text = re.sub(r"\\neq|\\ne", "neq", text)
    text = re.sub(r"\\notin", "notin", text)
    text = re.sub(r"\\subseteq", "subseteq", text)
    text = re.sub(r"\\subset", "subset", text)
    text = re.sub(r"\\in", "in", text)
    text = re.sub(r"\\to|\\rightarrow", "to", text)
    text = re.sub(r"\\times", "times", text)
    text = re.sub(r"\\circ", "circ", text)
    text = re.sub(r"\\land", "land", text)
    text = re.sub(r"\\lor", "lor", text)
    text = re.sub(r"\\text\{([^{}]*)\}", lambda match: "text{" + re.sub(r"\s+", "", match.group(1).strip()) + "}", text)
    text = text.replace(r"\{", "{").replace(r"\}", "}")
    text = re.sub(r"(?<=[A-Za-z0-9])circ(?=[A-Za-z0-9_])", "circ", text)
    text = re.sub(r"\s+", "", text)
    text = text.replace(":=", "=").replace(":=", "=")
    text = text.replace(":", "")
    text = text.replace("_", "")
    text = text.replace("\\", "")
    text = text.replace("(", "").replace(")", "").replace(",", "")
    text = text.replace("{", "").replace("}", "")
    return text.lower()


def normalize_ast_for_audit(value: Any) -> Any:
    if isinstance(value, list):
        return [normalize_ast_for_audit(item) for item in value]
    if not isinstance(value, dict):
        return value
    kind = value.get("kind")
    if kind == "raw_latex" and isinstance(value.get("latex"), str):
        return {"kind": "surface_atom", "surface": audit_surface(value["latex"])}
    if kind == "variable" and isinstance(value.get("binder_id"), str):
        return {"kind": "surface_atom", "surface": audit_surface(value["binder_id"])}
    if kind == "application" and isinstance(value.get("function"), str):
        arguments = value.get("arguments")
        if isinstance(arguments, list):
            surface = audit_surface(value["function"] + "".join(term_surface_for_audit(argument) for argument in arguments))
            return {"kind": "surface_atom", "surface": surface}
    normalized: dict[str, Any] = {}
    for key, item in value.items():
        if key in {"latex", "binder_id", "symbol", "name", "function"} and isinstance(item, str):
            normalized[key] = audit_surface(item)
        elif key == "relation" and isinstance(item, str):
            normalized[key] = audit_surface(item)
        else:
            normalized[key] = normalize_ast_for_audit(item)
    return normalized


def term_surface_for_audit(value: Any) -> str:
    if isinstance(value, dict):
        kind = value.get("kind")
        if kind == "raw_latex":
            return str(value.get("latex", ""))
        if kind == "variable":
            return str(value.get("binder_id", ""))
        if kind == "constant":
            return str(value.get("name", ""))
        if kind == "application":
            function = str(value.get("function", ""))
            args = value.get("arguments")
            if isinstance(args, list):
                return function + "(" + ",".join(term_surface_for_audit(arg) for arg in args) + ")"
        if kind == "tuple":
            elements = value.get("elements")
            if isinstance(elements, list):
                return "(" + ",".join(term_surface_for_audit(element) for element in elements) + ")"
    return str(value)


def ast_equivalent_for_audit(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return normalize_ast_for_audit(left) == normalize_ast_for_audit(right)


def compare_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    summary = {
        "display_count": len(cases),
        "both_parse_count": 0,
        "ast_match_count": 0,
        "ast_mismatch_count": 0,
        "audit_equivalent_count": 0,
        "audit_mismatch_count": 0,
        "hand_parse_error_count": 0,
        "lark_parse_error_count": 0,
    }
    for case in cases:
        formula = str(case.get("tex", ""))
        hand = parse_with("hand", formula)
        lark = parse_with("lark", formula)
        if hand["status"] == "parse_error":
            summary["hand_parse_error_count"] += 1
        if lark["status"] == "parse_error":
            summary["lark_parse_error_count"] += 1
        if hand["status"] == "pass" and lark["status"] == "pass":
            summary["both_parse_count"] += 1
            if hand["ast"] == lark["ast"]:
                summary["ast_match_count"] += 1
                summary["audit_equivalent_count"] += 1
            else:
                summary["ast_mismatch_count"] += 1
                audit_equivalent = ast_equivalent_for_audit(hand["ast"], lark["ast"])
                if audit_equivalent:
                    summary["audit_equivalent_count"] += 1
                else:
                    summary["audit_mismatch_count"] += 1
                failures.append(
                    {
                        "id": case["id"],
                        "source": case["source"],
                        "tex": formula,
                        "hand": hand,
                        "lark": lark,
                        "audit_equivalent": audit_equivalent,
                    }
                )
        else:
            failures.append({"id": case["id"], "source": case["source"], "tex": formula, "hand": hand, "lark": lark})
    both = summary["both_parse_count"]
    total = summary["display_count"]
    summary["ast_mismatch_percent_of_both_parsed"] = round((summary["ast_mismatch_count"] / both * 100), 2) if both else 0.0
    summary["audit_mismatch_percent_of_both_parsed"] = (
        round((summary["audit_mismatch_count"] / both * 100), 2) if both else 0.0
    )
    nonmatch = total - summary["ast_match_count"]
    summary["nonmatch_or_parse_error_percent_of_all_displays"] = round((nonmatch / total * 100), 2) if total else 0.0
    audit_nonmatch = total - summary["audit_equivalent_count"]
    summary["audit_nonmatch_or_parse_error_percent_of_all_displays"] = (
        round((audit_nonmatch / total * 100), 2) if total else 0.0
    )
    return {"summary": summary, "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--volume-root", type=Path, required=True)
    parser.add_argument("--book-root", type=Path, required=True)
    parser.add_argument("--corpus-output", type=Path, required=True)
    parser.add_argument("--report-output", type=Path, required=True)
    args = parser.parse_args()

    volume_root = args.volume_root.resolve()
    book_root = args.book_root.resolve()
    cases = formal_display_cases(book_root, volume_root)
    args.corpus_output.parent.mkdir(parents=True, exist_ok=True)
    args.corpus_output.write_text(yaml.safe_dump(cases, sort_keys=False, allow_unicode=True), encoding="utf-8")
    report = compare_cases(cases)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    summary = report["summary"]
    print(
        f"Compared {summary['display_count']} displays: "
        f"{summary['ast_mismatch_count']} AST mismatches among {summary['both_parse_count']} both-parsed "
        f"({summary['ast_mismatch_percent_of_both_parsed']}%); "
        f"{summary['audit_mismatch_count']} audit mismatches "
        f"({summary['audit_mismatch_percent_of_both_parsed']}%); "
        f"{summary['nonmatch_or_parse_error_percent_of_all_displays']}% nonmatch-or-parse-error overall"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
