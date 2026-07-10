from __future__ import annotations

import re
from collections.abc import Iterable

from core.finding import Finding


def _dependency_remark_body(decoration: str) -> str:
    match = re.search(
        r"\\begin\{remark\*?\}\[Dependencies\](?P<body>.*?)\\end\{remark\*?\}",
        decoration,
        re.DOTALL | re.IGNORECASE,
    )
    return match.group("body") if match else ""


def check(block, ctx) -> Iterable[Finding]:
    decoration = block.decoration
    has_dependencies = (
        "\\begin{dependencies}" in decoration
        or bool(_dependency_remark_body(decoration))
        or "\\NoLocalDependencies" in decoration
        or "\\DefinitionalRoot" in decoration
    )
    if not has_dependencies:
        yield Finding(
            "missing_dependencies",
            "Dependencies are missing (use \\begin{dependencies}, \\NoLocalDependencies, or \\DefinitionalRoot).",
            "error",
            block.line_start,
        )
