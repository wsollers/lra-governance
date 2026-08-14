from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools" / "governance"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from generators.mathematical_tex import (  # noqa: E402
    MathematicalContentError,
    load_schema,
    populate_proof_stub,
    render_combined,
    render_payload,
    render_requested_proof_stubs,
    validate_contract_sync,
    validate_payload,
    write_artifacts,
)
from generators.proof_stub import render_proof_stub  # noqa: E402
from validators.proof_file_contract import validate_text as validate_proof_text  # noqa: E402


def paragraph(*segments: tuple[str, str] | str) -> list[dict]:
    rendered = []
    for segment in segments:
        if isinstance(segment, str):
            rendered.append({"type": "text", "value": segment})
        else:
            rendered.append({"type": segment[0], "value": segment[1]})
    return [{"segments": rendered}]


def display(value: str) -> list[dict]:
    return [{"type": "display_math", "value": value}]


def root(records: list[dict] | None = None, mode: str = "explicit") -> dict:
    return {"mode": mode, "records": records or []}


def monotone_definition() -> dict:
    return {
        "id": "monotone-increasing",
        "kind": "definition",
        "title": "Monotone Increasing",
        "label": "def:monotone-increasing",
        "defined_term": "monotone increasing",
        "defining_condition": paragraph(
            "A function ",
            ("math", "f:A\\to\\mathbb{R}"),
            " is monotone increasing when ",
            ("math", "x≤y\\Longrightarrow f(x)≤f(y)"),
            ".",
        ),
        "standard_form": display(r"\forall x,y\in A\;\bigl(x\leq y\Longrightarrow f(x)\leq f(y)\bigr)"),
        "interpretation": paragraph("The function preserves the order of its inputs."),
        "dependencies": root(mode="definitional-root"),
        "boxed": False,
        "output_path": "notes/order/def-monotone-increasing.tex",
    }


def bolzano_weierstrass(*, subtype: str = "theorem") -> dict:
    prefix = {"theorem": "thm", "lemma": "lem", "proposition": "prop", "corollary": "cor"}[subtype]
    return {
        "id": f"bolzano-weierstrass-{subtype}",
        "kind": "theorem",
        "subtype": subtype,
        "title": "Bolzano--Weierstrass",
        "label": f"{prefix}:bolzano-weierstrass-{subtype}",
        "hypotheses": [paragraph("Let ", ("math", "(x_n)"), " be a bounded sequence in ", ("math", "\\mathbb{R}"), ".")],
        "conclusion": paragraph("Then ", ("math", "(x_n)"), " has a convergent subsequence."),
        "standard_form": display(r"(x_n)\text{ bounded}\Longrightarrow\exists (x_{n_k})\text{ convergent}"),
        "interpretation": paragraph("Bounded real sequences cannot avoid all sequential accumulation."),
        "dependencies": root([{"label": "def:bounded-sequence", "display": "Bounded sequence"}]),
        "boxed": subtype == "theorem",
        "proof_stub": subtype == "theorem",
    }


def full_proof() -> dict:
    return {
        "id": "identity-proof",
        "kind": "proof",
        "title": "Identity Result",
        "theorem_label": "thm:identity-result",
        "theorem_subtype": "theorem",
        "proof_label": "prf:identity-result",
        "restatement": paragraph("For every ", ("math", "x\\in\\mathbb{R}"), ", one has ", ("math", "x=x"), "."),
        "professional_proof": paragraph("Reflexivity of equality gives ", ("math", "x=x"), "."),
        "detailed_steps": [
            {"title": "Step 1", "body": paragraph("Fix ", ("math", "x\\in\\mathbb{R}"), ".")},
            {"title": "Step 2", "body": paragraph("Apply reflexivity to obtain ", ("math", "x=x"), ".")},
        ],
        "proof_structure": paragraph("The proof is a direct application of reflexivity."),
        "dependencies": root(mode="no-local"),
    }


def payload(*artifacts: dict) -> dict:
    return {"schema_version": 1, "artifacts": list(artifacts)}


def test_monotone_increasing_definition_contract_and_unicode_math():
    tex = render_combined(payload(monotone_definition()))
    assert r"\begin{definition}[Monotone Increasing]" in tex
    assert r"\begin{definitionbox}" not in tex
    assert r"x\leq y\Longrightarrow f(x)\leq f(y)" in tex
    assert "≤" not in tex
    assert tex.endswith("\n")


def test_bolzano_weierstrass_theorem_family_artifact():
    tex = render_combined(payload(bolzano_weierstrass()))
    assert r"\begin{theorem}[Bolzano--Weierstrass]" in tex
    assert r"\begin{theorembox}{Theorem (Bolzano--Weierstrass)}" in tex
    assert r"\begin{tcolorbox}" not in tex
    assert r"\label{thm:bolzano-weierstrass-theorem}" in tex
    assert r"\hyperref[prf:bolzano-weierstrass-theorem]" in tex


@pytest.mark.parametrize("subtype", ["lemma", "proposition", "corollary"])
def test_theorem_subtype_is_preserved(subtype: str):
    tex = render_combined(payload(bolzano_weierstrass(subtype=subtype)))
    assert f"\\begin{{{subtype}}}[Bolzano--Weierstrass]" in tex
    assert f"\\end{{{subtype}}}" in tex


def test_example_contract():
    artifact = {
        "id": "constant-sequence-example",
        "kind": "example",
        "title": "A Constant Sequence",
        "setup": paragraph("Let ", ("math", "x_n=3"), " for every ", ("math", "n\\in\\mathbb{N}"), "."),
        "calculation": [r"\lim_{n\to\infty}x_n=3"],
        "explanation": paragraph("The sequence converges to its constant value."),
    }
    tex = render_combined(payload(artifact))
    assert r"\begin{example}[A Constant Sequence]" in tex
    assert r"\lim_{n\to\infty}x_n=3" in tex


def test_exposition_motivation_contract():
    artifact = {
        "id": "compactness-motivation",
        "kind": "exposition",
        "subtype": "motivation",
        "title": "Motivation",
        "body": paragraph("Compactness turns global boundedness into local convergence information."),
    }
    tex = render_combined(payload(artifact))
    assert tex.startswith(r"\begin{remark*}[Motivation]")


def test_full_proof_is_authored_and_uses_canonical_layers():
    tex = render_combined(payload(full_proof()))
    assert "TODO" not in tex
    assert tex.count(r"\LRAProofBodyStart") == 2
    assert r"\begin{proof}[Professional Standard Proof]" in tex
    assert r"\begin{proof}[Detailed Learning Proof]" in tex
    assert not [finding for finding in validate_proof_text(tex) if finding.severity == "error"]


def test_deterministic_proof_stub_post_step():
    value = payload(bolzano_weierstrass())
    first = render_requested_proof_stubs(value)
    second = render_requested_proof_stubs(copy.deepcopy(value))
    assert first == second
    assert len(first) == 1
    assert "TODO: supply the compact professional proof." in first[0].tex
    assert first[0].output_path == "prf-bolzano-weierstrass-theorem.tex"


def test_full_proof_populates_durable_stub_in_place():
    artifact = full_proof()
    restatement = r"For every $x\in\mathbb{R}$, one has $x=x$."
    stub = render_proof_stub(
        "theorem",
        "identity-result",
        "Identity Result",
        restatement,
        statement_label="thm:identity-result",
    )
    populated = populate_proof_stub(stub, artifact)
    assert "TODO" not in populated
    assert r"\LRAProofFor{thm:identity-result}" in populated
    assert restatement in populated
    assert "Reflexivity of equality gives" in populated
    assert not [finding for finding in validate_proof_text(populated) if finding.severity == "error"]


def test_multiple_blocks_preserve_request_order():
    example = {
        "id": "order-example",
        "kind": "example",
        "title": "Order Example",
        "setup": paragraph("The identity function is monotone increasing."),
    }
    rendered = render_payload(payload(monotone_definition(), bolzano_weierstrass(), example))
    assert [item.artifact_id for item in rendered] == [
        "monotone-increasing",
        "bolzano-weierstrass-theorem",
        "order-example",
    ]


def test_model_theory_uses_lazy_specialization_and_canonical_registry():
    artifact = {
        "id": "language-example",
        "kind": "example",
        "title": "A First-Order Language",
        "registry_ids": ["struct:first-order-language"],
        "setup": paragraph("Let ", ("math", "L\\in\\mathsf{FirstOrderLanguage}"), "."),
    }
    tex = render_combined(payload(artifact))
    assert r"\mathsf{FirstOrderLanguage}" in tex
    specialization = ROOT / "capabilities" / "author-mathematics" / "model-theory-universal-algebra.md"
    assert "structures.yaml" in specialization.read_text(encoding="utf-8")


def test_malformed_payload_is_rejected():
    malformed = bolzano_weierstrass()
    del malformed["conclusion"]
    with pytest.raises(MathematicalContentError, match="schema validation failed"):
        validate_payload(payload(malformed))


def test_repeated_rendering_is_byte_identical():
    value = payload(monotone_definition(), bolzano_weierstrass())
    assert render_combined(value).encode("ascii") == render_combined(copy.deepcopy(value)).encode("ascii")


def test_tex_escaping_labels_dependencies_macros_and_unicode():
    artifact = monotone_definition()
    artifact["title"] = "Growth & Order_Theory"
    artifact["interpretation"] = paragraph("Values rise – never fall; 100% order-safe.")
    artifact["dependencies"] = root(
        [{"label": "def:ordered-set", "display": "Order & carrier"}]
    )
    tex = render_combined(payload(artifact))
    assert r"Growth \& Order\_Theory" in tex
    assert "rise -- never fall; 100\\% order-safe" in tex
    assert r"\hyperref[def:ordered-set]{Order \& carrier}" in tex
    assert r"\label{def:monotone-increasing}" in tex


def test_unselected_governed_macro_is_rejected():
    artifact = {
        "id": "language-example",
        "kind": "example",
        "title": "Language",
        "setup": paragraph(("math", "L=\\mathsf{FirstOrderLanguage}(C,F,R)")),
    }
    with pytest.raises(MathematicalContentError, match="unselected canonical structure"):
        validate_payload(payload(artifact))


def test_selected_predicate_arity_and_typed_arguments_are_validated():
    artifact = monotone_definition()
    artifact["registry_ids"] = ["pred:is-lipschitz"]
    artifact["standard_form"] = display(
        r"\operatorname{IsLipschitz}(f,A,\mathbb{R},\mathbb{R},K)"
    )
    validate_payload(payload(artifact))

    artifact["standard_form"] = display(
        r"\operatorname{IsLipschitz}(f,A,\mathbb{R},\mathbb{R})"
    )
    with pytest.raises(MathematicalContentError, match="expects 5"):
        validate_payload(payload(artifact))

    artifact["standard_form"] = display(
        r"\operatorname{IsLipschitz}(f,A,\mathbb{R},\mathbb{R},\mathbb{R})"
    )
    with pytest.raises(MathematicalContentError, match="expects scalar"):
        validate_payload(payload(artifact))


def test_schema_renderer_validator_drift_is_detected():
    schema = load_schema()
    schema["$defs"]["common"]["properties"]["kind"]["enum"].append("exercise")
    with pytest.raises(MathematicalContentError, match="schema/renderer kind drift"):
        validate_contract_sync(schema)


def test_payload_schema_is_valid_draft_2020_12():
    Draft202012Validator.check_schema(load_schema())


def test_file_behavior_is_atomic_and_no_overwrite(tmp_path: Path):
    rendered = render_payload(payload(monotone_definition()))
    paths = write_artifacts(rendered, tmp_path)
    assert paths == [tmp_path / "notes" / "order" / "def-monotone-increasing.tex"]
    assert paths[0].read_bytes() == rendered[0].tex.encode("ascii")
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        write_artifacts(rendered, tmp_path)


def test_uncertainty_is_explicit_not_silently_discarded():
    artifact = {
        "id": "source-summary",
        "kind": "exposition",
        "subtype": "summary",
        "body": paragraph("The source appears to use sequential compactness."),
        "dependencies": root([{"label": "def:compactness", "display": "Compactness"}]),
        "source": {"attribution": "Source screenshot", "context": "Theorem margin note"},
        "uncertainty": {"status": "uncertain", "note": "The screenshot omits the preceding hypothesis."},
    }
    tex = render_combined(payload(artifact))
    assert "% UNCERTAINTY: The screenshot omits the preceding hypothesis." in tex
    assert "% SOURCE: attribution=Source screenshot | context=Theorem margin note" in tex
    assert r"\hyperref[def:compactness]{Compactness}" in tex


def test_typed_reference_emphasis_and_support_blocks_use_canonical_order():
    artifact = monotone_definition()
    artifact["support_blocks"] = [
        {
            "type": "predicate_reading",
            "body": display(r"\forall x,y\in A\;(x\leq y\Longrightarrow f(x)\leq f(y))"),
        }
    ]
    artifact["interpretation"] = [
        {
            "segments": [
                {"type": "emphasis", "value": "Order preservation"},
                {"type": "text", "value": " uses "},
                {"type": "reference", "label": "def:ordered-set", "display": "ordered sets"},
                {"type": "text", "value": "."},
            ]
        }
    ]
    tex = render_combined(payload(artifact))
    assert r"\emph{Order preservation} uses \hyperref[def:ordered-set]{ordered sets}." in tex
    assert tex.index("Standard quantified statement") < tex.index("Predicate Reading") < tex.index("Interpretation")


def test_support_block_relationships_are_validated_from_shared_contract():
    artifact = monotone_definition()
    artifact["support_blocks"] = [
        {
            "type": "negated_quantified_statement",
            "body": display(r"\exists x,y\in A\;(x\leq y\land f(x)>f(y))"),
        }
    ]
    with pytest.raises(MathematicalContentError, match="requires negation predicate reading"):
        validate_payload(payload(artifact))
