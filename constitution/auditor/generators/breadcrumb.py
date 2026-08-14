"""Deterministic breadcrumb generator retained at the legacy import path."""
from __future__ import annotations

import sys
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[3] / "tools" / "governance"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from generators.breadcrumb import render_breadcrumb  # noqa: E402


def generate_breadcrumb(
    chapter_subject: str,
    chapter_display_title: str,
    chapter_registry: list[dict],
    is_stub: bool = False,
) -> str:
    return render_breadcrumb(
        chapter_subject,
        chapter_display_title,
        chapter_registry,
        is_stub=is_stub,
    )
