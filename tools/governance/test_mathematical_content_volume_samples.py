"""Live-volume compatibility tests for typed mathematical content.

The tiny adapter in this module is deliberately test-only. It transcribes
already-authored TeX into typed fields so the renderer can be exercised against
real LRA material without copying mathematical examples into governance or
turning Python into an author.
"""

from __future__ import annotations

import copy
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REPOS = ROOT.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from core.formal_blocks import FormalBlock, formal_blocks_for_file  # noqa: E402
from core.formal_decoration_contract import DECORATION_ORDER  # noqa: E402
from generators.mathematical_tex import (  # noqa: E402
    MathematicalContentError,
    populate_proof_stub,
    render_combined,
    render_requested_proof_stubs,
    validate_payload,
)
from validators.proof_file_contract import validate_text as validate_proof_text  # noqa: E402


@dataclass(frozen=True)
class FormalSample:
    volume: str
    source: str
    label: str
    registry_ids: tuple[str, ...] = ()

    @property
    def volume_root(self) -> Path:
        return REPOS / self.volume / self.volume.replace("lra-", "")

    @property
    def path(self) -> Path:
        return self.volume_root / self.source


@dataclass(frozen=True)
class ProofSample:
    statement: FormalSample
    proof: str

    @property
    def proof_path(self) -> Path:
        return self.statement.volume_root / self.proof


AXIOMS = (
    FormalSample(
        "lra-volume-i",
        "book-logic/propositional-logic/notes/axioms/notes-axioms.tex",
        "ax:propositional-weakening",
    ),
    FormalSample(
        "lra-volume-i",
        "book-sets/set-theory/notes/sets/notes-foundations.tex",
        "ax:empty-set",
        ("pred:empty-set",),
    ),
    FormalSample(
        "lra-volume-ii",
        "book-discrete-algebraic/natural-numbers/notes/nz-axioms/notes-nz-axioms.tex",
        "ax:n-successor-closure",
    ),
    FormalSample(
        "lra-volume-i",
        "book-logic/propositional-logic/notes/axioms/notes-axioms.tex",
        "ax:propositional-implication-distribution",
    ),
)

LEGACY_ARITY_SAMPLE = FormalSample(
    "lra-volume-iii",
    "book-analysis-i/completeness/notes/completeness/notes-axiom-of-completeness.tex",
    "ax:completeness-of-reals",
    ("pred:has-least-upper-bound-property", "pred:least-upper-bound", "struct:ordered-set"),
)

DEFINITIONS = (
    FormalSample(
        "lra-volume-i",
        "book-sets/set-theory/notes/sets/notes-set-operations.tex",
        "def:empty-set",
        ("pred:empty-set",),
    ),
    FormalSample(
        "lra-volume-ii",
        "book-discrete-algebraic/natural-numbers/notes/nz-axioms/notes-nz-axioms.tex",
        "def:natural-numbers",
        ("pred:peano-system",),
    ),
    FormalSample(
        "lra-volume-iii",
        "book-analysis-i/sequences/notes/definition/notes-null-constant-sequences.tex",
        "def:bounded-sequence",
        ("pred:bounded",),
    ),
    FormalSample(
        "lra-volume-iv",
        "book-spaces/metric-spaces/notes/distances-and-diameter/notes-distances-and-diameter.tex",
        "def:metric-diameter",
        ("not:diameter",),
    ),
)

PROOFS = (
    ProofSample(
        FormalSample(
            "lra-volume-i",
            "book-sets/set-theory/notes/sets/notes-set-operations.tex",
            "thm:empty-set-exists-unique",
        ),
        "book-sets/set-theory/proofs/sets/prf-empty-set-exists-unique.tex",
    ),
    ProofSample(
        FormalSample(
            "lra-volume-i",
            "book-sets/functions/notes/functions/notes-composition.tex",
            "prop:preimage-under-inverse-function",
        ),
        "book-sets/functions/proofs/functions/prf-preimage-under-inverse-function.tex",
    ),
    ProofSample(
        FormalSample(
            "lra-volume-iii",
            "book-analysis-i/bounding/notes/bounds-algebra/notes-algebra-of-supremum-infimum.tex",
            "thm:infimum-sum-set",
            ("pred:greatest-lower-bound", "struct:ordered-set"),
        ),
        "book-analysis-i/bounding/proofs/bounds-algebra/prf-infimum-sum-set.tex",
    ),
    ProofSample(
        FormalSample(
            "lra-volume-iv",
            "book-spaces/metric-spaces/notes/distances-and-diameter/notes-distances-and-diameter.tex",
            "thm:metric-diameter-monotone-under-inclusion",
            ("not:diameter",),
        ),
        "book-spaces/metric-spaces/proofs/distances-and-diameter/prf-metric-diameter-monotone-under-inclusion.tex",
    ),
)


if not all(sample.path.is_file() for sample in (*AXIOMS, *DEFINITIONS)) or not all(
    sample.statement.path.is_file() and sample.proof_path.is_file() for sample in PROOFS
):
    pytest.skip("live LRA volume siblings are unavailable", allow_module_level=True)


DISPLAY_RE = re.compile(r"\\\[(?P<body>.*?)\\\]", re.DOTALL)
INLINE_RE = re.compile(
    r"(?P<reference>\\hyperref\[(?P<label>[^\]]+)\]\{(?P<display>[^{}]*)\})"
    r"|(?P<style>\\(?P<command>emph|textbf|texttt)\{(?P<style_value>[^{}]*)\})"
    r"|(?P<dollar>\$(?P<dollar_value>[^$]+)\$)"
    r"|(?P<paren>\\\((?P<paren_value>.*?)\\\))",
    re.DOTALL,
)
FORMAL_INNER_RE = re.compile(
    r"\\begin\{(?P<env>definition|axiom|theorem|lemma|proposition|corollary)\}"
    r"(?:\[(?P<title>[^\]]*)\])?(?P<body>.*?)\\end\{(?P=env)\}",
    re.DOTALL,
)
REMARK_RE = re.compile(
    r"\\begin\{remark\*\}\[(?P<title>[^\]]+)\](?P<body>.*?)\\end\{remark\*\}",
    re.DOTALL,
)
DEPENDENCIES_RE = re.compile(r"\\begin\{dependencies\}(?P<body>.*?)\\end\{dependencies\}", re.DOTALL)
PROOF_RE = re.compile(
    r"\\begin\{proof\}\[(?P<title>[^\]]+)\]\s*\\LRAProofBodyStart\s*"
    r"(?P<body>.*?)\\end\{proof\}",
    re.DOTALL,
)
DESCRIPTION_RE = re.compile(r"\\begin\{description\}(?P<body>.*?)\\end\{description\}", re.DOTALL)
DESCRIPTION_ITEM_RE = re.compile(
    r"\\item\[(?P<title>[^\]]+)\](?P<body>.*?)(?=\\item\[|\Z)",
    re.DOTALL,
)
EXTRA_SUPPORT_KEYS = set(DECORATION_ORDER) - {
    "proof_link",
    "standard quantified statement",
    "interpretation",
    "notation",
    "historical note",
    "source comparison",
    "exposition",
    "dependencies",
}


def _formal(sample: FormalSample) -> FormalBlock:
    matches = [block for block in formal_blocks_for_file(sample.path) if block.label == sample.label]
    assert len(matches) == 1, f"expected one live block for {sample.label}: {sample.path}"
    return matches[0]


def _plain_title(value: str) -> str:
    value = value.replace(r"$\mathbb{R}$", "the Real Numbers")
    value = value.replace("$", "")
    value = value.replace(r"\(", "").replace(r"\)", "")
    value = re.sub(r"\\(?:mathbb|mathcal|mathrm|operatorname)\{([^{}]+)\}", r"\1", value)
    return " ".join(value.split())


def _paragraphs(text: str) -> list[dict]:
    description = DESCRIPTION_RE.search(text)
    if description:
        blocks = _paragraphs_optional(text[: description.start()])
        items = [
            {
                "title": _plain_title(match.group("title").rstrip(".")),
                "body": _paragraphs(match.group("body")),
            }
            for match in DESCRIPTION_ITEM_RE.finditer(description.group("body"))
        ]
        assert items
        blocks.append({"type": "description", "items": items})
        blocks.extend(_paragraphs_optional(text[description.end() :]))
        return blocks
    return _paragraphs_optional(text)


def _paragraphs_optional(text: str) -> list[dict]:
    blocks: list[dict] = []
    cursor = 0
    for display in DISPLAY_RE.finditer(text):
        blocks.extend(_text_paragraphs(text[cursor : display.start()]))
        blocks.append({"type": "display_math", "value": display.group("body").strip()})
        cursor = display.end()
    blocks.extend(_text_paragraphs(text[cursor:]))
    return blocks


def _text_paragraphs(text: str) -> list[dict]:
    return [_inline(part) for part in re.split(r"\n\s*\n", text) if " ".join(part.split())]


def _inline(text: str) -> dict:
    segments: list[dict] = []
    cursor = 0
    for match in INLINE_RE.finditer(text):
        _append_text(segments, text[cursor : match.start()])
        if match.group("reference"):
            segments.append(
                {
                    "type": "reference",
                    "label": match.group("label"),
                    "display": " ".join(match.group("display").split()),
                }
            )
        elif match.group("style"):
            segment_type = {"emph": "emphasis", "textbf": "strong", "texttt": "code"}[
                match.group("command")
            ]
            segments.append(
                {"type": segment_type, "value": " ".join(match.group("style_value").split())}
            )
        else:
            value = match.group("dollar_value") or match.group("paren_value")
            segments.append({"type": "math", "value": value.strip()})
        cursor = match.end()
    _append_text(segments, text[cursor:])
    assert segments
    return {"segments": segments}


def _append_text(segments: list[dict], value: str) -> None:
    value = " ".join(value.split())
    if value:
        segments.append({"type": "text", "value": value})


def _inner(block: FormalBlock) -> tuple[str, str]:
    match = FORMAL_INNER_RE.fullmatch(block.body.strip())
    assert match
    body = re.sub(r"\\label\{[^{}]+\}", "", match.group("body"))
    body = re.sub(r"\\(?:smallskip|noindent)\b", "", body)
    body = re.sub(
        r"\\hyperref\[prf:[^\]]+\]\{(?:\\textit\{)?Go to proof\.(?:\})?\}",
        "",
        body,
        flags=re.IGNORECASE,
    )
    return _plain_title(match.group("title") or block.title or block.label), body.strip()


def _remark(decoration: str, title: str) -> list[dict]:
    matches = [match for match in REMARK_RE.finditer(decoration) if match.group("title").lower() == title.lower()]
    assert matches, f"live full block lacks {title}"
    return _paragraphs(matches[-1].group("body"))


def _support_blocks(decoration: str) -> list[dict]:
    support = []
    for match in REMARK_RE.finditer(decoration):
        key = match.group("title").strip().lower()
        if key == "non examples":
            key = "non-examples"
        if key not in EXTRA_SUPPORT_KEYS:
            continue
        support.append({"type": key.replace("-", "_").replace(" ", "_"), "body": _paragraphs(match.group("body"))})
    return support


def _dependencies(decoration: str, *, kind: str) -> dict:
    matches = list(DEPENDENCIES_RE.finditer(decoration))
    if matches:
        records = [
            {"label": label, "display": " ".join(display.split())}
            for label, display in re.findall(r"\\hyperref\[([^\]]+)\]\{([^{}]+)\}", matches[-1].group("body"))
        ]
        assert records
        return {"mode": "explicit", "records": records}
    if r"\DefinitionalRoot" in decoration:
        return {"mode": "definitional-root", "records": []}
    assert r"\NoLocalDependencies" in decoration
    mode = "definitional-root" if kind == "definition" else "no-local"
    return {"mode": mode, "records": []}


def _formal_artifact(sample: FormalSample) -> dict:
    block = _formal(sample)
    title, body = _inner(block)
    common = {
        "id": sample.label.replace(":", "-"),
        "title": title,
        "label": sample.label,
        "registry_ids": list(sample.registry_ids),
        "standard_form": _remark(block.decoration, "Standard quantified statement"),
        "interpretation": _remark(block.decoration, "Interpretation"),
        "support_blocks": _support_blocks(block.decoration),
        "dependencies": _dependencies(block.decoration, kind=block.env),
        "boxed": True,
    }
    if block.env == "axiom":
        artifact = {**common, "kind": "axiom", "statement": _paragraphs(body)}
        return _canonicalize_registry_math(artifact, sample.registry_ids)
    if block.env == "definition":
        artifact = {
            **common,
            "kind": "definition",
            "defined_term": title,
            "defining_condition": _paragraphs(body),
        }
        return _canonicalize_registry_math(artifact, sample.registry_ids)
    artifact = {
        **common,
        "kind": "theorem",
        "subtype": block.env,
        "hypotheses": [],
        "conclusion": _paragraphs(body),
        "proof_stub": True,
    }
    return _canonicalize_registry_math(artifact, sample.registry_ids)


def _canonicalize_registry_math(value, registry_ids: tuple[str, ...]):
    """Apply only representations explicitly owned by selected registries."""
    structures = yaml.safe_load((ROOT / "structures.yaml").read_text(encoding="utf-8"))["structures"]
    selected = {entry["id"]: entry for entry in structures if entry.get("id") in registry_ids}
    replacements = {
        rf"\operatorname{{{entry['name']}}}": entry["constructor"]
        for entry in selected.values()
        if entry.get("name") and entry.get("constructor")
    }

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") in {"math", "display_math"}:
                for old, new in replacements.items():
                    node["value"] = node["value"].replace(old, new)
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(value)
    return value


def _proof_artifact(sample: ProofSample, statement: dict) -> dict:
    text = sample.proof_path.read_text(encoding="utf-8")
    proof_blocks = {match.group("title"): match.group("body") for match in PROOF_RE.finditer(text)}
    assert {"Professional Standard Proof", "Detailed Learning Proof"} <= set(proof_blocks)
    structure = _remark(text, "Proof structure")
    return {
        "id": statement["label"].replace(":", "-") + "-proof",
        "kind": "proof",
        "title": statement["title"],
        "theorem_label": statement["label"],
        "theorem_subtype": statement["subtype"],
        "proof_label": "prf:" + statement["label"].split(":", 1)[1],
        "registry_ids": list(statement.get("registry_ids", [])),
        "restatement": copy.deepcopy(statement["conclusion"]),
        "professional_proof": _paragraphs(proof_blocks["Professional Standard Proof"]),
        "detailed_steps": [
            {"title": "Detailed proof", "body": _paragraphs(proof_blocks["Detailed Learning Proof"])}
        ],
        "proof_structure": structure,
        "dependencies": _dependencies(text, kind="proof"),
    }


def _assert_support_roundtrip(artifact: dict, rendered: str) -> None:
    positions = []
    for support in artifact["support_blocks"]:
        key = support["type"].replace("_", " ")
        title = ("non-examples" if key == "non examples" else key).title()
        marker = f"\\begin{{remark*}}[{title}]"
        assert rendered.count(marker) == 1
        positions.append(rendered.index(marker))
    assert positions == sorted(positions)


@pytest.mark.parametrize("sample", AXIOMS, ids=lambda sample: sample.label)
def test_four_live_axiom_full_blocks_are_representable(sample: FormalSample):
    artifact = _formal_artifact(sample)
    payload = {"schema_version": 1, "artifacts": [artifact]}
    validate_payload(payload)
    first = render_combined(payload)
    second = render_combined(copy.deepcopy(payload))
    assert first.encode("ascii") == second.encode("ascii")
    assert r"\begin{axiombox}" in first
    assert "Standard quantified statement" in first and "Interpretation" in first
    _assert_support_roundtrip(artifact, first)


def test_live_legacy_predicate_arity_is_detected_instead_of_normalized():
    artifact = _formal_artifact(LEGACY_ARITY_SAMPLE)
    payload = {"schema_version": 1, "artifacts": [artifact]}

    with pytest.raises(MathematicalContentError, match="LeastUpperBound has 2 argument.*expects 3"):
        validate_payload(payload)


@pytest.mark.parametrize("sample", DEFINITIONS, ids=lambda sample: sample.label)
def test_four_live_definition_full_blocks_are_representable(sample: FormalSample):
    artifact = _formal_artifact(sample)
    payload = {"schema_version": 1, "artifacts": [artifact]}
    validate_payload(payload)
    rendered = render_combined(payload)
    assert r"\begin{definitionbox}" in rendered
    assert artifact["label"] in rendered
    assert artifact["dependencies"]["mode"] in {"explicit", "definitional-root"}
    _assert_support_roundtrip(artifact, rendered)


@pytest.mark.parametrize("sample", PROOFS, ids=lambda sample: sample.statement.label)
def test_four_live_theorem_and_full_proof_pairs_populate_canonical_stubs(sample: ProofSample):
    source_proof = sample.proof_path.read_text(encoding="utf-8")
    source_errors = [finding for finding in validate_proof_text(source_proof) if finding.severity == "error"]
    assert not source_errors

    statement = _formal_artifact(sample.statement)
    proof = _proof_artifact(sample, statement)
    statement_payload = {"schema_version": 1, "artifacts": [statement]}
    proof_payload = {"schema_version": 1, "artifacts": [proof]}
    validate_payload(statement_payload)
    validate_payload(proof_payload)

    statement_tex = render_combined(statement_payload)
    _assert_support_roundtrip(statement, statement_tex)

    stub = render_requested_proof_stubs(statement_payload)[0].tex
    populated = populate_proof_stub(stub, proof)
    repeated = populate_proof_stub(stub, copy.deepcopy(proof))
    assert populated.encode("ascii") == repeated.encode("ascii")
    assert "TODO:" not in populated
    assert not [finding for finding in validate_proof_text(populated) if finding.severity == "error"]
