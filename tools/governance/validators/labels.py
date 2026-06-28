from __future__ import annotations

import re
from pathlib import Path

from core.finding import Finding, finding
from core.file_inventory import validator_files
from core.tex import read_text
from core.volume import chapter_roots


LABEL_RE = re.compile(r"\\label\{([^}]+)\}")
FORMAL_BEGIN_RE = re.compile(
    r"\\begin\{(?P<env>definition|axiom|theorem|lemma|proposition|corollary)\}"
    r"(?:\[[^\]]*\])?",
)
ENV_PREFIX = {
    "definition": "def",
    "axiom": "ax",
    "theorem": "thm",
    "lemma": "lem",
    "proposition": "prop",
    "corollary": "cor",
}
IGNORED_LABEL_PREFIXES = {"ch", "chap", "sec", "subsec", "toc", "fig", "cap", "prf", "ex"}
BAD_LABEL_PARTS = {
    "the",
    "following",
    "this",
    "with",
    "for",
    "therefore",
    "and",
    "or",
    "let",
    "denote",
    "page",
}


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    _check_duplicate_and_slug_labels(volume_root, findings, files)
    for chapter in chapter_roots(volume_root):
        for tex in validator_files(chapter, files):
            _check_formal_block_labels(volume_root, tex, findings)
    return findings


def _check_duplicate_and_slug_labels(volume_root: Path, findings: list[Finding], files=None) -> None:
    seen: dict[str, Path] = {}
    for tex in validator_files(volume_root, files):
        text = read_text(tex)
        for match in LABEL_RE.finditer(text):
            label = match.group(1)
            line = text.count("\n", 0, match.start()) + 1
            if label in seen:
                findings.append(
                    finding(
                        "duplicate_label",
                        f"Duplicate label {label}; first seen in {seen[label].relative_to(volume_root).as_posix()}.",
                        tex,
                        volume_root,
                        line,
                        "warning",
                    )
                )
            else:
                seen[label] = tex
            if ":" not in label:
                continue
            prefix, slug = label.split(":", 1)
            if prefix in IGNORED_LABEL_PREFIXES:
                continue
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)+", slug):
                findings.append(
                    finding(
                        "weak_label_slug",
                        f"Label slug should be lowercase kebab-case with readable terms: {label}.",
                        tex,
                        volume_root,
                        line,
                        "warning",
                    )
                )
            if any(part in BAD_LABEL_PARTS for part in slug.split("-")):
                findings.append(
                    finding(
                        "ocr_like_label",
                        f"Label appears to include prose/OCR filler: {label}.",
                        tex,
                        volume_root,
                        line,
                        "warning",
                    )
                )


def _check_formal_block_labels(volume_root: Path, tex: Path, findings: list[Finding]) -> None:
    text = read_text(tex)
    for begin in FORMAL_BEGIN_RE.finditer(text):
        env = begin.group("env")
        end = re.search(rf"\\end\{{{env}\}}", text[begin.end():])
        block_end = begin.end() + end.end() if end else len(text)
        block_text = text[begin.start():block_end]
        line = text.count("\n", 0, begin.start()) + 1
        labels = LABEL_RE.findall(block_text)
        if not labels:
            findings.append(
                finding("missing_label", "The block has no visible label.", tex, volume_root, line)
            )
            continue
        prefix = labels[0].split(":", 1)[0] if ":" in labels[0] else ""
        expected = ENV_PREFIX[env]
        if prefix != expected:
            findings.append(
                finding(
                    "wrong_label_prefix",
                    f"Expected label prefix '{expected}:' but found '{prefix}:'.",
                    tex,
                    volume_root,
                    line,
                )
            )
