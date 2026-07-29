from __future__ import annotations

from tools.governance.plan_lean_tex_formalizations import build_plan, lean_module_for


def test_plan_skips_starred_restatement_and_uses_production_lean_only() -> None:
    payload = {
        "objects": [
            {
                "object_id": "tex:thm:nested",
                "source_family": "tex",
                "kind": "theorem",
                "name": "Nested Interval Theorem",
                "label": "thm:nested",
                "repo_root": "R:/lra-volume",
                "path": "volume-iii/book/notes/topic/thm-nested/source.tex",
                "line": 1,
                "metadata": {"starred": False, "lean_formalizes": []},
            },
            {
                "object_id": "tex:volume-iii/book/proofs/topic/prf-nested.tex:10",
                "source_family": "tex",
                "kind": "theorem",
                "name": "Nested Interval Theorem",
                "label": None,
                "repo_root": "R:/lra-volume",
                "path": "volume-iii/book/proofs/topic/prf-nested.tex",
                "line": 10,
                "metadata": {"starred": True, "lean_formalizes": []},
            },
            {
                "object_id": "lean:LRA.VolumeIII.Analysis.NestedIntervalTheorem",
                "source_family": "lean",
                "kind": "theorem",
                "name": "NestedIntervalTheorem",
                "declaration": "LRA.VolumeIII.Analysis.NestedIntervalTheorem",
                "module": "LRA.VolumeIII.Analysis",
                "path": "LRA/VolumeIII/Analysis.lean",
                "line": 7,
            },
            {
                "object_id": "lean:LRA.VolumeIII.Analysis.Scratch.NestedIntervalTheorem",
                "source_family": "lean",
                "kind": "theorem",
                "name": "NestedIntervalTheorem",
                "declaration": "LRA.VolumeIII.Analysis.Scratch.NestedIntervalTheorem",
                "module": "LRA.VolumeIII.Analysis.Scratch",
                "path": "blueprint/VolumeIII/Analysis.lean",
                "line": 7,
            },
        ]
    }

    plan = build_plan(payload, status="pending", production_only=True)

    assert plan["counts"]["planned"] == 1
    assert plan["entries"][0]["tex_label"] == "thm:nested"
    assert plan["entries"][0]["lean_declaration"] == "NestedIntervalTheorem"
    assert any(item["reason"] == "starred_restatement" for item in plan["skipped"])


def test_lean_module_for_preserves_file_module_matching_declaration_name() -> None:
    record = {
        "module": "LRA.VolumeII.PeanoSystems.PeanoSystem",
        "declaration": "LRA.VolumeII.PeanoSystems.PeanoSystem",
        "name": "PeanoSystem",
    }

    assert lean_module_for(record) == "LRA.VolumeII.PeanoSystems.PeanoSystem"
