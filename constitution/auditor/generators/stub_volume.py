"""Deterministic volume-stub generator retained at the legacy import path."""
from __future__ import annotations

import sys
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[3] / "tools" / "governance"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from generators.volume_stub import render_volume_stub  # noqa: E402


def generate_stub_volume(
    volume_identifier: str,
    volume_display_title: str,
    volume_scope: str,
    chapter_registry: list[dict],
    frontispiece_mathematician: str | None = None,
    frontispiece_years: str | None = None,
    frontispiece_image: str | None = None,
) -> dict[str, str]:
    frontispiece = None
    supplied = (
        frontispiece_mathematician,
        frontispiece_years,
        frontispiece_image,
    )
    if any(supplied):
        if not all(supplied):
            raise ValueError(
                "frontispiece requires mathematician, years, and image; "
                "the stub generator does not infer biographical facts"
            )
        frontispiece = {
            "mathematician": frontispiece_mathematician,
            "years": frontispiece_years,
            "image": frontispiece_image,
        }
    return render_volume_stub(
        volume_identifier,
        volume_display_title,
        volume_scope,
        chapter_registry,
        frontispiece=frontispiece,
    )


__all__ = ["generate_stub_volume", "render_volume_stub"]
