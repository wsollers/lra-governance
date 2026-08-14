from __future__ import annotations

import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONSTITUTION = ROOT / "constitution"
for path in (HERE, CONSTITUTION):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from audit_chapter_symbols import (  # noqa: E402
    audit_chapter_symbols,
    format_symbol_audit_markdown,
)
from auditor.audits import symbols as symbol_audit_wrapper  # noqa: E402


def _chapter(tmp_path: Path, content: str) -> Path:
    chapter = tmp_path / "volume-ii" / "order"
    note = chapter / "notes" / "basics" / "notes-basics.tex"
    proof = chapter / "proofs" / "basics" / "prf-basics.tex"
    note.parent.mkdir(parents=True)
    proof.parent.mkdir(parents=True)
    note.write_text(content, encoding="utf-8")
    proof.write_text("% no symbol uses\n", encoding="utf-8")
    (note.parent / "index.tex").write_text("SHOULD_NOT_SCAN", encoding="utf-8")
    return chapter


def test_audit_extracts_exact_registered_uses_and_skips_routers(tmp_path):
    chapter = _chapter(
        tmp_path,
        "\n".join(
            [
                r"Let A\subseteq\mathbb{R} and P=\mathsf{OrderedSet}(A,\leq).",
                r"\begin{remark*}[Predicate reading]",
                r"\operatorname{UpperBound}(u,S,P)",
                r"\end{remark*}",
            ]
        ),
    )

    result = audit_chapter_symbols(chapter)

    assert "UpperBound" in result.used_predicates
    assert "OrderedSet" in result.used_structures
    assert r"\mathbb{R}" in result.used_notation
    assert len(result.files) == 2
    assert all(path.name != "index.tex" for path in result.files)


def test_audit_flags_unknown_and_wrong_command_forms(tmp_path):
    chapter = _chapter(
        tmp_path,
        "\n".join(
            [
                r"\operatorname{UnknownLocalPredicate}(x)",
                r"\operatorname{OrderedSet}(A,\leq)",
                r"\mathsf{UpperBound}(u,S,P)",
                r"\mathsf{UnknownStructure}(A)",
            ]
        ),
    )

    result = audit_chapter_symbols(chapter)
    codes = {item.code for item in result.findings}

    assert "unregistered_operatorname" in codes
    assert "structure_constructor_operatorname" in codes
    assert "predicate_constructor_mathsf" in codes
    assert "unregistered_structure_constructor" in codes


def test_report_states_relation_registry_boundary(tmp_path):
    result = audit_chapter_symbols(_chapter(tmp_path, r"\mathbb{R}"))
    markdown = format_symbol_audit_markdown(result)
    expanded = format_symbol_audit_markdown(result, include_unused_entries=True)

    assert "does not define TeX relation spellings" in markdown
    assert "does not infer mathematical meaning from prose" in markdown
    assert "Registered Uses" in markdown
    assert "Pass `--include-unused`" in markdown
    assert "### Unused Predicates" in expanded


def test_auditor_wrapper_does_not_call_model(tmp_path, monkeypatch):
    chapter = _chapter(tmp_path, r"\operatorname{UnknownLocalPredicate}(x)")
    saved: dict[str, str] = {}

    def fake_save(markdown: str, chapter_name: str):
        saved["markdown"] = markdown
        saved["chapter"] = chapter_name
        return tmp_path / "report.md"

    monkeypatch.setattr(symbol_audit_wrapper, "save_symbol_audit_report", fake_save)
    markdown = symbol_audit_wrapper.audit_symbols(chapter)

    assert "unregistered_operatorname" in markdown
    assert saved["chapter"] == "order"
    assert saved["markdown"] == markdown
    assert not hasattr(symbol_audit_wrapper, "client")
