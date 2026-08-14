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

from generators.chapter_stub import (  # noqa: E402,F401
    main,
    render_chapter_stub_files,
    render_lrameta,
    stub_chapter,
)


if __name__ == "__main__":
    main()
