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
SYMBOL_RE = re.compile(
    r"^(?:"
    r"[A-Za-z][A-Za-z0-9_']*"
    r"|\\[A-Za-z]+(?:_\{[^{}]+\}|_[A-Za-z0-9]+)?"
    r"|\\mathbf\{[^{}]+\}"
    r"|\\mathcal\{[^{}]+\}"
    r"|\\mathsf\{[^{}]+\}"
    r")(?:_\{[^{}]+\}|_[A-Za-z0-9]+)?$"
)
FUNCTIONAL_ROLES = {"functional_formula", "function", "map", "relation"}
SET_ROLES = {"domain_set", "carrier", "set", "family_set", "index_set", "input_domains"}


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    signatures = _canonical_signatures()
    if not signatures:
        return findings

    for tex in validator_files(volume_root, files):
        text = read_stripped_text(tex)
        for block in PREDICATE_READING_RE.finditer(text):
            _validate_block(volume_root, tex, text, block, signatures, findings)
    return findings


def _validate_block(
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
        if signature is None or len(call.args) != len(signature.roles):
            continue

        prefix = body[: call.start]
        for arg, role in zip(call.args, signature.roles):
            normalized = _normalize_arg(arg)
            if not normalized:
                continue
            if role in FUNCTIONAL_ROLES:
                _validate_functional_argument(volume_root, path, full_text, block_start, call, normalized, prefix, findings)
            elif role in SET_ROLES:
                _validate_set_argument(volume_root, path, full_text, block_start, call, normalized, prefix, findings)


def _validate_functional_argument(
    volume_root: Path,
    path: Path,
    full_text: str,
    block_start: int,
    call: "Call",
    arg: str,
    prefix: str,
    findings: list[Finding],
) -> None:
    if r"\mapsto" in arg:
        findings.append(
            finding(
                "predicate_reading_untyped_functional_argument",
                (
                    rf"{call.name} receives an inline functional rule {arg!r}; "
                    "construct a typed map or functional relation before passing it as a predicate argument."
                ),
                path,
                volume_root,
                line_at(full_text, block_start + call.start),
                severity="review",
            )
        )
        return
    if not _is_symbol_like(arg):
        return
    if _has_function_construction(prefix, arg):
        return
    findings.append(
        finding(
            "predicate_reading_unconstructed_functional_argument",
            (
                rf"{call.name} uses {arg!r} as a functional argument, but the predicate-reading block "
                "does not first construct it as a typed map, Function, or FunctionalRelation."
            ),
            path,
            volume_root,
            line_at(full_text, block_start + call.start),
            severity="review",
        )
    )


def _validate_set_argument(
    volume_root: Path,
    path: Path,
    full_text: str,
    block_start: int,
    call: "Call",
    arg: str,
    prefix: str,
    findings: list[Finding],
) -> None:
    if not _is_symbol_like(arg):
        return
    if _has_set_construction(prefix, arg):
        return
    findings.append(
        finding(
            "predicate_reading_unconstructed_set_argument",
            (
                rf"{call.name} uses {arg!r} as a set-like argument, but the predicate-reading block "
                "does not first construct or declare that object."
            ),
            path,
            volume_root,
            line_at(full_text, block_start + call.start),
            severity="review",
        )
    )


def _has_function_construction(prefix: str, arg: str) -> bool:
    escaped = re.escape(arg)
    patterns = [
        rf"{escaped}\s*\\colon[\s\S]{{0,120}}\\to",
        rf"\\operatorname\{{Function\}}\s*\(\s*{escaped}\s*,",
        rf"\\operatorname\{{FunctionalRelation\}}\s*\(\s*{escaped}\s*,",
        rf"\\mathsf\{{Function\}}\s*\(\s*{escaped}\s*,",
        rf"\\mathsf\{{FunctionalRelation\}}\s*\(\s*{escaped}\s*,",
    ]
    return any(re.search(pattern, prefix) for pattern in patterns)


def _has_set_construction(prefix: str, arg: str) -> bool:
    escaped = re.escape(arg)
    patterns = [
        rf"{escaped}\s*(?:=|:=|\\coloneqq)",
        rf"{escaped}\s*\\subseteq",
        rf"{escaped}\s*\\subset",
        rf"{escaped}\s*\\in",
    ]
    return any(re.search(pattern, prefix) for pattern in patterns)


def _iter_calls(text: str) -> list["Call"]:
    calls: list[Call] = []
    for match in CALL_RE.finditer(text):
        tail_start = match.start("tail")
        paren = _first_nonspace(text, tail_start)
        if paren is None or text[paren] != "(":
            continue
        close = _matching_paren(text, paren)
        if close is None:
            continue
        args = _split_arguments(text[paren + 1 : close])
        calls.append(Call(name=match.group("name").strip(), args=args, start=match.start()))
    return calls


def _split_arguments(args: str) -> list[str]:
    if not args.strip():
        return []
    parts: list[str] = []
    start = 0
    depth = 0
    brace_depth = 0
    bracket_depth = 0
    escaped = False
    for index, ch in enumerate(args):
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
            parts.append(args[start:index].strip())
            start = index + 1
    parts.append(args[start:].strip())
    return parts


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


def _normalize_arg(arg: str) -> str:
    return re.sub(r"\s+", " ", arg).strip().rstrip(".")


def _is_symbol_like(arg: str) -> bool:
    return bool(SYMBOL_RE.fullmatch(arg))


@lru_cache(maxsize=1)
def _canonical_signatures() -> dict[str, "Signature"]:
    root = Path(__file__).resolve().parents[3]
    signatures: dict[str, Signature] = {}
    for filename, key in (("predicates.yaml", "predicates"), ("structures.yaml", "structures")):
        data = _load_yaml(root / filename)
        for item in data.get(key, []) or []:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            args = item.get("arguments") or []
            if not name or not isinstance(args, list):
                continue
            roles = tuple(str(arg.get("role") or "") for arg in args if isinstance(arg, dict))
            signatures[str(name)] = Signature(str(name), roles)
    return signatures


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


class Signature:
    def __init__(self, name: str, roles: tuple[str, ...]) -> None:
        self.name = name
        self.roles = roles


class Call:
    def __init__(self, name: str, args: list[str], start: int) -> None:
        self.name = name
        self.args = args
        self.start = start
