from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TypeVar

from .finding import Finding

T = TypeVar("T")

Rule = Callable[..., Iterable[Finding] | None]


def run_checks(checks: Iterable[Rule], *args) -> list[Finding]:
    findings: list[Finding] = []
    for check in checks:
        result = check(*args)
        if result:
            findings.extend(result)
    return findings
