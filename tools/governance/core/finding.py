from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    severity: str = "warning"
    line: int = 0
