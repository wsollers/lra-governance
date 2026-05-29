#!/usr/bin/env python3
"""Validate Phase 4 governance wrapper preview inputs and outputs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from merge_repo_overlays import REPO_OVERLAY_MAP, overlay_path, repo_names


REQUIRED_SOURCE_DOCS = [
    "docs/governance/agent-instruction-policy.md",
    "docs/governance/task-scope-limits.md",
    "docs/architecture/generated-file-policy.md",
    "docs/architecture/multi-repo-sync.md",
]
TEMPLATE_FILES = [
    "AGENTS.md.j2",
    "CLAUDE.md.j2",
    "GEMINI.md.j2",
    "copilot-instructions.md.j2",
    "github-instructions.md.j2",
]
PREVIEW_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".github/copilot-instructions.md",
    ".github/instructions/lra.instructions.md",
]
VOLUME_REPOS = {
    "lra-volume-i",
    "lra-volume-ii",
    "lra-volume-iii",
    "lra-volume-iv",
    "lra-volume-v",
}
SPECIALIST_KEYWORDS = [
    "Lean-specific",
    "Vulkan",
    "NURBS",
    "benchmark",
    "plotting",
    "PDF extraction",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate generated wrapper previews.")
    parser.add_argument("--preview", required=True, help="Preview output directory.")
    return parser.parse_args(argv)


def governance_root() -> Path:
    return Path(__file__).resolve().parents[2]


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_sources(root: Path, errors: list[str]) -> None:
    for relative in REQUIRED_SOURCE_DOCS:
        require((root / relative).exists(), f"missing source doc: {relative}", errors)
    for repo in repo_names():
        require(repo in REPO_OVERLAY_MAP, f"missing overlay map for repo: {repo}", errors)
        path = overlay_path(repo, root)
        require(path.exists(), f"missing overlay for {repo}: {path}", errors)
    template_dir = root / "tools" / "governance" / "templates"
    for name in TEMPLATE_FILES:
        require((template_dir / name).exists(), f"missing template: {name}", errors)


def validate_preview(preview: Path, errors: list[str]) -> None:
    for repo in repo_names():
        for relative in PREVIEW_FILES:
            path = preview / repo / relative
            require(path.exists(), f"missing preview file: {path}", errors)
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            require(
                "GENERATED FILE — DO NOT EDIT BY HAND" in text,
                f"missing generated header in: {path}",
                errors,
            )
            if repo in VOLUME_REPOS:
                for keyword in SPECIALIST_KEYWORDS:
                    if keyword in text:
                        errors.append(f"volume preview contains specialist keyword '{keyword}': {path}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = governance_root()
    preview = Path(args.preview).expanduser().resolve(strict=False)
    errors: list[str] = []

    validate_sources(root, errors)
    validate_preview(preview, errors)

    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print("validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

