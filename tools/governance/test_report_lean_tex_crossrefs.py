from __future__ import annotations

from tools.governance.report_lean_tex_crossrefs import build_report, parse_scratch_mapping, render_markdown


def test_build_report_classifies_core_crossref_buckets() -> None:
    payload = {
        "inputs": {"tex_roots": ["R:/lra-volume-iii"], "lean_roots": ["R:/lra-lean"]},
        "objects": [
            {
                "object_id": "tex:thm:tagged",
                "source_family": "tex",
                "kind": "theorem",
                "name": "Tagged Theorem",
                "label": "thm:tagged",
                "path": "volume-iii/book/notes/topic/tagged/source.tex",
                "line": 4,
                "volume": "volume-iii",
                "metadata": {
                    "lean_formalizes": [
                        {
                            "label": "thm:tagged",
                            "repo": "lra-lean",
                            "module": "LRA.VolumeIII.Topic",
                            "declaration": "TaggedTheorem",
                            "status": "checked",
                        }
                    ]
                },
            },
            {
                "object_id": "tex:thm:safe",
                "source_family": "tex",
                "kind": "theorem",
                "name": "Safe Match Theorem",
                "label": "thm:safe",
                "path": "volume-iii/book/notes/topic/safe/source.tex",
                "line": 8,
                "volume": "volume-iii",
                "metadata": {"lean_formalizes": []},
            },
            {
                "object_id": "tex:def:group",
                "source_family": "tex",
                "kind": "definition",
                "name": "Group",
                "label": "def:group",
                "path": "volume-iii/book/notes/topic/group/source.tex",
                "line": 12,
                "volume": "volume-iii",
                "metadata": {"lean_formalizes": []},
            },
            {
                "object_id": "tex:thm:missing",
                "source_family": "tex",
                "kind": "theorem",
                "name": "Missing Lean Theorem",
                "label": "thm:missing",
                "path": "volume-iii/book/notes/topic/missing/source.tex",
                "line": 16,
                "volume": "volume-iii",
                "metadata": {"lean_formalizes": []},
            },
            {
                "object_id": "lean:LRA.VolumeIII.Topic.TaggedTheorem",
                "source_family": "lean",
                "kind": "theorem",
                "name": "TaggedTheorem",
                "declaration": "TaggedTheorem",
                "module": "LRA.VolumeIII.Topic",
                "path": "LRA/VolumeIII/Topic.lean",
                "line": 3,
            },
            {
                "object_id": "lean:LRA.VolumeIII.Topic.SafeMatchTheorem",
                "source_family": "lean",
                "kind": "theorem",
                "name": "SafeMatchTheorem",
                "declaration": "SafeMatchTheorem",
                "module": "LRA.VolumeIII.Topic",
                "path": "LRA/VolumeIII/Topic.lean",
                "line": 9,
            },
            {
                "object_id": "lean:LRA.VolumeIII.Topic.UnmatchedLean",
                "source_family": "lean",
                "kind": "theorem",
                "name": "UnmatchedLean",
                "declaration": "UnmatchedLean",
                "module": "LRA.VolumeIII.Topic",
                "path": "LRA/VolumeIII/Topic.lean",
                "line": 14,
            },
            {
                "object_id": "lean:LRA.VolumeIII.Topic.Group",
                "source_family": "lean",
                "kind": "structure",
                "name": "Group",
                "declaration": "Group",
                "module": "LRA.VolumeIII.Topic",
                "path": "LRA/VolumeIII/Topic.lean",
                "line": 20,
            },
        ],
        "match_report": {
            "candidate_matches": [
                {
                    "tex_object_id": "tex:def:group",
                    "candidates": [
                        {
                            "score": 100,
                            "lean_object_id": "lean:LRA.VolumeIII.Topic.Group",
                            "declaration": "Group",
                            "module": "LRA.VolumeIII.Topic",
                        }
                    ],
                }
            ]
        },
    }
    strict_plan = {
        "entries": [
            {
                "tex_object_id": "tex:thm:safe",
                "tex_label": "thm:safe",
                "tex_name": "Safe Match Theorem",
                "tex_path": "volume-iii/book/notes/topic/safe/source.tex",
                "tex_line": 8,
                "lean_module": "LRA.VolumeIII.Topic",
                "lean_declaration": "SafeMatchTheorem",
            }
        ]
    }

    report = build_report(payload, strict_plan=strict_plan, example_limit=5)

    assert report["counts"]["tex_with_leanformalizes"] == 1
    assert report["counts"]["tex_with_exact_safe_matches"] == 1
    assert report["counts"]["tex_missing_lean_matches"] == 1
    assert report["counts"]["lean_missing_tex_matches"] == 2
    assert report["counts"]["ambiguous_or_suspicious_matches"] == 1
    assert report["categories"]["ambiguous_or_suspicious_matches"][0]["reasons"] == ["generic_title"]
    assert "| Volume | Kind | Count |" in render_markdown(report)


def test_report_includes_scratch_mapping_as_review_only_evidence(tmp_path) -> None:
    mapping_path = tmp_path / "LEAN_TEX_MAPPING.md"
    mapping_path.write_text(
        "\n".join(
            [
                "# Mapping",
                "### `Continuity/Scratch/Limits.lean`",
                "- **theorem `squeeze_function_limits`** ← `thm:squeeze-function-limits`",
                "- **def `helper_decl`** ← *(no book label found)*",
            ]
        ),
        encoding="utf-8",
    )
    mappings = parse_scratch_mapping(mapping_path)
    payload = {
        "objects": [
            {
                "object_id": "tex:thm:squeeze-function-limits",
                "source_family": "tex",
                "kind": "theorem",
                "name": "Squeeze Theorem for Function Limits",
                "label": "thm:squeeze-function-limits",
                "path": "volume-iii/book/analysis/continuity/source.tex",
                "line": 12,
                "volume": "volume-iii",
                "metadata": {"lean_formalizes": []},
            },
            {
                "object_id": "lean:LRA.VolumeIII.Analysis.Continuity.Limits.other",
                "source_family": "lean",
                "kind": "theorem",
                "name": "other",
                "declaration": "other",
                "module": "LRA.VolumeIII.Analysis.Continuity.Limits",
                "path": "LRA/VolumeIII/Analysis/Continuity/Limits.lean",
                "line": 5,
            },
            {
                "object_id": "lean:LRA.VolumeIII.Analysis.Continuity.Limits.HelperDecl",
                "source_family": "lean",
                "kind": "def",
                "name": "HelperDecl",
                "declaration": "HelperDecl",
                "module": "LRA.VolumeIII.Analysis.Continuity.Limits",
                "path": "LRA/VolumeIII/Analysis/Continuity/Limits.lean",
                "line": 8,
            },
        ],
        "match_report": {"candidate_matches": []},
    }

    report = build_report(payload, strict_plan={"entries": []}, scratch_mappings=mappings)

    assert mappings == [
        {
            "tex_label": "thm:squeeze-function-limits",
            "lean_kind": "theorem",
            "lean_module": "LRA.VolumeIII.Analysis.Continuity.Scratch.Limits",
            "lean_declaration": "squeeze_function_limits",
            "has_tex_label": True,
            "source": str(mapping_path),
            "source_line": 3,
            "scratch_path": "Continuity/Scratch/Limits.lean",
        },
        {
            "tex_label": None,
            "lean_kind": "def",
            "lean_module": "LRA.VolumeIII.Analysis.Continuity.Scratch.Limits",
            "lean_declaration": "helper_decl",
            "has_tex_label": False,
            "source": str(mapping_path),
            "source_line": 4,
            "scratch_path": "Continuity/Scratch/Limits.lean",
        },
    ]
    assert report["counts"]["tex_with_scratch_lean_mappings"] == 1
    assert report["counts"]["tex_with_scratch_only_mappings"] == 1
    assert report["counts"]["lean_mapping_entries_without_tex_labels"] == 1
    addition = report["categories"]["lean_mapping_entries_without_tex_labels"][0]
    assert addition["lean_module"] == "LRA.VolumeIII.Analysis.Continuity.Limits"
    assert addition["lean_declaration"] == "HelperDecl"
    assert addition["lean_path"] == "LRA/VolumeIII/Analysis/Continuity/Limits.lean"
    assert report["counts"]["tex_with_exact_safe_matches"] == 0
    assert "Lean Additions Without TeX Labels" in render_markdown(report)
