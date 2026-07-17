from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import yaml


GOVERNANCE_ROOT = Path(__file__).resolve().parents[2]
COMMON_MALFORMED_CONTROL_SEQUENCES = {
    r"\leqft": r"\left",
    r"\rigth": r"\right",
}


@dataclass(frozen=True)
class StyleFinding:
    code: str
    severity: str
    path: str
    line: int
    message: str
    suggestion: str


@dataclass(frozen=True)
class NotationRoles:
    function_type_arrow: frozenset[str]
    function_rule_arrow: frozenset[str]
    function_signature_colon: frozenset[str]
    set_builder_separator: frozenset[str]
    logical_implication: frozenset[str]
    logical_equivalence: frozenset[str]


def load_notation_roles(governance_root: Path = GOVERNANCE_ROOT) -> NotationRoles:
    data = yaml.safe_load((governance_root / "notation.yaml").read_text(encoding="utf-8")) or {}
    by_role: dict[str, set[str]] = {
        "function_type_arrow": set(),
        "function_rule_arrow": set(),
        "function_signature_colon": set(),
        "set_builder_separator": set(),
        "logical_implication": set(),
        "logical_equivalence": set(),
    }
    for item in data.get("notation", []) or []:
        if not isinstance(item, dict):
            continue
        role_data = item.get("notation_role") or {}
        if not isinstance(role_data, dict):
            continue
        role = str(role_data.get("role") or "")
        symbol = str(item.get("symbol") or "")
        if role in by_role and symbol:
            by_role[role].add(symbol)

    return NotationRoles(
        function_type_arrow=frozenset(by_role["function_type_arrow"]),
        function_rule_arrow=frozenset(by_role["function_rule_arrow"]),
        function_signature_colon=frozenset(by_role["function_signature_colon"]),
        set_builder_separator=frozenset(by_role["set_builder_separator"]),
        logical_implication=frozenset(by_role["logical_implication"]),
        logical_equivalence=frozenset(by_role["logical_equivalence"]),
    )


def validate_target(target: Path, *, governance_root: Path = GOVERNANCE_ROOT) -> list[StyleFinding]:
    roles = load_notation_roles(governance_root)
    root = target if target.is_dir() else target.parent
    findings: list[StyleFinding] = []
    for path in _tex_files(target):
        findings.extend(validate_tex_file(path, root=root, roles=roles))
    return findings


def validate_tex_file(path: Path, *, root: Path, roles: NotationRoles) -> list[StyleFinding]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    findings: list[StyleFinding] = []
    in_display = False
    display_start = 0
    display_lines: list[str] = []
    in_standard_quantified_statement = False
    in_formal_support_block = False

    for index, raw_line in enumerate(lines, start=1):
        line = _strip_comments(raw_line)
        if r"\begin{remark*}[Standard quantified statement]" in line:
            in_standard_quantified_statement = True
        if _begins_formal_support_remark(line):
            in_formal_support_block = True
        if r"\end{remark*}" in line and in_standard_quantified_statement:
            in_standard_quantified_statement = False
        if r"\end{remark*}" in line and in_formal_support_block:
            in_formal_support_block = False

        if "=======" in line:
            findings.append(
                _finding(
                    "markdown_artifact_in_tex",
                    path,
                    root,
                    index,
                    "Markdown conflict/header artifact appears in TeX source.",
                    "Remove the markdown artifact and restore valid LaTeX.",
                )
            )

        if r"\left{" in line or r"\right}" in line:
            findings.append(
                _finding(
                    "malformed_set_brace_delimiter",
                    path,
                    root,
                    index,
                    r"Set braces use malformed \left{ or \right} syntax.",
                    r"Use \left\{...\right\} or simple escaped braces \{...\}.",
                )
            )

        for malformed, intended in COMMON_MALFORMED_CONTROL_SEQUENCES.items():
            if malformed in line:
                findings.append(
                    _finding(
                        "malformed_common_control_sequence",
                        path,
                        root,
                        index,
                        f"Common malformed TeX control sequence {malformed} appears.",
                        f"Use {intended} if that was intended, or replace with the correct control sequence.",
                    )
                )

        if _plain_colon_function_signature(line):
            findings.append(
                _finding(
                    "function_signature_uses_plain_colon",
                    path,
                    root,
                    index,
                    "Function signature appears to use a plain colon.",
                    r"Use \colon for function signatures, for example f\colon A\to B.",
                )
            )

        if _signature_uses_logical_arrow(line, roles):
            findings.append(
                _finding(
                    "function_signature_uses_logical_arrow",
                    path,
                    root,
                    index,
                    "Function signature appears to use a logical connective as its type arrow.",
                    r"Use \to in function signatures, for example f\colon A\to B.",
                )
            )

        if _rule_uses_type_arrow(line):
            findings.append(
                _finding(
                    "function_rule_uses_type_arrow",
                    path,
                    root,
                    index,
                    r"Function rule appears to use \to instead of \mapsto.",
                    r"Use \mapsto for function rules, for example x\mapsto f(x).",
                )
            )

        display_line = in_display or r"\[" in line or r"\begin{align" in line or r"\begin{equation" in line
        if display_line:
            if _contains_any(line, {"\\Rightarrow", "\\implies"}):
                findings.append(
                    _finding(
                        "display_implication_uses_compact_connective",
                        path,
                        root,
                        index,
                        "Displayed formal logic uses compact implication notation.",
                        r"Use \Longrightarrow for displayed formal implication.",
                    )
                )
            if r"\iff" in line:
                findings.append(
                    _finding(
                        "display_equivalence_uses_inline_connective",
                        path,
                        root,
                        index,
                        "Displayed formal logic uses inline biconditional notation.",
                        r"Use \Longleftrightarrow for displayed formal equivalence.",
                    )
                )

        if not in_display and r"\[" in line:
            in_display = True
            display_start = index
            display_lines = [line]
        elif in_display:
            display_lines.append(line)

        if in_display and r"\]" in line:
            findings.extend(
                _family_style_findings(
                    "\n".join(display_lines),
                    path,
                    root,
                    display_start,
                    require_visible_scope_closure=in_standard_quantified_statement,
                    check_family_symbol_closure=in_formal_support_block,
                )
            )
            in_display = False
            display_lines = []

        if in_standard_quantified_statement and re.search(r"\\text\{[^}]*\b(Let|Suppose|Assume|If|Then)\b", line):
            findings.append(
                _finding(
                    "standard_quantified_statement_contains_prose",
                    path,
                    root,
                    index,
                    "Standard quantified statement block contains prose instead of a symbolic quantified form.",
                    "Move prose to the formal statement or interpretation layer and keep this block symbolic.",
                )
            )

    return findings


def _tex_files(target: Path) -> Iterable[Path]:
    if target.is_file():
        if target.suffix == ".tex":
            yield target
        return
    for path in sorted(target.rglob("*.tex")):
        if any(part in {".git", "build", ".venv", "__pycache__"} for part in path.parts):
            continue
        yield path


def _strip_comments(line: str) -> str:
    escaped = False
    for index, char in enumerate(line):
        if char == "\\":
            escaped = not escaped
            continue
        if char == "%" and not escaped:
            return line[:index]
        escaped = False
    return line


def _plain_colon_function_signature(line: str) -> bool:
    if r"\colon" in line:
        return False
    return bool(
        re.search(
            r"(^|[^\w\\])(?:[A-Za-z]|\\[A-Za-z]+)(?:_[A-Za-z0-9{}]+)?\s*:\s*[^:{},]+\\to\b",
            line,
        )
    )


def _signature_uses_logical_arrow(line: str, roles: NotationRoles) -> bool:
    if r"\colon" not in line:
        return False
    logical = set(roles.logical_implication) | {"\\Rightarrow", "\\Longrightarrow", "\\implies"}
    return any(symbol in line for symbol in logical if symbol != r"\to")


def _rule_uses_type_arrow(line: str) -> bool:
    if r"\mapsto" in line or r"\colon" in line:
        return False
    return bool(
        re.search(
            r"(^|[^\w\\])(?:[A-Za-z]|\\[A-Za-z]+|\([^)]{1,80}\))\s*\\to\s*(?:[A-Za-z0-9\\({\-])",
            line,
        )
    )


def _contains_any(line: str, needles: set[str]) -> bool:
    return any(needle in line for needle in needles)


def _begins_formal_support_remark(line: str) -> bool:
    labels = {
        "Standard quantified statement",
        "Predicate reading",
        "Negated quantified statement",
        "Negation predicate reading",
        "Failure modes",
    }
    return any(rf"\begin{{remark*}}[{label}]" in line for label in labels)


def _normalize_display_for_family_lint(latex: str) -> str:
    text = latex.strip()
    if text.startswith(r"\[") and text.endswith(r"\]"):
        text = text[2:-2].strip()
    text = re.sub(r"\\begin\{(?:aligned|gathered|array)\}", "", text)
    text = re.sub(r"\\end\{(?:aligned|gathered|array)\}", "", text)
    text = text.replace("\\\\", "\n")
    text = re.sub(r"&", "", text)
    text = re.sub(r"\\(?:qquad|quad|;|,|!|:)", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _family_style_findings(
    display: str,
    path: Path,
    root: Path,
    line: int,
    *,
    require_visible_scope_closure: bool = False,
    check_family_symbol_closure: bool = False,
) -> list[StyleFinding]:
    text = _normalize_display_for_family_lint(display)
    findings: list[StyleFinding] = []

    for match in re.finditer(r"\\in\s*[A-Z][A-Za-z_]+", text):
        findings.append(
            _finding(
                "suspect_lost_delimiter_after_membership_domain",
                path,
                root,
                line,
                "Membership domain appears concatenated with a following expression.",
                r"Preserve a delimiter or separator, e.g. \forall i\in I,\ U_i or \forall i\in I\; U_i.",
            )
        )
    for match in re.finditer(r"\\subseteq\s*[A-Z][A-Z]\\", text):
        findings.append(
            _finding(
                "suspect_lost_delimiter_after_subset_domain",
                path,
                root,
                line,
                "Subset target appears concatenated with a following expression.",
                r"Preserve a delimiter or separator, e.g. J\subseteq I,\ K\not\subseteq\cdots.",
            )
        )

    declared = _quantified_family_symbols(text) | _indexed_family_declarations(text) | _local_union_indices(text)
    family_uses = _indexed_family_uses(text)
    has_set_family = bool(re.search(r"\\mathcal\{[A-Za-z]\}", text))
    has_indexed_family = bool(family_uses or re.search(r"\\[{}][A-Za-z]_i\\[{}]_\{i\\in", text))
    has_family_context = has_set_family or has_indexed_family or r"\bigcup_" in text

    if not has_family_context:
        return findings

    if not check_family_symbol_closure:
        return findings

    undeclared_families = sorted(symbol for symbol in family_uses if symbol not in declared)
    for symbol in undeclared_families:
        findings.append(
            _finding(
                "undeclared_indexed_family_symbol",
                path,
                root,
                line,
                f"Indexed family symbol {symbol} is used without a matching indexed-family binder.",
                rf"Quantify the indexed family, e.g. \forall \{{{symbol[0]}_i\}}_{{i\in I}}, or use a set-family formulation consistently.",
            )
        )

    undeclared_upper = sorted(symbol for symbol in _uppercase_family_domain_uses(text) if symbol not in declared and symbol not in {"K", "R"})
    for symbol in undeclared_upper:
        findings.append(
            _finding(
                "possibly_undeclared_family_index_set",
                path,
                root,
                line,
                f"Uppercase symbol {symbol} is used as a family domain or index set without a visible binder.",
                "Bind the index/domain symbol in the displayed formula or use a set-family formulation.",
            )
        )

    if require_visible_scope_closure and (undeclared_families or undeclared_upper):
        evidence = ", ".join(undeclared_families + undeclared_upper)
        findings.append(
            _finding(
                "support_block_not_visibly_closed",
                path,
                root,
                line,
                f"Displayed support block has symbols not bound or declared in the visible formula: {evidence}.",
                "Make each displayed formal support block closed relative to its visible formula, or add an explicit local context in the same block.",
            )
        )

    has_indexed_declaration = bool(_indexed_family_declarations(text))
    if has_set_family and has_indexed_family and not has_indexed_declaration:
        findings.append(
            _finding(
                "mixed_set_and_indexed_family_representation",
                path,
                root,
                line,
                r"Displayed formula mixes set-family notation such as \mathcal{U} with indexed-family notation such as U_i without declaring their relationship.",
                r"Use one representation consistently, or explicitly quantify/define the indexed family \{U_i\}_{i\in I}.",
            )
        )

    return findings


def _indexed_family_declarations(text: str) -> set[str]:
    declarations: set[str] = set()
    for match in re.finditer(r"\\[{}](?P<family>[A-Za-z])_i\\[{}]_\{i\\in\s*(?P<index>[A-Za-z])\}", text):
        declarations.add(f"{match.group('family')}_i")
        declarations.add(match.group("index"))
    return declarations


def _quantified_family_symbols(text: str) -> set[str]:
    symbols: set[str] = set()
    symbol_pattern = r"(?:[A-Za-z]|\\[A-Za-z]+|\\mathcal\{[A-Za-z]\}|[A-Za-z]_[A-Za-z])"
    for match in re.finditer(rf"\\(?:forall|exists)\s+(?P<symbol>{symbol_pattern})", text):
        symbols.add(match.group("symbol"))
    for match in re.finditer(r"\\(?:forall|exists)\s+\\text\{finite\s*\}\s*(?P<symbol>[A-Za-z])\\subseteq", text):
        symbols.add(match.group("symbol"))
    return symbols


def _local_union_indices(text: str) -> set[str]:
    return set(re.findall(r"\\bigcup_\{(?P<index>[A-Za-z])\\in\s*[^{}]+\}", text))


def _indexed_family_uses(text: str) -> set[str]:
    return set(re.findall(r"(?<![A-Za-z])(?P<family>[A-Za-z]_[A-Za-z])(?![A-Za-z])", text))


def _uppercase_family_domain_uses(text: str) -> set[str]:
    uses: set[str] = set()
    for pattern in [
        r"\\subseteq\s*(?P<symbol>[A-Z])",
        r"\\in\s*(?P<symbol>[A-Z])",
        r"\\bigcup_\{[A-Za-z]\\in\s*(?P<symbol>[A-Z])\}",
    ]:
        uses.update(match.group("symbol") for match in re.finditer(pattern, text))
    return uses


def _finding(code: str, path: Path, root: Path, line: int, message: str, suggestion: str) -> StyleFinding:
    return StyleFinding(
        code=code,
        severity="error",
        path=_rel_path(path, root),
        line=line,
        message=message,
        suggestion=suggestion,
    )


def _rel_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate LRA LaTeX math notation/style conventions.")
    parser.add_argument("--target", required=True, type=Path, help="A .tex file or directory to validate.")
    parser.add_argument("--governance-root", default=GOVERNANCE_ROOT, type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    findings = validate_target(args.target, governance_root=args.governance_root)
    if args.format == "json":
        print(json.dumps({"clean": not findings, "findings": [asdict(item) for item in findings]}, indent=2))
    else:
        if not findings:
            print("latex math style: clean")
        for item in findings:
            print(f"{item.path}:{item.line}: {item.severity}: {item.code}: {item.message}")
            print(f"  suggestion: {item.suggestion}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
