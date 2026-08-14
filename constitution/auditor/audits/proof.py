"""
audits/proof.py
Audits a single proof .tex file against the canonical proof-file contract.
"""

from pathlib import Path
import re
import sys

from auditor import client, loader
from auditor.report import audit_report_from_checks, merge_audit_reports, save_audit_report


TOOLS = Path(__file__).resolve().parents[3] / "tools" / "governance"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import audit_proof_layout  # noqa: E402
from validators import proof_file_contract  # noqa: E402


PROOF_FOR_RE = re.compile(r"\\LRAProofFor\{((?:thm|lem|prop|cor):[^}]+)\}")

_LAYER_IDS = [
    "layer1_newpage",
    "layer2_phantomsection",
    "layer3_proof_label",
    "layer4_proof_for",
    "layer5_return_remark",
    "layer6_proof_vault_url",
    "layer7_theorem_restatement",
    "layer8_professional_proof",
    "layer9_detailed_proof",
    "layer10_structure_remark",
    "layer11_dependencies",
    "layer12_clearpage",
]

_FINDING_LAYER = {
    "missing_newpage": 0,
    "missing_phantomsection": 1,
    "missing_proof_label": 2,
    "proof_label_count": 2,
    "label_root_mismatch": 2,
    "filename_label_mismatch": 2,
    "filename_style": 2,
    "proof_label_after_environment": 2,
    "proof_label_after_proof_for": 2,
    "missing_proof_for": 3,
    "proof_for_count": 3,
    "missing_return_navigation": 4,
    "missing_return_link": 4,
    "multiple_return_navigation": 4,
    "return_navigation_mismatch": 4,
    "empty_proof_vault_url": 5,
    "raw_image_proof_vault_url": 5,
    "proof_vault_url_position": 5,
    "missing_theorem_restatement": 6,
    "invalid_restatement_count": 6,
    "label_inside_restatement": 6,
    "restatement_type_mismatch": 6,
    "missing_professional_standard_proof": 7,
    "missing_professional_body": 7,
    "missing_professional_proof_body_start": 7,
    "missing_detailed_learning_proof": 8,
    "missing_detailed_body": 8,
    "missing_detailed_proof_body_start": 8,
    "proof_step_macro": 8,
    "remark_organizer_inside_detailed_proof": 8,
    "partial_proof_population": 8,
    "partial_stub": 8,
    "missing_proof_structure": 9,
    "missing_proof_structure_body": 9,
    "missing_dependencies": 10,
    "missing_dependencies_body": 10,
    "proof_dependency_target": 10,
    "proof_dependencies_without_hyperref": 10,
    "invalid_proof_dependency_target": 10,
    "dependencies_unpopulated_for_populated_proof": 10,
    "missing_clearpage": 11,
    "content_after_clearpage": 11,
}

_SEMANTIC_CHECK_REQUIREMENTS = {
    "restatement_fidelity": "R",
    "professional_proof_validity": "R",
    "detailed_proof_validity": "R",
    "proof_layer_equivalence": "R",
    "proof_structure_fidelity": "R",
    "dependency_usage_completeness": "C",
}


def _local_contract_findings(proof_path: Path):
    findings = []
    proof_file_contract._validate_file(_chapter_root(proof_path), proof_path.resolve(), findings)
    return findings


def _has_stub_proof_bodies(tex: str) -> bool:
    professional, detailed = audit_proof_layout.proof_blocks(tex)
    return bool(
        professional
        and detailed
        and audit_proof_layout.has_todo(professional)
        and audit_proof_layout.has_todo(detailed)
    )


def _deterministic_proof_report(
    proof_path: Path,
    layout,
    *,
    label: str,
) -> dict:
    """Render the canonical layout and local proof validators as layer checks."""
    layer_findings: list[list[tuple[str, str, str]]] = [[] for _ in _LAYER_IDS]
    extra_findings: list[tuple[str, str, str]] = []

    combined = [
        (item.code, item.severity, item.message)
        for item in layout.findings
    ]
    combined.extend(
        (item.code, item.severity, item.message)
        for item in _local_contract_findings(proof_path)
    )
    seen = set()
    for code, severity, message in combined:
        key = (code, severity, message)
        if key in seen:
            continue
        seen.add(key)
        layer_index = _FINDING_LAYER.get(code)
        target = layer_findings[layer_index] if layer_index is not None else extra_findings
        target.append(key)

    tex = proof_path.read_text(encoding="utf-8", errors="ignore")
    is_stub = _has_stub_proof_bodies(tex)
    checks = []
    for index, block_id in enumerate(_LAYER_IDS):
        requirement = "C" if index == 5 else "R"
        findings = layer_findings[index]
        if findings:
            has_error = any(severity == "error" for _, severity, _ in findings)
            if requirement == "C":
                status = "CONDITIONAL_VIOLATION"
            else:
                status = "FAIL" if has_error else "NONCOMPLIANT"
            finding_text = " ".join(f"{code}: {message}" for code, _, message in findings)
        elif is_stub and index in {7, 8}:
            status = "STUB"
            finding_text = "Intentional TODO proof stub; mathematical proof content was not audited."
        elif requirement == "C":
            status = (
                "CONDITIONAL_MET"
                if audit_proof_layout.PROOF_VAULT_RE.search(tex)
                else "CONDITIONAL_UNMET"
            )
            finding_text = ""
        else:
            status = "PASS"
            finding_text = ""
        checks.append(
            {
                "block_id": block_id,
                "requirement": requirement,
                "status": status,
                "finding": finding_text,
            }
        )

    for code, severity, message in extra_findings:
        checks.append(
            {
                "block_id": code,
                "requirement": "R",
                "status": "FAIL" if severity == "error" else "NONCOMPLIANT",
                "finding": message,
            }
        )

    return audit_report_from_checks(
        checks,
        audit_type="proof",
        artifact_type="proof",
        label=label,
        stub=is_stub,
    )


def _semantic_proof_report(payload: dict, *, label: str) -> dict:
    judgments = payload.get("judgments")
    if not isinstance(judgments, list):
        raise RuntimeError("Semantic proof review must return a judgments array.")

    by_id = {}
    received_ids = []
    for judgment in judgments:
        if not isinstance(judgment, dict):
            raise RuntimeError("Each semantic proof judgment must be an object.")
        check_id = judgment.get("check_id")
        if check_id not in _SEMANTIC_CHECK_REQUIREMENTS:
            raise RuntimeError(f"Unknown semantic proof check id: {check_id!r}")
        if check_id in by_id:
            raise RuntimeError(f"Duplicate semantic proof check id: {check_id}")
        status = judgment.get("status")
        if status not in {"PASS", "FAIL", "NOT_APPLICABLE"}:
            raise RuntimeError(f"Semantic proof check {check_id} has invalid status: {status!r}")
        requirement = _SEMANTIC_CHECK_REQUIREMENTS[check_id]
        if status == "NOT_APPLICABLE" and requirement != "C":
            raise RuntimeError(f"Required semantic proof check {check_id} cannot be NOT_APPLICABLE.")
        finding = judgment.get("finding", "")
        if not isinstance(finding, str):
            raise RuntimeError(f"Semantic proof check {check_id} finding must be a string.")
        if status == "FAIL" and not finding.strip():
            raise RuntimeError(f"Failing semantic proof check {check_id} requires a finding.")
        if status != "FAIL" and finding.strip():
            raise RuntimeError(f"Passing semantic proof check {check_id} must have an empty finding.")
        by_id[check_id] = judgment
        received_ids.append(check_id)

    expected_ids = list(_SEMANTIC_CHECK_REQUIREMENTS)
    missing = set(expected_ids) - set(by_id)
    if missing:
        raise RuntimeError("Semantic proof review omitted required checks: " + ", ".join(sorted(missing)))
    if received_ids != expected_ids:
        raise RuntimeError("Semantic proof review returned checks out of canonical order.")

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
        audit_type="proof",
        artifact_type="proof",
        label=label,
    )


def _semantic_proof_input(tex: str, source_context: str, source_label: str) -> str:
    restatement = audit_proof_layout.block(tex, audit_proof_layout.THEOREM_STAR_RE)
    professional, detailed = audit_proof_layout.proof_blocks(tex)
    structure = audit_proof_layout.block(tex, audit_proof_layout.PROOF_STRUCTURE_RE)
    dependencies = audit_proof_layout.block(tex, audit_proof_layout.DEPENDENCIES_RE)
    return (
        f"## Associated Source\n\nLabel: {source_label}\n\n```latex\n{source_context}\n```\n\n"
        f"## Proof Restatement\n\n```latex\n{restatement}\n```\n\n"
        f"## Professional Proof Body\n\n```latex\n{professional}\n```\n\n"
        f"## Detailed Proof Body\n\n```latex\n{detailed}\n```\n\n"
        f"## Proof Structure\n\n```latex\n{structure}\n```\n\n"
        f"## Dependencies\n\n```latex\n{dependencies}\n```"
    )


def audit_proof(
    proof_path: Path,
    chapter: str,
    label: str | None = None,
    theorem_label: str | None = None,
    semantic_review: bool = True,
    print_report: bool = True,
    output_dir: Path | None = None,
    filename_prefix: str = "",
) -> dict:
    """
    Audits a proof .tex file.

    Args:
        proof_path: Path to the proof .tex file.
        chapter:    Chapter subject name (for report filing).

    Returns:
        The audit report dict.
    """
    tex = proof_path.read_text(encoding="utf-8")
    layout = _deterministic_layout_audit(proof_path)
    macro_label = _infer_theorem_label(tex)
    if theorem_label and macro_label and theorem_label != macro_label:
        raise ValueError(
            f"proof metadata target {theorem_label} disagrees with "
            f"\\LRAProofFor target {macro_label}"
        )
    source_label = macro_label or theorem_label
    source_context = _find_source_statement(proof_path, source_label)
    proof_label = label or _infer_label(tex, proof_path)

    report = _deterministic_proof_report(
        proof_path,
        layout,
        label=proof_label,
    )
    if semantic_review and not _has_stub_proof_bodies(tex):
        if not source_label or not source_context:
            unavailable = audit_report_from_checks(
                [
                    {
                        "block_id": "semantic_source_context",
                        "requirement": "R",
                        "status": "NONCOMPLIANT",
                        "finding": "Associated source statement could not be resolved; mathematical proof review was not run.",
                    }
                ],
                audit_type="proof",
                artifact_type="proof",
                label=proof_label,
            )
            report = merge_audit_reports(report, unavailable)
        else:
            payload = client.call(
                loader.prompt("audit_proof"),
                _semantic_proof_input(tex, source_context, source_label),
                expect_json=True,
                validate_report=False,
            )
            report = merge_audit_reports(
                report,
                _semantic_proof_report(payload, label=proof_label),
            )

    client.validate_audit_report(report)

    report["_report_path"] = str(
        save_audit_report(
            report,
            chapter,
            "audit-proof",
            print_report=print_report,
            output_dir=output_dir,
            filename_prefix=filename_prefix,
        )
    )

    return report


def _chapter_root(proof_path: Path) -> Path:
    resolved = proof_path.resolve()
    for parent in resolved.parents:
        if parent.name == "proofs":
            return parent.parent
    raise ValueError(f"proof file is not under a proofs directory: {proof_path}")


def _deterministic_layout_audit(proof_path: Path):
    chapter_root = _chapter_root(proof_path)
    return audit_proof_layout.audit_proof(
        proof_path.resolve(),
        chapter_root,
        chapter_root,
        audit_proof_layout.note_topics(chapter_root),
        False,
    )


def _infer_theorem_label(tex: str) -> str | None:
    match = PROOF_FOR_RE.search(tex)
    return match.group(1) if match else None


def _find_source_statement(proof_path: Path, theorem_label: str | None) -> str | None:
    if not theorem_label:
        return None
    from auditor.audits.statement import _extract_environment_and_remarks

    notes_root = _chapter_root(proof_path) / "notes"
    if not notes_root.exists():
        return None
    needle = f"\\label{{{theorem_label}}}"
    for path in sorted(notes_root.rglob("*.tex")):
        if path.name == "index.tex":
            continue
        tex = path.read_text(encoding="utf-8", errors="ignore")
        if needle not in tex:
            continue
        return _extract_environment_and_remarks(tex, theorem_label)
    return None


def _infer_label(tex: str, proof_path: Path) -> str:
    import re

    match = re.search(r"\\label\{(prf:[^}]+)\}", tex)
    if match:
        return match.group(1)
    return f"prf:{proof_path.stem.removeprefix('prf-')}"


def _todo_stub_report(label: str) -> dict:
    checks = [
        ("layer1_newpage", "R", "PASS", ""),
        ("layer2_phantomsection", "R", "PASS", ""),
        ("layer3_proof_label", "R", "PASS", ""),
        ("layer4_proof_for", "R", "PASS", ""),
        ("layer5_return_remark", "R", "PASS", ""),
        ("layer6_proof_vault_url", "C", "CONDITIONAL_UNMET", ""),
        ("layer7_theorem_restatement", "R", "PASS", ""),
        ("layer8_professional_proof", "R", "STUB", "Intentional TODO proof stub; full proof not audited yet."),
        ("layer9_detailed_proof", "R", "STUB", "Intentional TODO proof stub; full proof not audited yet."),
        ("layer10_structure_remark", "R", "PASS", ""),
        ("layer11_dependencies", "R", "PASS", ""),
        ("layer12_clearpage", "R", "PASS", ""),
    ]
    return {
        "audit_type": "proof",
        "artifact_type": "proof",
        "label": label,
        "summary": {
            "total_checks": len(checks),
            "passed": 9,
            "failed": 0,
            "noncompliant": 0,
            "conditional_met": 0,
            "conditional_unmet": 1,
            "conditional_violation": 0,
            "dependent_met": 0,
            "dependent_unmet": 0,
            "dependent_violation": 0,
            "forbidden_violation": 0,
            "stub": True,
        },
        "checks": [
            {
                "block_id": block_id,
                "requirement": requirement,
                "status": status,
                "finding": finding,
            }
            for block_id, requirement, status, finding in checks
        ],
        "violations": [],
    }


def audit_proof_from_yaml_entry(
    entry: dict,
    chapter_root: Path,
    chapter: str,
    print_report: bool = True,
    output_dir: Path | None = None,
    filename_prefix: str = "",
) -> dict:
    """
    Convenience wrapper that accepts a proof_files entry from chapter.yaml.
    """
    proof_path = chapter_root / entry["file"]
    return audit_proof(
        proof_path=proof_path,
        chapter=chapter,
        label=entry.get("label"),
        theorem_label=entry.get("theorem_label"),
        print_report=print_report,
        output_dir=output_dir,
        filename_prefix=filename_prefix,
    )
