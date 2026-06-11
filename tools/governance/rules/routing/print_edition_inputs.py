"""Print-edition routing checks.

Proof vaults, exercise vaults, and capstones must be routed through semantic
input macros so shelf/print builds can omit them without editing source files.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass
class Finding:
    code: str
    message: str
    severity: str = "error"
    line: int = 0


RAW_INPUT_RE = re.compile(r"\\(?:input|include)\{([^}]+)\}")
PRINT_AWARE_INPUT_RE = re.compile(r"\\(?:LRAProofsInput|LRAExercisesInput|LRACapstoneInput)\{([^}]+)\}")


def _line(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def _target_kind(target: str) -> str | None:
    normalized = target.replace("\\", "/").removesuffix(".tex")
    if "/proofs/exercises/capstone-" in normalized:
        return "capstone"
    if normalized.endswith("/proofs/exercises/index") or "/proofs/exercises/" in normalized:
        return "exercises"
    if normalized.endswith("/proofs/index") or "/proofs/" in normalized:
        return "proofs"
    return None


def check(text: str, info, ctx) -> Iterable[Finding]:
    for match in RAW_INPUT_RE.finditer(text):
        target = match.group(1)
        kind = _target_kind(target)
        if not kind:
            continue
        macro = {
            "proofs": r"\LRAProofsInput",
            "exercises": r"\LRAExercisesInput",
            "capstone": r"\LRACapstoneInput",
        }[kind]
        yield Finding(
            "print_edition_raw_input",
            f"Route {target} through {macro}{{...}} so print edition can omit {kind}.",
            "error",
            _line(text, match.start()),
        )

    for match in PRINT_AWARE_INPUT_RE.finditer(text):
        target = match.group(1)
        kind = _target_kind(target)
        if not kind:
            yield Finding(
                "print_edition_macro_non_vault_target",
                f"Print-edition input macro wraps non-vault target {target}; use \\input{{...}} for ordinary content.",
                "error",
                _line(text, match.start()),
            )
