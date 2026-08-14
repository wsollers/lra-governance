from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence


CALL_RE = re.compile(
    r"\\(?P<command>operatorname|mathsf)\{(?P<name>[^}]+)\}\s*(?P<tail>[\s\S]*?)",
    re.MULTILINE,
)
NUMBER_SYSTEM_RE = re.compile(
    r"\\mathbb(?:\{[A-Za-z]+\}|[A-Za-z])(?:_\{[^{}]+\}|_[A-Za-z0-9]+)?\Z"
)
STRUCTURE_RE = re.compile(r"\\mathsf\{[^{}]+\}(?:\([^)]*\))?\Z")
SCALAR_LITERAL_RE = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)\Z")

ARGUMENT_TYPES = frozenset(
    {
        "ambient",
        "formula",
        "function",
        "object",
        "operator",
        "relation",
        "scalar",
        "set",
        "structure",
    }
)


@dataclass(frozen=True)
class RegistryCall:
    name: str
    command: str
    arguments: tuple[str, ...]
    start: int

    @property
    def arity(self) -> int:
        return len(self.arguments)


@dataclass(frozen=True)
class RegistryCallIssue:
    code: str
    message: str


def iter_registry_calls(text: str) -> list[RegistryCall]:
    calls: list[RegistryCall] = []
    for match in CALL_RE.finditer(text):
        paren = _first_nonspace(text, match.start("tail"))
        if paren is None or text[paren] != "(":
            continue
        close = _matching_paren(text, paren)
        if close is None:
            continue
        calls.append(
            RegistryCall(
                name=match.group("name").strip(),
                command=match.group("command"),
                arguments=tuple(split_arguments(text[paren + 1 : close])),
                start=match.start(),
            )
        )
    return calls


def validate_registry_call(
    call: RegistryCall,
    entry: Mapping[str, Any],
    *,
    allowed_arities: Sequence[int] | None = None,
) -> list[RegistryCallIssue]:
    arguments = entry.get("arguments")
    if not isinstance(arguments, list):
        return []

    allowed = frozenset(allowed_arities or (len(arguments),))
    if call.arity not in allowed:
        expected = " or ".join(str(value) for value in sorted(allowed))
        return [
            RegistryCallIssue(
                "registry_call_arity",
                f"{call.name} has {call.arity} argument(s); canonical signature expects {expected}",
            )
        ]

    issues: list[RegistryCallIssue] = []
    for index, (value, specification) in enumerate(zip(call.arguments, arguments), start=1):
        if not isinstance(specification, Mapping):
            continue
        expected_type = str(specification.get("type") or "")
        if not expected_type:
            continue
        actual_type = infer_literal_type(value)
        if actual_type is None or _types_compatible(expected_type, actual_type):
            continue
        argument_name = str(specification.get("name") or index)
        issues.append(
            RegistryCallIssue(
                "registry_call_argument_type",
                (
                    f"{call.name} argument {index} ({argument_name}) expects {expected_type}, "
                    f"but {value!r} is an explicit {actual_type} expression"
                ),
            )
        )
    return issues


def infer_literal_type(value: str) -> str | None:
    normalized = re.sub(r"\s+", "", value).rstrip(".")
    if not normalized:
        return None
    if NUMBER_SYSTEM_RE.fullmatch(normalized):
        return "ambient"
    if STRUCTURE_RE.fullmatch(normalized):
        return "structure"
    if SCALAR_LITERAL_RE.fullmatch(normalized):
        return "scalar"
    if r"\mapsto" in normalized:
        return "function"
    return None


def split_arguments(value: str) -> list[str]:
    if not value.strip():
        return []
    parts: list[str] = []
    start = 0
    depth = 0
    brace_depth = 0
    bracket_depth = 0
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "{":
            brace_depth += 1
            continue
        if char == "}" and brace_depth:
            brace_depth -= 1
            continue
        if char == "[":
            bracket_depth += 1
            continue
        if char == "]" and bracket_depth:
            bracket_depth -= 1
            continue
        if brace_depth or bracket_depth:
            continue
        if char == "(":
            depth += 1
            continue
        if char == ")" and depth:
            depth -= 1
            continue
        if char == "," and depth == 0:
            parts.append(value[start:index].strip())
            start = index + 1
    parts.append(value[start:].strip())
    return parts


def _types_compatible(expected: str, actual: str) -> bool:
    if expected == actual or expected == "object":
        return True
    if expected == "set" and actual == "ambient":
        return True
    if expected == "ambient" and actual == "structure":
        return True
    return False


def _first_nonspace(text: str, start: int) -> int | None:
    for index in range(start, len(text)):
        if not text[index].isspace():
            return index
    return None


def _matching_paren(text: str, open_index: int) -> int | None:
    depth = 0
    brace_depth = 0
    bracket_depth = 0
    escaped = False
    for index in range(open_index, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "{":
            brace_depth += 1
            continue
        if char == "}" and brace_depth:
            brace_depth -= 1
            continue
        if char == "[":
            bracket_depth += 1
            continue
        if char == "]" and bracket_depth:
            bracket_depth -= 1
            continue
        if brace_depth or bracket_depth:
            continue
        if char == "(":
            depth += 1
            continue
        if char == ")":
            depth -= 1
            if depth == 0:
                return index
    return None
