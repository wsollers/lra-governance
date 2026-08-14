from __future__ import annotations

import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONSTITUTION = ROOT / "constitution"
if str(CONSTITUTION) not in sys.path:
    sys.path.insert(0, str(CONSTITUTION))

from auditor.audits.proof import _find_source_statement, _todo_stub_report  # noqa: E402
from auditor.audits import proof as proof_audit  # noqa: E402
from auditor.audits.statement import _extract_environment_and_remarks  # noqa: E402
from auditor.audits import statement as statement_audit  # noqa: E402
from auditor.audits import stub as stub_audit  # noqa: E402
from auditor.audits.symbols import _collect_chapter_tex  # noqa: E402
from auditor.generators import capstone as capstone_generator  # noqa: E402
from auditor.scanner import scan_chapter  # noqa: E402
from generators.chapter_stub import stub_chapter  # noqa: E402


def test_statement_extraction_includes_canonical_dependency_environment():
    tex = r"""
\begin{theorem}[Result]
\label{thm:result}
Body.
\end{theorem}

\begin{remark*}[Interpretation]
Meaning.
\end{remark*}

\begin{dependencies}
\begin{itemize}
\item \hyperref[def:input]{Input}
\end{itemize}
\end{dependencies}

\section{Next}
"""
    block = _extract_environment_and_remarks(tex, "thm:result")
    assert block is not None
    assert r"\begin{dependencies}" in block
    assert r"\hyperref[def:input]" in block
    assert r"\section{Next}" not in block


def test_statement_extraction_includes_no_local_dependencies_marker():
    tex = r"""
\begin{axiom}[Root]
\label{ax:root}
Body.
\end{axiom}
\NoLocalDependencies
"""
    block = _extract_environment_and_remarks(tex, "ax:root")
    assert block is not None
    assert block.rstrip().endswith(r"\NoLocalDependencies")


def test_statement_extraction_includes_definitional_root_marker():
    tex = r"""
\begin{definition}[Primitive]
\label{def:primitive-object}
Body.
\end{definition}
\DefinitionalRoot
"""
    block = _extract_environment_and_remarks(tex, "def:primitive-object")
    assert block is not None
    assert block.rstrip().endswith(r"\DefinitionalRoot")


def _complete_statement_tex() -> str:
    return r"""
\begin{theorem}[Result]
\label{thm:result}
If $P$, then $Q$.
\hyperref[prf:result]{\textit{Go to proof.}}
\end{theorem}
\begin{remark*}[Standard quantified statement]
\[
P\Longrightarrow Q.
\]
\end{remark*}
\begin{remark*}[Interpretation]
The conclusion follows whenever the hypothesis holds.
\end{remark*}
\begin{dependencies}
\begin{itemize}
\item \hyperref[def:input-object]{Input object}
\end{itemize}
\end{dependencies}
"""


def test_statement_structural_only_audit_does_not_call_model(tmp_path, monkeypatch):
    tex_path = tmp_path / "statement.tex"
    tex_path.write_text(_complete_statement_tex(), encoding="utf-8")

    def reject_model_call(*_args, **_kwargs):
        raise AssertionError("structural-only statement audit must not call a model")

    monkeypatch.setattr(statement_audit.client, "call", reject_model_call)
    monkeypatch.setattr(
        statement_audit,
        "save_audit_report",
        lambda *_args, **_kwargs: tmp_path / "audit-statement.md",
    )
    report = statement_audit.audit_statement(
        tex_path,
        "thm:result",
        "thm",
        "chapter",
        semantic_review=False,
        print_report=False,
    )

    assert report["summary"]["failed"] == 0
    assert report["checks"] == [
        {
            "block_id": "deterministic_statement_structure",
            "requirement": "R",
            "status": "PASS",
            "finding": "",
        }
    ]


def test_statement_local_preflight_enforces_dependency_and_proof_navigation():
    block = r"""
\begin{theorem}[Result]
\label{thm:result}
If $P$, then $Q$.
\end{theorem}
\begin{remark*}[Standard quantified statement]
\[P\Longrightarrow Q.\]
\end{remark*}
\begin{remark*}[Interpretation]
The conclusion follows from the hypothesis.
\end{remark*}
"""
    report = statement_audit._deterministic_structure_report(
        block,
        label="thm:result",
        artifact_type="thm",
    )
    codes = {check["block_id"] for check in report["checks"]}
    assert "missing_go_to_proof_link" in codes
    assert "missing_dependencies" in codes


def test_statement_local_preflight_checks_canonical_dependency_environment():
    block = _complete_statement_tex().replace("def:input-object", "prf:input-object")
    report = statement_audit._deterministic_structure_report(
        block,
        label="thm:result",
        artifact_type="thm",
    )
    codes = {check["block_id"] for check in report["checks"]}
    assert "proof_label_in_dependencies" in codes


def test_statement_semantic_review_receives_compact_block_without_registries(tmp_path, monkeypatch):
    tex_path = tmp_path / "statement.tex"
    tex_path.write_text(_complete_statement_tex(), encoding="utf-8")
    captured: dict[str, str] = {}
    check_ids = list(statement_audit._SEMANTIC_CHECK_REQUIREMENTS)

    monkeypatch.setattr(statement_audit.loader, "prompt", lambda _name: "SEMANTIC ONLY")

    def fake_call(system, user, *, expect_json, validate_report):
        captured["system"] = system
        captured["user"] = user
        assert expect_json is True
        assert validate_report is False
        return {
            "judgments": [
                {
                    "check_id": check_id,
                    "status": "NOT_APPLICABLE"
                    if statement_audit._SEMANTIC_CHECK_REQUIREMENTS[check_id] == "C"
                    else "PASS",
                    "finding": "",
                }
                for check_id in check_ids
            ]
        }

    monkeypatch.setattr(statement_audit.client, "call", fake_call)
    monkeypatch.setattr(
        statement_audit,
        "save_audit_report",
        lambda *_args, **_kwargs: tmp_path / "audit-statement.md",
    )
    report = statement_audit.audit_statement(
        tex_path,
        "thm:result",
        "thm",
        "chapter",
        print_report=False,
    )

    assert captured["system"] == "SEMANTIC ONLY"
    assert "block-registry" not in captured["user"]
    assert "artifact-matrix" not in captured["user"]
    assert r"\begin{theorem}" in captured["user"]
    assert [check["block_id"] for check in report["checks"][-7:]] == check_ids
    assert report["summary"]["conditional_unmet"] == 4


def test_statement_semantic_review_rejects_missing_checks():
    try:
        statement_audit._semantic_judgment_report(
            {"judgments": []},
            label="thm:result",
            artifact_type="thm",
        )
    except RuntimeError as error:
        assert "omitted required checks" in str(error)
    else:
        raise AssertionError("missing semantic checks must be rejected")


def test_statement_semantic_conditional_failure_uses_canonical_status():
    judgments = []
    for check_id, requirement in statement_audit._SEMANTIC_CHECK_REQUIREMENTS.items():
        status = "PASS"
        finding = ""
        if requirement == "C":
            status = "NOT_APPLICABLE"
        if check_id == "negation_correctness":
            status = "FAIL"
            finding = "The displayed quantifier was not dualized."
        judgments.append({"check_id": check_id, "status": status, "finding": finding})

    report = statement_audit._semantic_judgment_report(
        {"judgments": judgments},
        label="thm:result",
        artifact_type="thm",
    )
    negation = next(check for check in report["checks"] if check["block_id"] == "negation_correctness")
    assert negation["status"] == "CONDITIONAL_VIOLATION"
    assert report["summary"]["conditional_violation"] == 1


def test_symbol_collection_uses_current_recursive_notes_and_proofs_trees(tmp_path):
    chapter = tmp_path / "chapter"
    note = chapter / "notes" / "topic" / "note.tex"
    proof = chapter / "proofs" / "topic" / "prf-result.tex"
    exercise = chapter / "proofs" / "exercises" / "capstone-chapter.tex"
    index = chapter / "proofs" / "topic" / "index.tex"
    for path, content in (
        (note, "NOTE_CURRENT"),
        (proof, "PROOF_CURRENT"),
        (exercise, "CAPSTONE_CURRENT"),
        (index, "INDEX_MUST_NOT_BE_INCLUDED"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    collected = _collect_chapter_tex(chapter)
    assert "NOTE_CURRENT" in collected
    assert "PROOF_CURRENT" in collected
    assert "CAPSTONE_CURRENT" in collected
    assert "INDEX_MUST_NOT_BE_INCLUDED" not in collected
    assert collected.count("PROOF_CURRENT") == 1


def test_chapter_scanner_discovers_current_topic_proof_path(tmp_path):
    chapter = tmp_path / "chapter"
    note = chapter / "notes" / "topic" / "note.tex"
    proof = chapter / "proofs" / "topic" / "prf-result.tex"
    note.parent.mkdir(parents=True, exist_ok=True)
    proof.parent.mkdir(parents=True, exist_ok=True)
    note.write_text(
        r"\begin{theorem}[Result]\label{thm:result}Body.\end{theorem}",
        encoding="utf-8",
    )
    proof.write_text(
        r"\label{prf:result}\LRAProofFor{thm:result}"
        r"\hyperref[thm:result]{Return}",
        encoding="utf-8",
    )

    result = scan_chapter(chapter)
    assert [entry.file.replace("\\", "/") for entry in result.proof_files] == [
        "proofs/topic/prf-result.tex"
    ]
    assert result.proof_files[0].theorem_label == "thm:result"


def test_proof_source_context_is_resolved_from_current_notes_tree(tmp_path):
    chapter = tmp_path / "chapter"
    note = chapter / "notes" / "topic" / "note.tex"
    proof = chapter / "proofs" / "topic" / "prf-result.tex"
    note.parent.mkdir(parents=True, exist_ok=True)
    proof.parent.mkdir(parents=True, exist_ok=True)
    note.write_text(
        r"\begin{theorem}[Result]"
        r"\label{thm:result}Exact source statement."
        r"\end{theorem}",
        encoding="utf-8",
    )
    proof.write_text("", encoding="utf-8")

    context = _find_source_statement(proof, "thm:result")
    assert context is not None
    assert "Exact source statement." in context


def _write_full_proof_fixture(tmp_path: Path, *, include_body_starts: bool = True):
    chapter = tmp_path / "chapter"
    note = chapter / "notes" / "topic" / "result.tex"
    proof = chapter / "proofs" / "topic" / "prf-result-test.tex"
    note.parent.mkdir(parents=True)
    proof.parent.mkdir(parents=True)
    note.write_text(
        r"\begin{theorem}[Result]"
        r"\label{thm:result-test}If $P$, then $Q$."
        r"\end{theorem}",
        encoding="utf-8",
    )
    body_start = "\\LRAProofBodyStart\n" if include_body_starts else ""
    proof.write_text(
        "\n".join(
            [
                r"\newpage",
                r"\phantomsection",
                r"\label{prf:result-test}",
                r"\LRAProofFor{thm:result-test}",
                r"\begin{remark*}[Return]",
                r"\hyperref[thm:result-test]{Return to Result}",
                r"\end{remark*}",
                r"\begin{theorem*}[Result]",
                r"If $P$, then $Q$.",
                r"\end{theorem*}",
                r"\begin{proof}[Professional Standard Proof]",
                body_start + "Assume $P$. The hypothesis gives $Q$.",
                r"\end{proof}",
                r"\begin{proof}[Detailed Learning Proof]",
                body_start + r"\textbf{Step 1.} Assume $P$. The hypothesis gives $Q$.",
                r"\end{proof}",
                r"\begin{remark*}[Proof structure]",
                "This is a direct proof.",
                r"\end{remark*}",
                r"\begin{dependencies}",
                r"\NoLocalDependencies",
                r"\end{dependencies}",
                r"\clearpage",
            ]
        ),
        encoding="utf-8",
    )
    (chapter / "proofs" / "topic" / "index.tex").write_text(
        r"\input{proofs/topic/prf-result-test}",
        encoding="utf-8",
    )
    (chapter / "proofs" / "index.tex").write_text(
        r"\input{proofs/topic/index}",
        encoding="utf-8",
    )
    return chapter, proof


def test_proof_structural_only_audit_has_twelve_layers_without_model(tmp_path, monkeypatch):
    _chapter, proof = _write_full_proof_fixture(tmp_path)

    def reject_model_call(*_args, **_kwargs):
        raise AssertionError("structural-only proof audit must not call a model")

    monkeypatch.setattr(proof_audit.client, "call", reject_model_call)
    monkeypatch.setattr(
        proof_audit,
        "save_audit_report",
        lambda *_args, **_kwargs: tmp_path / "audit-proof.md",
    )
    report = proof_audit.audit_proof(
        proof,
        "chapter",
        semantic_review=False,
        print_report=False,
    )

    assert [check["block_id"] for check in report["checks"][:12]] == proof_audit._LAYER_IDS
    assert report["summary"]["failed"] == 0
    assert report["summary"]["conditional_unmet"] == 1


def test_proof_local_preflight_requires_both_body_start_markers(tmp_path):
    _chapter, proof = _write_full_proof_fixture(tmp_path, include_body_starts=False)
    layout = proof_audit._deterministic_layout_audit(proof)
    report = proof_audit._deterministic_proof_report(
        proof,
        layout,
        label="prf:result-test",
    )
    by_id = {check["block_id"]: check for check in report["checks"]}
    assert "missing_professional_proof_body_start" in by_id["layer8_professional_proof"]["finding"]
    assert "missing_detailed_proof_body_start" in by_id["layer9_detailed_proof"]["finding"]


def test_proof_semantic_review_receives_only_compact_extracted_fields(tmp_path, monkeypatch):
    _chapter, proof = _write_full_proof_fixture(tmp_path)
    captured = {}
    check_ids = list(proof_audit._SEMANTIC_CHECK_REQUIREMENTS)
    monkeypatch.setattr(proof_audit.loader, "prompt", lambda _name: "PROOF SEMANTICS")

    def fake_call(system, user, *, expect_json, validate_report):
        captured["system"] = system
        captured["user"] = user
        assert expect_json is True
        assert validate_report is False
        return {
            "judgments": [
                {
                    "check_id": check_id,
                    "status": "NOT_APPLICABLE"
                    if proof_audit._SEMANTIC_CHECK_REQUIREMENTS[check_id] == "C"
                    else "PASS",
                    "finding": "",
                }
                for check_id in check_ids
            ]
        }

    monkeypatch.setattr(proof_audit.client, "call", fake_call)
    monkeypatch.setattr(
        proof_audit,
        "save_audit_report",
        lambda *_args, **_kwargs: tmp_path / "audit-proof.md",
    )
    report = proof_audit.audit_proof(proof, "chapter", print_report=False)

    assert captured["system"] == "PROOF SEMANTICS"
    assert "Deterministic Layout Audit" not in captured["user"]
    assert "## Associated Source" in captured["user"]
    assert "## Professional Proof Body" in captured["user"]
    assert [check["block_id"] for check in report["checks"][-6:]] == check_ids


def test_proof_semantic_review_is_not_called_without_source_context(tmp_path, monkeypatch):
    _chapter, proof = _write_full_proof_fixture(tmp_path)
    (tmp_path / "chapter" / "notes" / "topic" / "result.tex").unlink()

    def reject_model_call(*_args, **_kwargs):
        raise AssertionError("proof semantic review must not run without source context")

    monkeypatch.setattr(proof_audit.client, "call", reject_model_call)
    monkeypatch.setattr(
        proof_audit,
        "save_audit_report",
        lambda *_args, **_kwargs: tmp_path / "audit-proof.md",
    )
    report = proof_audit.audit_proof(proof, "chapter", print_report=False)
    assert report["checks"][-1]["block_id"] == "semantic_source_context"
    assert report["checks"][-1]["status"] == "NONCOMPLIANT"


def test_noncompliant_todo_proof_does_not_call_semantic_model(tmp_path, monkeypatch):
    _chapter, proof = _write_full_proof_fixture(tmp_path, include_body_starts=False)
    text = proof.read_text(encoding="utf-8")
    text = text.replace("Assume $P$. The hypothesis gives $Q$.", "TODO: proof.")
    text = text.replace(
        r"\textbf{Step 1.} Assume $P$. The hypothesis gives $Q$.",
        "TODO: detailed proof.",
    )
    proof.write_text(text, encoding="utf-8")

    def reject_model_call(*_args, **_kwargs):
        raise AssertionError("TODO proof bodies must not be sent for mathematical review")

    monkeypatch.setattr(proof_audit.client, "call", reject_model_call)
    monkeypatch.setattr(
        proof_audit,
        "save_audit_report",
        lambda *_args, **_kwargs: tmp_path / "audit-proof.md",
    )
    report = proof_audit.audit_proof(proof, "chapter", print_report=False)
    assert report["summary"]["stub"] is True
    assert report["summary"]["failed"] >= 1


def test_compliant_stub_report_uses_twelve_layer_contract():
    report = _todo_stub_report("prf:result")
    assert report["summary"]["total_checks"] == 12
    assert len(report["checks"]) == 12
    assert report["checks"][3]["block_id"] == "layer4_proof_for"
    assert report["checks"][-1]["block_id"] == "layer12_clearpage"


def test_statement_schema_does_not_classify_section_toolkits_per_artifact():
    registry = yaml.safe_load(
        (ROOT / "constitution" / "schema" / "block-registry.yaml").read_text(encoding="utf-8")
    )
    matrix = yaml.safe_load(
        (ROOT / "constitution" / "schema" / "artifact-matrix.yaml").read_text(encoding="utf-8")
    )
    assert "toolkit_box" not in {block["id"] for block in registry["blocks"]}
    assert "toolkit_box" not in matrix["matrix"]


def test_stub_audit_is_deterministic_and_preserves_report_contract(tmp_path, monkeypatch):
    volume = tmp_path / "volume-ii"
    volume.mkdir()
    (volume / "index.tex").write_text("", encoding="utf-8")
    (volume / "main.tex").write_text("", encoding="utf-8")
    stub_chapter(volume, "ordered-fields", "Ordered Fields", [], [])

    def reject_model_call(*_args, **_kwargs):
        raise AssertionError("stub audit must not call a model")

    monkeypatch.setattr(stub_audit.client, "call", reject_model_call)
    monkeypatch.setattr(
        stub_audit,
        "save_audit_report",
        lambda *_args, **_kwargs: tmp_path / "audit-stub.md",
    )
    report = stub_audit.audit_stub_chapter(volume / "ordered-fields")

    assert report["audit_type"] == "stub_chapter"
    assert report["summary"]["failed"] == 0
    assert report["summary"]["passed"] == 1
    assert report["checks"][0]["block_id"] == "chapter_stub_contract"
    assert report["violations"] == []


def test_full_capstone_prompt_excludes_deterministic_stub_mode():
    capstone_prompt = (
        ROOT / "constitution" / "prompts" / "generate-capstone.md"
    ).read_text(encoding="utf-8")
    assert "used only for explicit full-capstone authoring" in capstone_prompt
    assert "STUB MODE" not in capstone_prompt
    assert "SOLUTION_KEY MODE" not in capstone_prompt


def _capstone_source_records() -> list[dict[str, str]]:
    return [
        {
            "label": "def:ordered-set",
            "type": "definition",
            "display_title": "Ordered Set",
            "statement_body": "A set $A$ equipped with an order $\\leq$ is an ordered set.",
            "source": "notes/order/ordered-set.tex",
        },
        {
            "label": "thm:maximum-principle",
            "type": "theorem",
            "display_title": "Maximum Principle",
            "statement_body": "Every finite nonempty ordered set has a maximal element.",
            "source": "notes/order/maximum-principle.tex",
        },
    ]


def _capstone_payload() -> dict[str, object]:
    return {
        "theorem": "Every finite nonempty ordered set admits a maximal element compatible with the stated order.",
        "what_it_says": "The order structure and finiteness combine to force an extremal element.",
        "architecture_of_proof": "Use the order definition to formulate maximality, then apply the maximum principle.",
        "components": [
            {
                "statement": "Identify the governing order structure.",
                "strategy": "Unpack the ordered-set definition.",
            },
            {
                "statement": "Produce the required extremal element.",
                "strategy": "Invoke the maximum principle after checking finiteness and nonemptiness.",
            },
        ],
        "scope_and_honest_limits": "Finiteness is load-bearing; no assertion is made for arbitrary infinite orders.",
        "instantiation_toward_program": "This supplies the finite-order model for later extremal arguments.",
    }


def test_capstone_source_extractor_reads_current_notes_without_router_text(tmp_path):
    chapter = tmp_path / "bounds"
    notes = chapter / "notes" / "order"
    notes.mkdir(parents=True)
    (chapter / "notes" / "index.tex").write_text("ROUTER_ONLY", encoding="utf-8")
    (notes / "results.tex").write_text(
        r"""
\begin{definition}[Ordered Set]
\label{def:ordered-set}
A set $A$ equipped with $\leq$ is ordered.
\end{definition}
\begin{theorem}[Maximum Principle]
\label{thm:maximum-principle}
Every finite nonempty ordered set has a maximal element.
\hyperref[prf:maximum-principle]{\textit{Go to proof.}}
\end{theorem}
""",
        encoding="utf-8",
    )
    records = capstone_generator.extract_chapter_source_records(chapter)
    assert [record["label"] for record in records] == [
        "def:ordered-set",
        "thm:maximum-principle",
    ]
    assert "ROUTER_ONLY" not in str(records)
    assert r"\label" not in records[0]["statement_body"]
    assert r"\hyperref" not in records[1]["statement_body"]


def test_full_capstone_request_rejects_unextracted_dependencies():
    try:
        capstone_generator.build_full_capstone_request(
            chapter_subject="bounds",
            chapter_display_title="Bounds",
            chapter_registry=[{"subject": "bounds", "display_title": "Bounds"}],
            chapter_environments=[],
            chapter_source_records=_capstone_source_records(),
            state_dependencies=[("def:missing", "Missing")],
            proof_dependencies=[("thm:maximum-principle", "Maximum Principle")],
        )
    except ValueError as error:
        assert "not a current-chapter source statement" in str(error)
    else:
        raise AssertionError("full capstone accepted an unextracted dependency")


def test_full_capstone_generation_uses_compact_sources_and_deterministic_renderer(monkeypatch):
    captured: dict[str, object] = {}
    monkeypatch.setattr(capstone_generator.loader, "prompt", lambda _name: "CAPSTONE AUTHOR")

    def fake_call(system, user, *, expect_json):
        captured.update(system=system, user=user, expect_json=expect_json)
        return _capstone_payload()

    monkeypatch.setattr(capstone_generator.client, "call", fake_call)
    latex = capstone_generator.generate_capstone(
        chapter_subject="bounds",
        chapter_display_title="Bounds",
        chapter_registry=[
            {"subject": "sets", "display_title": "Sets", "unused": "must not be sent"},
            {"subject": "bounds", "display_title": "Bounds", "unused": "must not be sent"},
            {"subject": "limits", "display_title": "Limits", "unused": "forbidden later chapter"},
        ],
        chapter_environments=[
            {"label": "def:ordered-set"},
            {"label": "thm:maximum-principle"},
        ],
        mode="full",
        state_dependencies=[("def:ordered-set", "Ordered Set")],
        proof_dependencies=[("thm:maximum-principle", "Maximum Principle")],
        chapter_source_records=_capstone_source_records(),
    )
    assert captured["system"] == "CAPSTONE AUTHOR"
    assert captured["expect_json"] is True
    assert '"subject": "limits"' not in str(captured["user"])
    assert "must not be sent" not in str(captured["user"])
    assert r"\label{cap:bounds}" in latex
    assert r"\label{prf:capstone-bounds}" not in latex
    assert latex.count(r"\begin{tcolorbox}") == 1
    assert r"\begin{remark*}[Dependencies to state]" in latex
    assert r"\begin{remark*}[Dependencies to prove]" in latex
    assert r"\begin{remark*}[Dependency ceiling]" in latex
    assert latex.rstrip().endswith(r"\clearpage")
    assert not [
        finding
        for finding in capstone_generator.validate_full_capstone_output(
            latex,
            capstone_generator.build_full_capstone_request(
                chapter_subject="bounds",
                chapter_display_title="Bounds",
                chapter_registry=[
                    {"subject": "sets", "display_title": "Sets"},
                    {"subject": "bounds", "display_title": "Bounds"},
                ],
                chapter_environments=[],
                chapter_source_records=_capstone_source_records(),
                state_dependencies=[("def:ordered-set", "Ordered Set")],
                proof_dependencies=[("thm:maximum-principle", "Maximum Principle")],
            ),
        )
        if finding["severity"] == "error"
    ]


def test_full_capstone_payload_cannot_override_renderer_structure():
    payload = _capstone_payload()
    payload["theorem"] = r"\label{cap:invented} Invented structure."
    try:
        capstone_generator.validate_authored_payload(payload)
    except ValueError as error:
        assert "caller-owned structural token" in str(error)
    else:
        raise AssertionError("capstone payload overrode deterministic structure")
