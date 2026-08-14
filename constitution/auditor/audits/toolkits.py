"""
audits/toolkits.py
Section-level Toolkit box inventory, planning, and deterministic auditing.

Toolkit boxes are not per-statement artifacts. This module keeps them out of
single-environment audits and treats them as section/file planning artifacts.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from auditor.report import _human_timestamp, report_path, write_report

import sys


TOOLS_ROOT = Path(__file__).resolve().parents[3] / "tools" / "governance"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from core.file_inventory import input_paths  # noqa: E402
from core.volume import VOLUME_RE  # noqa: E402


_TOPIC_SECTION_START = re.compile(r"\\section(?![A-Za-z*])(?:\[[^\]]*\])?\{")
_ENV_OPEN = re.compile(
    r"\\begin\{(definition|theorem|lemma|proposition|corollary|axiom)\}"
    r"(?:\[([^\]]*)\])?",
    re.IGNORECASE,
)
_LABEL = re.compile(r"\\label\{([a-z]+:[a-z0-9\-]+)\}")
_TCOLORBOX_OPEN = re.compile(r"\\begin\{tcolorbox\}(?:\[([^\]]*)\])?", re.IGNORECASE)
_TCOLORBOX_END = re.compile(r"\\end\{tcolorbox\}", re.IGNORECASE)
_TOOLKITBOX_OPEN = re.compile(r"\\begin\{toolkitbox\}\{", re.IGNORECASE)
_TOOLKITBOX_END = re.compile(r"\\end\{toolkitbox\}", re.IGNORECASE)


@dataclass
class FormalItem:
    label: str
    type: str
    title: str
    line: int


@dataclass
class ToolkitBox:
    line: int
    title: str
    labels_mentioned: list[str]
    excerpt: str


@dataclass
class SectionInventory:
    file: str
    section: str
    start_line: int
    end_line: int
    formal_items: list[FormalItem] = field(default_factory=list)
    existing_toolkit_boxes: list[ToolkitBox] = field(default_factory=list)


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _balanced_group_end(text: str, start: int) -> int | None:
    if start >= len(text) or text[start] != "{":
        return None
    depth = 0
    escaped = False
    for position in range(start, len(text)):
        char = text[position]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return position + 1
    return None


def _topic_sections(text: str) -> list[tuple[str, int]]:
    sections: list[tuple[str, int]] = []
    for match in _TOPIC_SECTION_START.finditer(text):
        title_start = match.end() - 1
        title_end = _balanced_group_end(text, title_start)
        if title_end is None:
            continue
        sections.append((text[title_start + 1 : title_end - 1].strip(), match.start()))
    return sections


def _find_formal_items(section_text: str, section_start: int, full_text: str) -> list[FormalItem]:
    items: list[FormalItem] = []
    for match in _ENV_OPEN.finditer(section_text):
        env_name = match.group(1).lower()
        title = (match.group(2) or "").strip()
        after = section_text[match.start() : match.start() + 1200]
        label_match = _LABEL.search(after)
        if not label_match:
            continue
        label = label_match.group(1)
        artifact_type = {
            "definition": "def",
            "theorem": "thm",
            "lemma": "lem",
            "proposition": "prop",
            "corollary": "cor",
            "axiom": "ax",
        }.get(env_name, env_name)
        items.append(
            FormalItem(
                label=label,
                type=artifact_type,
                title=title or label,
                line=_line_number(full_text, section_start + match.start()),
            )
        )
    return items


def _find_toolkit_boxes(section_text: str, section_start: int, full_text: str) -> list[ToolkitBox]:
    boxes: list[ToolkitBox] = []
    for match in _TOOLKITBOX_OPEN.finditer(section_text):
        title_start = match.end() - 1
        title_end = _balanced_group_end(section_text, title_start)
        if title_end is None:
            continue
        end_match = _TOOLKITBOX_END.search(section_text, title_end)
        if not end_match:
            continue
        box_text = section_text[match.start() : end_match.end()]
        labels = sorted(
            set(
                _LABEL.findall(box_text)
                + re.findall(r"\\hyperref\[([a-z]+:[a-z0-9\-]+)\]", box_text)
            )
        )
        boxes.append(
            ToolkitBox(
                line=_line_number(full_text, section_start + match.start()),
                title=section_text[title_start + 1 : title_end - 1].strip() or "Toolkit",
                labels_mentioned=labels,
                excerpt=" ".join(box_text.split())[:300],
            )
        )
    for match in _TCOLORBOX_OPEN.finditer(section_text):
        end_match = _TCOLORBOX_END.search(section_text, match.end())
        if not end_match:
            continue
        box_text = section_text[match.start() : end_match.end()]
        options = match.group(1) or ""
        if "toolkit" not in (options + box_text).lower():
            continue
        title_match = re.search(r"title\s*=\s*\{([^{}]*)\}", options)
        title = title_match.group(1).strip() if title_match else "Toolkit"
        labels = sorted(set(_LABEL.findall(box_text) + re.findall(r"\\hyperref\[([a-z]+:[a-z0-9\-]+)\]", box_text)))
        excerpt = " ".join(box_text.split())[:300]
        boxes.append(
            ToolkitBox(
                line=_line_number(full_text, section_start + match.start()),
                title=title,
                labels_mentioned=labels,
                excerpt=excerpt,
            )
        )
    return boxes


def _volume_root(chapter_root: Path) -> Path:
    for parent in chapter_root.resolve().parents:
        if VOLUME_RE.fullmatch(parent.name):
            return parent
    return chapter_root.resolve().parent


def _routed_topic_indexes(chapter_root: Path) -> list[Path]:
    notes_index = chapter_root / "notes" / "index.tex"
    if not notes_index.is_file():
        raise FileNotFoundError(f"notes/index.tex not found at {notes_index}")
    volume_root = _volume_root(chapter_root)
    notes_root = notes_index.parent.resolve()
    indexes = []
    for target in input_paths(notes_index, volume_root):
        try:
            relative = target.relative_to(notes_root)
        except ValueError:
            continue
        if target.name == "index.tex" and len(relative.parts) == 2:
            indexes.append(target.resolve())
    return sorted(set(indexes))


def _routed_topic_files(topic_index: Path, volume_root: Path) -> list[Path]:
    topic_root = topic_index.parent.resolve()
    visited: set[Path] = set()
    ordered: list[Path] = []

    def visit(path: Path) -> None:
        path = path.resolve()
        if path in visited:
            return
        try:
            path.relative_to(topic_root)
        except ValueError:
            return
        if not path.is_file():
            return
        visited.add(path)
        ordered.append(path)
        for child in input_paths(path, volume_root):
            visit(child)

    for path in input_paths(topic_index, volume_root):
        visit(path)
    return ordered


def inventory_chapter_toolkits(chapter_path: Path) -> list[SectionInventory]:
    chapter_root = chapter_path.resolve()
    yaml_path = chapter_root / "chapter.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(f"chapter.yaml not found at {yaml_path}")

    chapter_yaml = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    if not isinstance(chapter_yaml, dict):
        raise ValueError(f"chapter.yaml must be a mapping: {yaml_path}")

    inventories: list[SectionInventory] = []
    volume_root = _volume_root(chapter_root)
    for topic_index in _routed_topic_indexes(chapter_root):
        router_text = topic_index.read_text(encoding="utf-8")
        sections = _topic_sections(router_text)
        if len(sections) != 1:
            relative = topic_index.relative_to(chapter_root).as_posix()
            raise ValueError(
                f"{relative} must contain exactly one non-starred \\section{{...}}."
            )
        section_title, start = sections[0]
        section_title = section_title or "Untitled"
        end = len(router_text)
        line = _line_number(router_text, start)
        formal_items: list[FormalItem] = []
        for body in _routed_topic_files(topic_index, volume_root):
            if body == topic_index:
                continue
            text = body.read_text(encoding="utf-8")
            formal_items.extend(_find_formal_items(text, 0, text))
        toolkit_boxes = _find_toolkit_boxes(router_text[start:end], start, router_text)
        if not formal_items and not toolkit_boxes:
            continue
        inventories.append(
            SectionInventory(
                file=topic_index.relative_to(chapter_root).as_posix(),
                section=section_title,
                start_line=line,
                end_line=_line_number(router_text, end),
                formal_items=formal_items,
                existing_toolkit_boxes=toolkit_boxes,
            )
        )
    return inventories


def _inventory_payload(chapter: str, inventories: list[SectionInventory]) -> dict[str, Any]:
    return {
        "chapter": chapter,
        "sections": [
            {
                "file": section.file,
                "section": section.section,
                "start_line": section.start_line,
                "end_line": section.end_line,
                "formal_items": [asdict(item) for item in section.formal_items],
                "existing_toolkit_boxes": [asdict(box) for box in section.existing_toolkit_boxes],
            }
            for section in inventories
        ],
    }


def _write_json_report(payload: dict[str, Any], chapter: str, operation: str) -> Path:
    path = report_path(chapter, operation, chapter).with_suffix(".json")
    write_report(json.dumps(payload, indent=2, ensure_ascii=False), path)
    return path


def _write_markdown_report(content: str, chapter: str, operation: str) -> Path:
    path = report_path(chapter, operation, chapter)
    write_report(content, path)
    return path


def build_toolkit_plan(chapter: str, inventories: list[SectionInventory]) -> dict[str, Any]:
    """Build one deterministic plan row per routed formal-bearing topic."""
    toolkits = []
    for section in inventories:
        if not section.formal_items:
            continue
        topic = Path(section.file).parent.name
        toolkits.append(
            {
                "toolkit_id": f"toolkit:{topic}",
                "title": f"Toolkit: {section.section}",
                "file": section.file,
                "section": section.section,
                "placement_before": section.formal_items[0].label,
                "covers": [item.label for item in section.formal_items],
                "purpose": "Orient the formal items in this section.",
                "status": "existing" if len(section.existing_toolkit_boxes) == 1 else "missing",
            }
        )
    return {"chapter": chapter, "toolkits": toolkits, "notes": []}


def validate_toolkit_plan(
    plan: dict[str, Any],
    chapter: str,
    inventories: list[SectionInventory],
) -> list[str]:
    """Validate plan topology and coverage against the live routed inventory."""
    errors: list[str] = []
    if not isinstance(plan, dict):
        return ["Toolkit plan must be a JSON object."]
    if plan.get("chapter") != chapter:
        errors.append(f"Plan chapter must be {chapter!r}.")
    rows = plan.get("toolkits")
    if not isinstance(rows, list):
        return errors + ["Plan toolkits must be a list."]

    expected = build_toolkit_plan(chapter, inventories)
    expected_map = {
        (row["file"], row["section"]): row for row in expected["toolkits"]
    }
    actual_map: dict[tuple[str, str], dict[str, Any]] = {}
    for position, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            errors.append(f"Toolkit plan row {position} must be an object.")
            continue
        key = (str(row.get("file") or ""), str(row.get("section") or ""))
        if key in actual_map:
            errors.append(f"Duplicate toolkit plan row for {key[0]} / {key[1]}.")
            continue
        actual_map[key] = row

    for key, expected_row in expected_map.items():
        row = actual_map.get(key)
        if row is None:
            errors.append(f"Missing toolkit plan row for {key[0]} / {key[1]}.")
            continue
        for field_name in ("placement_before", "covers", "status"):
            if row.get(field_name) != expected_row[field_name]:
                errors.append(
                    f"Toolkit plan {key[0]} / {key[1]} has invalid {field_name}; "
                    f"expected {expected_row[field_name]!r}."
                )
        toolkit_id = row.get("toolkit_id")
        if not isinstance(toolkit_id, str) or not re.fullmatch(r"toolkit:[a-z0-9]+(?:-[a-z0-9]+)*", toolkit_id):
            errors.append(f"Toolkit plan {key[0]} / {key[1]} has an invalid toolkit_id.")
        for field_name in ("title", "purpose"):
            if not isinstance(row.get(field_name), str) or not row[field_name].strip():
                errors.append(f"Toolkit plan {key[0]} / {key[1]} requires {field_name}.")

    for key in actual_map.keys() - expected_map.keys():
        errors.append(f"Toolkit plan targets non-formal or unknown section {key[0]} / {key[1]}.")
    notes = plan.get("notes", [])
    if not isinstance(notes, list) or any(not isinstance(note, str) for note in notes):
        errors.append("Plan notes must be a list of strings.")
    return errors


def inventory_findings(inventories: list[SectionInventory]) -> list[dict[str, Any]]:
    """Return deterministic Toolkit presence, uniqueness, and coverage findings."""
    findings: list[dict[str, Any]] = []
    for section in inventories:
        if not section.formal_items:
            continue
        boxes = section.existing_toolkit_boxes
        if not boxes:
            findings.append({
                "status": "MISSING",
                "type": "section_without_toolkit",
                "file": section.file,
                "section": section.section,
                "first_formal_label": section.formal_items[0].label,
                "message": "Routed formal-bearing topic has no Toolkit box in its section router.",
            })
            continue
        if len(boxes) > 1:
            findings.append({
                "status": "FAIL",
                "type": "multiple_section_toolkits",
                "file": section.file,
                "section": section.section,
                "message": "Section router must contain exactly one Toolkit box.",
            })
            continue
        expected_labels = [item.label for item in section.formal_items]
        missing_labels = [
            label for label in expected_labels if label not in boxes[0].labels_mentioned
        ]
        if missing_labels:
            findings.append({
                "status": "FAIL",
                "type": "toolkit_missing_coverage",
                "file": section.file,
                "section": section.section,
                "covers": missing_labels,
                "message": "Toolkit does not link every routed formal label in its topic.",
            })
    return findings


def plan_toolkits(chapter_path: Path) -> dict[str, Any]:
    chapter_root = chapter_path.resolve()
    chapter = chapter_root.name
    inventories = inventory_chapter_toolkits(chapter_root)
    plan = build_toolkit_plan(chapter, inventories)

    json_path = _write_json_report(plan, chapter, "toolkit-plan")
    md_path = _write_markdown_report(format_toolkit_plan_markdown(plan), chapter, "toolkit-plan")
    print(f"Toolkit plan JSON written to: {json_path}")
    print(f"Toolkit plan markdown written to: {md_path}")
    return plan


def format_toolkit_plan_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# Toolkit Plan",
        f"- **Chapter:** {plan.get('chapter', '?')}",
        f"- **Timestamp:** {_human_timestamp()}",
        "",
    ]
    toolkits = plan.get("toolkits", [])
    if not toolkits:
        lines += ["_No toolkit recommendations returned._", ""]
    for toolkit in toolkits:
        lines += [
            f"## {toolkit.get('title', toolkit.get('toolkit_id', 'Toolkit'))}",
            "",
            f"- **ID:** `{toolkit.get('toolkit_id', '')}`",
            f"- **Status:** {toolkit.get('status', '')}",
            f"- **File:** `{toolkit.get('file', '')}`",
            f"- **Section:** {toolkit.get('section', '')}",
            f"- **Placement:** before `{toolkit.get('placement_before', '')}`",
            f"- **Purpose:** {toolkit.get('purpose', '')}",
            "",
            "### Covers",
            "",
        ]
        for label in toolkit.get("covers", []):
            lines.append(f"- `{label}`")
        lines.append("")
    if plan.get("notes"):
        lines += ["## Notes", ""]
        for note in plan["notes"]:
            lines.append(f"- {note}")
        lines.append("")
    return "\n".join(lines)


def audit_toolkits(chapter_path: Path, plan_path: Path | None = None) -> dict[str, Any]:
    chapter_root = chapter_path.resolve()
    chapter = chapter_root.name
    inventories = inventory_chapter_toolkits(chapter_root)
    inventory = _inventory_payload(chapter, inventories)

    plan: dict[str, Any] | None = None
    if plan_path:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))

    findings: list[dict[str, Any]] = []
    if plan is not None:
        for message in validate_toolkit_plan(plan, chapter, inventories):
            findings.append(
                {
                    "status": "FAIL",
                    "type": "invalid_toolkit_plan",
                    "message": message,
                }
            )

    findings.extend(inventory_findings(inventories))

    report = {
        "chapter": chapter,
        "timestamp": _human_timestamp(),
        "plan_path": str(plan_path) if plan_path else "",
        "summary": {
            "sections_scanned": len(inventories),
            "findings": len(findings),
            "planned_toolkits": (
                len(plan.get("toolkits", []))
                if isinstance(plan, dict) and isinstance(plan.get("toolkits"), list)
                else 0
            ),
        },
        "findings": findings,
        "inventory": inventory,
    }

    json_path = _write_json_report(report, chapter, "toolkit-audit")
    md_path = _write_markdown_report(format_toolkit_audit_markdown(report), chapter, "toolkit-audit")
    print(format_toolkit_audit_markdown(report))
    print(f"\nToolkit audit JSON written to: {json_path}")
    print(f"Toolkit audit markdown written to: {md_path}")
    return report


def format_toolkit_audit_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Toolkit Audit",
        f"- **Chapter:** {report.get('chapter', '?')}",
        f"- **Timestamp:** {report.get('timestamp', '')}",
        f"- **Sections scanned:** {report.get('summary', {}).get('sections_scanned', 0)}",
        f"- **Findings:** {report.get('summary', {}).get('findings', 0)}",
        "",
    ]
    findings = report.get("findings", [])
    if not findings:
        lines += ["_No toolkit findings._", ""]
        return "\n".join(lines)
    for finding in findings:
        lines += [
            f"## {finding.get('status', '')}: {finding.get('type', '')}",
            "",
            finding.get("message", ""),
            "",
        ]
        for key in ("toolkit_id", "file", "section", "placement_before", "first_formal_label"):
            if finding.get(key):
                lines.append(f"- **{key}:** `{finding[key]}`")
        if finding.get("covers"):
            lines.append("- **covers:** " + ", ".join(f"`{label}`" for label in finding["covers"]))
        lines.append("")
    return "\n".join(lines)
