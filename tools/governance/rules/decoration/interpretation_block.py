from __future__ import annotations

from collections.abc import Iterable

from core.finding import Finding


def check(block, ctx) -> Iterable[Finding]:
    if "interpretation" not in block.decoration.lower():
        yield Finding(
            "missing_interpretation",
            "Interpretation remark is missing.",
            "error",
            block.line_start,
        )
