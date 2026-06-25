#!/usr/bin/env python3
"""Canonical leaf volume build wrapper."""

from __future__ import annotations

import argparse
import os
import re
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


def governance_root() -> Path:
    env = os.environ.get("LRA_GOVERNANCE_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parents[1]


def discover_tex_roots(root: Path) -> list[Path]:
    volume_entry_re = re.compile(r"^volume-(i|ii|iii|iv|v|vi|vii|viii)\.tex$")
    book_entry_re = re.compile(r"^volume-(i|ii|iii|iv|v|vi|vii|viii)-[a-z0-9]+(?:-[a-z0-9]+)*\.tex$")
    roots = sorted(
        tex_root for tex_root in root.glob("volume-*.tex")
        if volume_entry_re.fullmatch(tex_root.name) or book_entry_re.fullmatch(tex_root.name)
    )
    if not roots:
        roots = sorted(root.glob("volume-*-*-main.tex"))
    if not roots:
        roots = sorted(root.glob("main-book-*.tex"))
    if not roots and (root / "main.tex").exists():
        roots = [root / "main.tex"]
    if not roots:
        raise SystemExit(
            "no TeX build roots found: expected volume-{roman}.tex or "
            "volume-{roman}-{book-slug}.tex, legacy volume-{roman}-{book-slug}-main.tex "
            "or main-book-*.tex, or transitional main.tex"
        )
    return roots


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
    validator = governance_root() / "tools" / "governance" / "validate_volume.py"
    if not validator.exists():
        raise SystemExit(
            f"canonical governance validator not found: {validator}. "
            "Set LRA_GOVERNANCE_ROOT or run from the lra-governance checkout."
        )
    run([sys.executable, str(validator), str(root), "--fail-on-errors"], root)

    if not args.validate_only:
        latex_cmd_base = args.latex_command or ["latexmk", "-lualatex"]
        if shutil.which(latex_cmd_base[0]) is None:
            raise SystemExit(
                f"Build command not found: {latex_cmd_base[0]}. Validation already passed; "
                "install latexmk or use --validate-only."
            )
        env = os.environ.copy()
        if args.print_edition:
            env["LRA_PRINT_EDITION"] = "1"
        for tex_root in discover_tex_roots(root):
            run([*latex_cmd_base, tex_root.name], root, env=env)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
