#!/usr/bin/env python3
"""Build an LRA volume in Docker with external governance and common checkouts."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


IMAGE_NAME = "learning-real-analysis-latex"
COMMON_REPO = "https://github.com/wsollers/lra-common.git"
DEFAULT_LATEX_ARGS = [
    "latexmk",
    "-lualatex",
    "-interaction=nonstopmode",
    "-file-line-error",
    "-synctex=1",
    "-shell-escape",
]


def run(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    print("+ " + " ".join(str(part) for part in cmd))
    try:
        subprocess.run(cmd, cwd=cwd, check=True, env=env)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from None


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"required tool not found on PATH: {name}")


def governance_root() -> Path:
    env = os.environ.get("LRA_GOVERNANCE_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


def resolve_common_root(volume_root: Path, explicit: Path | None, checkout_dir: Path | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(explicit)
    env = os.environ.get("LRA_COMMON_ROOT")
    if env:
        candidates.append(Path(env))
    candidates.append(volume_root.parent / "lra-common")
    candidates.append(governance_root().parent / "lra-common")

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.expanduser().resolve(strict=False)
        if resolved in seen:
            continue
        seen.add(resolved)
        if (resolved / "common" / "volume-preamble.tex").exists() and (resolved / "docker" / "Dockerfile").exists():
            return resolved

    if checkout_dir is None:
        raise SystemExit(
            "lra-common checkout not found. Pass --common-root, set LRA_COMMON_ROOT, "
            "place lra-common next to the volume/governance checkout, or pass --checkout-common."
        )

    checkout_root = checkout_dir.expanduser().resolve(strict=False)
    if checkout_root.exists() and any(checkout_root.iterdir()):
        raise SystemExit(f"--checkout-common target already exists and is not empty: {checkout_root}")
    require_tool("git")
    checkout_root.parent.mkdir(parents=True, exist_ok=True)
    run(["git", "clone", "--depth", "1", COMMON_REPO, str(checkout_root)])
    return checkout_root


def docker_path(path: Path) -> str:
    return str(path.resolve())


def docker_run(
    volume_root: Path,
    common_root: Path,
    gov_root: Path,
    image_name: str,
    edition: str,
    paper: str,
    latex_args: list[str],
) -> None:
    cmd = [
        "docker",
        "run",
        "--rm",
        "-e",
        "LRA_GOVERNANCE_ROOT=/lra-governance",
        "-e",
        f"LRA_EDITION={edition}",
        "-e",
        f"LRA_PAPER={paper}",
        "-v",
        f"{docker_path(volume_root)}:/workspace",
        "-v",
        f"{docker_path(common_root / 'common')}:/workspace/common:ro",
        "-v",
        f"{docker_path(gov_root)}:/lra-governance:ro",
        "-v",
        f"{docker_path(volume_root.parent)}:/lra-repos:ro",
        "-w",
        "/workspace",
    ]
    if edition == "print":
        cmd.extend(["-e", "LRA_PRINT_EDITION=1"])
    cmd.append(image_name)
    cmd.extend(latex_args)
    run(cmd)


def discover_tex_roots(volume_root: Path, requested: list[str] | None) -> list[Path]:
    if requested:
        roots = [volume_root / item for item in requested]
    else:
        volume_entry_re = re.compile(r"^volume-(i|ii|iii|iv|v|vi|vii|viii)\.tex$")
        book_entry_re = re.compile(r"^volume-(i|ii|iii|iv|v|vi|vii|viii)-[a-z0-9]+(?:-[a-z0-9]+)*\.tex$")
        roots = sorted(
            root for root in volume_root.glob("volume-*.tex")
            if volume_entry_re.fullmatch(root.name) or book_entry_re.fullmatch(root.name)
        )
        if not roots:
            roots = sorted(volume_root.glob("volume-*-*-main.tex"))
        if not roots:
            roots = sorted(volume_root.glob("main-book-*.tex"))
        if not roots and (volume_root / "main.tex").exists():
            roots = [volume_root / "main.tex"]

    missing = [root for root in roots if not root.exists()]
    if missing:
        raise SystemExit("missing TeX build root(s): " + ", ".join(str(path) for path in missing))
    if not roots:
        raise SystemExit(
            "no TeX build roots found. Expected one or more "
            "volume-{roman}.tex / volume-{roman}-{book-slug}.tex files, "
            "legacy volume-{roman}-{book-slug}-main.tex or main-book-*.tex files, "
            "or transitional main.tex."
        )
    return roots


def clean_args_for(tex_root: Path) -> list[str]:
    return ["latexmk", "-C", tex_root.name]


def latex_args_for(base_args: list[str] | None, tex_root: Path) -> list[str]:
    if base_args:
        return [*base_args, tex_root.name]
    return [*DEFAULT_LATEX_ARGS, tex_root.name]


def built_pdf_for(volume_root: Path, tex_root: Path) -> Path:
    return volume_root / "build" / f"{tex_root.stem}.pdf"


def copy_outputs(volume_root: Path, tex_roots: list[Path], output_dir: Path | None) -> None:
    if output_dir is None:
        return
    output_dir.mkdir(parents=True, exist_ok=True)
    for tex_root in tex_roots:
        pdf = built_pdf_for(volume_root, tex_root)
        if not pdf.exists():
            raise SystemExit(f"expected PDF was not produced: {pdf}")
        shutil.copy2(pdf, output_dir / pdf.name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build an LRA volume PDF through Docker.")
    parser.add_argument("--root", type=Path, default=Path("."), help="volume repo root")
    parser.add_argument("--common-root", type=Path, help="lra-common checkout root")
    parser.add_argument(
        "--checkout-common",
        type=Path,
        nargs="?",
        const=Path(tempfile.gettempdir()) / "lra-common-build-checkout",
        help="clone lra-common here if no checkout is found",
    )
    parser.add_argument("--image", default=IMAGE_NAME, help="Docker image tag to build/use")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--skip-validate", action="store_true")
    parser.add_argument("--skip-image-build", action="store_true")
    parser.add_argument("--edition", choices=("digital", "print"), default="digital")
    parser.add_argument("--paper", choices=("letter", "a4", "sixbynine"), default="letter")
    parser.add_argument("--print-edition", action="store_true", help="compatibility alias for --edition print")
    parser.add_argument("--clean", action="store_true", help="run latexmk -C in Docker before building")
    parser.add_argument(
        "--tex-root",
        action="append",
        help=(
            "specific TeX root to build, relative to --root; repeatable. Defaults to "
            "all canonical volume-{roman}.tex and volume-{roman}-{book-slug}.tex roots, "
            "legacy volume-{roman}-{book-slug}-main.tex or main-book-*.tex roots, "
            "or transitional main.tex."
        ),
    )
    parser.add_argument("--output-dir", type=Path, help="copy produced PDFs here after a successful build")
    parser.add_argument("--latex-command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)

    require_tool("docker")
    volume_root = args.root.expanduser().resolve()
    gov_root = governance_root()
    common_root = resolve_common_root(volume_root, args.common_root, args.checkout_common)
    tex_roots = discover_tex_roots(volume_root, args.tex_root)
    edition = "print" if args.print_edition else args.edition

    if not args.skip_validate:
        run([sys.executable, str(gov_root / "scripts" / "build_volume.py"), "--root", str(volume_root), "--validate-only"], volume_root)
    if args.validate_only:
        return 0

    if not args.skip_image_build:
        run(["docker", "build", "-t", args.image, "-f", str(common_root / "docker" / "Dockerfile"), str(common_root / "docker")])

    for tex_root in tex_roots:
        if args.clean:
            docker_run(volume_root, common_root, gov_root, args.image, edition, args.paper, clean_args_for(tex_root))
        docker_run(volume_root, common_root, gov_root, args.image, edition, args.paper, latex_args_for(args.latex_command, tex_root))
    copy_outputs(volume_root, tex_roots, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
