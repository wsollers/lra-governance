#!/usr/bin/env python3
"""Validate one LRA semantic artifact YAML record."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
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
DEPENDENCY_KINDS = {
    "dependency",
    "prerequisite",
    "structural-existence",
    "structural-pairing",
    "proof-use",
    "proof-tool",
    "equivalent-language",
    "equivalent-characterization",
}
ONTOLOGY_KINDS = {"specializes", "derives_from", "uses_ambient", "legacy_alias_of", "instantiates", "uses"}
PROVENANCE_KINDS = {"source_variant_of", "reduces_to"}
PROOF_KINDS = {"proof-use", "proof-tool", "has_canonical_proof", "canonical-proof", "has_handwritten_attempt", "handwritten_source_for_canonical_proof", "alternate_proof", "related-proof", "supports"}
PRESENTATION_KEYS = {"color", "background", "border", "icon", "column", "indent", "spacing", "css_class", "page_break", "tcolorbox"}
FORMULA_KINDS = {"variable", "constant", "application", "predicate", "relation", "membership", "not", "and", "or", "implies", "iff", "forall", "exists", "exists_unique", "equals", "raw_latex"}
LABEL_RE = re.compile(r"\\label\{(?P<label>[^{}]+)\}")
ENV_START_RE = re.compile(r"\\begin\{(?P<env>definition|theorem|lemma|proposition|corollary|theorem\*|proof)\}")
ENV_END_RE = re.compile(r"\\end\{(?P<env>definition|theorem|lemma|proposition|corollary|theorem\*|proof)\}")
NONBLOCKING_UNRESOLVED_CODES = {
    "PROOF_BODY_MISSING",
    "PROOF_INCOMPLETE",
    "PROOF_STRUCTURE_EMPTY",
    "PROOF_DEPENDENCIES_TODO",
    "PROFESSIONAL_PROOF_TODO",
    "DETAILED_PROOF_TODO",
    "THREE_WAY_EQUIVALENCE_AST_REPAIRED",
}

@dataclass
class Result:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.errors

    @property
    def governance_ready(self) -> str:
        if self.errors:
            return "fail"
        if self.warnings:
            return "pass_with_warnings"
        return "pass"

    def warn(self, code: str, message: str) -> None:
        text = f"{code}: {message}"
        if text not in self.warnings:
            self.warnings.append(text)

    def error(self, code: str, message: str) -> None:
        text = f"{code}: {message}"
        if text not in self.errors:
            self.errors.append(text)


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


def registry_ids(governance_root: Path) -> set[str]:
    ids: set[str] = set()
    for filename, key in (("predicates.yaml", "predicates"), ("structures.yaml", "structures")):
        path = governance_root / filename
        if not path.exists():
            continue
        for entry in load_mapping(path).get(key, []) or []:
            if isinstance(entry, dict) and entry.get("id"):
                ids.add(str(entry["id"]))
    return ids


def labels_from_chapter_yamls(repo_root: Path) -> set[str]:
    labels: set[str] = set()
    for path in repo_root.rglob("chapter.yaml"):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for _walk_path, value in walk(data):
            if isinstance(value, dict) and isinstance(value.get("label"), str):
                labels.add(value["label"])
    return labels


def labels_from_tex(repo_root: Path) -> set[str]:
    labels: set[str] = set()
    for path in repo_root.rglob("*.tex"):
        parts = {part.lower() for part in path.parts}
        if "build" in parts:
            continue
        try:
            labels.update(LABEL_RE.findall(path.read_text(encoding="utf-8", errors="ignore")))
        except Exception:
            continue
    return labels


def tex_files(repo_root: Path) -> Iterable[Path]:
    for path in repo_root.rglob("*.tex"):
        parts = {part.lower() for part in path.parts}
        if "build" in parts:
            continue
        yield path


def find_label_block(repo_root: Path, label: str, *, radius: int = 80) -> tuple[Path, int, int, str] | None:
    needle = f"\\label{{{label}}}"
    for path in tex_files(repo_root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        index = text.find(needle)
        if index < 0:
            continue
        lines = text.splitlines()
        line_index = text[:index].count("\n")
        start = max(0, line_index - radius)
        end = min(len(lines), line_index + radius + 1)
        # Prefer the local environment containing the label when it is visible
        # in the radius window; fall back to a conservative neighbourhood.
        for candidate_start in range(line_index, start - 1, -1):
            if ENV_START_RE.search(lines[candidate_start]):
                for candidate_end in range(line_index, end):
                    if ENV_END_RE.search(lines[candidate_end]):
                        return path, candidate_start + 1, candidate_end + 1, "\n".join(lines[candidate_start:candidate_end + 1])
                break
        return path, start + 1, end, "\n".join(lines[start:end])
    return None


def label_index(governance_root: Path, repos_root: Path | None, data: dict[str, Any]) -> tuple[set[str], set[str], Path | None]:
    labels = registry_ids(governance_root)
    proof_labels: set[str] = set()
    repo_root: Path | None = None
    if repos_root is not None:
        repo_name = str(((data.get("location") or {}).get("repository") or "")).split("/")[-1]
        repo_root = repos_root / repo_name if repo_name else None
        roots = [repo_root] if repo_root and repo_root.exists() else []
        roots.extend(path for path in sorted(repos_root.glob("lra-volume-*")) if path.is_dir() and path not in roots)
        for root in roots:
            source_labels = labels_from_chapter_yamls(root) | labels_from_tex(root)
            labels.update(source_labels)
            proof_labels.update(label for label in source_labels if label.startswith("prf:"))
    return labels, proof_labels, repo_root


def ast_uses_application(data: dict[str, Any], function_id: str) -> bool:
    return any(
        isinstance(node, dict)
        and node.get("kind") == "application"
        and str(node.get("function") or "") == function_id
        for _path, node in walk(data)
    )


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
        elif not ast_uses_application(data, struct_id):
            result.errors.append(f"registry: structure {struct_id!r} is claimed in registry_structures but no AST application uses it")
    known_registry = set(predicate_arities) | structures
    for path, node in walk(data):
        if not isinstance(node, dict) or "ontology_id" not in node:
            continue
        ontology_id = node.get("ontology_id")
        if ontology_id is None:
            continue
        ontology_id = str(ontology_id)
        if ontology_id.startswith(("pred:", "struct:")) and ontology_id not in known_registry:
            result.errors.append(f"registry:{path}.ontology_id: unknown ontology id {ontology_id!r}")


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


def relationship_check(data: dict[str, Any], result: Result, known_labels: set[str] | None = None, proof_labels: set[str] | None = None) -> None:
    namespaces = {
        "dependency_edges": DEPENDENCY_KINDS,
        "ontology_edges": ONTOLOGY_KINDS,
        "provenance_edges": PROVENANCE_KINDS,
        "proof_edges": PROOF_KINDS,
    }
    relationships = data.get("relationships") or {}
    identity = data.get("identity") or {}
    for namespace, allowed in namespaces.items():
        for index, edge in enumerate(relationships.get(namespace, []) or []):
            kind = edge.get("kind")
            if kind not in allowed:
                result.errors.append(f"relationships.{namespace}[{index}].kind: {kind!r} is invalid")
            target = str(edge.get("target") or "")
            if namespace == "dependency_edges" and target.startswith("prf:"):
                result.errors.append(f"relationships.{namespace}[{index}]: proof labels are not dependencies")
            if (
                namespace == "dependency_edges"
                and str(identity.get("label") or "") == "thm:darboux"
                and target == "thm:darboux-property"
            ):
                result.errors.append(
                    f"relationships.{namespace}[{index}]: thm:darboux-property is not a valid dependency for thm:darboux because it would require continuity of the derivative"
                )
            if (
                namespace == "dependency_edges"
                and kind == "equivalent-characterization"
                and str(identity.get("kind") or "") == "definition"
                and target.startswith("def:")
            ):
                result.warn(
                    "FORMAL_KIND_MIGRATION_REQUIRED",
                    f"{identity.get('label')} is a definition with an equivalent-characterization edge to {target}; migrate the characterization to a theorem-like artifact before permanent normalization",
                )
            if known_labels is not None and target and target not in known_labels:
                if namespace == "proof_edges" or target.startswith("prf:"):
                    result.warn("PROOF_EDGE_UNVERIFIED", f"relationships.{namespace}[{index}].target {target!r} does not resolve to a known proof label")
                elif namespace == "ontology_edges" and target.startswith(("pred:", "struct:")):
                    result.warn("ONTOLOGY_TARGET_UNRESOLVED", f"relationships.{namespace}[{index}].target {target!r} does not resolve in canonical registries")
                elif namespace in {"dependency_edges", "provenance_edges"}:
                    result.warn("DEPENDENCY_LABEL_UNRESOLVED", f"relationships.{namespace}[{index}].target {target!r} does not resolve in the visible label/registry index")
            if (
                proof_labels is not None
                and namespace == "proof_edges"
                and target.startswith("prf:")
                and target not in proof_labels
            ):
                result.warn("PROOF_EDGE_UNVERIFIED", f"relationships.{namespace}[{index}].target {target!r} is not present in the proof-label index")


def unresolved_check(data: dict[str, Any], result: Result) -> None:
    for item in (data.get("provenance") or {}).get("unresolved", []) or []:
        code = str(item.get("code") or "")
        text = f"{code}: {item.get('question')}"
        if code in NONBLOCKING_UNRESOLVED_CODES:
            result.warnings.append(f"unresolved:{text}")
        else:
            (result.errors if item.get("blocks_generation") else result.warnings).append(f"unresolved:{text}")


def provenance_origin_check(data: dict[str, Any], result: Result) -> None:
    provenance = data.get("provenance") or {}
    origin = provenance.get("origin") or {}
    kind = str(origin.get("kind") or "")
    source_status = str(origin.get("source_status") or "")
    component_sources = origin.get("component_sources") or []
    primary_source = origin.get("primary_source_statement")
    derivation_rule = str(origin.get("derivation_rule") or "").strip()

    if not kind:
        return
    if kind == "author_derived_from_source_components":
        if source_status != "composite_source_route":
            result.error(
                "DERIVED_THEOREM_ORIGIN_ROUTE_REQUIRED",
                "author-derived artifacts must use provenance.origin.source_status: composite_source_route",
            )
        if primary_source is not None:
            result.warn(
                "DERIVED_THEOREM_PRIMARY_SOURCE_UNEXPECTED",
                "author-derived composite artifacts should leave provenance.origin.primary_source_statement null unless a single source statement also exists",
            )
        if len(component_sources) < 2:
            result.error(
                "DERIVED_THEOREM_COMPONENT_EVIDENCE_REQUIRED",
                "author-derived composite artifacts must list at least two component source evidence records",
            )
        if not derivation_rule:
            result.error(
                "DERIVED_THEOREM_DERIVATION_RULE_REQUIRED",
                "author-derived composite artifacts must state the derivation/instantiation rule that combines the source components",
            )
    elif source_status == "composite_source_route":
        result.warn(
            "COMPOSITE_SOURCE_ROUTE_KIND_MISMATCH",
            f"provenance.origin.source_status is composite_source_route but origin.kind is {kind!r}",
        )
    if kind in {"explicit_source_statement", "normalized_source_statement"} and primary_source is None:
        result.warn(
            "PRIMARY_SOURCE_STATEMENT_MISSING",
            f"{kind} should identify the primary source statement used as authority",
        )


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
        result.warn("SOURCE_PROVENANCE_NOT_CHECKED", "--repos-root was not supplied; source labels, source hash, and commit provenance were not independently verified")
        return
    location = data.get("location") or {}
    repo_name = str(location.get("repository") or "").split("/")[-1]
    repo_root = repos_root / repo_name
    source = repo_root / str(location.get("source_file") or "")
    if not source.exists():
        result.errors.append(f"repos: source file does not exist: {source}")
    else:
        expected_hash = str(location.get("source_hash") or "")
        if expected_hash.startswith("sha256:"):
            actual_hash = f"sha256:{file_sha256(source)}"
            if actual_hash != expected_hash:
                result.warn("SOURCE_HASH_MISMATCH", f"location.source_hash {expected_hash} does not match current source hash {actual_hash}")
        else:
            result.warn("SOURCE_HASH_MISSING", "location.source_hash is missing or not a sha256 digest")
    commit = str(location.get("commit") or "")
    if commit and repo_root.exists():
        local = subprocess.run(["git", "-C", str(repo_root), "cat-file", "-e", f"{commit}^{{commit}}"], capture_output=True, text=True)
        if local.returncode != 0:
            result.warn("SOURCE_COMMIT_NOT_LOCAL", f"location.commit {commit} is not present in the local repository")
        else:
            remote = subprocess.run(["git", "-C", str(repo_root), "branch", "-r", "--contains", commit], capture_output=True, text=True)
            if remote.returncode != 0 or not remote.stdout.strip():
                result.warn("SOURCE_COMMIT_NOT_REMOTE", f"location.commit {commit} is local/unpushed or not contained in a visible remote branch")
    elif not commit:
        result.warn("SOURCE_COMMIT_MISSING", "location.commit is missing")
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


def theorem_source_consistency_check(data: dict[str, Any], repos_root: Path | None, result: Result) -> None:
    """Heuristic governance checks for theorem/proof restatement alignment.

    This is deliberately conservative: it does not attempt full mathematics.
    It catches the class of mismatches exposed by thm:derivative-equivalence:
    a theorem calibrated under a cluster-point hypothesis while cited
    definitions still require interior points, and a proof restatement that
    changes which neighbourhood is quantified.
    """
    identity = data.get("identity") or {}
    if identity.get("kind") not in {"theorem", "lemma", "proposition", "corollary"}:
        return
    if repos_root is None:
        return
    location = data.get("location") or {}
    repo_name = str(location.get("repository") or "").split("/")[-1]
    repo_root = repos_root / repo_name
    if not repo_root.exists():
        return

    label = str(identity.get("label") or "")
    theorem_block = find_label_block(repo_root, label)
    theorem_text = theorem_block[3] if theorem_block else ""
    theorem_lower = theorem_text.lower()
    dependency_edges = (data.get("relationships") or {}).get("dependency_edges", []) or []
    dependency_labels = [str(edge.get("target") or "") for edge in dependency_edges if str(edge.get("target") or "").startswith("def:")]

    theorem_uses_cluster = "limit point" in theorem_lower or "iscluster" in theorem_lower or "cluster point" in theorem_lower
    if theorem_uses_cluster:
        interior_dependencies: list[str] = []
        for dep_label in dependency_labels:
            dep_block = find_label_block(repo_root, dep_label)
            if not dep_block:
                continue
            dep_text = dep_block[3]
            if r"\operatorname{int}" in dep_text or "interior" in dep_text.lower():
                interior_dependencies.append(dep_label)
        if interior_dependencies:
            result.error(
                "HYPOTHESIS_ALIGNMENT_REQUIRED",
                "theorem uses a cluster/limit-point hypothesis, but cited definitions require an interior-point hypothesis: "
                + ", ".join(sorted(interior_dependencies)),
            )

    proof_edges = (data.get("relationships") or {}).get("proof_edges", []) or []
    proof_labels = [str(edge.get("target") or "") for edge in proof_edges if str(edge.get("target") or "").startswith("prf:")]
    for proof_label in proof_labels:
        proof_block = find_label_block(repo_root, proof_label, radius=120)
        if not proof_block:
            continue
        proof_text = proof_block[3]
        proof_lower = proof_text.lower()
        if "todo:" in proof_lower or "todo" in proof_lower:
            result.warn("PROOF_INCOMPLETE", f"{proof_label} contains TODO proof bodies or placeholder proof material")
        if "proof structure" in proof_lower and re.search(r"\\begin\{remark\*\}\[Proof structure\]\s*\\end\{remark\*\}", proof_text, re.S):
            result.warn("PROOF_STRUCTURE_EMPTY", f"{proof_label} has an empty proof-structure block")
        if "todo: list mathematical dependencies" in proof_lower:
            result.warn("PROOF_DEPENDENCIES_TODO", f"{proof_label} still has TODO proof dependencies")

        topological_deps = [dep for dep in dependency_labels if "topological" in dep]
        def mentions_neighbourhood_of(text: str, symbol: str) -> bool:
            # Accept common TeX presentations: "$V$", "\(V\)", or bare V.
            sym = re.escape(symbol)
            marker = rf"(?:\$?{sym}\$?|\\\({sym}\\\))"
            return bool(re.search(rf"neighbou?rhood\s+{marker}\s+of", text, re.I))

        if topological_deps:
            for dep_label in topological_deps:
                dep_block = find_label_block(repo_root, dep_label)
                dep_text = dep_block[3] if dep_block else ""
                def_mentions_output_neighbourhood = mentions_neighbourhood_of(dep_text, "V") and re.search(r"of\s+(?:\$?L\$?|\\\(L\\\))", dep_text, re.I)
                proof_mentions_epsilon_input_neighbourhood = bool(
                    re.search(r"for every\s+(?:\$?\\varepsilon|\\\(\\varepsilon)", proof_text, re.I)
                    and mentions_neighbourhood_of(proof_text, "V")
                    and re.search(r"of\s+(?:\$?c\$?|\\\(c\\\))", proof_text, re.I)
                )
                if def_mentions_output_neighbourhood and proof_mentions_epsilon_input_neighbourhood:
                    result.error(
                        "PROOF_NEIGHBOURHOOD_FORM_MISMATCH",
                        f"{proof_label} restates {dep_label} with an epsilon/input-neighbourhood form rather than the definition's output-neighbourhood form",
                    )


def review_evidence_check(package_dir: Path, manifest: dict[str, Any], result: Result) -> None:
    review = manifest.get("review") or {}
    reviewer = review.get("reviewer") or {}
    notes = str(review.get("notes") or "")
    response_id = str(reviewer.get("response_id") or "")
    request_id = str(reviewer.get("request_id") or "")
    input_hash = str(reviewer.get("input_sha256") or "")
    output_hash = str(reviewer.get("output_sha256") or "")
    local_markers = ("LOCAL", "REFERENCE", "PLACEHOLDER")
    looks_synthetic = (
        any(marker in response_id.upper() for marker in local_markers)
        or any(marker in request_id.upper() for marker in local_markers)
        or "LOCAL" in notes.upper()
        or "PLACEHOLDER" in notes.upper()
        or input_hash == "sha256:" + "0" * 64
        or output_hash == "sha256:" + "0" * 64
    )
    if looks_synthetic and reviewer.get("provider") == "openai_responses_api":
        result.error(
            "LOCAL_REFERENCE_ENVELOPE_MIMICS_EXTERNAL_EVIDENCE",
            f"{package_dir / 'package.yaml'} uses an external-review envelope with local/reference/synthetic evidence markers",
        )


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
    review_evidence_check(package_dir, manifest, result)
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
        payload = {
            "clean": result.clean,
            "governance_ready": result.governance_ready,
            "summary": {
                "schema_validity": "fail" if any(item.startswith("schema:") for item in result.errors) else "pass",
                "registry_alignment": "fail" if any(item.startswith("registry:") or "SIGNATURE" in item for item in result.errors) else "pass",
                "source_provenance": "not_verified" if any("SOURCE_" in item for item in result.warnings + result.errors) else "verified_or_not_applicable",
                "proof_provenance": "not_verified" if any("PROOF_" in item for item in result.warnings + result.errors) else "verified_or_not_applicable",
                "migration_required": any("MIGRATION_REQUIRED" in item for item in result.warnings + result.errors),
            },
            "errors": result.errors,
            "warnings": result.warnings,
        }
        return json.dumps(payload, indent=2) + "\n"
    status = "PASS" if result.clean else "FAIL"
    lines = [
        "# Semantic Artifact Validation",
        f"- **Result:** {status}",
        f"- **Governance readiness:** {result.governance_ready}",
        f"- **Errors:** {len(result.errors)}",
        f"- **Warnings:** {len(result.warnings)}",
        "",
        "## Errors",
        "",
    ]
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
        known_labels, proof_labels, _repo_root = label_index(args.governance_root, args.repos_root, data)
        relationship_check(
            data,
            result,
            known_labels if args.repos_root is not None else None,
            proof_labels if args.repos_root is not None else None,
        )
        provenance_origin_check(data, result)
        unresolved_check(data, result)
        verification_check(data, result)
        path_check(data, args.repos_root, result)
        theorem_source_consistency_check(data, args.repos_root, result)
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
