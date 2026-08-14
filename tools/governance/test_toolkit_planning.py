from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONSTITUTION = ROOT / "constitution"
TOOLS = ROOT / "tools" / "governance"
for path in (CONSTITUTION, TOOLS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from auditor.audits import toolkits  # noqa: E402
from auditor import cli  # noqa: E402
from validators import toolkit_coverage  # noqa: E402


def _chapter(tmp_path: Path, *, toolkit: bool = False) -> Path:
    volume = tmp_path / "volume-ii"
    chapter = volume / "order"
    notes = chapter / "notes"
    topic = notes / "basics"
    topic.mkdir(parents=True)
    (volume / "index.tex").write_text(
        r"\input{volume-ii/order/index}" + "\n",
        encoding="utf-8",
    )
    (chapter / "index.tex").write_text(
        "\n".join(
            [
                r"\input{volume-ii/order/notes/index}",
                r"\input{volume-ii/order/proofs/index}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (chapter / "proofs").mkdir()
    (chapter / "proofs" / "index.tex").write_text("% empty\n", encoding="utf-8")
    (chapter / "chapter.yaml").write_text(
        "subject: order\nenvironments: []\n",
        encoding="utf-8",
    )
    (notes / "index.tex").write_text(
        r"\input{volume-ii/order/notes/basics/index}" + "\n",
        encoding="utf-8",
    )
    toolkit_text = ""
    if toolkit:
        toolkit_text = "\n".join(
            [
                r"\begin{toolkitbox}{Order Basics}",
                r"\begin{tabular}{l l}",
                r"\textbf{Name} & \textbf{Meaning} \\",
                r"\hyperref[def:order]{Order} & Basic order structure \\",
                r"\hyperref[thm:order]{Order theorem} & Main local result \\",
                r"\end{tabular}",
                r"\end{toolkitbox}",
                "",
            ]
        )
    (topic / "index.tex").write_text(
        "\n".join(
            [
                r"\section{Order Basics}",
                toolkit_text,
                r"\input{volume-ii/order/notes/basics/notes-definitions}",
                r"\input{volume-ii/order/notes/basics/notes-results}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (topic / "notes-definitions.tex").write_text(
        "\n".join(
            [
                r"\begin{definition}[Order]",
                r"\label{def:order}",
                "Definition body.",
                r"\end{definition}",
            ]
        ),
        encoding="utf-8",
    )
    (topic / "notes-results.tex").write_text(
        "\n".join(
            [
                r"\begin{theorem}[Order Theorem]",
                r"\label{thm:order}",
                "Theorem body.",
                r"\end{theorem}",
            ]
        ),
        encoding="utf-8",
    )
    return chapter


def test_inventory_targets_topic_router_and_follows_routed_formals(tmp_path):
    inventories = toolkits.inventory_chapter_toolkits(_chapter(tmp_path, toolkit=True))

    assert len(inventories) == 1
    section = inventories[0]
    assert section.file == "notes/basics/index.tex"
    assert section.section == "Order Basics"
    assert [item.label for item in section.formal_items] == ["def:order", "thm:order"]
    assert len(section.existing_toolkit_boxes) == 1
    assert section.existing_toolkit_boxes[0].title == "Order Basics"


def test_inventory_accepts_nested_tex_in_section_and_toolkit_titles(tmp_path):
    chapter = _chapter(tmp_path, toolkit=True)
    router = chapter / "notes" / "basics" / "index.tex"
    text = router.read_text(encoding="utf-8").replace(
        r"\section{Order Basics}",
        r"\section{Order on $\mathbb{R}$}",
    ).replace(
        r"\begin{toolkitbox}{Order Basics}",
        r"\begin{toolkitbox}{Order on $\mathbb{R}$}",
    )
    router.write_text(text, encoding="utf-8")

    section = toolkits.inventory_chapter_toolkits(chapter)[0]

    assert section.section == r"Order on $\mathbb{R}$"
    assert section.existing_toolkit_boxes[0].title == r"Order on $\mathbb{R}$"


def test_deterministic_plan_emits_one_row_per_formal_topic(tmp_path):
    chapter = _chapter(tmp_path)
    plan = toolkits.build_toolkit_plan(
        chapter.name,
        toolkits.inventory_chapter_toolkits(chapter),
    )

    assert plan == {
        "chapter": "order",
        "toolkits": [
            {
                "toolkit_id": "toolkit:basics",
                "title": "Toolkit: Order Basics",
                "file": "notes/basics/index.tex",
                "section": "Order Basics",
                "placement_before": "def:order",
                "covers": ["def:order", "thm:order"],
                "purpose": "Orient the formal items in this section.",
                "status": "missing",
            }
        ],
        "notes": [],
    }


def test_plan_validator_rejects_coverage_and_location_drift(tmp_path):
    chapter = _chapter(tmp_path)
    inventories = toolkits.inventory_chapter_toolkits(chapter)
    plan = toolkits.build_toolkit_plan(chapter.name, inventories)
    plan["toolkits"][0]["covers"] = ["def:order"]
    plan["toolkits"][0]["file"] = "notes/wrong/index.tex"

    errors = toolkits.validate_toolkit_plan(plan, chapter.name, inventories)

    assert any("Missing toolkit plan row" in error for error in errors)
    assert any("unknown section" in error for error in errors)


def test_planner_does_not_call_model_and_writes_deterministic_plan(tmp_path, monkeypatch):
    chapter = _chapter(tmp_path, toolkit=True)
    written: dict[str, object] = {}

    def fake_json(payload, _chapter, _operation):
        written["json"] = json.loads(json.dumps(payload))
        return tmp_path / "plan.json"

    def fake_markdown(content, _chapter, _operation):
        written["markdown"] = content
        return tmp_path / "plan.md"

    monkeypatch.setattr(toolkits, "_write_json_report", fake_json)
    monkeypatch.setattr(toolkits, "_write_markdown_report", fake_markdown)
    plan = toolkits.plan_toolkits(chapter)

    assert plan["toolkits"][0]["status"] == "existing"
    assert written["json"] == plan
    assert "# Toolkit Plan" in written["markdown"]
    assert not hasattr(toolkits, "client")


def test_audit_reports_missing_toolkit_and_accepts_complete_toolkit(tmp_path, monkeypatch):
    monkeypatch.setattr(toolkits, "_write_json_report", lambda *_args: tmp_path / "audit.json")
    monkeypatch.setattr(toolkits, "_write_markdown_report", lambda *_args: tmp_path / "audit.md")

    missing = toolkits.audit_toolkits(_chapter(tmp_path / "missing"))
    complete = toolkits.audit_toolkits(_chapter(tmp_path / "complete", toolkit=True))

    assert [item["type"] for item in missing["findings"]] == ["section_without_toolkit"]
    assert complete["findings"] == []


def test_plan_toolkits_cli_does_not_require_ai(tmp_path, monkeypatch):
    captured: dict[str, object] = {}

    def fake_validate_config(*, ai_provider, require_ai):
        captured["require_ai"] = require_ai
        return []

    def fake_plan(args):
        captured["path"] = args.path

    monkeypatch.setattr(cli, "validate_config", fake_validate_config)
    monkeypatch.setattr(cli.client, "set_provider", lambda _provider: None)
    monkeypatch.setattr(cli, "cmd_plan_toolkits", fake_plan)
    monkeypatch.setattr(
        sys,
        "argv",
        ["auditor", "plan", "toolkits", str(tmp_path / "chapter")],
    )

    cli.main()

    assert captured["require_ai"] is False
    assert captured["path"] == str(tmp_path / "chapter")


def test_integrated_validator_uses_same_inventory_contract(tmp_path):
    missing_chapter = _chapter(tmp_path / "missing")
    complete_chapter = _chapter(tmp_path / "complete", toolkit=True)

    missing = toolkit_coverage.validate(missing_chapter.parent, [])
    complete = toolkit_coverage.validate(complete_chapter.parent, [])

    assert [item.code for item in missing] == ["section_without_toolkit"]
    assert complete == []
