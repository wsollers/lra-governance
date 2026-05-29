#!/usr/bin/env python3
"""Map LRA repositories to governance overlays."""

from __future__ import annotations

from pathlib import Path


REPO_OVERLAY_MAP: dict[str, str] = {
    "Learning-Real-Analysis": "learning-real-analysis.md",
    "lra-common": "lra-common.md",
    "lra-volume-i": "lra-volume.md",
    "lra-volume-ii": "lra-volume.md",
    "lra-volume-iii": "lra-volume.md",
    "lra-volume-iv": "lra-volume.md",
    "lra-volume-v": "lra-volume.md",
    "lra-lean": "lra-lean.md",
    "lra-nurbs": "lra-nurbs.md",
    "lra-knowledge-explorer": "lra-knowledge-explorer.md",
    "lra-numerical-analysis": "lra-numerical-analysis.md",
    "lra-pdf-extractor": "lra-pdf-extractor.md",
}


def repo_names() -> list[str]:
    return list(REPO_OVERLAY_MAP)


def overlay_for_repo(repo: str) -> str:
    try:
        return REPO_OVERLAY_MAP[repo]
    except KeyError as exc:
        raise KeyError(f"unknown LRA repo: {repo}") from exc


def overlay_path(repo: str, governance_root: Path) -> Path:
    return governance_root / "docs" / "governance" / "repo-overlays" / overlay_for_repo(repo)


def load_overlay(repo: str, governance_root: Path) -> str:
    path = overlay_path(repo, governance_root)
    return path.read_text(encoding="utf-8")

