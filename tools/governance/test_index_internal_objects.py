from __future__ import annotations

from pathlib import Path

from tools.governance.index_internal_objects import build_index, build_match_report


def test_indexes_tex_formal_objects_and_skips_corrected_by_default(tmp_path: Path) -> None:
    root = tmp_path / "lra-volume-iii"
    artifact = root / "volume-iii" / "book-analysis-i" / "completeness" / "notes" / "completeness" / "thm-nested"
    artifact.mkdir(parents=True)
    (artifact / "source.tex").write_text(
        r"""
\section{Completeness}
\begin{theorem}[Nested Interval Theorem]
\label{thm:nested-interval-theorem}
Every nested sequence of nonempty closed bounded intervals has nonempty intersection.
\end{theorem}
\LeanFormalizes{thm:nested-interval-theorem}{lra-lean}{LRA.VolumeIII.Analysis.Completeness}{NestedIntervalTheorem}{pending}
""",
        encoding="utf-8",
    )
    (artifact / "corrected.tex").write_text(
        r"""
\begin{theorem}[Nested Interval Theorem Corrected]
\label{thm:nested-interval-theorem-corrected}
\end{theorem}
""",
        encoding="utf-8",
    )

    payload = build_index(tex_roots=[root], lean_roots=[], artifact_source="source")

    assert payload["counts"] == {"objects": 1, "tex": 1, "lean": 0}
    record = payload["objects"][0]
    assert record["object_id"] == "tex:thm:nested-interval-theorem"
    assert record["kind"] == "theorem"
    assert record["name"] == "Nested Interval Theorem"
    assert record["label"] == "thm:nested-interval-theorem"
    assert record["volume"] == "volume-iii"
    assert record["book"] == "book-analysis-i"
    assert record["chapter"] == "completeness"
    assert record["topic"] == "completeness"
    assert record["section_path"] == ["Completeness"]
    assert record["metadata"]["lean_formalizes"] == [
        {
            "label": "thm:nested-interval-theorem",
            "repo": "lra-lean",
            "module": "LRA.VolumeIII.Analysis.Completeness",
            "declaration": "NestedIntervalTheorem",
            "status": "pending",
        }
    ]


def test_indexes_lean_declarations_with_module_and_namespace(tmp_path: Path) -> None:
    root = tmp_path / "lra-lean"
    source = root / "LRA" / "VolumeIII" / "Analysis" / "Completeness.lean"
    source.parent.mkdir(parents=True)
    source.write_text(
        """
namespace LRA.VolumeIII.Analysis

def IsNestedInterval (I : Nat -> Set Real) : Prop :=
  True

theorem NestedIntervalTheorem {I : Nat -> Set Real} :
    IsNestedInterval I -> True := by
  intro _h
  trivial

end LRA.VolumeIII.Analysis
""",
        encoding="utf-8",
    )

    payload = build_index(tex_roots=[], lean_roots=[root], artifact_source="source")

    assert payload["counts"] == {"objects": 2, "tex": 0, "lean": 2}
    declarations = {record["name"]: record for record in payload["objects"]}
    assert declarations["IsNestedInterval"]["object_id"] == "lean:LRA.VolumeIII.Analysis.IsNestedInterval"
    assert declarations["IsNestedInterval"]["kind"] == "def"
    assert declarations["IsNestedInterval"]["volume"] == "VolumeIII"
    assert declarations["NestedIntervalTheorem"]["kind"] == "theorem"
    assert "IsNestedInterval I -> True" in declarations["NestedIntervalTheorem"]["statement"]
    assert declarations["NestedIntervalTheorem"]["metadata"]["leading_comment"] == ""
    assert declarations["NestedIntervalTheorem"]["metadata"]["has_sorry"] is False
    assert declarations["NestedIntervalTheorem"]["metadata"]["sorry_lines"] == []
    assert declarations["NestedIntervalTheorem"]["metadata"]["verification_status"] == "checked"


def test_indexes_lean_sorry_status_per_declaration(tmp_path: Path) -> None:
    root = tmp_path / "lra-lean"
    source = root / "LRA" / "VolumeIII" / "Analysis" / "Completeness.lean"
    source.parent.mkdir(parents=True)
    source.write_text(
        """
namespace LRA.VolumeIII.Analysis

theorem ProvenTheorem : True := by
  trivial

theorem IncompleteTheorem : True := by
  sorry

end LRA.VolumeIII.Analysis
""",
        encoding="utf-8",
    )

    payload = build_index(tex_roots=[], lean_roots=[root], artifact_source="source")

    declarations = {record["name"]: record for record in payload["objects"]}
    assert declarations["ProvenTheorem"]["metadata"]["has_sorry"] is False
    assert declarations["ProvenTheorem"]["metadata"]["verification_status"] == "checked"
    assert declarations["IncompleteTheorem"]["metadata"]["has_sorry"] is True
    assert declarations["IncompleteTheorem"]["metadata"]["sorry_lines"] == [8]
    assert declarations["IncompleteTheorem"]["metadata"]["verification_status"] == "incomplete"


def test_indexes_lean_sorry_status_ignores_comments_and_strings(tmp_path: Path) -> None:
    root = tmp_path / "lra-lean"
    source = root / "LRA" / "VolumeIII" / "Analysis" / "Completeness.lean"
    source.parent.mkdir(parents=True)
    source.write_text(
        '''
namespace LRA.VolumeIII.Analysis

/- This declaration mentions sorry in a comment. -/
def SorryWordInComment : String := "sorry in a string"

end LRA.VolumeIII.Analysis
''',
        encoding="utf-8",
    )

    payload = build_index(tex_roots=[], lean_roots=[root], artifact_source="source")

    record = payload["objects"][0]
    assert record["metadata"]["has_sorry"] is False
    assert record["metadata"]["sorry_lines"] == []
    assert record["metadata"]["verification_status"] == "checked"


def test_indexes_definition_like_lean_declarations_with_modifiers(tmp_path: Path) -> None:
    root = tmp_path / "lra-lean"
    source = root / "LRA" / "VolumeII" / "PeanoSystems" / "TexSkeleton.lean"
    source.parent.mkdir(parents=True)
    source.write_text(
        """
namespace LRA.VolumeII.PeanoSystems.TexSkeleton

abbrev PeanoSystemFromTex := True

noncomputable def IteratorGeneratedFunction : True := by
  trivial

end LRA.VolumeII.PeanoSystems.TexSkeleton
""",
        encoding="utf-8",
    )

    payload = build_index(tex_roots=[], lean_roots=[root], artifact_source="source")

    declarations = {record["name"]: record for record in payload["objects"]}
    assert declarations["PeanoSystemFromTex"]["kind"] == "abbrev"
    assert declarations["IteratorGeneratedFunction"]["kind"] == "def"


def test_indexes_lean_leading_comment_metadata(tmp_path: Path) -> None:
    root = tmp_path / "lra-lean"
    source = root / "LRA" / "VolumeIII" / "Analysis" / "Continuity" / "Limits.lean"
    source.parent.mkdir(parents=True)
    source.write_text(
        """
namespace LRA.VolumeIII.Analysis.Continuity

/-!
**[Theorem — Squeeze Theorem for Function Limits]**
Mathematical statement (Lean): squeezed functions have the expected limit.
-/
theorem squeeze_fn_limits : True := by
  trivial

end LRA.VolumeIII.Analysis.Continuity
""",
        encoding="utf-8",
    )

    payload = build_index(tex_roots=[], lean_roots=[root], artifact_source="source")

    record = payload["objects"][0]
    assert "Squeeze Theorem for Function Limits" in record["metadata"]["leading_comment"]
    assert record["metadata"]["leading_comment_role"] == "theorem"
    assert record["metadata"]["leading_comment_name"] == "Squeeze Theorem for Function Limits"
    assert "squeezed functions" in record["search_text"]


def test_build_match_report_suggests_unlinked_lean_candidate(tmp_path: Path) -> None:
    tex_root = tmp_path / "lra-volume-iii"
    tex = tex_root / "volume-iii" / "book-analysis-i" / "completeness" / "notes" / "completeness" / "thm-nested" / "source.tex"
    tex.parent.mkdir(parents=True)
    tex.write_text(
        r"""
\begin{theorem}[Nested Interval Theorem]
\label{thm:nested-interval-theorem}
Every nested sequence of nonempty closed bounded intervals has nonempty intersection.
\end{theorem}
""",
        encoding="utf-8",
    )
    lean_root = tmp_path / "lra-lean"
    lean = lean_root / "LRA" / "VolumeIII" / "Analysis" / "Completeness.lean"
    lean.parent.mkdir(parents=True)
    lean.write_text(
        """
theorem NestedIntervalTheorem : True := by
  trivial
""",
        encoding="utf-8",
    )

    payload = build_index(tex_roots=[tex_root], lean_roots=[lean_root], artifact_source="source")
    report = build_match_report(payload, limit=3)

    assert report["counts"]["tex_with_candidates"] == 1
    assert report["candidate_matches"][0]["tex_label"] == "thm:nested-interval-theorem"
    assert report["candidate_matches"][0]["candidates"][0]["declaration"] == "NestedIntervalTheorem"


def test_build_match_report_uses_lean_leading_comment_for_candidates(tmp_path: Path) -> None:
    tex_root = tmp_path / "lra-volume-iii"
    tex = tex_root / "volume-iii" / "book-analysis-ii" / "continuity" / "notes" / "limits" / "source.tex"
    tex.parent.mkdir(parents=True)
    tex.write_text(
        r"""
\begin{theorem}[Squeeze Theorem for Function Limits]
\label{thm:squeeze-function-limits}
If two functions squeeze a third, the middle function has the same limit.
\end{theorem}
""",
        encoding="utf-8",
    )
    lean_root = tmp_path / "lra-lean"
    lean = lean_root / "LRA" / "VolumeIII" / "Analysis" / "Continuity" / "Limits.lean"
    lean.parent.mkdir(parents=True)
    lean.write_text(
        """
namespace LRA.VolumeIII.Analysis.Continuity

/-!
**[Theorem — Squeeze Theorem for Function Limits]**
Mathematical statement (Lean): a squeeze result for limits.
-/
theorem squeeze_fn_limits : True := by
  trivial

end LRA.VolumeIII.Analysis.Continuity
""",
        encoding="utf-8",
    )

    payload = build_index(tex_roots=[tex_root], lean_roots=[lean_root], artifact_source="source")
    report = build_match_report(payload, limit=3)

    assert report["counts"]["tex_with_candidates"] == 1
    candidate = report["candidate_matches"][0]["candidates"][0]
    assert candidate["declaration"] == "LRA.VolumeIII.Analysis.Continuity.squeeze_fn_limits"
    assert candidate["leading_comment_role"] == "theorem"
    assert candidate["leading_comment_name"] == "Squeeze Theorem for Function Limits"


def test_match_report_allows_tex_proposition_and_corollary_to_match_theorem_like_lean(tmp_path: Path) -> None:
    tex_root = tmp_path / "lra-volume-iii"
    prop = tex_root / "volume-iii" / "book-analysis-i" / "completeness" / "notes" / "completeness" / "prop-order" / "source.tex"
    prop.parent.mkdir(parents=True)
    prop.write_text(
        r"""
\begin{proposition}[Order Separation]
\label{prop:order-separation}
Order separation holds.
\end{proposition}
""",
        encoding="utf-8",
    )
    cor = tex_root / "volume-iii" / "book-analysis-i" / "completeness" / "notes" / "completeness" / "cor-density" / "source.tex"
    cor.parent.mkdir(parents=True)
    cor.write_text(
        r"""
\begin{corollary}[Density Corollary]
\label{cor:density-corollary}
Density follows.
\end{corollary}
""",
        encoding="utf-8",
    )
    lean_root = tmp_path / "lra-lean"
    lean = lean_root / "LRA" / "VolumeIII" / "Analysis" / "Completeness.lean"
    lean.parent.mkdir(parents=True)
    lean.write_text(
        """
theorem OrderSeparation : True := by
  trivial

lemma DensityCorollary : True := by
  trivial
""",
        encoding="utf-8",
    )

    payload = build_index(tex_roots=[tex_root], lean_roots=[lean_root], artifact_source="source")
    report = build_match_report(payload, limit=3)

    by_label = {item["tex_label"]: item["candidates"][0] for item in report["candidate_matches"]}
    assert by_label["prop:order-separation"]["lean_kind"] == "theorem"
    assert by_label["cor:density-corollary"]["lean_kind"] == "lemma"


def test_match_report_restricts_candidates_to_same_production_volume(tmp_path: Path) -> None:
    tex_root = tmp_path / "lra-volume-iii"
    tex = tex_root / "volume-iii" / "book-analysis-i" / "completeness" / "notes" / "completeness" / "thm-nested" / "source.tex"
    tex.parent.mkdir(parents=True)
    tex.write_text(
        r"""
\begin{theorem}[Nested Interval Theorem]
\label{thm:nested-interval-theorem}
Every nested sequence of nonempty closed bounded intervals has nonempty intersection.
\end{theorem}
""",
        encoding="utf-8",
    )
    lean_root = tmp_path / "lra-lean"
    wrong_volume = lean_root / "LRA" / "VolumeII" / "Analysis" / "Completeness.lean"
    wrong_volume.parent.mkdir(parents=True)
    wrong_volume.write_text("theorem NestedIntervalTheorem : True := by\n  trivial\n", encoding="utf-8")
    nonproduction = lean_root / "blueprint" / "volume-iii-lean-drafts" / "Completeness.lean"
    nonproduction.parent.mkdir(parents=True)
    nonproduction.write_text("theorem NestedIntervalTheorem : True := by\n  trivial\n", encoding="utf-8")

    payload = build_index(tex_roots=[tex_root], lean_roots=[lean_root], artifact_source="source")
    report = build_match_report(payload, limit=3)

    assert report["counts"]["tex_with_candidates"] == 0
    assert report["counts"]["tex_without_candidates"] == 1


def test_match_report_restricts_aligned_volumes_to_local_hierarchy(tmp_path: Path) -> None:
    tex_root = tmp_path / "lra-volume-iii"
    tex = tex_root / "volume-iii" / "book-analysis-i" / "completeness" / "notes" / "completeness" / "thm-nested" / "source.tex"
    tex.parent.mkdir(parents=True)
    tex.write_text(
        r"""
\begin{theorem}[Nested Interval Theorem]
\label{thm:nested-interval-theorem}
Every nested sequence of nonempty closed bounded intervals has nonempty intersection.
\end{theorem}
""",
        encoding="utf-8",
    )
    lean_root = tmp_path / "lra-lean"
    unrelated = lean_root / "LRA" / "VolumeIII" / "Analysis" / "Sequences.lean"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_text("theorem NestedIntervalTheorem : True := by\n  trivial\n", encoding="utf-8")

    payload = build_index(tex_roots=[tex_root], lean_roots=[lean_root], artifact_source="source")
    report = build_match_report(payload, limit=3)

    assert report["counts"]["tex_with_candidates"] == 0
    assert report["counts"]["tex_without_candidates"] == 1


def test_match_report_uses_explicit_volume_two_hierarchy_map(tmp_path: Path) -> None:
    tex_root = tmp_path / "lra-volume-ii"
    tex = tex_root / "volume-ii" / "book-discrete-algebraic" / "integers" / "notes" / "integer-order" / "thm-order" / "source.tex"
    tex.parent.mkdir(parents=True)
    tex.write_text(
        r"""
\begin{theorem}[Order Compatibility]
\label{thm:integer-order-compatibility}
Integer order is compatible with addition.
\end{theorem}
""",
        encoding="utf-8",
    )
    lean_root = tmp_path / "lra-lean"
    integer_module = lean_root / "LRA" / "VolumeII" / "Integers" / "Order.lean"
    integer_module.parent.mkdir(parents=True)
    integer_module.write_text("theorem OrderCompatibility : True := by\n  trivial\n", encoding="utf-8")
    real_module = lean_root / "LRA" / "VolumeII" / "RealNumbers" / "Order.lean"
    real_module.parent.mkdir(parents=True)
    real_module.write_text("theorem OrderCompatibility : True := by\n  trivial\n", encoding="utf-8")

    payload = build_index(tex_roots=[tex_root], lean_roots=[lean_root], artifact_source="source")
    report = build_match_report(payload, limit=3)

    candidates = report["candidate_matches"][0]["candidates"]
    assert [item["module"] for item in candidates] == ["LRA.VolumeII.Integers.Order"]


def test_match_report_treats_volume_three_discrete_calculus_as_out_of_scope(tmp_path: Path) -> None:
    tex_root = tmp_path / "lra-volume-iii"
    tex = tex_root / "volume-iii" / "book-analysis-i" / "discrete-calculus" / "notes" / "foundations" / "thm-sum" / "source.tex"
    tex.parent.mkdir(parents=True)
    tex.write_text(
        r"""
\begin{theorem}[Summation By Parts]
\label{thm:summation-by-parts}
Summation by parts holds.
\end{theorem}
""",
        encoding="utf-8",
    )
    lean_root = tmp_path / "lra-lean"
    lean = lean_root / "LRA" / "VolumeIII" / "Analysis" / "Sequences.lean"
    lean.parent.mkdir(parents=True)
    lean.write_text("theorem SummationByParts : True := by\n  trivial\n", encoding="utf-8")

    payload = build_index(tex_roots=[tex_root], lean_roots=[lean_root], artifact_source="source")
    report = build_match_report(payload, limit=3)

    assert report["counts"]["tex_with_candidates"] == 0
    assert report["counts"]["tex_without_candidates"] == 1


def test_match_report_treats_volume_one_geometry_as_out_of_scope(tmp_path: Path) -> None:
    tex_root = tmp_path / "lra-volume-i"
    tex = tex_root / "volume-i" / "book-geometry" / "analytical-geometry" / "notes" / "lines" / "source.tex"
    tex.parent.mkdir(parents=True)
    tex.write_text(
        r"""
\begin{definition}[Point-Slope Form]
\label{def:point-slope-form}
The point-slope form describes a line.
\end{definition}
""",
        encoding="utf-8",
    )
    lean_root = tmp_path / "lra-lean"
    lean = lean_root / "LRA" / "VolumeI" / "Logic" / "Propositional.lean"
    lean.parent.mkdir(parents=True)
    lean.write_text("def PointSlopeForm : Prop := True\n", encoding="utf-8")

    payload = build_index(tex_roots=[tex_root], lean_roots=[lean_root], artifact_source="source")
    report = build_match_report(payload, limit=3)

    assert report["counts"]["tex_with_candidates"] == 0
    assert report["counts"]["tex_without_candidates"] == 1
