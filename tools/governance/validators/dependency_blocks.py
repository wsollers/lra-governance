from __future__ import annotations

import re
from pathlib import Path

from core.formal_blocks import formal_blocks_for_file
from core.finding import Finding, finding
from core.tex import read_stripped_text
from core.file_inventory import validator_files


FORMAL_ENVS = {"definition", "axiom", "theorem", "lemma", "proposition", "corollary"}
FORMAL_PREFIXES = {"def", "ax", "thm", "lem", "prop", "cor"}
SECTION_RE = re.compile(r"\\(?:chapter|section|subsection|subsubsection)\*?\{")
DEPENDENCIES_ENV_RE = re.compile(r"\\begin\{dependencies\}(?P<body>[\s\S]*?)\\end\{dependencies\}", re.IGNORECASE)
DEPENDENCIES_REMARK_RE = re.compile(r"\\begin\{remark\*\}\[Dependencies\](?P<body>[\s\S]*?)\\end\{remark\*\}", re.IGNORECASE)
NO_LOCAL_RE = re.compile(r"\\NoLocalDependencies\b")
DEFINITIONAL_ROOT_RE = re.compile(r"\\DefinitionalRoot\b")
HYPERREF_RE = re.compile(r"\\hyperref\[(?P<label>[^\]]+)\]")
ITEM_RE = re.compile(r"^[ \t]*\\item\s+(?P<text>[^\n]+)$", re.MULTILINE)
LABEL_RE = re.compile(r"\\label\{(?P<label>[a-z]+:[^{}]+)\}")

LAYER_NAMES = {
    0: "carrier/type foundation",
    1: "ambient/set context",
    2: "constructor/operation/notation",
    3: "defining concept",
    4: "theorem or proof-use dependency",
}

FOUNDATION_DEF_TOKENS = {
    "natural",
    "naturals",
    "integer",
    "integers",
    "rational",
    "rationals",
    "real",
    "reals",
    "complex",
    "complexes",
    "field",
    "ordered-field",
}
AMBIENT_DEF_TOKENS = {
    "ordered-set",
    "order",
    "metric-space",
    "topological-space",
    "function-space",
    "set-family",
    "subset",
    "cartesian-product",
    "relation",
}
CONSTRUCTOR_DEF_TOKENS = {
    "addition",
    "subtraction",
    "multiplication",
    "division",
    "absolute-value",
    "set-arithmetic-images",
    "image",
    "preimage",
    "reciprocal-image",
    "sequence",
    "function",
    "interval",
}
CONCEPT_DEF_TOKENS = {
    "upper-bound",
    "lower-bound",
    "bounded",
    "supremum",
    "infimum",
    "maximum",
    "minimum",
    "least-upper-bound",
    "greatest-lower-bound",
    "limit",
    "convergence",
    "continuity",
    "derivative",
    "integral",
}


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    for tex in validator_files(volume_root, files):
        _validate_file(volume_root, tex, findings)
    return findings


def _validate_file(volume_root: Path, path: Path, findings: list[Finding]) -> None:
    text = read_stripped_text(path)
    for block in formal_blocks_for_file(path):
        label = block.label if block.label.split(":", 1)[0] in FORMAL_PREFIXES else "(unlabeled formal block)"
        window_start = block.end
        window_end = block.next_boundary
        window = text[window_start:window_end]
        declarations = _dependency_declarations(window)
        if not declarations:
            findings.append(
                finding(
                    "missing_dependencies",
                    f"{label} lacks a dependencies declaration.",
                    path,
                    volume_root,
                    block.line,
                    "error",
                )
            )
            continue
        for decl_kind, decl_body, decl_offset in declarations:
            if decl_kind == "dependencies_env" and DEFINITIONAL_ROOT_RE.search(decl_body):
                findings.append(
                    finding(
                        "definitional_root_inside_dependencies",
                        f"{label} places \\DefinitionalRoot inside a dependencies environment; use it as a standalone marker.",
                        path,
                        volume_root,
                        text.count("\n", 0, window_start + decl_offset) + 1,
                        "error",
                    )
                )
        if len(declarations) > 1:
            findings.append(
                finding(
                    "multiple_dependency_declarations",
                    f"{label} has multiple dependency declarations.",
                    path,
                    volume_root,
                    text.count("\n", 0, window_start + declarations[-1][2]) + 1,
                    "warning",
                )
            )
        kind, body, offset = declarations[-1]
        dep_line = text.count("\n", 0, window_start + offset) + 1
        if kind == "dependencies_remark":
            findings.append(
                finding(
                    "legacy_dependency_remark",
                    f"{label} uses remark*[Dependencies] instead of the dependencies environment.",
                    path,
                    volume_root,
                    dep_line,
                    "warning",
                )
            )
        if kind == "no_local" and block.env.lower() != "axiom":
            findings.append(
                finding(
                    "no_local_dependencies_on_non_axiom",
                    f"{label} uses \\NoLocalDependencies outside an axiom; use explicit dependencies or \\DefinitionalRoot for reviewed primitive definitions.",
                    path,
                    volume_root,
                    dep_line,
                    "warning",
                )
            )
        if kind in {"no_local", "definitional_root"}:
            continue
        refs = list(HYPERREF_RE.finditer(body))
        if not refs and "TODO" not in body:
            findings.append(
                finding(
                    "dependencies_without_hyperref",
                    f"{label} dependency block has no hyperref targets.",
                    path,
                    volume_root,
                    dep_line,
                    "error",
                )
            )
        for item in ITEM_RE.finditer(body):
            item_text = item.group("text").strip()
            if "TODO" in item_text or HYPERREF_RE.search(item_text):
                continue
            findings.append(
                finding(
                    "dependency_item_without_hyperref",
                    f"{label} dependency item lacks a hyperref target: {item_text}",
                    path,
                    volume_root,
                    text.count("\n", 0, window_start + offset + item.start()) + 1,
                    "error",
                )
            )
        for ref in refs:
            target = ref.group("label").strip()
            if target.startswith("prf:"):
                findings.append(
                    finding(
                        "dependency_targets_proof",
                        f"{label} targets proof label {target}.",
                        path,
                        volume_root,
                        dep_line,
                        "warning",
                    )
                )
            elif ":" not in target or target.split(":", 1)[0] not in FORMAL_PREFIXES:
                findings.append(
                    finding(
                        "invalid_dependency_target_prefix",
                        f"{label} targets non-formal label {target}.",
                        path,
                        volume_root,
                        dep_line,
                        "warning",
                    )
                )
        _check_dependency_order(volume_root, path, text, label, window_start, offset, body, findings)


def _check_dependency_order(
    volume_root: Path,
    path: Path,
    full_text: str,
    owner_label: str,
    window_start: int,
    decl_offset: int,
    body: str,
    findings: list[Finding],
) -> None:
    classified: list[tuple[int, str, int]] = []
    for ref in HYPERREF_RE.finditer(body):
        target = ref.group("label").strip()
        layer = _dependency_order_layer(target)
        if layer is None:
            continue
        classified.append((layer, target, ref.start()))
    if len(classified) < 2:
        return

    highest_layer = classified[0][0]
    highest_target = classified[0][1]
    for layer, target, start in classified[1:]:
        if layer < highest_layer:
            findings.append(
                finding(
                    "dependency_order_inversion",
                    (
                        f"{owner_label} lists {target} ({LAYER_NAMES[layer]}) after "
                        f"{highest_target} ({LAYER_NAMES[highest_layer]}). Order dependency blocks by "
                        "carrier/type foundations, ambient/set context, constructors/operations, "
                        "defining concepts, then theorem/proof-use dependencies."
                    ),
                    path,
                    volume_root,
                    full_text.count("\n", 0, window_start + decl_offset + start) + 1,
                    "review",
                )
            )
            return
        if layer > highest_layer:
            highest_layer = layer
            highest_target = target


def _dependency_order_layer(label: str) -> int | None:
    prefix, _, slug = label.partition(":")
    if prefix in {"thm", "lem", "prop", "cor", "ax"}:
        return 4
    if prefix != "def":
        return None
    tokens = _label_tokens(slug)
    if tokens & CONCEPT_DEF_TOKENS:
        return 3
    if tokens & FOUNDATION_DEF_TOKENS:
        return 0
    if tokens & AMBIENT_DEF_TOKENS:
        return 1
    if tokens & CONSTRUCTOR_DEF_TOKENS:
        return 2
    return None


def _label_tokens(slug: str) -> set[str]:
    normalized = slug.lower().replace("_", "-")
    parts = {part for part in normalized.split("-") if part}
    tokens = set(parts)
    pieces = [part for part in normalized.split("-") if part]
    for width in range(2, min(4, len(pieces)) + 1):
        for index in range(0, len(pieces) - width + 1):
            tokens.add("-".join(pieces[index : index + width]))
    return tokens


def _dependency_declarations(window: str) -> list[tuple[str, str, int]]:
    declarations: list[tuple[str, str, int]] = []
    for match in DEPENDENCIES_ENV_RE.finditer(window):
        declarations.append(("dependencies_env", match.group("body"), match.start()))
    for match in DEPENDENCIES_REMARK_RE.finditer(window):
        declarations.append(("dependencies_remark", match.group("body"), match.start()))
    for match in NO_LOCAL_RE.finditer(window):
        declarations.append(("no_local", "", match.start()))
    for match in DEFINITIONAL_ROOT_RE.finditer(window):
        declarations.append(("definitional_root", "", match.start()))
    return sorted(declarations, key=lambda item: item[2])
