#!/usr/bin/env python3
"""Canonical leaf volume build wrapper."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    print("+ " + " ".join(cmd))
    try:
        subprocess.run(cmd, cwd=cwd, check=True, env=env)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from None


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and build a leaf LRA volume.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument(
        "--refactor-mode",
        action="store_true",
        help="accepted for compatibility; canonical volume validation no longer uses this flag",
    )
    parser.add_argument(
        "--print-edition",
        action="store_true",
        help="omit proof vaults, exercise vaults, and capstones from the rendered PDF",
    )
    parser.add_argument("--latex-command", nargs=argparse.REMAINDER, default=None)
    args = parser.parse_args()

    root = args.root.resolve()
    validator = root / "tools" / "governance" / "validate_volume.py"
    run([sys.executable, str(validator), str(root), "--fail-on-errors"], root)

    latex_cmd = args.latex_command or ["latexmk", "-lualatex", "main.tex"]
    if not args.validate_only:
        if shutil.which(latex_cmd[0]) is None:
            raise SystemExit(
                f"Build command not found: {latex_cmd[0]}. Validation already passed; "
                "install latexmk or use --validate-only."
            )
        env = os.environ.copy()
        if args.print_edition:
            env["LRA_PRINT_EDITION"] = "1"
        run(latex_cmd, root, env=env)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
