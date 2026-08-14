from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

from core.registry_calls import iter_registry_calls, validate_registry_call
from core.file_inventory import validator_files
from core.finding import Finding, finding
from core.tex import line_at, read_stripped_text


OPERATORNAME_RE = re.compile(r"\\operatorname\{([^}]+)\}")
OPERATOR_SURFACE_FORM_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")
PREDICATE_READING_RE = re.compile(
    r"\\begin\{remark\*\}\[(?:Predicate reading|Negation predicate reading|Contrapositive predicate reading)\]"
    r"[\s\S]*?\\end\{remark\*\}",
    re.IGNORECASE,
)


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    known_entries = _known_operator_entries()
    known_names = frozenset(known_entries)
    for tex in validator_files(volume_root, files):
        text = read_stripped_text(tex)
        predicate_reading_spans = [match.span() for match in PREDICATE_READING_RE.finditer(text)]
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
        for call in iter_registry_calls(text):
            if any(start <= call.start < end for start, end in predicate_reading_spans):
                continue
            entry = known_entries.get(call.name)
            if entry is None:
                continue
            for issue in validate_registry_call(call, entry):
                findings.append(
                    finding(
                        "operator_signature_arity"
                        if issue.code == "registry_call_arity"
                        else "operator_signature_type",
                        issue.message + ".",
                        tex,
                        volume_root,
                        line_at(text, call.start),
                        severity="review" if issue.code == "registry_call_arity" else "error",
                    )
                )
    return findings


@lru_cache(maxsize=1)
def _known_operator_entries() -> dict[str, dict]:
    root = Path(__file__).resolve().parents[3]
    entries: dict[str, dict] = {}

    for filename, key in (
        ("predicates.yaml", "predicates"),
        ("structures.yaml", "structures"),
        ("relations.yaml", "relations"),
    ):
        data = _load_yaml(root / filename)
        for item in data.get(key, []) or []:
            for name in _operator_names_from_item(item):
                entries[name] = item

    data = _load_yaml(root / "notation.yaml")
    for item in data.get("notation", []) or []:
        if not isinstance(item, dict):
            continue
        symbol = str(item.get("symbol") or "")
        for match in OPERATORNAME_RE.finditer(symbol):
            entries[match.group(1).strip()] = item

    return entries


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
