from __future__ import annotations

import re
from pathlib import Path

from core.finding import Finding, finding
from core.tex import read_text, strip_latex_comments
from core.file_inventory import files_to_validate


PROOF_FOR_RE = re.compile(r"\\LRAProofFor\{(?P<label>(?:thm|lem|prop|cor):[a-z0-9-]+)\}")
PROOF_LABEL_RE = re.compile(r"\\label\{prf:[a-z0-9-]+\}")
LABEL_RE = re.compile(r"\\label\{[^{}]+\}")
HYPERREF_RE = re.compile(r"\\hyperref\[(?P<label>[^\]]+)\]")
RESTATEMENT_RE = re.compile(
    r"\\begin\{(?P<env>theorem|lemma|proposition|corollary)\*\}(?P<body>[\s\S]*?)\\end\{(?P=env)\*\}",
    re.IGNORECASE,
)
PROOF_BODY_RE = re.compile(r"\\begin\{proof\}(?:\[[^\]]*\])?(?P<body>[\s\S]*?)\\end\{proof\}", re.IGNORECASE)
DEPENDENCIES_RE = re.compile(r"\\begin\{dependencies\}(?P<body>[\s\S]*?)\\end\{dependencies\}", re.IGNORECASE)
PROOF_STRUCTURE_RE = re.compile(r"\\begin\{remark\*\}\[Proof structure\][\s\S]*?\\end\{remark\*\}", re.IGNORECASE)
PROFESSIONAL_RE = re.compile(r"Professional Standard Proof", re.IGNORECASE)
DETAILED_RE = re.compile(r"Detailed (?:Learning|Instructional) Proof", re.IGNORECASE)
TODO_RE = re.compile(r"\bTODO\b", re.IGNORECASE)
FORMAL_PREFIXES = {"def", "ax", "thm", "lem", "prop", "cor"}
RESTATEMENT_ENV_BY_PREFIX = {
    "thm": "theorem",
    "lem": "lemma",
    "prop": "proposition",
    "cor": "corollary",
}


def validate(volume_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for tex in files_to_validate([volume_root]):
        rel = tex.resolve().relative_to(volume_root.resolve()).as_posix()
        if "/proofs/" not in f"/{rel}" or "/proofs/exercises/" in f"/{rel}" or tex.name == "index.tex":
            continue
        _validate_file(volume_root, tex, findings)
    return findings


def _validate_file(volume_root: Path, path: Path, findings: list[Finding]) -> None:
    text = strip_latex_comments(read_text(path))
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
    for match in PROOF_BODY_RE.finditer(text):
        if LABEL_RE.search(match.group("body")):
            findings.append(
                finding(
                    "label_inside_proof_environment",
                    "Proof environments must not contain labels.",
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
            )
        )


def _check_return_navigation(volume_root: Path, path: Path, text: str, proof_for, findings: list[Finding]) -> None:
    if not proof_for:
        return
    return_start = text.find(r"\begin{remark*}[Return]")
    if return_start < 0:
        return
    return_end = text.find(r"\end{remark*}", return_start)
    return_block = text[return_start:return_end] if return_end >= 0 else text[return_start:]
    expected = proof_for.group("label")
    if expected not in [match.group("label") for match in HYPERREF_RE.finditer(return_block)]:
        findings.append(
            finding(
                "return_navigation_mismatch",
                "Return navigation must hyperref to the associated source label.",
                path,
                volume_root,
                _line_at(text, return_start),
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
