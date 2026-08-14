"""Validate typed mathematical content and render canonical TeX deterministically.

The payload supplies every mathematical assertion.  This module owns only
representation: schema checks, canonical registry lookups, escaping, ordering,
house environments, file behavior, and the optional proof-stub post-step.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import jsonschema
import yaml

TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from core.formal_decoration_contract import (  # noqa: E402
    DECORATION_ORDER,
    DEPENDENT_DECORATION_CHILDREN,
    DEPENDENT_DECORATION_PARENTS,
    FAILURE_MODE_DECOMPOSITION_TRIGGERS,
    FORBIDDEN_DECORATION_BY_ENV,
    REPEATABLE_DECORATION_BLOCKS,
)
from core.registry_calls import iter_registry_calls, validate_registry_call  # noqa: E402

try:
    from .proof_stub import proof_filename, render_proof_stub
except ImportError:  # direct script execution
    from proof_stub import proof_filename, render_proof_stub


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "constitution" / "schemas" / "mathematical-content.schema.json"
SCHEMA_KINDS = frozenset({"axiom", "definition", "theorem", "example", "exposition", "proof"})
RENDERER_KINDS = SCHEMA_KINDS
THEOREM_SUBTYPES = frozenset({"theorem", "lemma", "proposition", "corollary"})
PREFIX_BY_KIND = {"axiom": "ax", "definition": "def"}
PREFIX_BY_SUBTYPE = {"theorem": "thm", "lemma": "lem", "proposition": "prop", "corollary": "cor"}
BOX_BY_ENV = {
    "axiom": ("axiombox", "Axiom"),
    "definition": ("definitionbox", "Definition"),
    "theorem": ("theorembox", "Theorem"),
    "lemma": ("lemmabox", "Lemma"),
    "proposition": ("propositionbox", "Proposition"),
    "corollary": ("corollarybox", "Corollary"),
}
FIXED_SUPPORT_KEYS = {
    "proof_link",
    "standard quantified statement",
    "interpretation",
    "notation",
    "historical note",
    "source comparison",
    "exposition",
    "dependencies",
}
EXTRA_SUPPORT_KEYS = frozenset(DECORATION_ORDER) - FIXED_SUPPORT_KEYS
REGISTRY_FILES = {
    "pred": ("predicates.yaml", "predicates"),
    "struct": ("structures.yaml", "structures"),
    "not": ("notation.yaml", "notation"),
    "rel": ("relations.yaml", "relations"),
}
FORMAL_LABEL_RE = re.compile(r"(?:def|ax|thm|lem|prop|cor):[a-z0-9]+(?:-[a-z0-9]+)*\Z")
CONTROL_SEQUENCE_RE = re.compile(r"\\([A-Za-z]+)")
OPERATOR_RE = re.compile(r"\\operatorname\{([^{}]+)\}")
STRUCTURE_RE = re.compile(r"\\mathsf\{([^{}]+)\}")
PROOF_LABEL_RE = re.compile(r"\\label\{(prf:[a-z0-9-]+)\}")
PROOF_FOR_RE = re.compile(r"\\LRAProofFor\{((?:thm|lem|prop|cor):[a-z0-9-]+)\}")
FORBIDDEN_MATH = re.compile(
    r"\\(?:documentclass|usepackage|input|include|write|openout|read|catcode|newcommand|renewcommand|def|label|hyperref|begin\{(?!aligned\b)|end\{(?!aligned\b))"
)

UNICODE_MATH = {
    "≤": r"\leq ",
    "≥": r"\geq ",
    "≠": r"\neq ",
    "∈": r"\in ",
    "∉": r"\notin ",
    "⊂": r"\subset ",
    "⊆": r"\subseteq ",
    "⊃": r"\supset ",
    "⊇": r"\supseteq ",
    "∀": r"\forall ",
    "∃": r"\exists ",
    "¬": r"\neg ",
    "∧": r"\land ",
    "∨": r"\lor ",
    "⇒": r"\Rightarrow ",
    "⇔": r"\Longleftrightarrow ",
    "→": r"\to ",
    "↦": r"\mapsto ",
    "∞": r"\infty ",
    "ℕ": r"\mathbb{N}",
    "ℤ": r"\mathbb{Z}",
    "ℚ": r"\mathbb{Q}",
    "ℝ": r"\mathbb{R}",
    "ℂ": r"\mathbb{C}",
    "α": r"\alpha ",
    "β": r"\beta ",
    "γ": r"\gamma ",
    "δ": r"\delta ",
    "ε": r"\varepsilon ",
    "θ": r"\theta ",
    "λ": r"\lambda ",
    "μ": r"\mu ",
    "π": r"\pi ",
    "σ": r"\sigma ",
    "φ": r"\varphi ",
    "ω": r"\omega ",
}
UNICODE_TEXT = {
    "–": "--",
    "—": "---",
    "−": "-",
    "“": "``",
    "”": "''",
    "‘": "`",
    "’": "'",
    "…": r"\ldots{}",
    " ": " ",
}
TEXT_ESCAPE = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "$": r"\$",
    "&": r"\&",
    "#": r"\#",
    "%": r"\%",
    "_": r"\_",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


@dataclass(frozen=True)
class RenderedArtifact:
    artifact_id: str
    kind: str
    tex: str
    output_path: str | None


class MathematicalContentError(ValueError):
    """Raised when a payload is structurally or representationally invalid."""


def load_schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_contract_sync(schema: Mapping[str, Any] | None = None) -> None:
    schema = dict(schema or load_schema())
    schema_kinds = frozenset(schema["$defs"]["common"]["properties"]["kind"]["enum"])
    if schema_kinds != RENDERER_KINDS:
        raise MathematicalContentError(
            "schema/renderer kind drift: "
            f"schema={sorted(schema_kinds)} renderer={sorted(RENDERER_KINDS)}"
        )
    refs = {
        entry["$ref"].rsplit("/", 1)[-1]
        for entry in schema["$defs"]["artifact"]["oneOf"]
    }
    if refs != schema_kinds:
        raise MathematicalContentError(
            f"schema artifact union drift: union={sorted(refs)} kinds={sorted(schema_kinds)}"
        )


def load_payload(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        value = json.loads(text)
    else:
        value = yaml.safe_load(text)
    if not isinstance(value, dict):
        raise MathematicalContentError("mathematical payload root must be an object")
    return value


def validate_payload(
    payload: Mapping[str, Any],
    *,
    governance_root: Path = ROOT,
    schema: Mapping[str, Any] | None = None,
) -> None:
    schema = dict(schema or load_schema())
    validate_contract_sync(schema)
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda item: list(item.absolute_path))
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.absolute_path) or "<root>"
        raise MathematicalContentError(f"schema validation failed at {location}: {first.message}")

    registry = _load_registry(governance_root)
    artifacts = list(payload["artifacts"])
    ids: set[str] = set()
    labels: set[str] = set()
    for index, artifact in enumerate(artifacts):
        artifact_id = artifact["id"]
        if artifact_id in ids:
            raise MathematicalContentError(f"duplicate artifact id: {artifact_id}")
        ids.add(artifact_id)
        label = artifact.get("label") or artifact.get("proof_label")
        if label:
            if label in labels:
                raise MathematicalContentError(f"duplicate artifact label: {label}")
            labels.add(label)
        _validate_artifact(artifact, index=index, registry=registry)


def render_payload(
    payload: Mapping[str, Any],
    *,
    governance_root: Path = ROOT,
) -> list[RenderedArtifact]:
    validate_payload(payload, governance_root=governance_root)
    return [
        RenderedArtifact(
            artifact_id=artifact["id"],
            kind=artifact["kind"],
            tex=_render_artifact(artifact),
            output_path=artifact.get("output_path"),
        )
        for artifact in payload["artifacts"]
    ]


def render_combined(payload: Mapping[str, Any], *, governance_root: Path = ROOT) -> str:
    return "\n".join(item.tex.rstrip() for item in render_payload(payload, governance_root=governance_root)) + "\n"


def render_requested_proof_stubs(
    payload: Mapping[str, Any],
    *,
    governance_root: Path = ROOT,
) -> list[RenderedArtifact]:
    validate_payload(payload, governance_root=governance_root)
    rendered: list[RenderedArtifact] = []
    for artifact in payload["artifacts"]:
        if artifact["kind"] != "theorem" or not artifact.get("proof_stub"):
            continue
        prefix, slug = artifact["label"].split(":", 1)
        subtype = artifact["subtype"]
        if prefix != PREFIX_BY_SUBTYPE[subtype]:
            raise MathematicalContentError("theorem subtype/label drift reached proof-stub rendering")
        statement_body = _render_theorem_body(artifact)
        dependencies = [
            (record["label"], escape_text(record["display"]))
            for record in artifact["dependencies"]["records"]
        ]
        tex = render_proof_stub(
            subtype,
            slug,
            escape_text(artifact["title"]),
            statement_body,
            dependencies,
            statement_label=artifact["label"],
        )
        rendered.append(
            RenderedArtifact(
                artifact_id=f"{artifact['id']}-proof-stub",
                kind="proof-stub",
                tex=tex,
                output_path=proof_filename(slug),
            )
        )
    return rendered


def write_artifacts(
    rendered: Sequence[RenderedArtifact],
    output_dir: Path,
    *,
    overwrite: bool = False,
) -> list[Path]:
    output_dir = output_dir.resolve()
    planned: list[tuple[Path, str]] = []
    for item in rendered:
        if not item.output_path:
            raise MathematicalContentError(
                f"artifact {item.artifact_id!r} needs output_path for directory output"
            )
        destination = (output_dir / item.output_path).resolve()
        try:
            destination.relative_to(output_dir)
        except ValueError as exc:
            raise MathematicalContentError(f"output path escapes target directory: {item.output_path}") from exc
        if destination.exists() and not overwrite:
            raise FileExistsError(f"refusing to overwrite existing file: {destination}")
        planned.append((destination, item.tex))

    written: list[Path] = []
    for destination, tex in planned:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(tex, encoding="ascii", newline="\n")
        temporary.replace(destination)
        written.append(destination)
    return written


def populate_proof_stub(existing_tex: str, artifact: Mapping[str, Any]) -> str:
    """Populate one durable proof stub while preserving its outer container."""
    if artifact.get("kind") != "proof":
        raise MathematicalContentError("proof-stub population requires exactly one proof artifact")
    proof_labels = PROOF_LABEL_RE.findall(existing_tex)
    theorem_labels = PROOF_FOR_RE.findall(existing_tex)
    if proof_labels != [artifact["proof_label"]]:
        raise MathematicalContentError(
            f"existing proof label mismatch: expected {artifact['proof_label']!r}, found {proof_labels}"
        )
    if theorem_labels != [artifact["theorem_label"]]:
        raise MathematicalContentError(
            f"existing theorem target mismatch: expected {artifact['theorem_label']!r}, found {theorem_labels}"
        )
    restatement_pattern = re.compile(
        rf"\\begin\{{{re.escape(artifact['theorem_subtype'])}\*\}}\[([^\]]*)\](.*?)"
        rf"\\end\{{{re.escape(artifact['theorem_subtype'])}\*\}}",
        re.DOTALL,
    )
    restatements = list(restatement_pattern.finditer(existing_tex))
    if len(restatements) != 1:
        raise MathematicalContentError(
            f"existing proof must contain exactly one matching starred restatement; found {len(restatements)}"
        )
    expected_title = escape_text(artifact["title"])
    expected_body = _render_rich_text(artifact["restatement"]).strip()
    if _normalize_space(restatements[0].group(1)) != _normalize_space(expected_title):
        raise MathematicalContentError("existing proof restatement title does not match the payload")
    if _normalize_space(restatements[0].group(2)) != _normalize_space(expected_body):
        raise MathematicalContentError("existing proof restatement body does not match the payload")

    populated = existing_tex
    populated = _replace_proof_body(
        populated,
        "Professional Standard Proof",
        _render_rich_text(artifact["professional_proof"]).rstrip(),
    )
    detailed = "\n\n".join(
        f"\\textbf{{{escape_text(step['title'])}.}} {_render_rich_text(step['body']).strip()}"
        for step in artifact["detailed_steps"]
    )
    populated = _replace_proof_body(populated, "Detailed Learning Proof", detailed)
    populated = _replace_unique_block(
        populated,
        re.compile(
            r"(\\begin\{remark\*\}\[Proof structure\]\s*)(.*?)(\s*\\end\{remark\*\})",
            re.DOTALL,
        ),
        _render_rich_text(artifact["proof_structure"]).rstrip(),
        "Proof structure",
    )
    dependency_pattern = re.compile(
        r"\\begin\{dependencies\}.*?\\end\{dependencies\}|\\NoLocalDependencies\b",
        re.DOTALL,
    )
    matches = list(dependency_pattern.finditer(populated))
    if len(matches) != 1:
        raise MathematicalContentError(
            f"existing proof must contain exactly one dependency declaration; found {len(matches)}"
        )
    rendered_dependencies = _render_dependencies(artifact["dependencies"])
    populated = dependency_pattern.sub(lambda _match: rendered_dependencies, populated, count=1)

    if artifact.get("proof_vault_url"):
        vault = f"\\ProofVaultURL{{{escape_text(artifact['proof_vault_url'])}}}"
        populated = re.sub(r"\n*\\clearpage", lambda _match: f"\n\n{vault}\n\n\\clearpage", populated, count=1)
    if artifact.get("uncertainty"):
        note = "% UNCERTAINTY: " + _comment_text(artifact["uncertainty"]["note"])
        populated = re.sub(r"\n*\\clearpage", lambda _match: f"\n\n{note}\n\n\\clearpage", populated, count=1)
    if artifact.get("source"):
        note = _render_source_comment(artifact["source"])
        populated = re.sub(r"\n*\\clearpage", lambda _match: f"\n\n{note}\n\n\\clearpage", populated, count=1)
    try:
        populated.encode("ascii")
    except UnicodeEncodeError as exc:
        raise MathematicalContentError("populated proof must be ASCII TeX") from exc
    return populated.rstrip() + "\n"


def escape_text(value: str) -> str:
    value = unicodedata.normalize("NFC", value)
    value = "".join(UNICODE_TEXT.get(char, char) for char in value)
    output: list[str] = []
    for char in value:
        if char in TEXT_ESCAPE:
            output.append(TEXT_ESCAPE[char])
        elif ord(char) < 128:
            output.append(char)
        else:
            decomposed = unicodedata.normalize("NFKD", char)
            ascii_value = decomposed.encode("ascii", "ignore").decode("ascii")
            if not ascii_value:
                raise MathematicalContentError(
                    f"unsupported Unicode text character U+{ord(char):04X}; use an ASCII name or typed math segment"
                )
            output.append(ascii_value)
    return "".join(output)


def normalize_math(value: str) -> str:
    value = unicodedata.normalize("NFC", value.strip())
    value = "".join(UNICODE_MATH.get(char, char) for char in value)
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        char = value[exc.start]
        raise MathematicalContentError(
            f"unsupported Unicode math character U+{ord(char):04X}; use canonical TeX notation"
        ) from exc
    if FORBIDDEN_MATH.search(value):
        raise MathematicalContentError("math fields may not contain document, file, label, link, or non-aligned environment commands")
    if value.count("{") != value.count("}"):
        raise MathematicalContentError("math field has unbalanced braces")
    return re.sub(r"[ \t]+\n", "\n", value).strip()


def _validate_artifact(
    artifact: Mapping[str, Any],
    *,
    index: int,
    registry: Mapping[str, Mapping[str, Any]],
) -> None:
    kind = artifact["kind"]
    registry_ids = list(artifact.get("registry_ids", []))
    missing = sorted(set(registry_ids) - set(registry))
    if missing:
        raise MathematicalContentError(f"artifact {index} uses unknown canonical registry id(s): {', '.join(missing)}")

    if kind in {"axiom", "definition", "theorem"}:
        expected_prefix = PREFIX_BY_KIND.get(kind)
        if kind == "theorem":
            expected_prefix = PREFIX_BY_SUBTYPE[artifact["subtype"]]
        if not artifact["label"].startswith(f"{expected_prefix}:"):
            raise MathematicalContentError(
                f"artifact {artifact['id']} kind/subtype requires {expected_prefix}: label"
            )
        boxed = artifact.get("boxed", False)
        if kind == "axiom" and not boxed:
            raise MathematicalContentError("axiom artifacts require boxed=true")
        _validate_dependencies(artifact["dependencies"], kind=kind)
        _validate_support_blocks(artifact, env=artifact.get("subtype", kind))

    if kind == "proof":
        expected_prefix = PREFIX_BY_SUBTYPE[artifact["theorem_subtype"]]
        if not artifact["theorem_label"].startswith(f"{expected_prefix}:"):
            raise MathematicalContentError("proof theorem_subtype does not match theorem_label")
        if artifact["proof_label"].split(":", 1)[1] != artifact["theorem_label"].split(":", 1)[1]:
            raise MathematicalContentError("proof_label must preserve the theorem label slug")
        _validate_dependencies(artifact["dependencies"], kind="proof")
    elif kind in {"example", "exposition"} and artifact.get("dependencies"):
        _validate_dependencies(artifact["dependencies"], kind=kind)

    selected = {registry_id: registry[registry_id] for registry_id in registry_ids}
    for math_value in _iter_math_values(artifact):
        normalized = normalize_math(math_value)
        _validate_registered_names(normalized, selected, artifact_id=artifact["id"])
    for text_value in _iter_text_values(artifact):
        escape_text(text_value)


def _validate_dependencies(contract: Mapping[str, Any], *, kind: str) -> None:
    mode = contract["mode"]
    records = contract["records"]
    if mode == "explicit" and not records:
        raise MathematicalContentError("explicit dependency mode requires records")
    if mode != "explicit" and records:
        raise MathematicalContentError(f"{mode} dependency mode forbids records")
    if mode == "no-local" and kind not in {"axiom", "proof"}:
        raise MathematicalContentError("no-local dependency mode is reserved for axioms and proofs")
    if mode == "definitional-root" and kind != "definition":
        raise MathematicalContentError("definitional-root mode is reserved for definitions")
    labels = [record["label"] for record in records]
    if len(labels) != len(set(labels)):
        raise MathematicalContentError("dependency records must not repeat labels")


def _validate_support_blocks(artifact: Mapping[str, Any], *, env: str) -> None:
    support = list(artifact.get("support_blocks", []))
    keys = [_support_key(block["type"]) for block in support]
    unknown = sorted(set(keys) - EXTRA_SUPPORT_KEYS)
    if unknown:
        raise MathematicalContentError(
            "unknown or fixed formal support type(s): " + ", ".join(unknown)
        )
    forbidden = sorted(set(keys) & FORBIDDEN_DECORATION_BY_ENV.get(env, set()))
    if forbidden:
        raise MathematicalContentError(
            f"{env} forbids formal support type(s): " + ", ".join(forbidden)
        )
    seen: set[str] = set()
    for key in keys:
        if key in seen and key not in REPEATABLE_DECORATION_BLOCKS:
            raise MathematicalContentError(f"formal support type may not repeat: {key}")
        seen.add(key)
    for child, parent in DEPENDENT_DECORATION_PARENTS.items():
        if child in seen and parent not in seen:
            raise MathematicalContentError(f"formal support type {child} requires {parent}")
    for parent, child in DEPENDENT_DECORATION_CHILDREN.items():
        if parent in seen and child not in seen:
            raise MathematicalContentError(f"formal support type {parent} requires {child}")
    if seen & FAILURE_MODE_DECOMPOSITION_TRIGGERS and "failure modes" not in seen:
        raise MathematicalContentError("negative or contrapositive support requires failure modes")
    for support_block, key in zip(support, keys):
        if key != "failure modes":
            continue
        descriptions = [block for block in support_block["body"] if block.get("type") == "description"]
        if len(descriptions) != 1:
            raise MathematicalContentError("failure modes require exactly one typed description block")
        titles = [item["title"].strip().lower().rstrip(".") for item in descriptions[0]["items"]]
        if not titles or titles[0] != "exposition":
            raise MathematicalContentError("failure modes must begin with an Exposition item")
        if seen & FAILURE_MODE_DECOMPOSITION_TRIGGERS and all(title == "exposition" for title in titles):
            raise MathematicalContentError("negative or contrapositive failure modes require a named branch")


def _support_key(value: str) -> str:
    key = value.replace("_", " ")
    return "non-examples" if key == "non examples" else key


def _load_registry(governance_root: Path) -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    for prefix, (filename, root_key) in REGISTRY_FILES.items():
        path = governance_root / filename
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for entry in data.get(root_key, []) or []:
            registry_id = entry.get("id")
            if not registry_id or not registry_id.startswith(f"{prefix}:"):
                continue
            entries[registry_id] = dict(entry)
    return entries


def _validate_registered_names(
    math_value: str,
    selected: Mapping[str, Mapping[str, Any]],
    *,
    artifact_id: str,
) -> None:
    allowed_operators = {
        str(entry.get("name"))
        for entry in selected.values()
        if entry.get("name")
        and (
            entry.get("kind") == "predicate"
            or str(entry.get("symbol", "")).startswith(r"\operatorname")
        )
    }
    for entry in selected.values():
        symbol = str(entry.get("symbol", ""))
        match = OPERATOR_RE.search(symbol)
        if match:
            allowed_operators.add(match.group(1))
    allowed_structures = {
        str(entry.get("name"))
        for entry in selected.values()
        if entry.get("name") and str(entry.get("constructor", "")).startswith(r"\mathsf")
    }
    unknown_operators = sorted(set(OPERATOR_RE.findall(math_value)) - allowed_operators)
    unknown_structures = sorted(set(STRUCTURE_RE.findall(math_value)) - allowed_structures)
    if unknown_operators:
        raise MathematicalContentError(
            f"artifact {artifact_id} uses unselected canonical operator name(s): {', '.join(unknown_operators)}"
        )
    if unknown_structures:
        raise MathematicalContentError(
            f"artifact {artifact_id} uses unselected canonical structure name(s): {', '.join(unknown_structures)}"
        )

    entries_by_name: dict[str, Mapping[str, Any]] = {}
    for entry in selected.values():
        name = entry.get("name")
        if name:
            entries_by_name[str(name)] = entry
        symbol = str(entry.get("symbol") or "")
        match = OPERATOR_RE.search(symbol)
        if match:
            entries_by_name[match.group(1)] = entry
    for call in iter_registry_calls(math_value):
        entry = entries_by_name.get(call.name)
        if entry is None:
            continue
        issues = validate_registry_call(call, entry)
        if issues:
            raise MathematicalContentError(
                f"artifact {artifact_id} has invalid canonical call: {issues[0].message}"
            )


def _iter_math_values(value: Any) -> Iterable[str]:
    if isinstance(value, Mapping):
        if value.get("type") in {"math", "display_math"} and isinstance(value.get("value"), str):
            yield value["value"]
        for key, child in value.items():
            if key == "calculation":
                if isinstance(child, list):
                    yield from (item for item in child if isinstance(item, str))
            elif key not in {"source", "uncertainty"}:
                yield from _iter_math_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_math_values(child)


def _iter_text_values(value: Any) -> Iterable[str]:
    if isinstance(value, Mapping):
        if value.get("type") in {"text", "emphasis", "strong", "code"} and isinstance(value.get("value"), str):
            yield value["value"]
        for key in ("title", "defined_term", "display", "attribution", "context", "note"):
            child = value.get(key)
            if isinstance(child, str):
                yield child
        for key, child in value.items():
            if key not in {"title", "defined_term", "display", "attribution", "context", "note"}:
                yield from _iter_text_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_text_values(child)


def _render_artifact(artifact: Mapping[str, Any]) -> str:
    kind = artifact["kind"]
    if kind == "axiom":
        return _render_formal(artifact, env="axiom", body=_render_rich_text(artifact["statement"]))
    if kind == "definition":
        return _render_formal(artifact, env="definition", body=_render_rich_text(artifact["defining_condition"]))
    if kind == "theorem":
        return _render_formal(artifact, env=artifact["subtype"], body=_render_theorem_body(artifact))
    if kind == "example":
        return _render_example(artifact)
    if kind == "exposition":
        return _render_exposition(artifact)
    if kind == "proof":
        return _render_full_proof(artifact)
    raise AssertionError(f"validated unsupported artifact kind: {kind}")


def _render_formal(artifact: Mapping[str, Any], *, env: str, body: str) -> str:
    title = escape_text(artifact["title"])
    formal = (
        f"\\begin{{{env}}}[{title}]\n"
        f"\\label{{{artifact['label']}}}\n"
        f"{body.rstrip()}\n"
    )
    if artifact["kind"] == "theorem":
        slug = artifact["label"].split(":", 1)[1]
        formal += f"\\hyperref[prf:{slug}]{{\\textit{{Go to proof.}}}}\n"
    formal += f"\\end{{{env}}}"
    if artifact.get("boxed", False):
        box_env, display = BOX_BY_ENV[env]
        formal = (
            f"\\begin{{{box_env}}}{{{display} ({title})}}\n"
            f"{formal}\n"
            f"\\end{{{box_env}}}"
        )
    decorations = [
        (DECORATION_ORDER["standard quantified statement"], _render_remark("Standard quantified statement", artifact["standard_form"])),
        (DECORATION_ORDER["interpretation"], _render_remark("Interpretation", artifact["interpretation"])),
    ]
    for support in artifact.get("support_blocks", []):
        key = _support_key(support["type"])
        title = key.title()
        decorations.append((DECORATION_ORDER[key], _render_remark(title, support["body"])))
    if artifact.get("notation"):
        decorations.append((DECORATION_ORDER["notation"], _render_remark("Notation", artifact["notation"])))
    if artifact.get("source_note"):
        decorations.append((DECORATION_ORDER["source comparison"], _render_remark("Source comparison", artifact["source_note"])))
    if artifact.get("exposition"):
        decorations.append((DECORATION_ORDER["exposition"], _render_remark("Exposition", artifact["exposition"])))
    blocks = [formal] + [block for _rank, block in sorted(decorations, key=lambda item: item[0])]
    if artifact.get("uncertainty"):
        blocks.append("% UNCERTAINTY: " + _comment_text(artifact["uncertainty"]["note"]))
    if artifact.get("source"):
        blocks.append(_render_source_comment(artifact["source"]))
    blocks.append(_render_dependencies(artifact["dependencies"]))
    return "\n\n".join(blocks) + "\n"


def _render_theorem_body(artifact: Mapping[str, Any]) -> str:
    parts = [_render_rich_text(item).rstrip() for item in artifact["hypotheses"]]
    parts.append(_render_rich_text(artifact["conclusion"]).rstrip())
    return "\n\n".join(parts) + "\n"


def _render_example(artifact: Mapping[str, Any]) -> str:
    title = escape_text(artifact["title"])
    blocks = [f"\\begin{{example}}[{title}]", _render_rich_text(artifact["setup"]).rstrip()]
    for expression in artifact.get("calculation", []):
        blocks.extend(("\\[", normalize_math(expression), "\\]"))
    if artifact.get("explanation"):
        blocks.append(_render_rich_text(artifact["explanation"]).rstrip())
    blocks.append("\\end{example}")
    if artifact.get("uncertainty"):
        blocks.append("% UNCERTAINTY: " + _comment_text(artifact["uncertainty"]["note"]))
    if artifact.get("source"):
        blocks.append(_render_source_comment(artifact["source"]))
    if artifact.get("dependencies"):
        blocks.append(_render_dependencies(artifact["dependencies"]))
    return "\n".join(blocks) + "\n"


def _render_exposition(artifact: Mapping[str, Any]) -> str:
    title = artifact.get("title") or artifact["subtype"].capitalize()
    blocks = [f"\\begin{{remark*}}[{escape_text(title)}]", _render_rich_text(artifact["body"]).rstrip(), "\\end{remark*}"]
    if artifact.get("uncertainty"):
        blocks.append("% UNCERTAINTY: " + _comment_text(artifact["uncertainty"]["note"]))
    if artifact.get("source"):
        blocks.append(_render_source_comment(artifact["source"]))
    if artifact.get("dependencies"):
        blocks.append(_render_dependencies(artifact["dependencies"]))
    return "\n".join(blocks) + "\n"


def _render_full_proof(artifact: Mapping[str, Any]) -> str:
    title = escape_text(artifact["title"])
    theorem_label = artifact["theorem_label"]
    proof_label = artifact["proof_label"]
    env = artifact["theorem_subtype"] + "*"
    professional = _render_rich_text(artifact["professional_proof"]).rstrip()
    detailed = "\n\n".join(
        f"\\textbf{{{escape_text(step['title'])}.}} {_render_rich_text(step['body']).strip()}"
        for step in artifact["detailed_steps"]
    )
    blocks = [
        "\\newpage",
        "\\phantomsection",
        f"\\label{{{proof_label}}}",
        f"\\LRAProofFor{{{theorem_label}}}",
        f"\\begin{{remark*}}[Return]\n\\hyperref[{theorem_label}]{{Return to {title}}}\n\\end{{remark*}}",
        f"\\begin{{{env}}}[{title}]\n{_render_rich_text(artifact['restatement']).rstrip()}\n\\end{{{env}}}",
        f"\\begin{{proof}}[Professional Standard Proof]\n\\LRAProofBodyStart\n{professional}\n\\end{{proof}}",
        f"\\begin{{proof}}[Detailed Learning Proof]\n\\LRAProofBodyStart\n{detailed}\n\\end{{proof}}",
        f"\\begin{{remark*}}[Proof structure]\n{_render_rich_text(artifact['proof_structure']).rstrip()}\n\\end{{remark*}}",
        _render_dependencies(artifact["dependencies"]),
    ]
    if artifact.get("proof_vault_url"):
        blocks.append(f"\\ProofVaultURL{{{escape_text(artifact['proof_vault_url'])}}}")
    if artifact.get("uncertainty"):
        blocks.append("% UNCERTAINTY: " + _comment_text(artifact["uncertainty"]["note"]))
    if artifact.get("source"):
        blocks.append(_render_source_comment(artifact["source"]))
    blocks.append("\\clearpage")
    return "\n\n".join(blocks) + "\n"


def _replace_proof_body(text: str, title: str, body: str) -> str:
    pattern = re.compile(
        rf"(\\begin\{{proof\}}\[{re.escape(title)}\]\s*\\LRAProofBodyStart\s*)(.*?)(\s*\\end\{{proof\}})",
        re.DOTALL,
    )
    return _replace_unique_block(text, pattern, body, title)


def _replace_unique_block(text: str, pattern: re.Pattern[str], body: str, name: str) -> str:
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise MathematicalContentError(f"existing proof must contain exactly one {name} block; found {len(matches)}")
    return pattern.sub(lambda match: match.group(1) + "\n" + body + "\n" + match.group(3), text, count=1)


def _render_rich_text(paragraphs: Sequence[Mapping[str, Any]]) -> str:
    rendered = []
    for block in paragraphs:
        if block.get("type") == "display_math":
            rendered.append(f"\\[\n{normalize_math(block['value'])}\n\\]")
            continue
        if block.get("type") == "description":
            items = []
            for item in block["items"]:
                title = escape_text(item["title"])
                body = _render_rich_text(item["body"]).strip()
                items.append(f"  \\item[{title}] {body}")
            rendered.append("\\begin{description}\n" + "\n\n".join(items) + "\n\\end{description}")
            continue
        pieces = []
        for segment in block["segments"]:
            if segment["type"] == "text":
                pieces.append(escape_text(segment["value"]))
            elif segment["type"] == "math":
                pieces.append(f"${normalize_math(segment['value'])}$")
            elif segment["type"] == "citation":
                pieces.append(f"\\{segment.get('command', 'citep')}{{{segment['key']}}}")
            elif segment["type"] == "reference":
                pieces.append(f"\\hyperref[{segment['label']}]{{{escape_text(segment['display'])}}}")
            else:
                command = {"emphasis": "emph", "strong": "textbf", "code": "texttt"}[segment["type"]]
                pieces.append(f"\\{command}{{{escape_text(segment['value'])}}}")
        rendered.append("".join(pieces))
    return "\n\n".join(rendered) + "\n"


def _render_display_remark(title: str, expressions: Sequence[str]) -> str:
    body = "\n".join(f"\\[\n{normalize_math(expression)}\n\\]" for expression in expressions)
    return f"\\begin{{remark*}}[{title}]\n{body}\n\\end{{remark*}}"


def _render_remark(title: str, body: Sequence[Mapping[str, Any]]) -> str:
    return f"\\begin{{remark*}}[{title}]\n{_render_rich_text(body).rstrip()}\n\\end{{remark*}}"


def _render_dependencies(contract: Mapping[str, Any]) -> str:
    mode = contract["mode"]
    if mode == "no-local":
        return r"\NoLocalDependencies"
    if mode == "definitional-root":
        return r"\DefinitionalRoot"
    items = "\n".join(
        f"  \\item \\hyperref[{record['label']}]{{{escape_text(record['display'])}}}"
        for record in contract["records"]
    )
    return "\\begin{dependencies}\n\\begin{itemize}\n" + items + "\n\\end{itemize}\n\\end{dependencies}"


def _comment_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("%", "percent")).strip().encode("ascii", "backslashreplace").decode("ascii")


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _render_source_comment(source: Mapping[str, Any]) -> str:
    fields = [
        f"attribution={_comment_text(source['attribution'])}" if source.get("attribution") else None,
        f"citation={source['citation_key']}" if source.get("citation_key") else None,
        f"context={_comment_text(source['context'])}" if source.get("context") else None,
    ]
    return "% SOURCE: " + " | ".join(field for field in fields if field)


def _write_single(path: Path, text: str, *, overwrite: bool) -> None:
    path = path.resolve()
    if path.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="ascii", newline="\n")
    temporary.replace(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload", type=Path, required=True, help="Typed JSON or YAML mathematical payload")
    destination = parser.add_mutually_exclusive_group(required=True)
    destination.add_argument("--check", action="store_true", help="Validate without rendering files")
    destination.add_argument("--stdout", action="store_true", help="Render the ordered collection to stdout")
    destination.add_argument("--output", type=Path, help="Write the ordered collection to one TeX file")
    destination.add_argument("--output-dir", type=Path, help="Write artifacts using their output_path fields")
    destination.add_argument("--populate-proof-stub", type=Path, help="Populate one existing durable proof stub in place")
    parser.add_argument("--proof-stubs-dir", type=Path, help="Also write requested canonical proof stubs")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacement of explicit output targets")
    parser.add_argument("--governance-root", type=Path, default=ROOT)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = load_payload(args.payload)
    rendered = render_payload(payload, governance_root=args.governance_root)
    if args.check:
        print(f"mathematical content: PASS ({len(rendered)} artifact(s))")
    elif args.stdout:
        print("\n".join(item.tex.rstrip() for item in rendered))
    elif args.output:
        _write_single(args.output, "\n".join(item.tex.rstrip() for item in rendered) + "\n", overwrite=args.overwrite)
    elif args.output_dir:
        write_artifacts(rendered, args.output_dir, overwrite=args.overwrite)
    else:
        artifacts = payload["artifacts"]
        if len(artifacts) != 1 or artifacts[0].get("kind") != "proof":
            raise MathematicalContentError("--populate-proof-stub requires one proof artifact")
        existing = args.populate_proof_stub.read_text(encoding="utf-8")
        populated = populate_proof_stub(existing, artifacts[0])
        _write_single(args.populate_proof_stub, populated, overwrite=True)
    if args.proof_stubs_dir:
        stubs = render_requested_proof_stubs(payload, governance_root=args.governance_root)
        write_artifacts(stubs, args.proof_stubs_dir, overwrite=args.overwrite)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
