from __future__ import annotations

from tools.governance.audit_checked_lean_tex_tags import build_audit


def test_audit_checked_lean_theorem_tex_tags() -> None:
    payload = {
        "objects": [
            {
                "object_id": "lean:LRA.VolumeIII.Topic.Tagged",
                "source_family": "lean",
                "kind": "theorem",
                "name": "Tagged",
                "module": "LRA.VolumeIII.Topic",
                "declaration": "Tagged",
                "path": "LRA/VolumeIII/Topic.lean",
                "line": 3,
                "metadata": {"verification_status": "checked"},
            },
            {
                "object_id": "lean:LRA.VolumeIII.Topic.Missing",
                "source_family": "lean",
                "kind": "theorem",
                "name": "Missing",
                "module": "LRA.VolumeIII.Topic",
                "declaration": "Missing",
                "path": "LRA/VolumeIII/Topic.lean",
                "line": 8,
                "metadata": {"verification_status": "checked"},
            },
            {
                "object_id": "lean:LRA.VolumeIII.Topic.Incomplete",
                "source_family": "lean",
                "kind": "theorem",
                "name": "Incomplete",
                "module": "LRA.VolumeIII.Topic",
                "declaration": "Incomplete",
                "path": "LRA/VolumeIII/Topic.lean",
                "line": 12,
                "metadata": {"verification_status": "incomplete"},
            },
            {
                "object_id": "lean:Scratch.Tagged",
                "source_family": "lean",
                "kind": "theorem",
                "name": "ScratchTagged",
                "module": "Scratch",
                "declaration": "ScratchTagged",
                "path": "Scratch/Topic.lean",
                "line": 1,
                "metadata": {"verification_status": "checked"},
            },
            {
                "object_id": "tex:thm:tagged",
                "source_family": "tex",
                "kind": "theorem",
                "name": "Tagged",
                "label": "thm:tagged",
                "path": "volume-iii/book/notes/topic/source.tex",
                "line": 5,
                "metadata": {
                    "lean_formalizes": [
                        {
                            "label": "thm:tagged",
                            "repo": "lra-lean",
                            "module": "LRA.VolumeIII.Topic",
                            "declaration": "Tagged",
                            "status": "checked",
                        }
                    ]
                },
            },
        ]
    }

    audit = build_audit(payload, include_candidate_lookup=True)

    assert audit["counts"]["checked_lean_theorems"] == 2
    assert audit["counts"]["checked_lean_theorems_with_tex_tag"] == 1
    assert audit["counts"]["checked_lean_theorems_missing_tex_tag"] == 1
    assert audit["counts"]["tex_link_statuses_for_tagged_lean"] == {"checked": 1}
    assert audit["counts"]["missing_candidate_lookup"] == {"none": 1}
    assert audit["examples"]["missing"][0]["declaration"] == "Missing"


def test_audit_can_include_checked_lemmas() -> None:
    payload = {
        "objects": [
            {
                "object_id": "lean:LRA.VolumeIII.Topic.HelperLemma",
                "source_family": "lean",
                "kind": "lemma",
                "name": "HelperLemma",
                "module": "LRA.VolumeIII.Topic",
                "declaration": "HelperLemma",
                "path": "LRA/VolumeIII/Topic.lean",
                "line": 1,
                "metadata": {"verification_status": "checked"},
            }
        ]
    }

    audit = build_audit(payload, include_lemmas=True)

    assert audit["counts"]["checked_lean_theorems"] == 1
    assert audit["examples"]["missing"][0]["declaration"] == "HelperLemma"


def test_audit_classifies_reliable_tex_candidate_for_missing_lean() -> None:
    payload = {
        "objects": [
            {
                "object_id": "lean:LRA.VolumeIII.Analysis.NestedIntervalTheorem",
                "source_family": "lean",
                "kind": "theorem",
                "name": "NestedIntervalTheorem",
                "module": "LRA.VolumeIII.Analysis.Completeness",
                "declaration": "NestedIntervalTheorem",
                "path": "LRA/VolumeIII/Analysis/Completeness.lean",
                "line": 1,
                "statement": "theorem NestedIntervalTheorem : nested intervals have nonempty intersection",
                "metadata": {
                    "verification_status": "checked",
                    "leading_comment_name": "Nested Interval Theorem",
                    "leading_comment": "Theorem: nested closed bounded intervals have nonempty intersection.",
                },
            },
            {
                "object_id": "tex:thm:nested-interval-theorem",
                "source_family": "tex",
                "kind": "theorem",
                "name": "Nested Interval Theorem",
                "label": "thm:nested-interval-theorem",
                "path": "volume-iii/book-analysis-i/completeness/notes/source.tex",
                "line": 10,
                "statement": "Every nested sequence of nonempty closed bounded intervals has nonempty intersection.",
                "search_text": "theorem Nested Interval Theorem thm:nested-interval-theorem",
                "metadata": {"lean_formalizes": []},
            },
        ]
    }

    audit = build_audit(payload, include_candidate_lookup=True)

    lookup = audit["examples"]["missing_with_candidates"][0]["candidate_lookup"]
    assert lookup["classification"] == "reliable"
    assert lookup["candidates"][0]["label"] == "thm:nested-interval-theorem"
