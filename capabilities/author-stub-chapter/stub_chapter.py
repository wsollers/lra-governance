r"""Compatibility wrapper for the canonical chapter stub generator."""
from __future__ import annotations

import sys
from pathlib import Path

_here = Path(__file__).resolve()
for _parent in _here.parents:
    candidate = _parent / "tools" / "governance"
    if candidate.is_dir():
        sys.path.insert(0, str(candidate))
        break

from generators.chapter_stub import main, render_breadcrumb, stub_chapter  # noqa: E402,F401


if __name__ == "__main__":
    main()
