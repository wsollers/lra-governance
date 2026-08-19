#!/usr/bin/env python3
"""Create the local governance venv and install the canonical lock."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUPPORTED = ((3, 12), (3, 13))


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--venv", type=Path, default=ROOT / ".venv")
    parser.add_argument("--recreate", action="store_true")
    args = parser.parse_args(argv)

    current = sys.version_info[:2]
    if current not in SUPPORTED:
        supported = ", ".join(".".join(map(str, value)) for value in SUPPORTED)
        raise SystemExit(
            f"Python {supported} is required; current interpreter is "
            f"{sys.version_info.major}.{sys.version_info.minor}."
        )

    lock = ROOT / "requirements.lock"
    if not lock.exists():
        raise SystemExit(f"canonical lock file is missing: {lock}")

    venv_dir = args.venv.expanduser().resolve()
    if args.recreate and venv_dir.exists():
        import shutil

        shutil.rmtree(venv_dir)
    if not _venv_python(venv_dir).exists():
        venv.EnvBuilder(with_pip=True).create(venv_dir)

    python = _venv_python(venv_dir)
    subprocess.run(
        [str(python), "-m", "pip", "install", "--require-hashes", "-r", str(lock)],
        cwd=ROOT,
        check=True,
    )
    import hashlib

    (venv_dir / ".lock-sha256").write_text(
        hashlib.sha256(lock.read_bytes()).hexdigest() + "\n", encoding="utf-8"
    )
    print(f"governance Python environment ready: {python}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
