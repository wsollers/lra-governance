"""
Deterministic validation for generated statement blocks.

These checks are intentionally local and conservative. They catch structural
problems before generated LaTeX is patched into source files.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from auditor import config


_FORMAL_ENV = re.compile(
    r"\\begin\{(definition|theorem|lemma|proposition|corollary|axiom)\}"
    r"(?:\[[^\]]*\])?"
    r"(?P<body>.*?)"
    r"\\end\{\1\}",
    re.DOTALL,
)
_LABEL = re.compile(r"\\label\{([^{}]+)\}")
_TCOLORBOX = re.compile(r"\\begin\{tcolorbox\}\s*(?:\[([^\]]*)\])?", re.DOTALL)
_REMARK = re.compile(
    r"\\begin\{remark\*\}(?:\[([^\]]+)\])?(.*?)\\end\{remark\*\}",
    re.DOTALL,
)
_HYPERREF = re.compile(r"\\hyperref\[([^\]]+)\]")
_RAW_STRUCTURE_QUANTIFIER = re.compile(r"\\forall\s*\([^)]*,[^)]*\)")
_LINE_COMMENT = re.compile(r"(?<!\\)%.*$")
_BAD_TEXT_PUNCTUATION = re.compile(r"(?:â|ï»¿|�|“|”|‘|’|—|–)")
_BARE_PREDICATE_MACRO = re.compile(
    r"\\(UpperBound|LowerBound|Maximum|Minimum|Supremum|Infimum)\b"
)
_NO_LOCAL_DEPENDENCIES = re.compile(r"\\NoLocalDependencies\b")


_EXPECTED_BOX_COLORS = {
    "def": ("defbox", "defborder"),
    "ax": ("axiombox", "axiomborder"),
    "thm": ("thmbox", "thmborder"),
    "lem": ("lembox", "lemborder"),
    "prop": ("propbox", "propborder"),
    "cor": ("corbox", "corborder"),
}

_BOX_REQUIRED_TYPES = {"ax"}

_DEFINITION_REQUIRED_REMARKS = {
    "standard quantified statement",
    "interpretation",
    "dependencies",
}

@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    evidence: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "evidence": self.evidence,
        }


def validate_generated_block(
    tex: str,
    *,
    artifact_type: str | None = None,
    expected_label: str | None = None,
) -> dict[str, Any]:
    cleaned = _strip_comments(tex)
    findings: list[Finding] = []

    env_matches = list(_FORMAL_ENV.finditer(cleaned))
    if len(env_matches) != 1:
        findings.append(
            Finding(
                "FAIL",
                "formal_environment_count",
                "Generated block must contain exactly one formal mathematical environment.",
                f"found={len(env_matches)}",
            )
        )

    inferred_type = None
    env_body = ""
    if env_matches:
        env_name = env_matches[0].group(1)
        inferred_type = config.ENV_TO_TYPE.get(env_name)
        env_body = env_matches[0].group("body")
        if artifact_type and inferred_type != artifact_type:
            findings.append(
                Finding(
                    "FAIL",
                    "artifact_type_mismatch",
                    f"Expected artifact type `{artifact_type}` but found `{inferred_type}`.",
                    env_name,
                )
            )

    effective_type = artifact_type or inferred_type

    labels = _LABEL.findall(cleaned)
    if len(labels) != 1:
        findings.append(
            Finding(
                "FAIL",
                "label_count",
                "Generated block must contain exactly one label.",
                f"labels={labels}",
            )
        )
    elif expected_label and labels[0] != expected_label:
        findings.append(
            Finding(
                "FAIL",
                "label_mismatch",
                "Generated block label does not match the requested canonical label.",
                f"expected={expected_label}; found={labels[0]}",
            )
        )

    if effective_type:
        findings.extend(_validate_box(cleaned, effective_type))

    if env_body and r"\operatorname" in env_body:
        findings.append(
            Finding(
                "FAIL",
                "predicate_leakage_in_environment",
                "Formal environment body must use standard notation, not predicate names.",
                _excerpt(env_body, r"\operatorname"),
            )
        )

    if effective_type == "def":
        findings.extend(_validate_definition(cleaned, env_body))

    findings.extend(_validate_required_logical_blocks(cleaned))
    findings.extend(_validate_common_latex(cleaned))
    findings.extend(_validate_dependencies(cleaned))

    failures = sum(1 for finding in findings if finding.severity == "FAIL")
    warnings = sum(1 for finding in findings if finding.severity == "WARNING")
    return {
        "result": "PASS" if failures == 0 else "FAIL",
        "summary": {
            "failures": failures,
            "warnings": warnings,
            "findings": len(findings),
        },
        "artifact_type": effective_type,
        "label": labels[0] if len(labels) == 1 else None,
        "findings": [finding.as_dict() for finding in findings],
    }


def validate_generated_file(
    path: Path,
    *,
    artifact_type: str | None = None,
    expected_label: str | None = None,
) -> dict[str, Any]:
    report = validate_generated_block(
        path.read_text(encoding="utf-8-sig"),
        artifact_type=artifact_type,
        expected_label=expected_label,
    )
    report["path"] = str(path)
    return report


def format_generated_validation_report(report: dict[str, Any]) -> str:
    lines = [
        "# Generated Block Validation",
        f"- **Path:** `{report.get('path', '<memory>')}`",
        f"- **Result:** {report['result']}",
        f"- **Artifact Type:** {report.get('artifact_type') or '?'}",
        f"- **Label:** `{report.get('label') or '?'}`",
        f"- **Failures:** {report['summary']['failures']}",
        f"- **Warnings:** {report['summary']['warnings']}",
        "",
    ]

    findings = report.get("findings", [])
    if not findings:
        lines += ["_No deterministic validation findings._", ""]
        return "\n".join(lines)

    lines += ["## Findings", ""]
    for finding in findings:
        lines += [
            f"### {finding['severity']}: `{finding['code']}`",
            "",
            finding["message"],
            "",
        ]
        if finding.get("evidence"):
            lines += ["```text", finding["evidence"], "```", ""]
    return "\n".join(lines)


def _validate_box(tex: str, artifact_type: str) -> list[Finding]:
    findings: list[Finding] = []
    boxes = list(_TCOLORBOX.finditer(tex))
    if artifact_type in _BOX_REQUIRED_TYPES and not boxes:
        findings.append(
            Finding(
                "FAIL",
                "missing_required_box",
                f"`{artifact_type}` generated blocks must be wrapped in a house tcolorbox.",
            )
        )
        return findings

    if len(boxes) > 1:
        findings.append(
            Finding(
                "WARNING",
                "multiple_tcolorboxes",
                "Generated block contains more than one tcolorbox; verify this is intentional.",
                f"found={len(boxes)}",
            )
        )

    if not boxes:
        return findings

    options = boxes[0].group(1) or ""
    if not options.strip():
        findings.append(
            Finding(
                "FAIL",
                "bare_tcolorbox",
                "tcolorbox must declare house colback and colframe options.",
            )
        )
        return findings

    opts = _parse_options(options)
    expected = _EXPECTED_BOX_COLORS.get(artifact_type)
    if expected:
        expected_back, expected_frame = expected
        if opts.get("colback") != expected_back:
            findings.append(
                Finding(
                    "FAIL",
                    "wrong_box_colback",
                    f"`{artifact_type}` box must use colback={expected_back}.",
                    f"found={opts.get('colback')}",
                )
            )
        if opts.get("colframe") != expected_frame:
            findings.append(
                Finding(
                    "FAIL",
                    "wrong_box_colframe",
                    f"`{artifact_type}` box must use colframe={expected_frame}.",
                    f"found={opts.get('colframe')}",
                )
            )
    return findings


def _validate_definition(tex: str, env_body: str) -> list[Finding]:
    findings: list[Finding] = []
    titles = _support_titles(tex)
    required = set(_DEFINITION_REQUIRED_REMARKS)
    if _NO_LOCAL_DEPENDENCIES.search(tex):
        required.discard("dependencies")

    missing = sorted(required - titles)
    for title in missing:
        findings.append(
            Finding(
                "FAIL",
                "missing_definition_support_block",
                f"Generated definition is missing required remark block `{title}`.",
            )
        )

    if _definition_uses_one_way_if(env_body):
        findings.append(
            Finding(
                "FAIL",
                "definition_uses_one_way_if",
                "Definition body appears to use one-way `if`; use `if and only if` or `exactly when`.",
                _excerpt(env_body, r"\bif\b"),
            )
        )
    return findings


def _validate_required_logical_blocks(tex: str) -> list[Finding]:
    findings: list[Finding] = []
    remarks = [(_normalize_title(title), body) for title, body in _REMARK.findall(tex)]
    titles = _support_titles(tex)
    if "standard quantified statement" not in titles:
        findings.append(
            Finding(
                "FAIL",
                "missing_standard_quantified_statement",
                "Generated block must include a Standard quantified statement remark.",
            )
        )
    if "interpretation" not in titles:
        findings.append(
            Finding(
                "FAIL",
                "missing_interpretation",
                "Generated block must include an Interpretation remark.",
            )
        )
    binder_count = sum(
        _count_quantified_binders(body)
        for title, body in remarks
        if title == "standard quantified statement"
    )
    if binder_count >= 2 and "predicate reading" not in titles:
        findings.append(
            Finding(
                "FAIL",
                "missing_predicate_reading",
                "Generated block has at least two quantified binders but no Predicate reading remark.",
                f"binders={binder_count}",
            )
        )
    findings.extend(_validate_failure_modes(remarks, has_predicate_reading="predicate reading" in titles))
    return findings


def _validate_failure_modes(remarks: list[tuple[str, str]], *, has_predicate_reading: bool) -> list[Finding]:
    findings: list[Finding] = []
    for title, body in remarks:
        if title != "failure modes":
            continue
        if not re.search(r"\\begin\{description\}", body):
            findings.append(
                Finding(
                    "FAIL",
                    "failure_modes_missing_description",
                    "Failure modes remark must use a description environment.",
                )
            )
            continue
        items = list(re.finditer(r"\\item\[(?P<title>[^\]]+)\](?P<body>[\s\S]*?)(?=\\item\[|\\end\{description\})", body))
        if not items or items[0].group("title").strip().lower().rstrip(".") != "exposition":
            findings.append(
                Finding(
                    "FAIL",
                    "failure_modes_missing_exposition_item",
                    "Failure modes remark must start with \\item[Exposition.].",
                )
            )
        for item in items:
            if item.group("title").strip().lower().rstrip(".") == "exposition":
                continue
            displays = re.findall(r"\\\[[\s\S]*?\\\]", item.group("body"))
            if not displays:
                findings.append(
                    Finding(
                        "FAIL",
                        "failure_mode_missing_quantified_display",
                        f"Failure mode `{item.group('title').strip()}` lacks a quantified display.",
                    )
                )
            if has_predicate_reading and len(displays) < 2:
                findings.append(
                    Finding(
                        "FAIL",
                        "failure_mode_missing_predicate_display",
                        f"Failure mode `{item.group('title').strip()}` lacks a predicate-reading display.",
                    )
                )
    return findings


def _validate_common_latex(tex: str) -> list[Finding]:
    findings: list[Finding] = []
    bad_punctuation = _BAD_TEXT_PUNCTUATION.search(tex)
    if "\ufeff" in tex or bad_punctuation:
        findings.append(
            Finding(
                "FAIL",
                "bom_or_mojibake",
                "Generated block contains a byte-order mark, smart punctuation, or mojibake text; regenerate with plain ASCII punctuation.",
                "\\ufeff" if "\ufeff" in tex else (bad_punctuation.group(0) if bad_punctuation else ""),
            )
        )
    match = _RAW_STRUCTURE_QUANTIFIER.search(tex)
    if match:
        findings.append(
            Finding(
                "FAIL",
                "raw_structure_quantifier",
                "Do not quantify over raw structures with syntax like `\\forall (S,\\le)`.",
                match.group(0),
            )
        )
    if "\\begin{tcolorbox}\n" in tex or "\\begin{tcolorbox}\r\n" in tex:
        findings.append(
            Finding(
                "FAIL",
                "bare_tcolorbox",
                "tcolorbox must include explicit house options.",
            )
        )
    bare_predicate = _BARE_PREDICATE_MACRO.search(tex)
    if bare_predicate:
        findings.append(
            Finding(
                "FAIL",
                "bare_predicate_macro",
                "Predicate readings must use canonical text predicate form, e.g. `\\operatorname{UpperBound}`, not undefined bare predicate macros.",
                bare_predicate.group(0),
            )
        )
    return findings


def _validate_dependencies(tex: str) -> list[Finding]:
    findings: list[Finding] = []
    if _NO_LOCAL_DEPENDENCIES.search(tex):
        return findings

    dependencies = [
        body for title, body in _REMARK.findall(tex)
        if _normalize_title(title) == "dependencies"
    ]
    if not dependencies:
        return findings

    body = dependencies[-1]
    if "No local dependencies." in body:
        return findings

    refs = _HYPERREF.findall(body)
    if not refs and "UNRESOLVED_DEPENDENCY" not in body:
        findings.append(
            Finding(
                "WARNING",
                "dependencies_without_links",
                "Dependencies block has content but no formal hyperref labels or unresolved-dependency comments.",
                body.strip()[:240],
            )
        )
        return findings

    known = _load_known_formal_labels()
    for ref in refs:
        if ref.startswith("prf:"):
            findings.append(
                Finding(
                    "FAIL",
                    "proof_label_in_dependencies",
                    "Dependencies must refer to formal math items, not proof labels.",
                    ref,
                )
            )
        elif known and ref not in known:
            findings.append(
                Finding(
                    "FAIL",
                    "unknown_dependency_label",
                    "Dependency label is not present in the formal label index.",
                    ref,
                )
            )
    return findings


def _parse_options(options: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for part in re.split(r",(?![^{}]*\})", options):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        parsed[key.strip()] = value.strip().strip("{}")
    return parsed


def _definition_uses_one_way_if(body: str) -> bool:
    text = _latex_to_plain(body)
    has_biconditional = any(
        marker in text
        for marker in ("if and only if", "exactly when", " iff ", "Longleftrightarrow")
    ) or any(marker in body for marker in (r"\iff", r"\Longleftrightarrow"))
    if has_biconditional:
        return False
    return bool(re.search(r"\bis\b[^.]*\bif\b", text, re.IGNORECASE))


def _latex_to_plain(text: str) -> str:
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{([^{}]*)\})?", r"\1", text)
    text = text.replace("$", " ")
    return re.sub(r"\s+", " ", text)


def _count_quantified_binders(text: str) -> int:
    text = re.sub(r"\\(?:,|;|:|quad|qquad|enspace|thinspace|medspace|!)", " ", text)
    text = re.sub(r"\\text\{[^{}]*\}", " ", text)
    spans = list(re.finditer(r"\\(?:forall|exists)\b", text))
    count = 0
    for index, match in enumerate(spans):
        start = match.end()
        end = spans[index + 1].start() if index + 1 < len(spans) else len(text)
        segment = text[start:end]
        segment = re.split(
            r"\\(?:Rightarrow|Longrightarrow|Leftrightarrow|Longleftrightarrow|implies|iff|land|lor)\b|[.;:]",
            segment,
            maxsplit=1,
        )[0]
        segment = re.split(r"\\in\b|\\notin\b|\\subseteq\b|\\leq\b|\\geq\b|=|<|>|\\mid\b|\|", segment, maxsplit=1)[0]
        segment = re.sub(r"\\[A-Za-z]+", " ", segment)
        segment = segment.replace("{", " ").replace("}", " ")
        count += len(
            re.findall(
                r"[A-Za-z](?:_\{[^{}]+\}|_[A-Za-z0-9]+)?(?:\^\{[^{}]+\}|\^[A-Za-z0-9]+)?",
                segment,
            )
        )
    return count


def _normalize_title(title: str | None) -> str:
    return re.sub(r"\s+", " ", (title or "").strip().lower())


def _support_titles(tex: str) -> set[str]:
    titles = {_normalize_title(title) for title, _ in _REMARK.findall(tex)}
    if re.search(r"\\begin\{dependencies\}", tex):
        titles.add("dependencies")
    return titles


def _strip_comments(text: str) -> str:
    return "\n".join(_LINE_COMMENT.sub("", line) for line in text.splitlines())


def _excerpt(text: str, pattern: str, radius: int = 100) -> str:
    try:
        match = re.search(pattern, text, re.IGNORECASE)
    except re.PatternError:
        match = re.search(re.escape(pattern), text, re.IGNORECASE)
    if not match:
        return text.strip()[: radius * 2]
    start = max(0, match.start() - radius)
    end = min(len(text), match.end() + radius)
    return text[start:end].strip()


def _load_known_formal_labels() -> set[str]:
    index_dir = config.REPORTS_DIR / "indexes"
    candidates = sorted(
        index_dir.glob("*-formal-label-index.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return set()
    try:
        data = json.loads(candidates[0].read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    return {item["label"] for item in data.get("items", []) if item.get("label")}
