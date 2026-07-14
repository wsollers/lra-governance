from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

from core.file_inventory import validator_files
from core.finding import Finding, finding
from core.formal_blocks import formal_blocks_for_file
from core.tex import line_at, read_stripped_text


OPERATORNAME_RE = re.compile(r"\\operatorname\{([^}]+)\}")
UPPER_CAMEL_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    allowed_notation_names = _formal_statement_allowed_operator_names()
    forbidden_names = _formal_statement_forbidden_operator_names()
    if not forbidden_names:
        return findings

    for tex in validator_files(volume_root, files):
        text = read_stripped_text(tex)
        for block in formal_blocks_for_file(tex):
            for match in OPERATORNAME_RE.finditer(block.body):
                name = match.group(1).strip()
                if name in allowed_notation_names:
                    continue
                if name not in forbidden_names:
                    continue
                findings.append(
                    finding(
                        "predicate_operator_in_formal_statement",
                        (
                            rf"\operatorname{{{name}}} is predicate-style vocabulary. "
                            "Use ordinary mathematical notation in definition/theorem statements "
                            "and move predicate vocabulary to Predicate reading support blocks."
                        ),
                        tex,
                        volume_root,
                        line_at(text, block.begin + match.start()),
                    )
                )
    return findings


@lru_cache(maxsize=1)
def _formal_statement_forbidden_operator_names() -> frozenset[str]:
    root = Path(__file__).resolve().parents[3]
    names: set[str] = set()

    predicates = _load_yaml(root / "predicates.yaml").get("predicates", []) or []
    for item in predicates:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if name:
            names.add(str(name).strip())

    return frozenset(name for name in names if name)


@lru_cache(maxsize=1)
def _formal_statement_allowed_operator_names() -> frozenset[str]:
    root = Path(__file__).resolve().parents[3]
    names: set[str] = set()

    notation = _load_yaml(root / "notation.yaml").get("notation", []) or []
    for item in notation:
        if not isinstance(item, dict):
            continue
        symbol = str(item.get("symbol") or "")
        for match in OPERATORNAME_RE.finditer(symbol):
            name = match.group(1).strip()
            if name:
                names.add(name)

    return frozenset(name for name in names if name)


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}
