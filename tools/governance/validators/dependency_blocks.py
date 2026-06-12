from __future__ import annotations

import re
from pathlib import Path

from core.finding import Finding, finding
from core.tex import read_text, strip_latex_comments
from core.volume import iter_tex


FORMAL_ENVS = {"definition", "axiom", "theorem", "lemma", "proposition", "corollary"}
FORMAL_PREFIXES = {"def", "ax", "thm", "lem", "prop", "cor"}
BEGIN_FORMAL_RE = re.compile(
    r"\\begin\{(?P<env>definition|axiom|theorem|lemma|proposition|corollary)\}"
    r"(?:\[[^\]]*\])?",
    re.IGNORECASE,
)
SECTION_RE = re.compile(r"\\(?:chapter|section|subsection|subsubsection)\*?\{")
DEPENDENCIES_ENV_RE = re.compile(r"\\begin\{dependencies\}(?P<body>[\s\S]*?)\\end\{dependencies\}", re.IGNORECASE)
DEPENDENCIES_REMARK_RE = re.compile(r"\\begin\{remark\*\}\[Dependencies\](?P<body>[\s\S]*?)\\end\{remark\*\}", re.IGNORECASE)
NO_LOCAL_RE = re.compile(r"\\NoLocalDependencies\b")
HYPERREF_RE = re.compile(r"\\hyperref\[(?P<label>[^\]]+)\]")
LABEL_RE = re.compile(r"\\label\{(?P<label>[a-z]+:[^{}]+)\}")


def validate(volume_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for tex in iter_tex(volume_root):
        _validate_file(volume_root, tex, findings)
    return findings


def _validate_file(volume_root: Path, path: Path, findings: list[Finding]) -> None:
    text = strip_latex_comments(read_text(path))
    blocks = list(_formal_blocks(text))
    for begin, end_pos in blocks:
        block_text = text[begin.start():end_pos]
        labels = [label for label in LABEL_RE.findall(block_text) if label.split(":", 1)[0] in FORMAL_PREFIXES]
        label = labels[0] if labels else "(unlabeled formal block)"
        window_start = end_pos
        window_end = _next_boundary(text, window_start)
        window = text[window_start:window_end]
        declarations = _dependency_declarations(window)
        line = text.count("\n", 0, begin.start()) + 1
        if not declarations:
            findings.append(
                finding(
                    "missing_dependencies",
                    f"{label} lacks a dependencies declaration.",
                    path,
                    volume_root,
                    line,
                    "warning",
                )
            )
            continue
        if len(declarations) > 1:
            findings.append(
                finding(
                    "multiple_dependency_declarations",
                    f"{label} has multiple dependency declarations.",
                    path,
                    volume_root,
                    text.count("\n", 0, window_start + declarations[-1][2]) + 1,
                    "warning",
                )
            )
        kind, body, offset = declarations[-1]
        dep_line = text.count("\n", 0, window_start + offset) + 1
        if kind == "dependencies_remark":
            findings.append(
                finding(
                    "legacy_dependency_remark",
                    f"{label} uses remark*[Dependencies] instead of the dependencies environment.",
                    path,
                    volume_root,
                    dep_line,
                    "warning",
                )
            )
        if kind == "no_local":
            continue
        refs = list(HYPERREF_RE.finditer(body))
        if not refs and "TODO" not in body:
            findings.append(
                finding(
                    "dependencies_without_hyperref",
                    f"{label} dependency block has no hyperref targets.",
                    path,
                    volume_root,
                    dep_line,
                )
            )
        for ref in refs:
            target = ref.group("label").strip()
            if target.startswith("prf:"):
                findings.append(
                    finding(
                        "dependency_targets_proof",
                        f"{label} targets proof label {target}.",
                        path,
                        volume_root,
                        dep_line,
                    )
                )
            elif ":" not in target or target.split(":", 1)[0] not in FORMAL_PREFIXES:
                findings.append(
                    finding(
                        "invalid_dependency_target_prefix",
                        f"{label} targets non-formal label {target}.",
                        path,
                        volume_root,
                        dep_line,
                    )
                )


def _formal_blocks(text: str):
    for begin in BEGIN_FORMAL_RE.finditer(text):
        env = begin.group("env")
        end = re.search(rf"\\end\{{{re.escape(env)}\}}", text[begin.end():], re.IGNORECASE)
        if end:
            yield begin, begin.end() + end.end()


def _next_boundary(text: str, start: int) -> int:
    formal = BEGIN_FORMAL_RE.search(text, start)
    section = SECTION_RE.search(text, start)
    candidates = [match.start() for match in (formal, section) if match]
    return min(candidates) if candidates else len(text)


def _dependency_declarations(window: str) -> list[tuple[str, str, int]]:
    declarations: list[tuple[str, str, int]] = []
    for match in DEPENDENCIES_ENV_RE.finditer(window):
        declarations.append(("dependencies_env", match.group("body"), match.start()))
    for match in DEPENDENCIES_REMARK_RE.finditer(window):
        declarations.append(("dependencies_remark", match.group("body"), match.start()))
    for match in NO_LOCAL_RE.finditer(window):
        declarations.append(("no_local", "", match.start()))
    return sorted(declarations, key=lambda item: item[2])
