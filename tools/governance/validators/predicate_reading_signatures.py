from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

from core.registry_calls import iter_registry_calls, validate_registry_call
from core.file_inventory import validator_files
from core.finding import Finding, finding
from core.tex import line_at, read_stripped_text


PREDICATE_READING_RE = re.compile(
    r"\\begin\{remark\*\}\[(?P<title>"
    r"Predicate reading|Negation predicate reading|Contrapositive predicate reading"
    r")\](?P<body>[\s\S]*?)\\end\{remark\*\}",
    re.IGNORECASE,
)
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
    for call in iter_registry_calls(body):
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

        if call.name in LEGACY_AMBIENT_NAMES and call.arity == 1:
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
        if call.arity not in allowed:
            expected = _format_arities(allowed)
            findings.append(
                finding(
                    "predicate_reading_signature_arity",
                    rf"{call.command}{{{call.name}}} has {call.arity} argument(s) in a predicate-reading block; canonical {signature.kind} signature expects {expected}.",
                    path,
                    volume_root,
                    line_at(full_text, block_start + call.start),
                    severity="review",
                )
            )

        for issue in validate_registry_call(call, signature.entry, allowed_arities=allowed):
            if issue.code != "registry_call_argument_type":
                continue
            findings.append(
                finding(
                    "predicate_reading_signature_type",
                    issue.message + ".",
                    path,
                    volume_root,
                    line_at(full_text, block_start + call.start),
                    severity="error",
                )
            )


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
            signatures[str(name)] = Signature(str(name), kind, dict(item))
    return signatures


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


class Signature:
    def __init__(self, name: str, kind: str, entry: dict) -> None:
        self.name = name
        self.kind = kind
        self.entry = entry
        self.arity = len(entry.get("arguments") or [])
