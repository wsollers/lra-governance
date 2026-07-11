from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

from core.file_inventory import validator_files
from core.finding import Finding, finding
from core.tex import line_at, read_stripped_text


OPERATORNAME_RE = re.compile(r"\\operatorname\{([^}]+)\}")
OPERATOR_SURFACE_FORM_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    known_names = _known_operator_names()
    for tex in validator_files(volume_root, files):
        text = read_stripped_text(tex)
        for match in OPERATORNAME_RE.finditer(text):
            name = match.group(1).strip()
            if not name or name in known_names:
                continue
            findings.append(
                finding(
                    "unregistered_operatorname",
                    f"\\operatorname{{{name}}} is not registered in predicates.yaml, structures.yaml, relations.yaml, or notation.yaml.",
                    tex,
                    volume_root,
                    line_at(text, match.start()),
                )
            )
    return findings


@lru_cache(maxsize=1)
def _known_operator_names() -> frozenset[str]:
    root = Path(__file__).resolve().parents[3]
    names: set[str] = set()

    for filename, key in (
        ("predicates.yaml", "predicates"),
        ("structures.yaml", "structures"),
        ("relations.yaml", "relations"),
    ):
        data = _load_yaml(root / filename)
        for item in data.get(key, []) or []:
            names.update(_operator_names_from_item(item))

    data = _load_yaml(root / "notation.yaml")
    for item in data.get("notation", []) or []:
        if not isinstance(item, dict):
            continue
        symbol = str(item.get("symbol") or "")
        for match in OPERATORNAME_RE.finditer(symbol):
            names.add(match.group(1).strip())

    return frozenset(names)


def _operator_names_from_item(item) -> set[str]:
    if not isinstance(item, dict):
        return set()

    names: set[str] = set()
    name = item.get("name")
    if name:
        names.add(str(name))

    for surface_form in item.get("surface_forms") or []:
        surface = str(surface_form).strip()
        if OPERATOR_SURFACE_FORM_RE.fullmatch(surface):
            names.add(surface)

    return names


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}
