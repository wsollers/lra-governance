#!/usr/bin/env python3
"""Generate preview agent wrappers that delegate to canonical governance."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from merge_repo_overlays import overlay_for_repo, repo_names


TEMPLATE_OUTPUTS = {
    "AGENTS.md.j2": Path("AGENTS.md"),
    "CLAUDE.md.j2": Path("CLAUDE.md"),
    "GEMINI.md.j2": Path("GEMINI.md"),
    "copilot-instructions.md.j2": Path(".github/copilot-instructions.md"),
    "github-instructions.md.j2": Path(".github/instructions/lra.instructions.md"),
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview generated LRA agent wrappers without touching downstream repos."
    )
    parser.add_argument("--repo", action="append", choices=repo_names())
    parser.add_argument("--out", required=True, help="Preview output directory.")
    parser.add_argument("--dry-run", action="store_true", default=True)
    return parser.parse_args(argv)


def governance_root() -> Path:
    return Path(__file__).resolve().parents[2]


def generated_header(overlay_name: str) -> str:
    return f"""<!--
GENERATED POINTER WRAPPER — DO NOT EDIT BY HAND.

Source repo: wsollers/lra-governance
Canonical overlay: capabilities/overlays/{overlay_name}

Regenerate from lra-governance.
Emergency downstream edits must be ported upstream before regeneration.
-->"""


def governance_resolution() -> str:
    return """Resolve canonical governance in this order:

1. `LRA_GOVERNANCE_ROOT`;
2. sibling `../lra-governance`;
3. an explicit `lra-governance` checkout supplied by the build image or task.

If canonical governance cannot be resolved, stop and report that
`lra-governance` is not present."""


def provider_notes(template_name: str) -> str:
    if template_name == "AGENTS.md.j2":
        return "Codex reads this file as the local entrypoint, then follows canonical governance."
    if template_name == "CLAUDE.md.j2":
        return "Claude should import or follow `AGENTS.md`, then follow canonical governance."
    if template_name == "GEMINI.md.j2":
        return "Gemini should follow this pointer wrapper and canonical governance."
    return "Keep provider-specific guidance concise and defer durable policy to canonical governance."


def render_template(template: str, values: dict[str, str]) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace("{{ " + key + " }}", value)
    return rendered


def write_preview(root: Path, repo: str, out_dir: Path) -> list[Path]:
    overlay_name = overlay_for_repo(repo)
    template_dir = root / "tools" / "governance" / "templates"
    written: list[Path] = []

    for template_name, relative_output in TEMPLATE_OUTPUTS.items():
        template_text = (template_dir / template_name).read_text(encoding="utf-8")
        values = {
            "GENERATED_HEADER": generated_header(overlay_name),
            "REPO_NAME": repo,
            "OVERLAY_PATH": f"capabilities/overlays/{overlay_name}",
            "GOVERNANCE_RESOLUTION": governance_resolution(),
            "PROVIDER_NOTES": provider_notes(template_name),
        }
        rendered = render_template(template_text, values)
        output_path = out_dir / repo / relative_output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered.rstrip() + "\n", encoding="utf-8")
        written.append(output_path)
    return written


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = governance_root()
    out_dir = Path(args.out).expanduser().resolve(strict=False)
    selected_repos = args.repo or repo_names()

    if root not in out_dir.parents and out_dir != root:
        print(f"fatal: preview output must be under governance repo: {out_dir}", file=sys.stderr)
        return 1

    written: list[Path] = []
    for repo in selected_repos:
        written.extend(write_preview(root, repo, out_dir))

    print(f"preview generated: {len(written)} files under {out_dir}")
    print("downstream repos were not modified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
