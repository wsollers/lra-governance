#!/usr/bin/env python3
"""Validate one LRA semantic artifact YAML record."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml

try:
    import jsonschema
except ImportError:
    jsonschema = None

LABEL_PREFIX = {
    "definition": "def:", "axiom": "ax:", "theorem": "thm:",
    "lemma": "lem:", "proposition": "prop:", "corollary": "cor:",
}
DEPENDENCY_KINDS = {"dependency", "prerequisite", "structural-existence", "structural-pairing", "proof-use"}
ONTOLOGY_KINDS = {"specializes", "derives_from", "uses_ambient", "legacy_alias_of"}
PROVENANCE_KINDS = {"source_variant_of", "reduces_to"}
PROOF_KINDS = {"proof-use", "has_canonical_proof", "has_handwritten_attempt", "handwritten_source_for_canonical_proof", "alternate_proof"}
PRESENTATION_KEYS = {"color", "background", "border", "icon", "column", "indent", "spacing", "css_class", "page_break", "tcolorbox"}
FORMULA_KINDS = {"variable", "constant", "application", "predicate", "relation", "membership", "not", "and", "or", "implies", "iff", "forall", "exists", "exists_unique", "equals", "raw_latex"}

@dataclass
class Result:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.errors


def load_mapping(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a mapping")
    return data


def walk(value: Any, path: str = "") -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            yield from walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{path}[{index}]")


def schema_validate(data: dict[str, Any], schema_path: Path, prefix: str, result: Result) -> None:
    if jsonschema is None:
        result.warnings.append("jsonschema is not installed; full schema validation was skipped")
        return
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(data), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.path) or "<root>"
        result.errors.append(f"{prefix}:{location}: {error.message}")


def presentation_check(data: dict[str, Any], result: Result) -> None:
    for path, value in walk(data):
        if isinstance(value, dict):
            for key in value:
                if key in PRESENTATION_KEYS:
                    result.errors.append(f"presentation:{path or '<root>'}.{key}: presentation data is forbidden")


def identity_check(data: dict[str, Any], result: Result) -> None:
    identity = data.get("identity") or {}
    expected = LABEL_PREFIX.get(identity.get("kind"))
    label = str(identity.get("label") or "")
    if expected and not label.startswith(expected):
        result.errors.append(f"identity.label: {identity.get('kind')} artifacts must use prefix {expected}")
    status = (identity.get("atomicity") or {}).get("status")
    if status == "requires_split":
        result.errors.append("identity.atomicity: source must be split before generation")
    elif status == "compound":
        result.warnings.append("identity.atomicity: compound artifact requires review")


def registry_data(governance_root: Path, result: Result) -> tuple[dict[str, int], set[str]]:
    predicates: dict[str, int] = {}
    structures: set[str] = set()
    pred_path = governance_root / "predicates.yaml"
    struct_path = governance_root / "structures.yaml"
    if not pred_path.exists():
        result.errors.append(f"registry: missing {pred_path}")
    else:
        for entry in load_mapping(pred_path).get("predicates", []) or []:
            if entry.get("id"):
                predicates[str(entry["id"])] = len(entry.get("arguments") or [])
    if not struct_path.exists():
        result.errors.append(f"registry: missing {struct_path}")
    else:
        for entry in load_mapping(struct_path).get("structures", []) or []:
            if entry.get("id"):
                structures.add(str(entry["id"]))
    return predicates, structures


def predicate_check(data: dict[str, Any], predicate_arities: dict[str, int], structures: set[str], result: Result) -> None:
    for path, node in walk(data):
        if not isinstance(node, dict) or node.get("kind") != "predicate":
            continue
        pred_id = str(node.get("predicate_id") or "")
        if pred_id not in predicate_arities:
            result.errors.append(f"registry:{path}: unknown predicate {pred_id!r}")
            continue
        actual = len(node.get("arguments") or [])
        expected = predicate_arities[pred_id]
        if actual != expected:
            result.errors.append(f"registry:{path}: {pred_id} expects {expected} arguments, got {actual}")
    reading = ((data.get("logical_forms") or {}).get("predicate_reading") or {})
    for struct_id in reading.get("registry_structures", []) or []:
        if struct_id not in structures:
            result.errors.append(f"registry: unknown structure {struct_id!r}")


def scope_check(data: dict[str, Any], result: Result) -> None:
    declared = {str(item.get("id")) for item in (data.get("parameters") or []) + (data.get("context") or []) if item.get("id")}

    def visit(node: Any, bound: set[str], path: str) -> None:
        if not isinstance(node, dict):
            return
        kind = node.get("kind")
        if kind == "raw_latex":
            result.warnings.append(f"ast:{path}: raw_latex prevents complete scope validation")
            return
        if kind == "variable":
            binder_id = str(node.get("binder_id") or "")
            if binder_id not in bound and binder_id not in declared:
                result.errors.append(f"ast:{path}: undeclared/free binder id {binder_id!r}")
            return
        if kind in {"forall", "exists", "exists_unique"}:
            binder = node.get("binder") or {}
            binder_id = str(binder.get("binder_id") or "")
            if not binder_id:
                result.errors.append(f"ast:{path}: quantifier binder lacks binder_id")
                return
            visit(binder.get("domain"), bound, f"{path}.binder.domain")
            new_bound = set(bound)
            new_bound.add(binder_id)
            visit(node.get("restriction"), new_bound, f"{path}.restriction")
            visit(node.get("body"), new_bound, f"{path}.body")
            return
        for key, value in node.items():
            if key == "kind":
                continue
            if isinstance(value, dict):
                visit(value, bound, f"{path}.{key}")
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    visit(child, bound, f"{path}.{key}[{index}]")

    forms = data.get("logical_forms") or {}
    roots = [
        ("statement.semantic_ast", (data.get("statement") or {}).get("semantic_ast")),
        ("logical_forms.standard_quantified.ast", (forms.get("standard_quantified") or {}).get("ast")),
    ]
    if forms.get("predicate_reading"):
        roots.append(("logical_forms.predicate_reading.ast", forms["predicate_reading"].get("ast")))
    negation = forms.get("negation") or {}
    for name in ("mechanical", "approved_normal_form"):
        if negation.get(name):
            roots.append((f"logical_forms.negation.{name}.ast", negation[name].get("ast")))
    if forms.get("contrapositive"):
        roots.append(("logical_forms.contrapositive.ast", forms["contrapositive"].get("ast")))
    for path, root in roots:
        visit(root, set(), path)


def logical_policy_check(data: dict[str, Any], result: Result) -> None:
    kind = (data.get("identity") or {}).get("kind")
    forms = data.get("logical_forms") or {}
    if kind in {"definition", "axiom"} and forms.get("contrapositive") is not None:
        result.errors.append("logical_forms.contrapositive: definitions and axioms must not have one")
    negation = forms.get("negation") or {}
    mechanical = negation.get("mechanical")
    approved = negation.get("approved_normal_form")
    requires = negation.get("normalization_requires") or []
    if approved is not None and mechanical is None:
        result.warnings.append("logical_forms.negation: approved form exists without mechanical form")
    if approved is not None and approved != mechanical and not requires:
        result.warnings.append("logical_forms.negation: changed normal form lists no required assumptions")


def relationship_check(data: dict[str, Any], result: Result) -> None:
    namespaces = {
        "dependency_edges": DEPENDENCY_KINDS,
        "ontology_edges": ONTOLOGY_KINDS,
        "provenance_edges": PROVENANCE_KINDS,
        "proof_edges": PROOF_KINDS,
    }
    relationships = data.get("relationships") or {}
    for namespace, allowed in namespaces.items():
        for index, edge in enumerate(relationships.get(namespace, []) or []):
            kind = edge.get("kind")
            if kind not in allowed:
                result.errors.append(f"relationships.{namespace}[{index}].kind: {kind!r} is invalid")
            target = str(edge.get("target") or "")
            if namespace == "dependency_edges" and target.startswith("prf:"):
                result.errors.append(f"relationships.{namespace}[{index}]: proof labels are not dependencies")


def unresolved_check(data: dict[str, Any], result: Result) -> None:
    for item in (data.get("provenance") or {}).get("unresolved", []) or []:
        text = f"{item.get('code')}: {item.get('question')}"
        (result.errors if item.get("blocks_generation") else result.warnings).append(f"unresolved:{text}")


def verification_check(data: dict[str, Any], result: Result) -> None:
    label = str((data.get("identity") or {}).get("label") or "")
    location = data.get("location") or {}
    verification = data.get("verification") or {}
    proof = verification.get("canonical_proof")
    if proof and ":" in label:
        expected = f"prf:{label.split(':', 1)[1]}"
        if proof.get("proof_label") != expected:
            result.warnings.append(f"verification.canonical_proof: expected proof label {expected}")
    for index, item in enumerate(verification.get("formalizations", []) or []):
        if item.get("artifact_label") != label:
            result.errors.append(f"verification.formalizations[{index}].artifact_label must equal {label}")
        if location.get("volume") == "ii" and (item.get("environment") or {}).get("mathlib_policy") != "prohibited":
            result.errors.append(f"verification.formalizations[{index}]: Volume II forbids Mathlib")
    for index, item in enumerate(verification.get("proof_vault_records", []) or []):
        if item.get("theorem_id") != label:
            result.errors.append(f"verification.proof_vault_records[{index}].theorem_id must equal {label}")


def path_check(data: dict[str, Any], repos_root: Path | None, result: Result) -> None:
    if repos_root is None:
        return
    location = data.get("location") or {}
    repo_name = str(location.get("repository") or "").split("/")[-1]
    source = repos_root / repo_name / str(location.get("source_file") or "")
    if not source.exists():
        result.errors.append(f"repos: source file does not exist: {source}")
    verification = data.get("verification") or {}
    lean_root = repos_root / "lra-lean"
    for index, item in enumerate(verification.get("formalizations", []) or []):
        source = lean_root / str(item.get("source_path") or "")
        if item.get("status") != "pending" and lean_root.exists() and not source.exists():
            result.errors.append(f"repos: Lean source for formalization {index} does not exist: {source}")
    vault_root = repos_root / "lra-proof-vault"
    for index, item in enumerate(verification.get("proof_vault_records", []) or []):
        metadata = vault_root / str(item.get("metadata_path") or "")
        if vault_root.exists() and not metadata.exists():
            result.errors.append(f"repos: proof-vault metadata {index} does not exist: {metadata}")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_check(package_dir: Path, governance_root: Path, artifact_label: str, result: Result) -> None:
    manifest_path = package_dir / "package.yaml"
    if not manifest_path.exists():
        result.errors.append(f"package: missing {manifest_path}")
        return
    manifest = load_mapping(manifest_path)
    schema_validate(manifest, governance_root / "constitution/schema/semantic-artifact-package.schema.json", "package-schema", result)
    if manifest.get("artifact_label") != artifact_label:
        result.errors.append("package.artifact_label: must equal artifact identity label")
    required = {
        "artifact": "artifact.yaml", "corrected_tex": "corrected.tex", "source_patch": "source.patch",
        "validation": "validation.yaml", "source_map": "source-map.yaml", "registry_needs": "registry-needs.yaml",
        "formalization_links": "formalization-links.yaml", "proof_vault_links": "proof-vault-links.yaml",
    }
    support_schema = governance_root / "constitution/schema/semantic-artifact-support.schema.json"
    for key, expected_name in required.items():
        entry = (manifest.get("files") or {}).get(key) or {}
        rel = str(entry.get("path") or "")
        if rel != expected_name:
            result.errors.append(f"package.files.{key}.path: expected {expected_name!r}, got {rel!r}")
            continue
        target = package_dir / rel
        if not target.exists():
            result.errors.append(f"package.files.{key}: missing {target}")
            continue
        if str(entry.get("sha256") or "") != file_sha256(target):
            result.errors.append(f"package.files.{key}.sha256: digest mismatch")
        if target.suffix in {".yaml", ".yml"} and key != "artifact":
            support = load_mapping(target)
            schema_validate(support, support_schema, f"support-schema:{target.name}", result)
            if support.get("artifact_label") != artifact_label:
                result.errors.append(f"{target.name}.artifact_label: must equal {artifact_label}")


def render(result: Result, as_json: bool) -> str:
    if as_json:
        return json.dumps({"clean": result.clean, "errors": result.errors, "warnings": result.warnings}, indent=2) + "\n"
    status = "PASS" if result.clean else "FAIL"
    lines = ["# Semantic Artifact Validation", f"- **Result:** {status}", f"- **Errors:** {len(result.errors)}", f"- **Warnings:** {len(result.warnings)}", "", "## Errors", ""]
    lines.extend(f"- {item}" for item in result.errors)
    if not result.errors:
        lines.append("_None._")
    lines += ["", "## Warnings", ""]
    lines.extend(f"- {item}" for item in result.warnings)
    if not result.warnings:
        lines.append("_None._")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--package-dir", type=Path)
    parser.add_argument("--governance-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--repos-root", type=Path)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    result = Result()
    try:
        data = load_mapping(args.artifact)
        schema_validate(data, args.governance_root / "constitution/schema/semantic-artifact.schema.json", "schema", result)
        presentation_check(data, result)
        identity_check(data, result)
        predicates, structures = registry_data(args.governance_root, result)
        predicate_check(data, predicates, structures, result)
        scope_check(data, result)
        logical_policy_check(data, result)
        relationship_check(data, result)
        unresolved_check(data, result)
        verification_check(data, result)
        path_check(data, args.repos_root, result)
        if args.package_dir is not None:
            package_check(args.package_dir, args.governance_root, str((data.get("identity") or {}).get("label") or ""), result)
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    if args.strict and result.warnings:
        result.errors.extend(f"strict-warning: {item}" for item in result.warnings)
        result.warnings.clear()
    print(render(result, args.format == "json"), end="")
    return 0 if result.clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
