r"""Compatibility wrapper for the canonical section stub generator."""
from __future__ import annotations

import sys
from pathlib import Path

_here = Path(__file__).resolve()
for _parent in _here.parents:
    candidate = _parent / "tools" / "governance"
    if candidate.is_dir():
        sys.path.insert(0, str(candidate))
        break

from generators.section_stub import append_once, main, slugify, stub_section, write_new  # noqa: E402,F401


if __name__ == "__main__":
    main()
