"""
audits/statement.py
Audits a single theorem-like environment and its following remark* blocks.
"""

import re
from pathlib import Path

from auditor import client, loader
from auditor.config import THEOREM_LIKE_ENVS
from auditor.report import audit_report_from_checks, merge_audit_reports, save_audit_report
from auditor.validators.generated_block import validate_statement_block


# ---------------------------------------------------------------------------
# Environment extraction
# ---------------------------------------------------------------------------

# Matches \begin{envname} up to (and including) the matching \end{envname},
# then captures all immediately following remark* blocks.
_REMARK_BLOCK = re.compile(
    r"\\begin\{remark\*\}.*?\\end\{remark\*\}",
    re.DOTALL,
)
_DEPENDENCIES_BLOCK = re.compile(
    r"\\begin\{dependencies\}.*?\\end\{dependencies\}",
    re.DOTALL,
)
_NO_LOCAL_DEPENDENCIES = re.compile(r"\\NoLocalDependencies\b")
_DEFINITIONAL_ROOT = re.compile(r"\\DefinitionalRoot\b")


def _extract_environment_and_remarks(
    tex: str,
    label: str,
) -> str | None:
    """
    Extracts the environment block identified by `label` and all remark*
    blocks that immediately follow it (before the next environment or section).

    Returns the extracted LaTeX string, or None if the label is not found.
    """
    # Find the label position
    label_pattern = re.compile(re.escape(f"\\label{{{label}}}"))
    label_match = label_pattern.search(tex)
    if not label_match:
        return None

    # Walk back to find the \begin{...} that contains this label
    prefix = tex[:label_match.start()]
    begin_pattern = re.compile(
        r"\\begin\{(" + "|".join(THEOREM_LIKE_ENVS) + r")\}",
        re.IGNORECASE,
    )
    begins = list(begin_pattern.finditer(prefix))
    if not begins:
        return None

    last_begin = begins[-1]
    env_name = last_begin.group(1).lower()
    end_pattern = re.compile(re.escape(f"\\end{{{env_name}}}"))

    # Find matching \end
    env_start = last_begin.start()
    end_match = end_pattern.search(tex, label_match.start())
    if not end_match:
        return None

    block_start = env_start
    block_end = end_match.end()

    # If the formal environment is wrapped in a display box, audit the wrapper
    # too. Otherwise the model never sees the required box and the following
    # support remarks are hidden behind the wrapper's closing line.
    box_start, box_end = _expand_to_enclosing_display_box(tex, block_start, block_end)
    block_start, block_end = box_start, box_end
    env_block = tex[block_start:block_end]

    # Collect immediately following support blocks. Dependencies use their own
    # environment (or a silent marker), so limiting this to remark* silently
    # hid the canonical dependency record from the audit prompt.
    rest = tex[block_end:]
    support_blocks = []

    # Walk through rest; collect contiguous remark* blocks, allowing blank
    # lines and ordinary comment separators between support remarks.
    pos = 0
    while pos < len(rest):
        pos = _skip_whitespace_and_comments(rest, pos)
        for pattern in (
            _REMARK_BLOCK,
            _DEPENDENCIES_BLOCK,
            _NO_LOCAL_DEPENDENCIES,
            _DEFINITIONAL_ROOT,
        ):
            match = pattern.match(rest, pos)
            if match:
                support_blocks.append(match.group(0))
                pos = match.end()
                break
        else:
            if pos < len(rest):
                break
            continue

    combined = env_block
    if support_blocks:
        combined += "\n\n" + "\n\n".join(support_blocks)

    return combined


def _skip_whitespace_and_comments(text: str, pos: int) -> int:
    while pos < len(text):
        while pos < len(text) and text[pos].isspace():
            pos += 1
        if pos < len(text) and text[pos] == "%":
            newline = text.find("\n", pos)
            if newline == -1:
                return len(text)
            pos = newline + 1
            continue
        return pos
    return pos


def _expand_to_enclosing_display_box(tex: str, start: int, end: int) -> tuple[int, int]:
    """
    Expands an environment span to an immediately enclosing display box, if
    one exists. This intentionally mirrors the generated patcher span logic.
    """
    candidates = [
        (r"\\begin\{tcolorbox\}(?:\[[^\]]*\])?", r"\\end\{tcolorbox\}"),
        (r"\\begin\{bpnew\}\{[^}]*\}\{[^}]*\}", r"\\end\{bpnew\}"),
    ]

    best: tuple[int, int] | None = None
    for open_re, close_re in candidates:
        opens = list(re.finditer(open_re, tex[:start], re.DOTALL))
        if not opens:
            continue

        closes_before = list(re.finditer(close_re, tex[:start]))
        if closes_before and closes_before[-1].start() > opens[-1].start():
            continue

        open_match = opens[-1]
        close_after = re.search(close_re, tex[end:])
        if not close_after:
            continue

        candidate = (open_match.start(), end + close_after.end())
        if best is None or candidate[0] > best[0]:
            best = candidate

    return best if best is not None else (start, end)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_SEMANTIC_CHECK_REQUIREMENTS = {
    "semantic_atomicity": "R",
    "statement_quantified_equivalence": "R",
    "predicate_reading_equivalence": "C",
    "negation_correctness": "C",
    "failure_mode_correctness": "C",
    "contrapositive_correctness": "C",
    "interpretation_fidelity": "R",
}

def _deterministic_structure_report(
    block: str,
    *,
    label: str,
    artifact_type: str,
) -> dict:
    """Convert the local statement-block validator into the shared report form."""
    validation = validate_statement_block(
        block,
        artifact_type=artifact_type,
        expected_label=label,
    )
    checks = []
    for finding in validation["findings"]:
        status = "FAIL" if finding["severity"] == "FAIL" else "NONCOMPLIANT"
        message = finding["message"]
        if finding.get("evidence"):
            message += f" Evidence: {finding['evidence']}"
        checks.append(
            {
                "block_id": finding["code"],
                "requirement": "R",
                "status": status,
                "finding": message,
            }
        )
    if not checks:
        checks.append(
            {
                "block_id": "deterministic_statement_structure",
                "requirement": "R",
                "status": "PASS",
                "finding": "",
            }
        )
    return audit_report_from_checks(
        checks,
        audit_type="statement",
        artifact_type=artifact_type,
        label=label,
    )


def _semantic_judgment_report(
    payload: dict,
    *,
    label: str,
    artifact_type: str,
) -> dict:
    """Validate the compact model response and convert it to an audit report."""
    judgments = payload.get("judgments")
    if not isinstance(judgments, list):
        raise RuntimeError("Semantic statement review must return a judgments array.")

    by_id: dict[str, dict] = {}
    received_ids: list[str] = []
    for judgment in judgments:
        if not isinstance(judgment, dict):
            raise RuntimeError("Each semantic statement judgment must be an object.")
        check_id = judgment.get("check_id")
        if check_id not in _SEMANTIC_CHECK_REQUIREMENTS:
            raise RuntimeError(f"Unknown semantic statement check id: {check_id!r}")
        if check_id in by_id:
            raise RuntimeError(f"Duplicate semantic statement check id: {check_id}")
        status = judgment.get("status")
        if status not in {"PASS", "FAIL", "NOT_APPLICABLE"}:
            raise RuntimeError(
                f"Semantic statement check {check_id} has invalid status: {status!r}"
            )
        if status == "NOT_APPLICABLE" and _SEMANTIC_CHECK_REQUIREMENTS[check_id] != "C":
            raise RuntimeError(f"Required semantic statement check {check_id} cannot be NOT_APPLICABLE.")
        finding = judgment.get("finding", "")
        if not isinstance(finding, str):
            raise RuntimeError(f"Semantic statement check {check_id} finding must be a string.")
        if status == "FAIL" and not finding.strip():
            raise RuntimeError(f"Failing semantic statement check {check_id} requires a finding.")
        by_id[check_id] = judgment
        received_ids.append(check_id)

    missing = set(_SEMANTIC_CHECK_REQUIREMENTS) - set(by_id)
    if missing:
        raise RuntimeError(
            "Semantic statement review omitted required checks: " + ", ".join(sorted(missing))
        )
    expected_ids = list(_SEMANTIC_CHECK_REQUIREMENTS)
    if received_ids != expected_ids:
        raise RuntimeError("Semantic statement review returned checks out of canonical order.")

    checks = []
    for check_id, requirement in _SEMANTIC_CHECK_REQUIREMENTS.items():
        judgment = by_id[check_id]
        model_status = judgment["status"]
        if requirement == "C":
            status = {
                "PASS": "CONDITIONAL_MET",
                "FAIL": "CONDITIONAL_VIOLATION",
                "NOT_APPLICABLE": "CONDITIONAL_UNMET",
            }[model_status]
        else:
            status = model_status
        checks.append(
            {
                "block_id": check_id,
                "requirement": requirement,
                "status": status,
                "finding": judgment.get("finding", "").strip(),
            }
        )
    return audit_report_from_checks(
        checks,
        audit_type="statement",
        artifact_type=artifact_type,
        label=label,
    )

def audit_statement(
    tex_path: Path,
    label: str,
    artifact_type: str,
    chapter: str,
    semantic_review: bool = True,
    print_report: bool = True,
    output_dir: Path | None = None,
    filename_prefix: str = "",
) -> dict:
    """
    Audits a single statement environment identified by label.

    Args:
        tex_path:       Path to the .tex file containing the environment.
        label:          The full LaTeX label (e.g. "def:upper-bound").
        artifact_type:  One of: def, thm, lem, prop, cor, ax.
        chapter:        Chapter subject name (for report filing).

    Returns:
        The audit report dict (conforming to audit-report.json schema).
    """
    tex = tex_path.read_text(encoding="utf-8")

    block = _extract_environment_and_remarks(tex, label)
    if block is None:
        raise ValueError(
            f"Label '{label}' not found in {tex_path}. "
            f"Verify the label exists and the file is correct."
        )

    report = _deterministic_structure_report(
        block,
        label=label,
        artifact_type=artifact_type,
    )
    if semantic_review:
        system = loader.prompt("audit_statement")
        user = (
            f"## Statement Artifact\n\n"
            f"Artifact type: {artifact_type}\n"
            f"Label: {label}\n\n"
            f"```latex\n{block}\n```"
        )
        payload = client.call(system, user, expect_json=True, validate_report=False)
        semantic = _semantic_judgment_report(
            payload,
            label=label,
            artifact_type=artifact_type,
        )
        report = merge_audit_reports(report, semantic)

    client.validate_audit_report(report)

    report["_report_path"] = str(
        save_audit_report(
            report,
            chapter,
            "audit-statement",
            print_report=print_report,
            output_dir=output_dir,
            filename_prefix=filename_prefix,
        )
    )

    return report


def audit_statement_from_yaml_entry(
    entry: dict,
    chapter_root: Path,
    chapter: str,
    print_report: bool = True,
    output_dir: Path | None = None,
    filename_prefix: str = "",
) -> dict:
    """
    Convenience wrapper that accepts an environments entry from chapter.yaml.
    """
    tex_path = chapter_root / entry["file"]
    return audit_statement(
        tex_path=tex_path,
        label=entry["label"],
        artifact_type=entry["type"],
        chapter=chapter,
        print_report=print_report,
        output_dir=output_dir,
        filename_prefix=filename_prefix,
    )
