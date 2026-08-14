"""Deterministic chapter-stub generator retained at the legacy import path."""
from __future__ import annotations

import sys
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[3] / "tools" / "governance"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from generators.chapter_stub import render_chapter_stub_files  # noqa: E402


def generate_stub_chapter(
    volume_path: str,
    chapter_subject: str,
    chapter_display_title: str,
    chapter_registry: list[dict],
    sections_known: bool = False,
    section_titles: list[str] | None = None,
) -> dict[str, str]:
    if sections_known and not section_titles:
        raise ValueError("sections_known requires explicit section_titles")
    return render_chapter_stub_files(
        Path(volume_path),
        chapter_subject,
        chapter_display_title,
        chapter_registry,
        section_titles or [],
    )


__all__ = ["generate_stub_chapter", "render_chapter_stub_files"]
