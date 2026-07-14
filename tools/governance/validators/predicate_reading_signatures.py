from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

from core.file_inventory import validator_files
from core.finding import Finding, finding
from core.tex import line_at, read_stripped_text


PREDICATE_READING_RE = re.compile(
    r"\\begin\{remark\*\}\[(?P<title>"
    r"Predicate reading|Negation predicate reading|Contrapositive predicate reading"
    r")\](?P<body>[\s\S]*?)\\end\{remark\*\}",
    re.IGNORECASE,
)
CALL_RE = re.compile(r"\\(?:operatorname|mathsf)\{(?P<name>[^}]+)\}\s*(?P<tail>[\s\S]*?)", re.MULTILINE)
LEGACY_AMBIENT_NAMES = {"ConvergesTo", "IsCauchy", "Sequence"}
SEQUENCE_NAME = "Sequence"


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    signatures = _canonical_signatures()
    if not signatures:
        return findings

    for tex in validator_files(volume_root, files):
        text = read_stripped_text(tex)
        for block in PREDICATE_READING_RE.finditer(text):
            _validate_predicate_reading_block(volume_root, tex, text, block, signatures, findings)
    return findings


def _validate_predicate_reading_block(
    volume_root: Path,
    path: Path,
    full_text: str,
    block: re.Match[str],
    signatures: dict[str, Signature],
    findings: list[Finding],
) -> None:
    body = block.group("body")
    block_start = block.start("body")
    for call in _iter_calls(body):
        signature = signatures.get(call.name)
        if signature is None:
            continue

        if signature.kind == "structure" and call.command != "mathsf":
            findings.append(
                finding(
                    "structure_constructor_operatorname",
                    rf"\operatorname{{{call.name}}} is registered as a structure constructor; use \mathsf{{{call.name}}} in predicate-reading setup lines.",
                    path,
                    volume_root,
                    line_at(full_text, block_start + call.start),
                    severity="review",
                )
            )

        if call.name in LEGACY_AMBIENT_NAMES and call.arg_count == 1:
            findings.append(
                finding(
                    "predicate_reading_missing_ambient",
                    rf"{call.command}{{{call.name}}} uses the legacy one-argument form; include the ambient object or structure explicitly.",
                    path,
                    volume_root,
                    line_at(full_text, block_start + call.start),
                    severity="review",
                )
            )
            continue

        allowed = _allowed_arities(signature)
        if call.arg_count not in allowed:
            expected = _format_arities(allowed)
            findings.append(
                finding(
                    "predicate_reading_signature_arity",
                    rf"{call.command}{{{call.name}}} has {call.arg_count} argument(s) in a predicate-reading block; canonical {signature.kind} signature expects {expected}.",
                    path,
                    volume_root,
                    line_at(full_text, block_start + call.start),
                    severity="review",
                )
            )


def _iter_calls(text: str) -> list["Call"]:
    calls: list[Call] = []
    for match in CALL_RE.finditer(text):
        command_match = re.match(r"\\(?P<command>operatorname|mathsf)", match.group(0))
        if command_match is None:
            continue
        tail_start = match.start("tail")
        paren = _first_nonspace(text, tail_start)
        if paren is None or text[paren] != "(":
            continue
        close = _matching_paren(text, paren)
        if close is None:
            continue
        args = text[paren + 1 : close]
        calls.append(
            Call(
                name=match.group("name").strip(),
                command=command_match.group("command"),
                arg_count=_argument_count(args),
                start=match.start(),
            )
        )
    return calls


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
        ch = text[index]
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == "{":
            brace_depth += 1
            continue
        if ch == "}" and brace_depth:
            brace_depth -= 1
            continue
        if ch == "[":
            bracket_depth += 1
            continue
        if ch == "]" and bracket_depth:
            bracket_depth -= 1
            continue
        if brace_depth or bracket_depth:
            continue
        if ch == "(":
            depth += 1
            continue
        if ch == ")":
            depth -= 1
            if depth == 0:
                return index
    return None


def _argument_count(args: str) -> int:
    if not args.strip():
        return 0
    depth = 0
    brace_depth = 0
    bracket_depth = 0
    escaped = False
    count = 1
    for ch in args:
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == "{":
            brace_depth += 1
            continue
        if ch == "}" and brace_depth:
            brace_depth -= 1
            continue
        if ch == "[":
            bracket_depth += 1
            continue
        if ch == "]" and bracket_depth:
            bracket_depth -= 1
            continue
        if brace_depth or bracket_depth:
            continue
        if ch == "(":
            depth += 1
            continue
        if ch == ")" and depth:
            depth -= 1
            continue
        if ch == "," and depth == 0:
            count += 1
    return count


def _allowed_arities(signature: "Signature") -> frozenset[int]:
    if signature.name == SEQUENCE_NAME and signature.kind == "structure":
        return frozenset({2, signature.arity})
    return frozenset({signature.arity})


def _format_arities(arities: frozenset[int]) -> str:
    ordered = sorted(arities)
    if len(ordered) == 1:
        return f"{ordered[0]} argument(s)"
    return " or ".join(f"{value} argument(s)" for value in ordered)


@lru_cache(maxsize=1)
def _canonical_signatures() -> dict[str, "Signature"]:
    root = Path(__file__).resolve().parents[3]
    signatures: dict[str, Signature] = {}
    for filename, key, kind in (
        ("predicates.yaml", "predicates", "predicate"),
        ("structures.yaml", "structures", "structure"),
    ):
        data = _load_yaml(root / filename)
        for item in data.get(key, []) or []:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            args = item.get("arguments") or []
            if not name or not isinstance(args, list):
                continue
            signatures[str(name)] = Signature(str(name), kind, len(args))
    return signatures


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


class Signature:
    def __init__(self, name: str, kind: str, arity: int) -> None:
        self.name = name
        self.kind = kind
        self.arity = arity


class Call:
    def __init__(self, name: str, command: str, arg_count: int, start: int) -> None:
        self.name = name
        self.command = command
        self.arg_count = arg_count
        self.start = start
