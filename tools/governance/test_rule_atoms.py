#!/usr/bin/env python3
"""Focused tests for atomized governance rules.

These protect the small-rule contract independently of the legacy aggregate
decoration_rules test file, whose broad snippets may trigger unrelated rules.
"""
from __future__ import annotations

from dataclasses import dataclass

from rules.decoration import dependencies_block, interpretation_block, labels
from rules.proofs import proof_stub_state


@dataclass
class Block:
    environment: str
    text: str
    decoration: str
    line_start: int = 1


@dataclass
class FileInfo:
    path: str


def codes(findings):
    return {finding.code for finding in findings or []}


def test_missing_label_atom():
    block = Block("definition", r"\begin{definition}Body\end{definition}", "")
    assert "missing_label" in codes(labels.check_missing_label(block, None))


def test_wrong_label_prefix_atom():
    block = Block("lemma", r"\begin{lemma}\label{thm:x}Body\end{lemma}", "")
    assert "wrong_label_prefix" in codes(labels.check_label_prefix(block, None))


def test_interpretation_atom():
    block = Block("definition", r"\begin{definition}\label{def:x}Body\end{definition}", "")
    assert "missing_interpretation" in codes(interpretation_block.check(block, None))


def test_dependencies_atom_accepts_no_local_marker():
    block = Block("definition", "", r"\NoLocalDependencies")
    assert "missing_dependencies" not in codes(dependencies_block.check(block, None))


def test_proof_stub_state_atom_flags_filled_stub_structure():
    text = (
        r"\begin{proof}[Professional Standard Proof]" "\n"
        "TODO\n"
        r"\end{proof}" "\n"
        r"\begin{proof}[Detailed Learning Proof]" "\n"
        "TODO\n"
        r"\end{proof}" "\n"
        r"\begin{remark*}[Proof structure]" "\n"
        "Use induction.\n"
        r"\end{remark*}" "\n"
    )
    assert "proof_stub_structure_not_blank" in codes(
        proof_stub_state.check(text, FileInfo("proofs/topic/prf-x.tex"), None)
    )


def test_proof_stub_state_atom_accepts_untitled_proof_envs():
    text = (
        r"\begin{proof}" "\n"
        "TODO: Professional Standard Proof\n"
        r"\end{proof}" "\n"
        r"\begin{proof}" "\n"
        "TODO: Detailed Learning Proof\n"
        r"\end{proof}" "\n"
        r"\begin{remark*}[Proof structure]" "\n"
        "Use induction.\n"
        r"\end{remark*}" "\n"
    )
    assert "proof_stub_structure_not_blank" in codes(
        proof_stub_state.check(text, FileInfo("proofs/topic/prf-x.tex"), None)
    )


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {test.__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    raise SystemExit(1 if failed else 0)
