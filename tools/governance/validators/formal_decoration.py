from __future__ import annotations

import re
from pathlib import Path

from core.finding import Finding, finding
from core.tex import read_text, strip_latex_comments
from core.file_inventory import validator_files


FORMAL_RE = re.compile(
    r"\\begin\{(?P<env>definition|axiom|theorem|lemma|proposition|corollary)\}"
    r"(?:\[[^\]]*\])?",
    re.IGNORECASE,
)
SECTION_RE = re.compile(r"\\(?:chapter|section|subsection|subsubsection)\*?\{")
LABEL_RE = re.compile(r"\\label\{([^}]+)\}")
DECORATION_BLOCK_RE = re.compile(
    r"\\begin\{(?P<env>remark\*|example\*|dependencies)\}(?:\[(?P<title>[^\]]+)\])?",
    re.IGNORECASE,
)
EXPOSITORY_BLOCK_RE = re.compile(
    r"\\begin\{remark\*\}\[(Examples|Non-Examples|Exposition)\]([\s\S]*?)\\end\{remark\*\}",
    re.IGNORECASE,
)
FORMAL_INNER_RE = re.compile(r"\\begin\{(?:definition|axiom|theorem|lemma|proposition|corollary)\}", re.IGNORECASE)
CITATION_RE = re.compile(r"\\cite[t|p]?\{")

DECORATION_ORDER = {
    "proof_link": 10,
    "standard quantified statement": 20,
    "definition predicate reading": 30,
    "predicate reading": 30,
    "negated quantified statement": 40,
    "negation predicate reading": 50,
    "failure modes": 60,
    "failure mode decomposition": 70,
    "contrapositive quantified statement": 80,
    "contrapositive predicate reading": 90,
    "interpretation": 100,
    "notation": 102,
    "historical note": 105,
    "comparison with feferman": 105,
    "exposition": 110,
    "examples": 120,
    "non-examples": 130,
    "dependencies": 140,
}
DEPENDENT_DECORATION_PARENTS = {
    "negation predicate reading": "negated quantified statement",
    "failure mode decomposition": "failure modes",
    "contrapositive predicate reading": "contrapositive quantified statement",
}
FORBIDDEN_DECORATION_BY_ENV = {
    "definition": {"contrapositive quantified statement", "contrapositive predicate reading"},
    "axiom": {"contrapositive quantified statement", "contrapositive predicate reading", "examples", "non-examples"},
    "theorem": {"examples", "non-examples"},
    "lemma": {"examples", "non-examples"},
    "proposition": {"examples", "non-examples"},
    "corollary": {"examples", "non-examples"},
}


def validate(volume_root: Path, files=None) -> list[Finding]:
    findings: list[Finding] = []
    for tex in validator_files(volume_root, files):
        rel = tex.resolve().relative_to(volume_root.resolve()).as_posix()
        if "/notes/" not in f"/{rel}":
            continue
        _validate_file(volume_root, tex, findings)
    return findings


def _validate_file(volume_root: Path, path: Path, findings: list[Finding]) -> None:
    text = strip_latex_comments(read_text(path))
    for begin, end_pos in _formal_blocks(text):
        block_text = text[begin.start():end_pos]
        labels = LABEL_RE.findall(block_text)
        if not labels:
            continue
        label = labels[0]
        env = begin.group("env").lower()
        line = text.count("\n", 0, begin.start()) + 1
        decoration = text[end_pos:_next_boundary(text, end_pos)]
        _check_source_citations(volume_root, path, decoration, label, line, findings)
        _check_expository_formal_claims(volume_root, path, decoration, label, line, findings)
        _check_decoration_blocks(volume_root, path, decoration, label, env, line, findings)


def _check_source_citations(
    volume_root: Path,
    path: Path,
    decoration: str,
    label: str,
    line: int,
    findings: list[Finding],
) -> None:
    if re.search(r"\\begin\{remark\*\}\[(Historical note|Comparison with Feferman)\]", decoration) and not CITATION_RE.search(decoration):
        findings.append(
            finding(
                "source_crosswalk_without_citation",
                f"{label} has a source/provenance block without a citation.",
                path,
                volume_root,
                line,
            )
        )


def _check_expository_formal_claims(
    volume_root: Path,
    path: Path,
    decoration: str,
    label: str,
    line: int,
    findings: list[Finding],
) -> None:
    for match in EXPOSITORY_BLOCK_RE.finditer(decoration):
        body = match.group(2)
        if LABEL_RE.search(body) or FORMAL_INNER_RE.search(body):
            findings.append(
                finding(
                    "formal_claim_inside_expository_block",
                    f"{match.group(1)} block for {label} must not introduce labels or formal theorem-like environments.",
                    path,
                    volume_root,
                    line + _line_at(decoration, match.start()) - 1,
                )
            )


def _check_decoration_blocks(
    volume_root: Path,
    path: Path,
    decoration: str,
    label: str,
    env: str,
    line: int,
    findings: list[Finding],
) -> None:
    seen: list[tuple[str, int, int]] = []
    for match in DECORATION_BLOCK_RE.finditer(decoration):
        key = _decoration_key(match)
        block_line = line + _line_at(decoration, match.start()) - 1
        if key not in DECORATION_ORDER:
            findings.append(
                finding(
                    "unknown_decoration_block",
                    f"{label} has nonstandard decoration block '{key}'.",
                    path,
                    volume_root,
                    block_line,
                    "warning",
                )
            )
            continue
        if key in FORBIDDEN_DECORATION_BY_ENV.get(env, set()):
            findings.append(
                finding(
                    "forbidden_decoration_block",
                    f"{env} must not use decoration block '{key}' by artifact-matrix rules.",
                    path,
                    volume_root,
                    block_line,
                )
            )
        seen.append((key, DECORATION_ORDER[key], match.start()))

    seen_keys = {key for key, _rank, _pos in seen}
    for child, parent in DEPENDENT_DECORATION_PARENTS.items():
        if child in seen_keys and parent not in seen_keys:
            findings.append(
                finding(
                    "missing_dependent_parent_block",
                    f"{child} requires parent block {parent} for {label}.",
                    path,
                    volume_root,
                    line,
                )
            )
    for (left_key, left_rank, _left_pos), (right_key, right_rank, right_pos) in zip(seen, seen[1:]):
        if right_rank < left_rank:
            findings.append(
                finding(
                    "decoration_order",
                    f"{right_key} appears before {left_key} for {label}; use the canonical decoration order.",
                    path,
                    volume_root,
                    line + _line_at(decoration, right_pos) - 1,
                )
            )


def _formal_blocks(text: str):
    for begin in FORMAL_RE.finditer(text):
        env = begin.group("env")
        end = re.search(rf"\\end\{{{re.escape(env)}\}}", text[begin.end():], re.IGNORECASE)
        if end:
            yield begin, begin.end() + end.end()


def _next_boundary(text: str, start: int) -> int:
    formal = FORMAL_RE.search(text, start)
    section = SECTION_RE.search(text, start)
    candidates = [match.start() for match in (formal, section) if match]
    return min(candidates) if candidates else len(text)


def _decoration_key(match) -> str:
    env = match.group("env").lower()
    if env == "dependencies":
        return "dependencies"
    return re.sub(r"\s+", " ", (match.group("title") or "").strip().lower())


def _line_at(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1
