"""Materialize a reviewed experimental Lean concept package.

This tool writes only beneath ``LRA/Pilot`` and only updates its own marked
wiring blocks. Mathematical source is copied from the reviewed package; the
tool does not synthesize declarations or LaTeX formulas.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_VERSION = "lra.lean-concept-package/0.1"
PASCAL = re.compile(r"^[A-Z][A-Za-z0-9]*$")
DECLARATION_KINDS = {"axiom", "definition", "theorem", "example", "counterexample"}
PROOF_STATUSES = {"not-applicable", "stub-sorry", "checked"}


class PackageError(ValueError):
    """A deterministic package validation failure."""


AUTHORING_GATE_ERROR = (
    f"{SCHEMA_VERSION} is a legacy package format and cannot be materialized: "
    "it does not encode a reviewed concept contract, immutable evidence lanes, "
    "stable candidate/revision IDs, or approval of the current normalized "
    "revision; define and review the successor package schema before generation"
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PackageError(message)


def _safe_segment(value: str, field: str) -> str:
    _require(isinstance(value, str) and bool(PASCAL.fullmatch(value)), f"invalid {field}: {value!r}")
    return value


def _safe_file_name(value: str, suffix: str, field: str) -> str:
    path = PurePosixPath(value)
    _require(not path.is_absolute() and len(path.parts) == 1, f"unsafe {field}: {value!r}")
    _require(path.suffix == suffix and ".." not in path.parts, f"invalid {field}: {value!r}")
    return value


def load_and_validate(package_path: Path) -> dict[str, Any]:
    try:
        package = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PackageError(f"cannot read package: {error}") from error

    _require(package.get("schema_version") == SCHEMA_VERSION, "unsupported schema_version")
    package_id = package.get("package_id")
    _require(isinstance(package_id, str) and re.fullmatch(r"[a-z0-9][a-z0-9.-]+", package_id) is not None,
             "invalid package_id")
    _require(isinstance(package.get("request_id"), str) and package["request_id"], "missing request_id")
    _require(isinstance(package.get("concept"), dict), "missing concept")
    _require(isinstance(package.get("decisions"), list), "missing decisions")
    instances = package.get("instances")
    _require(isinstance(instances, list) and instances, "instances must be nonempty")

    instance_ids: set[str] = set()
    modules: set[str] = set()
    declarations: set[str] = set()
    output_paths: set[PurePosixPath] = set()
    for instance in instances:
        _require(isinstance(instance, dict), "instance must be an object")
        instance_id = instance.get("instance_id")
        _require(isinstance(instance_id, str) and instance_id and instance_id not in instance_ids,
                 f"duplicate or invalid instance_id: {instance_id!r}")
        instance_ids.add(instance_id)
        volume = _safe_segment(instance.get("volume"), "volume")
        _require(re.fullmatch(r"Volume[IVX]+", volume) is not None, f"invalid volume: {volume}")
        subject = _safe_segment(instance.get("subject"), "subject")
        topic = _safe_segment(instance.get("topic"), "topic")
        concept_folder = _safe_segment(instance.get("concept_folder"), "concept_folder")
        expected_namespace = f"LRA.Pilot.{volume}.{subject}.{topic}"
        _require(instance.get("namespace") == expected_namespace,
                 f"namespace must be {expected_namespace}")
        relation = instance.get("relation_to_primary")
        _require(relation in {"primary", "definitionally-equal", "checked-proof", "stub-statement", "author-selected-unverified"},
                 f"invalid relation_to_primary for {instance_id}")
        module_files = instance.get("module_files")
        _require(isinstance(module_files, list) and module_files, f"missing module_files for {instance_id}")

        for module_file in module_files:
            file_name = _safe_file_name(module_file.get("file_name"), ".lean", "module file")
            _require(PASCAL.fullmatch(Path(file_name).stem) is not None, f"module file must be PascalCase: {file_name}")
            module = f"{expected_namespace}.Concepts.{concept_folder}.{Path(file_name).stem}"
            _require(module not in modules, f"duplicate module: {module}")
            modules.add(module)
            relative = PurePosixPath("LRA", "Pilot", volume, subject, topic, "Concepts", concept_folder, file_name)
            _require(relative not in output_paths, f"duplicate output: {relative}")
            output_paths.add(relative)
            imports = module_file.get("imports")
            _require(isinstance(imports, list) and all(isinstance(item, str) and item for item in imports),
                     f"invalid imports in {module}")
            declaration_list = module_file.get("declarations")
            _require(isinstance(declaration_list, list) and declaration_list, f"no declarations in {module}")
            for declaration in declaration_list:
                name = declaration.get("name")
                _require(isinstance(name, str) and PASCAL.fullmatch(name) is not None,
                         f"invalid public declaration name: {name!r}")
                full_name = f"{expected_namespace}.{name}"
                _require(full_name not in declarations, f"duplicate declaration: {full_name}")
                declarations.add(full_name)
                kind = declaration.get("kind")
                status = declaration.get("proof_status")
                source = declaration.get("source")
                _require(kind in DECLARATION_KINDS, f"invalid declaration kind for {full_name}")
                _require(status in PROOF_STATUSES, f"invalid proof status for {full_name}")
                _require(isinstance(source, str) and source.strip(), f"missing source for {full_name}")
                if kind == "definition":
                    _require(status == "not-applicable", f"definition {full_name} must use not-applicable proof status")
                    _require("sorry" not in source, f"definition {full_name} may not contain sorry")
                if status == "stub-sorry":
                    _require(kind in {"theorem", "example", "counterexample"} and "sorry" in source,
                             f"stub {full_name} must be theorem-like and contain sorry")
                if status == "checked":
                    _require("sorry" not in source, f"checked declaration {full_name} contains sorry")

        latex = instance.get("latex")
        _require(isinstance(latex, dict), f"missing latex for {instance_id}")
        _safe_file_name(latex.get("file_name"), ".tex", "latex file")
        _require(isinstance(latex.get("source"), str) and latex["source"].strip(), f"missing latex source for {instance_id}")

    return package


def require_authoring_gate(package: dict[str, Any]) -> None:
    """Fail closed until a reviewed package format can prove current approval.

    The pilot's only live format predates the Concept Authoring Gate.  Treating
    its broad ``family_status`` or per-output publication flags as candidate
    approval would silently invent semantics that the format does not record.
    Keep this check separate from legacy structural validation so old fixtures
    remain inspectable while all generation paths are blocked.
    """

    if package.get("schema_version") == SCHEMA_VERSION:
        raise PackageError(AUTHORING_GATE_ERROR)
    raise PackageError("package format is not approved for materialization")


def _generated_lean(package_id: str, namespace: str, module_file: dict[str, Any]) -> str:
    imports = "\n".join(f"import {module}" for module in module_file["imports"])
    preamble = module_file.get("preamble", "").strip()
    declarations = "\n\n".join(item["source"].rstrip() for item in module_file["declarations"])
    parts = [
        f"-- GENERATED PILOT ARTIFACT from {package_id}; edit the reviewed package, not this file.",
        imports,
        f"namespace {namespace}",
    ]
    if preamble:
        parts.append(preamble)
    parts.extend([declarations, f"end {namespace}"])
    return "\n\n".join(part for part in parts if part) + "\n"


def _generated_router(package_id: str, imports: list[str], description: str) -> str:
    import_text = "\n".join(f"import {module}" for module in sorted(set(imports)))
    return (
        f"-- GENERATED PILOT ROUTER from {package_id}; edit the reviewed package, not this file.\n"
        f"{import_text}\n\n/-!\n{description}\n-/\n"
    )


def _marker(package_id: str, payload: str, comment: str) -> str:
    return (
        f"{comment} BEGIN LRA LEAN AUTHORING PILOT: {package_id}\n"
        f"{payload.rstrip()}\n"
        f"{comment} END LRA LEAN AUTHORING PILOT: {package_id}\n"
    )


def _with_marker(existing: str, package_id: str, payload: str, comment: str, before_doc: bool = False) -> str:
    block = _marker(package_id, payload, comment)
    start = f"{comment} BEGIN LRA LEAN AUTHORING PILOT: {package_id}"
    end = f"{comment} END LRA LEAN AUTHORING PILOT: {package_id}"
    if start in existing:
        start_at = existing.index(start)
        end_at = existing.index(end, start_at) + len(end)
        if end_at < len(existing) and existing[end_at] == "\n":
            end_at += 1
        return existing[:start_at] + block + existing[end_at:]
    insertion = existing.find("/-!") if before_doc else -1
    if insertion >= 0:
        return existing[:insertion] + block + "\n" + existing[insertion:]
    separator = "" if not existing or existing.endswith("\n") else "\n"
    return existing + separator + block


def _apply(path: Path, expected: str, check: bool, mismatches: list[str]) -> None:
    actual = path.read_text(encoding="utf-8") if path.exists() else None
    if actual == expected:
        return
    if check:
        mismatches.append(str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(expected, encoding="utf-8", newline="\n")


def materialize(package: dict[str, Any], package_path: Path, lean_root: Path, check: bool) -> list[str]:
    require_authoring_gate(package)
    _require((lean_root / "LRA").is_dir(), f"Lean root has no LRA directory: {lean_root}")
    package_id = package["package_id"]
    mismatches: list[str] = []
    topic_imports: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    volume_imports: dict[str, list[str]] = defaultdict(list)
    topic_tex_inputs: dict[tuple[str, str, str], list[str]] = defaultdict(list)

    normalized_package = json.dumps(package, indent=2, ensure_ascii=False) + "\n"
    for instance in package["instances"]:
        volume = instance["volume"]
        subject = instance["subject"]
        topic = instance["topic"]
        concept = instance["concept_folder"]
        namespace = instance["namespace"]
        concept_dir = lean_root / "LRA" / "Pilot" / volume / subject / topic / "Concepts" / concept
        modules: list[str] = []
        for module_file in instance["module_files"]:
            stem = Path(module_file["file_name"]).stem
            module = f"{namespace}.Concepts.{concept}.{stem}"
            modules.append(module)
            _apply(concept_dir / module_file["file_name"],
                   _generated_lean(package_id, namespace, module_file), check, mismatches)

        all_module = f"{namespace}.Concepts.{concept}.All"
        _apply(concept_dir / "All.lean",
               _generated_router(package_id, modules, f"Aggregate import for the {concept} concept family."),
               check, mismatches)
        _apply(concept_dir / "concept-package.json", normalized_package, check, mismatches)
        latex = instance["latex"]
        _apply(concept_dir / latex["file_name"], latex["source"], check, mismatches)
        topic_imports[(volume, subject, topic)].append(all_module)
        volume_imports[volume].append(f"LRA.Pilot.{volume}.{subject}.{topic}.Topic")
        topic_tex_inputs[(volume, subject, topic)].append(
            f"Concepts/{concept}/{Path(latex['file_name']).stem}"
        )

    for (volume, subject, topic), imports in topic_imports.items():
        topic_dir = lean_root / "LRA" / "Pilot" / volume / subject / topic
        topic_module = f"LRA.Pilot.{volume}.{subject}.{topic}.Topic"
        _apply(topic_dir / "Topic.lean",
               _generated_router(package_id, imports, f"Aggregate import for the experimental {topic} topic."),
               check, mismatches)

        tex_path = topic_dir / "index.tex"
        existing_tex = tex_path.read_text(encoding="utf-8") if tex_path.exists() else f"\\section{{{topic}}}\n\n"
        tex_payload = "\n".join(f"\\input{{{item}}}" for item in sorted(topic_tex_inputs[(volume, subject, topic)]))
        expected_tex = _with_marker(existing_tex, package_id, tex_payload, "%")
        _apply(tex_path, expected_tex, check, mismatches)
        _require(topic_module in volume_imports[volume], "internal topic wiring failure")

    pilot_root_imports: list[str] = []
    for volume, imports in volume_imports.items():
        volume_path = lean_root / "LRA" / "Pilot" / f"{volume}.lean"
        _apply(volume_path,
               _generated_router(package_id, imports, f"Aggregate import for experimental {volume} topics."),
               check, mismatches)
        pilot_root_imports.append(f"LRA.Pilot.{volume}")

    pilot_path = lean_root / "LRA" / "Pilot.lean"
    existing_pilot = pilot_path.read_text(encoding="utf-8")
    payload = "\n".join(f"import {module}" for module in sorted(pilot_root_imports))
    expected_pilot = _with_marker(existing_pilot, package_id, payload, "--", before_doc=True)
    _apply(pilot_path, expected_pilot, check, mismatches)
    return mismatches


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--lean-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true", help="report drift without writing")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        package = load_and_validate(args.package.resolve())
        mismatches = materialize(package, args.package.resolve(), args.lean_root.resolve(), args.check)
    except PackageError as error:
        print(f"lean-authoring pilot: ERROR: {error}", file=sys.stderr)
        return 2
    if mismatches:
        print("lean-authoring pilot: generated output differs:", file=sys.stderr)
        for mismatch in mismatches:
            print(f"  {mismatch}", file=sys.stderr)
        return 1
    action = "checked" if args.check else "materialized"
    print(f"lean-authoring pilot: {action} {package['package_id']} ({len(package['instances'])} instances)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
