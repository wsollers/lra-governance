#!/usr/bin/env python3
"""Validate canonical predicate and structure registry contracts.

The registry is more than a name list: argument order is semantic position,
roles are type/assembly hints, predicates declare return type, and structures
declare what mathematical context they package.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class RegistryResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.errors

    def as_json(self) -> dict[str, Any]:
        return {"clean": self.clean, "errors": self.errors, "warnings": self.warnings}


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a mapping")
    return data


def arg_names(entry: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for arg in entry.get("arguments") or []:
        if isinstance(arg, dict):
            names.append(str(arg.get("name") or ""))
    return names


def validate_arguments(entry: dict[str, Any], label: str, result: RegistryResult) -> set[str]:
    arguments = entry.get("arguments")
    if not isinstance(arguments, list):
        result.errors.append(f"{label}: arguments must be a list")
        return set()

    seen: set[str] = set()
    for index, arg in enumerate(arguments, start=1):
        if not isinstance(arg, dict):
            result.errors.append(f"{label}: argument {index} must be a mapping")
            continue
        name = str(arg.get("name") or "")
        role = str(arg.get("role") or "")
        if not name:
            result.errors.append(f"{label}: argument {index} is missing name")
        if not role:
            result.errors.append(f"{label}: argument {index} ({name or '?'}) is missing role")
        if name in seen:
            result.errors.append(f"{label}: duplicate argument name {name!r}")
        if name:
            seen.add(name)
        if "position" in arg and arg.get("position") != index:
            result.errors.append(
                f"{label}: argument {name or index} declares position {arg.get('position')}, but YAML position is {index}"
            )
    return seen


def validate_carried_context(entry: dict[str, Any], label: str, names: set[str], result: RegistryResult) -> None:
    carried = entry.get("carried_context")
    if carried is None:
        return
    if not isinstance(carried, list):
        result.errors.append(f"{label}: carried_context must be a list")
        return
    for index, item in enumerate(carried, start=1):
        if not isinstance(item, dict):
            result.errors.append(f"{label}: carried_context item {index} must be a mapping")
            continue
        kind = str(item.get("kind") or "")
        source = str(item.get("source") or "")
        argument = str(item.get("argument") or item.get("source_argument") or "")
        if not kind:
            result.errors.append(f"{label}: carried_context item {index} is missing kind")
        if not source:
            result.errors.append(f"{label}: carried_context item {index} is missing source")
        if not argument:
            result.errors.append(f"{label}: carried_context item {index} is missing argument")
        elif argument not in names:
            result.errors.append(
                f"{label}: carried_context item {index} references unknown argument {argument!r}"
            )


def validate_predicates(root: Path, result: RegistryResult) -> None:
    data = load_yaml(root / "predicates.yaml")
    predicates = data.get("predicates")
    if not isinstance(predicates, list):
        result.errors.append("predicates.yaml: predicates must be a list")
        return

    ids: set[str] = set()
    for entry in predicates:
        if not isinstance(entry, dict):
            result.errors.append("predicates.yaml: each predicate entry must be a mapping")
            continue
        pred_id = str(entry.get("id") or "")
        label = pred_id or "<missing predicate id>"
        if not pred_id.startswith("pred:"):
            result.errors.append(f"{label}: predicate id must start with pred:")
        if pred_id in ids:
            result.errors.append(f"{label}: duplicate predicate id")
        ids.add(pred_id)
        for field_name in ("name", "kind", "category", "returns", "description"):
            if entry.get(field_name) in (None, ""):
                result.errors.append(f"{label}: missing {field_name}")
        if entry.get("kind") != "predicate":
            result.errors.append(f"{label}: kind must be predicate")
        if entry.get("returns") != "truth_value":
            result.errors.append(f"{label}: predicates must return truth_value")
        names = validate_arguments(entry, label, result)
        validate_carried_context(entry, label, names, result)


def validate_structures(root: Path, result: RegistryResult) -> None:
    data = load_yaml(root / "structures.yaml")
    structures = data.get("structures")
    if not isinstance(structures, list):
        result.errors.append("structures.yaml: structures must be a list")
        return

    ids: set[str] = set()
    for entry in structures:
        if not isinstance(entry, dict):
            result.errors.append("structures.yaml: each structure entry must be a mapping")
            continue
        struct_id = str(entry.get("id") or "")
        label = struct_id or "<missing structure id>"
        if not struct_id.startswith("struct:"):
            result.errors.append(f"{label}: structure id must start with struct:")
        if struct_id in ids:
            result.errors.append(f"{label}: duplicate structure id")
        ids.add(struct_id)
        for field_name in ("name", "kind", "category", "constructor", "description"):
            if entry.get(field_name) in (None, ""):
                result.errors.append(f"{label}: missing {field_name}")
        if entry.get("kind") != "structure":
            result.errors.append(f"{label}: kind must be structure")
        names = validate_arguments(entry, label, result)

        carrier = entry.get("carrier_argument")
        if carrier is not None and str(carrier) not in names:
            result.errors.append(f"{label}: carrier_argument {carrier!r} is not an argument")

        structural = entry.get("structural_arguments")
        if not isinstance(structural, list):
            result.errors.append(f"{label}: structural_arguments must be a list")
        else:
            for item in structural:
                if str(item) not in names:
                    result.errors.append(f"{label}: structural_argument {item!r} is not an argument")

        validate_carried_context(entry, label, names, result)


def validate_registry(root: Path) -> RegistryResult:
    result = RegistryResult()
    validate_predicates(root, result)
    validate_structures(root, result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--governance-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = validate_registry(args.governance_root)
    if args.format == "json":
        print(json.dumps(result.as_json(), indent=2))
    else:
        if result.clean:
            print("registry contract: pass")
        for warning in result.warnings:
            print(f"warning: {warning}")
        for error in result.errors:
            print(f"error: {error}")
    return 0 if result.clean else 1


if __name__ == "__main__":
    sys.exit(main())
