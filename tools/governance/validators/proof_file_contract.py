from __future__ import annotations

import re
from pathlib import Path

from core.finding import Finding, finding
from core.tex import read_text, strip_latex_comments
from core.file_inventory import validator_files


PROOF_FOR_RE = re.compile(r"\\LRAProofFor\{(?P<label>(?:thm|lem|prop|cor):[A-Za-z0-9-]+)\}")
PROOF_LABEL_RE = re.compile(r"\\label\{prf:[a-z0-9-]+\}")
LABEL_RE = re.compile(r"\\label\{[^{}]+\}")
HYPERREF_RE = re.compile(r"\\hyperref\[(?P<label>[^\]]+)\]")
RESTATEMENT_RE = re.compile(
    r"\\begin\{(?P<env>theorem|lemma|proposition|corollary)\*\}(?P<body>[\s\S]*?)\\end\{(?P=env)\*\}",
    re.IGNORECASE,
)
PROOF_BODY_RE = re.compile(
    r"\\begin\{proof\}(?:\[(?P<title>[^\]]*)\])?(?P<body>[\s\S]*?)\\end\{proof\}",
    re.IGNORECASE,
)
DEPENDENCIES_RE = re.compile(r"\\begin\{dependencies\}(?P<body>[\s\S]*?)\\end\{dependencies\}", re.IGNORECASE)
RETURN_RE = re.compile(r"\\begin\{remark\*\}\[Return\](?P<body>[\s\S]*?)\\end\{remark\*\}", re.IGNORECASE)
PROOF_STRUCTURE_RE = re.compile(r"\\begin\{remark\*\}\[Proof structure\][\s\S]*?\\end\{remark\*\}", re.IGNORECASE)
PROFESSIONAL_RE = re.compile(r"Professional Standard Proof", re.IGNORECASE)
DETAILED_RE = re.compile(r"Detailed (?:Learning|Instructional) Proof", re.IGNORECASE)
TODO_RE = re.compile(r"\bTODO\b", re.IGNORECASE)
PROOF_BODY_START_RE = re.compile(r"^\s*\\LRAProofBodyStart\b")
FORBIDDEN_PROOF_ORGANIZER_RE = re.compile(
    r"\\begin\{(?P<env>topicbox|exposition)\}",
    re.IGNORECASE,
)
FORBIDDEN_STEP_MACRO_RE = re.compile(r"\\(?:ProofStep|Step|Flash[A-Za-z]*)\b")
REMARK_ENV_RE = re.compile(r"\\begin\{remark\*?\}", re.IGNORECASE)
FORMAL_PREFIXES = {"def", "ax", "thm", "lem", "prop", "cor"}
RESTATEMENT_ENV_BY_PREFIX = {
    "thm": "theorem",
    "lem": "lemma",
    "prop": "proposition",
    "cor": "corollary",
}


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    for tex in validator_files(volume_root, files):
        rel = tex.resolve().relative_to(volume_root.resolve()).as_posix()
        if "/proofs/" not in f"/{rel}" or "/proofs/exercises/" in f"/{rel}" or tex.name == "index.tex":
            continue
        _validate_file(volume_root, tex, findings)
    return findings


def _validate_file(volume_root: Path, path: Path, findings: list[Finding]) -> None:
    text = strip_latex_comments(read_text(path))
    _validate_text(volume_root, path, text, findings)


def validate_text(
    text: str,
    *,
    virtual_path: Path | None = None,
) -> list[Finding]:
    """Validate an in-memory proof file without repository routing checks."""
    path = virtual_path or Path("proofs/generated/prf-generated.tex")
    root = Path(".")
    cleaned = strip_latex_comments(text)
    findings: list[Finding] = []
    _validate_text(root, path, cleaned, findings)

    from audit_proof_layout import ProofAudit, validate_order

    layout = ProofAudit(path=path.as_posix(), status="non_compliant")
    validate_order(cleaned, layout)
    findings.extend(
        finding(item.code, item.message, path, root, severity=item.severity)
        for item in layout.findings
    )
    return findings


def _validate_text(
    volume_root: Path,
    path: Path,
    text: str,
    findings: list[Finding],
) -> None:
    proof_for = PROOF_FOR_RE.search(text)
    proof_label = PROOF_LABEL_RE.search(text)
    first_env = re.search(r"\\begin\{", text)
    if proof_label and first_env and proof_label.start() > first_env.start():
        findings.append(
            finding(
                "proof_label_after_environment",
                "Proof label must appear outside and before all environments.",
                path,
                volume_root,
                _line_at(text, proof_label.start()),
            )
        )
    if proof_label and proof_for and proof_label.start() > proof_for.start():
        findings.append(
            finding(
                "proof_label_after_proof_for",
                "Proof label must appear before \\LRAProofFor{...}.",
                path,
                volume_root,
                _line_at(text, proof_label.start()),
            )
        )

    _check_restatement(volume_root, path, text, proof_for, findings)
    _check_proof_bodies(volume_root, path, text, findings)
    _check_forbidden_structure(volume_root, path, text, findings)
    _check_proof_layers(volume_root, path, text, findings)
    _check_todo_placement(volume_root, path, text, findings)
    _check_return_navigation(volume_root, path, text, proof_for, findings)
    _check_dependencies(volume_root, path, text, findings)
    _check_clearpage(volume_root, path, text, findings)


def _check_restatement(volume_root: Path, path: Path, text: str, proof_for, findings: list[Finding]) -> None:
    restatements = list(RESTATEMENT_RE.finditer(text))
    if len(restatements) != 1:
        findings.append(
            finding(
                "invalid_restatement_count",
                "Proof file must contain exactly one starred theorem-like restatement.",
                path,
                volume_root,
            )
        )
    for match in restatements:
        if LABEL_RE.search(match.group("body")):
            findings.append(
                finding(
                    "label_inside_restatement",
                    "Starred theorem-like restatement must not contain labels.",
                    path,
                    volume_root,
                    _line_at(text, match.start()),
                )
            )
    if proof_for and restatements:
        proof_for_label = proof_for.group("label")
        expected_env = RESTATEMENT_ENV_BY_PREFIX.get(proof_for_label.split(":", 1)[0])
        if expected_env and restatements[0].group("env").lower() != expected_env:
            findings.append(
                finding(
                    "restatement_type_mismatch",
                    f"Proof restatement must use {expected_env} for {proof_for_label}.",
                    path,
                    volume_root,
                    _line_at(text, restatements[0].start()),
                )
            )


def _check_proof_bodies(volume_root: Path, path: Path, text: str, findings: list[Finding]) -> None:
    bodies = list(PROOF_BODY_RE.finditer(text))
    governed_titles = {
        "professional standard proof": 0,
        "detailed learning proof": 0,
        "detailed instructional proof": 0,
    }
    for match in bodies:
        body = match.group("body")
        title = (match.group("title") or "").strip().lower()
        if title in governed_titles:
            governed_titles[title] += 1
            if not PROOF_BODY_START_RE.search(body):
                layer_name = (
                    "professional" if title == "professional standard proof" else "detailed"
                )
                findings.append(
                    finding(
                        f"missing_{layer_name}_proof_body_start",
                        f"{match.group('title')} must begin with \\LRAProofBodyStart.",
                        path,
                        volume_root,
                        _line_at(text, match.start()),
                    )
                )
        if LABEL_RE.search(body):
            findings.append(
                finding(
                    "label_inside_proof_environment",
                    "Proof environments must not contain labels.",
                    path,
                    volume_root,
                    _line_at(text, match.start()),
                )
            )
        if title in {"detailed learning proof", "detailed instructional proof"}:
            if FORBIDDEN_STEP_MACRO_RE.search(body):
                findings.append(
                    finding(
                        "proof_step_macro",
                        "Detailed proof must use inline \\textbf{Step N.} headings, not step or flash macros.",
                        path,
                        volume_root,
                        _line_at(text, match.start()),
                    )
                )
            if REMARK_ENV_RE.search(body):
                findings.append(
                    finding(
                        "remark_organizer_inside_detailed_proof",
                        "Detailed proof must not use remark environments to organize steps.",
                        path,
                        volume_root,
                        _line_at(text, match.start()),
                    )
                )

    professional_count = governed_titles["professional standard proof"]
    detailed_count = (
        governed_titles["detailed learning proof"]
        + governed_titles["detailed instructional proof"]
    )
    if professional_count > 1:
        findings.append(
            finding(
                "multiple_professional_proofs",
                "Proof file must contain exactly one Professional Standard Proof layer.",
                path,
                volume_root,
            )
        )
    if detailed_count > 1:
        findings.append(
            finding(
                "multiple_detailed_proofs",
                "Proof file must contain exactly one Detailed Learning Proof layer.",
                path,
                volume_root,
            )
        )


def _check_forbidden_structure(
    volume_root: Path,
    path: Path,
    text: str,
    findings: list[Finding],
) -> None:
    for match in FORBIDDEN_PROOF_ORGANIZER_RE.finditer(text):
        findings.append(
            finding(
                "forbidden_proof_organizer",
                f"Proof files must not contain {match.group('env')} environments.",
                path,
                volume_root,
                _line_at(text, match.start()),
            )
        )


def _check_proof_layers(volume_root: Path, path: Path, text: str, findings: list[Finding]) -> None:
    professional = PROFESSIONAL_RE.search(text)
    detailed = DETAILED_RE.search(text)
    if professional and detailed and professional.start() > detailed.start():
        findings.append(
            finding(
                "proof_layer_order",
                "Professional proof layer must precede detailed instructional proof layer.",
                path,
                volume_root,
                _line_at(text, detailed.start()),
            )
        )


def _check_todo_placement(volume_root: Path, path: Path, text: str, findings: list[Finding]) -> None:
    allowed_spans = [(match.start(), match.end()) for match in PROOF_BODY_RE.finditer(text)]
    allowed_spans.extend((match.start(), match.end()) for match in PROOF_STRUCTURE_RE.finditer(text))
    allowed_spans.extend((match.start(), match.end()) for match in DEPENDENCIES_RE.finditer(text))
    for match in TODO_RE.finditer(text):
        if any(start <= match.start() <= end for start, end in allowed_spans):
            continue
        findings.append(
            finding(
                "todo_outside_stub_layers",
                "Proof stubs may use TODO only in proof bodies, proof-structure, or dependencies.",
                path,
                volume_root,
                _line_at(text, match.start()),
                "warning",
            )
        )


def _check_return_navigation(volume_root: Path, path: Path, text: str, proof_for, findings: list[Finding]) -> None:
    if not proof_for:
        return
    return_blocks = list(RETURN_RE.finditer(text))
    if not return_blocks:
        findings.append(
            finding(
                "missing_return_navigation",
                "Proof file must contain exactly one Return remark linking to the associated source label.",
                path,
                volume_root,
                _line_at(text, proof_for.start()),
            )
        )
        return
    if len(return_blocks) > 1:
        findings.append(
            finding(
                "multiple_return_navigation",
                "Proof file must contain exactly one Return remark.",
                path,
                volume_root,
                _line_at(text, return_blocks[1].start()),
            )
        )
    return_block = return_blocks[0].group("body")
    expected = proof_for.group("label")
    if expected not in [match.group("label") for match in HYPERREF_RE.finditer(return_block)]:
        findings.append(
            finding(
                "return_navigation_mismatch",
                "Return navigation must hyperref to the associated source label.",
                path,
                volume_root,
                _line_at(text, return_blocks[0].start()),
            )
        )


def _check_dependencies(volume_root: Path, path: Path, text: str, findings: list[Finding]) -> None:
    for match in DEPENDENCIES_RE.finditer(text):
        body = match.group("body")
        if r"\NoLocalDependencies" in body:
            continue
        refs = [ref.group("label") for ref in HYPERREF_RE.finditer(body)]
        if not refs and "TODO" not in body:
            findings.append(
                finding(
                    "proof_dependencies_without_hyperref",
                    "Proof dependencies must contain hyperref links or \\NoLocalDependencies.",
                    path,
                    volume_root,
                    _line_at(text, match.start()),
                )
            )
        for target in refs:
            if ":" not in target or target.split(":", 1)[0] not in FORMAL_PREFIXES:
                findings.append(
                    finding(
                        "invalid_proof_dependency_target",
                        f"Proof dependency targets non-statement label {target}.",
                        path,
                        volume_root,
                        _line_at(text, match.start()),
                    )
                )


def _check_clearpage(volume_root: Path, path: Path, text: str, findings: list[Finding]) -> None:
    clearpage_pos = text.rfind(r"\clearpage")
    if clearpage_pos < 0:
        return
    trailer = "\n".join(
        line.strip()
        for line in text[clearpage_pos + len(r"\clearpage"):].splitlines()
        if line.strip() and not line.strip().startswith("%")
    )
    if trailer:
        findings.append(
            finding(
                "content_after_clearpage",
                "Proof file must not contain source content after terminal \\clearpage.",
                path,
                volume_root,
                _line_at(text, clearpage_pos),
            )
        )


def _line_at(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1
