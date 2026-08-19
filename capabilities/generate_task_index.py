#!/usr/bin/env python3
"""Generate the human route index from capabilities/manifest.yaml."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "capabilities" / "manifest.yaml"
DEFAULT_OUTPUT = ROOT / "capabilities" / "task-index.md"


def _cell(values: list[object] | None) -> str:
    if not values:
        return "—"
    return "<br>".join(f"`{str(value).replace('|', '&#124;')}`" for value in values)


def render(manifest: dict) -> str:
    lines = [
        "<!-- GENERATED FILE. DO NOT EDIT BY HAND.",
        "Source: capabilities/manifest.yaml",
        "Regenerate: python capabilities/generate_task_index.py",
        "-->",
        "",
        "# Agent Task Index",
        "",
        "This is the human view of the authoritative route manifest. Agents should not",
        "preload this document. Resolve the current repository and task instead:",
        "",
        "```text",
        'python <governance-root>/capabilities/resolve.py --repo <repo> --task "<user task>" --root <repo-root>',
        "```",
        "",
        "The resolver loads only the global entrypoint, one repository overlay, and the",
        "route's eager instructions. Lazy references, tools, schemas, and examples stay",
        "out of context until needed. Budgets cover the wrapper plus eager packet and",
        "use deterministic `ceil(Unicode characters / 4)` estimation.",
        "",
        "## Task Routes",
        "",
        "| Task (`route id`) | Eager instructions | Lazy references | Executable tools | Schemas/data | Examples | Context budget |",
        "| --- | --- | --- | --- | --- | --- | ---: |",
    ]
    for route in manifest.get("routes", []):
        title = str(route["title"]).replace("|", "&#124;")
        lines.append(
            f"| {title} (`{route['id']}`) | "
            f"{_cell(route.get('eager_instructions'))} | "
            f"{_cell(route.get('lazy_references'))} | "
            f"{_cell(route.get('tools'))} | "
            f"{_cell(route.get('schemas'))} | "
            f"{_cell(route.get('examples'))} | "
            f"{route.get('token_budget', manifest.get('default_token_budget', '—'))} |"
        )

    lines.extend(
        [
            "",
            "## Prompt Routes",
            "",
            "Prompts are examples/templates and remain lazy until explicitly requested.",
            "",
            "| Prompted task | Prompt | Schemas/data | Verification |",
            "| --- | --- | --- | --- |",
        ]
    )
    for route in manifest.get("prompt_routes", []):
        lines.append(
            f"| {route['title']} | `{route['prompt']}` | "
            f"{_cell(route.get('schemas'))} | {_cell(route.get('verify'))} |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    expected = render(manifest)
    output = args.output.resolve(strict=False)
    if args.check:
        if not output.exists() or output.read_text(encoding="utf-8") != expected:
            print(f"stale generated task index: {output}", file=sys.stderr)
            return 1
        print(f"task index current: {output}")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(expected, encoding="utf-8")
    print(f"generated task index: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
