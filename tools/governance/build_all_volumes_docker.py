#!/usr/bin/env python3
"""Build one combined all-volume LRA PDF through Docker."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


IMAGE_NAME = "learning-real-analysis-latex"
DEFAULT_LATEX_ARGS = [
    "latexmk",
    "-f",
    "-lualatex",
    "-interaction=nonstopmode",
    "-file-line-error",
    "-synctex=1",
    "-shell-escape",
    "-output-directory=build",
]


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+ " + " ".join(str(part) for part in cmd))
    try:
        subprocess.run(cmd, cwd=cwd, check=True)
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


def resolve_common_root(repos_root: Path, explicit: Path | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(explicit)
    env = os.environ.get("LRA_COMMON_ROOT")
    if env:
        candidates.append(Path(env))
    candidates.append(repos_root / "lra-common")
    candidates.append(governance_root().parent / "lra-common")

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.expanduser().resolve(strict=False)
        if resolved in seen:
            continue
        seen.add(resolved)
        if (resolved / "common" / "volume-preamble.tex").exists() and (resolved / "docker" / "Dockerfile").exists():
            return resolved
    raise SystemExit("lra-common checkout not found. Pass --common-root or place lra-common under --repos-root.")


def docker_path(path: Path) -> str:
    return str(path.resolve())


def texinputs_for(volumes: list[str]) -> str:
    pieces = ["/workspace", "/workspace/common"]
    pieces.extend(f"/lra-repos/lra-volume-{roman}" for roman in volumes)
    return ":".join(pieces) + ":"


def bibinputs_for(volumes: list[str]) -> str:
    pieces = ["/workspace"]
    pieces.extend(f"/lra-repos/lra-volume-{roman}" for roman in volumes)
    pieces.extend(f"/lra-repos/lra-volume-{roman}/bibliography" for roman in volumes)
    return ":".join(pieces) + ":"


def verify_pdf(pdf: Path) -> None:
    if not pdf.exists():
        raise SystemExit(f"expected PDF was not produced: {pdf}")
    data = pdf.read_bytes()
    if not data.startswith(b"%PDF-"):
        raise SystemExit(f"{pdf} does not start with a PDF header")
    if b"%%EOF" not in data[-2048:]:
        raise SystemExit(f"{pdf} is missing a PDF EOF trailer")


def latex_args_for(base_args: list[str] | None, tex_name: str) -> list[str]:
    if base_args:
        return [*base_args, tex_name]
    return [*DEFAULT_LATEX_ARGS, tex_name]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build one PDF containing all LRA volumes.")
    parser.add_argument("--repos-root", type=Path, default=Path(".").resolve().parent)
    parser.add_argument("--common-root", type=Path)
    parser.add_argument("--work-dir", type=Path, default=Path("build") / "all-volumes")
    parser.add_argument("--output-dir", type=Path, default=Path("pdf-output") / "all-volumes")
    parser.add_argument("--image", default=IMAGE_NAME)
    parser.add_argument("--skip-image-build", action="store_true")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--title", default="From Cantor to Ito")
    parser.add_argument("--stem", default="from-cantor-to-ito")
    parser.add_argument("--edition", choices=("digital", "print", "reference"), default="digital")
    parser.add_argument(
        "--volume",
        action="append",
        choices=("i", "ii", "iii", "iv", "v", "vi", "vii", "viii"),
        help="volume roman numeral to include; repeatable. Defaults to all volumes.",
    )
    parser.add_argument("--latex-command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)

    require_tool("docker")
    gov_root = governance_root()
    repos_root = args.repos_root.expanduser().resolve()
    common_root = resolve_common_root(repos_root, args.common_root)
    volumes = args.volume or ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii"]
    work_dir = args.work_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    tex_name = f"{args.stem}.tex"
    pdf_name = f"{args.stem}.pdf"
    work_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_image_build:
        run(["docker", "build", "-t", args.image, "-f", str(common_root / "docker" / "Dockerfile"), str(common_root / "docker")])

    assemble_cmd = [
        "python3",
        "/lra-governance/tools/governance/assemble_all_volumes_tex.py",
        "--repos-root",
        "/lra-repos",
        "--out",
        f"/workspace/{tex_name}",
        "--title",
        args.title,
        "--edition",
        args.edition,
    ]
    for volume in volumes:
        assemble_cmd.extend(["--volume", volume])

    docker_prefix = [
        "docker",
        "run",
        "--rm",
        "-e",
        "LRA_GOVERNANCE_ROOT=/lra-governance",
        "-e",
        f"LRA_EDITION={args.edition}",
        "-e",
        "LRA_PAPER=letter",
        "-e",
        f"TEXINPUTS={texinputs_for(volumes)}",
        "-e",
        f"BIBINPUTS={bibinputs_for(volumes)}",
        "-v",
        f"{docker_path(work_dir)}:/workspace",
        "-v",
        f"{docker_path(common_root / 'common')}:/workspace/common:ro",
        "-v",
        f"{docker_path(gov_root)}:/lra-governance:ro",
        "-v",
        f"{docker_path(repos_root)}:/lra-repos:ro",
        "-w",
        "/workspace",
    ]
    if args.edition == "print":
        docker_prefix.extend(["-e", "LRA_PRINT_EDITION=1"])
    docker_prefix.append(args.image)

    run([*docker_prefix, *assemble_cmd])
    if args.clean:
        run([*docker_prefix, "latexmk", "-C", tex_name])
    run([*docker_prefix, *latex_args_for(args.latex_command, tex_name)])

    pdf = work_dir / "build" / pdf_name
    verify_pdf(pdf)
    shutil.copy2(pdf, output_dir / pdf_name)
    print(f"wrote {output_dir / pdf_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
