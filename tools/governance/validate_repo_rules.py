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
    "lra-volume-vi",
    "lra-volume-vii",
    "lra-volume-viii",
}
SPECIALIST_KEYWORDS = [
    "Lean-specific",
    "Lean",
    "Vulkan",
    "NURBS",
    "benchmark",
    "plotting",
    "PDF extraction",
]
NEGATIVE_CONTEXT_PATTERNS = [
    "do not",
    "does not",
    "must not",
    "should not",
    "not apply",
    "not receive",
    "belongs only",
    "belong only",
    "elsewhere",
    "exclude",
    "excluded",
    "volume-content only",
]
FORBIDDEN_SPECIALIST_PATTERNS = [
    "run Lean",
    "use Lean",
    "Lean CI",
    "Vulkan build",
    "NURBS implementation",
    "benchmark workflow",
    "plotting workflow",
    "PDF extraction workflow",
    "apply PDF extraction",
    "numerical benchmark",
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


def has_negative_context(line: str) -> bool:
    lowered = line.lower()
    return any(pattern in lowered for pattern in NEGATIVE_CONTEXT_PATTERNS)


def volume_specialist_leaks(text: str) -> list[tuple[int, str, str]]:
    leaks: list[tuple[int, str, str]] = []
    negative_continuation = False
    for line_number, line in enumerate(text.splitlines(), start=1):
        line_has_negative_context = has_negative_context(line)
        line_has_keyword = any(keyword in line for keyword in SPECIALIST_KEYWORDS)
        if line_has_negative_context:
            negative_continuation = True
        elif not line.strip():
            negative_continuation = False

        if not line_has_keyword:
            continue
        if any(pattern in line for pattern in FORBIDDEN_SPECIALIST_PATTERNS):
            leaks.append((line_number, "positive_specialist_instruction", line.strip()))
            continue
        if line_has_negative_context or negative_continuation:
            continue
        leaks.append((line_number, "ambiguous_specialist_context", line.strip()))
    return leaks


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
                for line_number, code, line in volume_specialist_leaks(text):
                    errors.append(
                        f"volume preview contains {code} at {path}:{line_number}: {line}"
                    )


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
