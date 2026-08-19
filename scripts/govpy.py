#!/usr/bin/env python3
"""Run a governance Python tool under the canonical .venv.

Bootstraps the venv from requirements.lock on first use (or when the lock
changes), then runs the given command under the venv interpreter. When the
venv cannot be provisioned — unsupported interpreter, failed install — it
falls back to the current interpreter with a loud warning so degraded
environments keep working instead of dying on the first import.

Usage:
    python scripts/govpy.py <tool.py> [args...]
    python scripts/govpy.py -m <module> [args...]

A leading tool path that does not exist relative to the caller's working
directory is resolved against the governance root, so
`python <governance-root>/scripts/govpy.py capabilities/resolve.py ...`
works from any repository.

Set GOVPY_NO_BOOTSTRAP=1 to skip venv provisioning (tests, offline runs).
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "requirements.lock"
VENV = ROOT / ".venv"
STAMP = VENV / ".lock-sha256"
SUPPORTED = ((3, 12), (3, 13))


def _venv_python() -> Path:
    if os.name == "nt":
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def _lock_digest() -> str:
    return hashlib.sha256(LOCK.read_bytes()).hexdigest()


def _venv_ready() -> bool:
    return (
        _venv_python().exists()
        and STAMP.exists()
        and STAMP.read_text(encoding="utf-8").strip() == _lock_digest()
    )


def _bootstrap() -> bool:
    if sys.version_info[:2] not in SUPPORTED:
        supported = ", ".join(".".join(map(str, v)) for v in SUPPORTED)
        print(
            f"govpy: interpreter {sys.version_info.major}.{sys.version_info.minor} "
            f"is outside the pinned set ({supported}); skipping venv bootstrap",
            file=sys.stderr,
        )
        return False
    try:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "bootstrap_python.py")],
            check=True,
        )
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"govpy: venv bootstrap failed ({exc})", file=sys.stderr)
        return False
    return _venv_python().exists()


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in {"-h", "--help"}:
        print(__doc__)
        return 0 if argv else 2

    # Resolve a leading tool path against the governance root when the caller's
    # working directory does not contain it.
    if argv[0].endswith(".py") and not Path(argv[0]).exists():
        candidate = ROOT / argv[0]
        if candidate.exists():
            argv[0] = str(candidate)

    if os.environ.get("GOVPY_NO_BOOTSTRAP") == "1":
        use_venv = _venv_python().exists()
    else:
        use_venv = _venv_ready() or _bootstrap()

    if use_venv:
        python = str(_venv_python())
    else:
        python = sys.executable
        print(
            "govpy: WARNING — running with the current interpreter, not the "
            "pinned governance venv; dependency errors may follow. For the "
            "canonical environment run scripts/bootstrap_python.py with "
            "Python 3.12 or 3.13.",
            file=sys.stderr,
        )
    return subprocess.run([python, *argv]).returncode


if __name__ == "__main__":
    raise SystemExit(main())
