from __future__ import annotations

import re
from collections.abc import Iterable

from core.finding import Finding

AUDITED_ENVS = {
    "definition": "def",
    "axiom": "ax",
    "theorem": "thm",
    "lemma": "lem",
    "proposition": "prop",
    "corollary": "cor",
}
LABEL_RE = re.compile(r"\\label\{([^}]+)\}")


def check_missing_label(block, ctx) -> Iterable[Finding]:
    labels = LABEL_RE.findall(block.text)
    if not labels:
        yield Finding("missing_label", "The block has no visible label.", "error", block.line_start)


def check_label_prefix(block, ctx) -> Iterable[Finding]:
    labels = LABEL_RE.findall(block.text)
    if not labels:
        return
    prefix = labels[0].split(":", 1)[0] if ":" in labels[0] else ""
    expected = AUDITED_ENVS[block.environment]
    if prefix != expected:
        yield Finding(
            "wrong_label_prefix",
            f"Expected label prefix '{expected}:' but found '{prefix}:'.",
            "error",
            block.line_start,
        )
