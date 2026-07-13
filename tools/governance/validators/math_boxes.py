from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from core.finding import Finding, finding
from core.tex import read_text
from core.file_inventory import validator_files


ENV_PREFIX = {
    "definition": "definitionbox",
    "axiom": "axiombox",
    "theorem": "theorembox",
    "lemma": "lemmabox",
    "proposition": "propositionbox",
    "corollary": "corollarybox",
}
FORMAL_RE = re.compile(
    r"\\begin\{(?P<env>definition|axiom|theorem|lemma|proposition|corollary)\}"
    r"(?:\[[^\]]*\])?",
    re.IGNORECASE,
)
ANY_BOX_RE = re.compile(r"\\begin\{(?:definition|definitional|axiom|theorem|lemma|proposition|corollary)box\}")
TCOLORBOX_RE = re.compile(r"\\begin\{tcolorbox\}(?P<body>[\s\S]*?)\\end\{tcolorbox\}", re.IGNORECASE)
NONFORMAL_BOXED_RE = re.compile(r"\\begin\{(?:remark\*?|example\*?|proof)\}", re.IGNORECASE)
FORMAL_LABEL_RE = re.compile(r"\\label\{(?:def|ax|thm|lem|prop|cor):[^{}]+\}")
FORMAL_BOX_RE = re.compile(
    r"\\begin\{(?P<env>definitionbox|definitionalbox|axiombox|theorembox|lemmabox|propositionbox|corollarybox)\}"
    r"(?:\{[^{}]*\})?"
    r"(?P<body>[\s\S]*?)"
    r"\\end\{(?P=env)\}",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class FormalBlock:
    env: str
    line: int
    prelines: list[str]


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    for tex in validator_files(volume_root, files):
        _validate_file(volume_root, tex, findings)
    return findings


def _validate_file(volume_root: Path, path: Path, findings: list[Finding]) -> None:
    text = read_text(path)
    _check_boxed_nonformal_content(volume_root, path, text, findings)
    _check_bare_formal_boxes(volume_root, path, text, findings)
    _check_labels_on_decorative_boxes(volume_root, path, text, findings)
    _check_multi_label_decorative_boxes(volume_root, path, text, findings)
    for block in _formal_blocks(text):
        kind = _classify_wrapper(block)
        expected = ENV_PREFIX[block.env]
        if kind == "semantic":
            continue
        if kind == "raw":
            findings.append(
                finding(
                    "raw_tcolorbox_wrapper",
                    f"{block.env} is wrapped in a hand-rolled tcolorbox; use \\begin{{{expected}}}{{...}}.",
                    path,
                    volume_root,
                    block.line,
                )
            )
        elif kind == "wrong_box":
            findings.append(
                finding(
                    "wrong_box_macro",
                    f"{block.env} is boxed with a non-matching box macro; expected {expected}.",
                    path,
                    volume_root,
                    block.line,
                )
            )
        # Unboxed formal environments are allowed. Boxes are reserved for
        # load-bearing statements; this validator only checks box correctness
        # when a box is actually present.


def _check_boxed_nonformal_content(volume_root: Path, path: Path, text: str, findings: list[Finding]) -> None:
    for match in TCOLORBOX_RE.finditer(text):
        if NONFORMAL_BOXED_RE.search(match.group("body")):
            findings.append(
                finding(
                    "boxed_nonformal_content",
                    "Remarks, examples, and proofs must not be boxed in tcolorbox.",
                    path,
                    volume_root,
                    text.count("\n", 0, match.start()) + 1,
                )
            )


def _check_bare_formal_boxes(volume_root: Path, path: Path, text: str, findings: list[Finding]) -> None:
    for match in FORMAL_BOX_RE.finditer(text):
        body = match.group("body")
        if FORMAL_RE.search(body):
            continue
        findings.append(
            finding(
                "bare_formal_box_content",
                f"{match.group('env')} contains content without an inner formal environment; wrap the statement in the matching definition/theorem/lemma/proposition/corollary/axiom environment.",
                path,
                volume_root,
                text.count("\n", 0, match.start()) + 1,
            )
        )


def _check_multi_label_decorative_boxes(volume_root: Path, path: Path, text: str, findings: list[Finding]) -> None:
    for match in FORMAL_BOX_RE.finditer(text):
        body = match.group("body")
        if FORMAL_RE.search(body):
            continue
        labels = FORMAL_LABEL_RE.findall(body)
        if len(labels) <= 1:
            continue
        findings.append(
            finding(
                "multiple_formal_labels_in_box",
                "Decorative formal box contains multiple formal labels but no inner formal environment; split it into one formal artifact per label.",
                path,
                volume_root,
                text.count("\n", 0, match.start()) + 1,
                "warning",
            )
        )


def _check_labels_on_decorative_boxes(volume_root: Path, path: Path, text: str, findings: list[Finding]) -> None:
    for match in FORMAL_BOX_RE.finditer(text):
        body = match.group("body")
        formal = FORMAL_RE.search(body)
        label = FORMAL_LABEL_RE.search(body)
        if not label:
            continue
        if formal and formal.start() < label.start():
            continue
        findings.append(
            finding(
                "formal_label_on_box",
                "Formal labels must be placed inside the theorem/definition/lemma/proposition/corollary environment, not directly on the decorative box.",
                path,
                volume_root,
                text.count("\n", 0, match.start("body") + label.start()) + 1,
            )
        )


def _formal_blocks(text: str):
    for begin in FORMAL_RE.finditer(text):
        env = begin.group("env").lower()
        line = text.count("\n", 0, begin.start()) + 1
        prelines = text[:begin.start()].splitlines()[-10:]
        yield FormalBlock(env=env, line=line, prelines=prelines)


def _classify_wrapper(block: FormalBlock) -> str:
    expected = ENV_PREFIX[block.env]
    for line in reversed(block.prelines):
        stripped = line.strip()
        if not stripped:
            continue
        if re.search(r"\\begin\{" + re.escape(expected) + r"\}", line):
            return "semantic"
        if block.env == "definition" and re.search(r"\\begin\{definitionalbox\}", line):
            return "semantic"
        if re.search(r"\\begin\{tcolorbox\}", line):
            return "raw"
        if ANY_BOX_RE.search(line):
            return "wrong_box"
        if re.search(r"\\(?:begin|end)\{", line):
            return "none"
    return "none"
