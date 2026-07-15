#!/usr/bin/env python3
"""Regression tests for (repo, task) -> capability routing in resolve.py.

Locks the author-definition / author-statement partition (G1): definitions must
route to author-definition (which authors a Definition + runs the definition
verifier), NOT to author-statement (which emits a provable proof stub). Also
guards cross-kind isolation. Run: python test_resolve.py
"""
from __future__ import annotations
import sys
from pathlib import Path

import resolve as R

GOV = R._gov_root(Path(__file__).resolve().parent)


def route(repo: str, task: str) -> str:
    """Return the resolved capability id, or 'FATAL:<msg>' if resolution fails."""
    try:
        return R.resolve(GOV, repo, task, {}).capability_id
    except (ValueError, FileNotFoundError) as e:
        return f"FATAL:{e}"


def expect(repo, task, cap):
    got = route(repo, task)
    assert got == cap, f"route({repo!r}, {task!r}) = {got!r}, expected {cap!r}"


# --- definitions route to author-definition (the G1 fix) ---
def test_define_routes_to_author_definition():
    expect("lra-volume-i", "define X", "author-definition")


def test_generate_the_definition_routes_to_author_definition():
    expect("lra-volume-i", "generate the definition for continuity", "author-definition")


def test_write_the_def_routes_to_author_definition():
    expect("lra-volume-i", "write the def for a Cauchy sequence", "author-definition")


def test_append_the_definition_routes_to_author_definition():
    # authoring a definition, not a provable statement
    expect("lra-volume-i", "append the definition", "author-definition")


# --- provable kinds STILL route to author-statement (not broken by the carve-out) ---
def test_append_the_lemma_routes_to_author_statement():
    expect("lra-volume-i", "append the lemma", "author-statement")


def test_the_theorem_routes_to_author_statement():
    expect("lra-volume-i", "author statement for the theorem", "author-statement")


def test_the_axiom_stays_with_author_statement():
    # axiom is non-provable but ruled to stay with author-statement (not author-definition)
    expect("lra-volume-i", "the axiom of completeness", "author-statement")


# --- semantic audit routing ---
def test_lra_audit_topic_routes_to_topic_semantic_audit():
    expect("lra-volume-iii", "LRA audit topic bounds-extremals", "audit-semantic-topic")


def test_single_artifact_calibration_still_routes_separately():
    expect("lra-volume-iii", "calibrate semantic artifact", "calibrate-semantic-artifact")


# --- a definition task in a non-volume kind must NOT select a volume authoring
#     capability. With overlays materialized, lra-lean resolves its kind and rejects
#     the task because no lean capability matches it (strict kind-rejection). ---
def test_define_does_not_leak_into_lean():
    got = route("lra-lean", "define X")
    assert got.startswith("FATAL:"), f"expected non-resolution in lean, got {got!r}"
    assert "no capability matches" in got, f"expected kind-rejection, got {got!r}"


def test_lean_routes_to_lean_capability():
    expect("lra-lean", "formalize addition commutativity", "author-lean-theorem")


def test_numerical_analysis_routes_to_cpp_capability():
    expect("lra-numerical-analysis", "implement the solver", "cpp-build-task")


def test_nurbs_routes_to_cpp_capability():
    expect("lra-nurbs", "implement surface evaluation", "cpp-build-task")


def test_volume_build_routes_to_build_repo():
    expect("lra-volume-viii", "build repo", "build-repo")


def test_lean_workflow_monitor_routes_to_build_repo():
    expect("lra-lean", "monitor workflows", "build-repo")


def test_cpp_build_repo_routes_to_build_repo():
    expect("lra-numerical-analysis", "build repository", "build-repo")


def test_governance_validate_routes_to_build_repo():
    expect("lra-governance", "validate repo", "build-repo")


if __name__ == "__main__":
    tests = [
        v
        for k, v in sorted(globals().items())
        if k.startswith("test_") and callable(v)
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {t.__name__}: {e}")
    print(f"\n{len(tests)-failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
