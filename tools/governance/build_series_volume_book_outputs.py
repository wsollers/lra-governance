#!/usr/bin/env python3
"""Build volume-level and book-level PDFs for the whole LRA series."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROMANS = ("i", "ii", "iii", "iv", "v", "vi", "vii", "viii")
EDITIONS = ("digital", "print", "reference")


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+ " + " ".join(str(part) for part in cmd))
    try:
        subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from None


def registry() -> dict:
    path = Path(__file__).resolve().parents[2] / "docs" / "architecture" / "book-registry.json"
    return json.loads(path.read_text(encoding="utf-8"))


def build_volume_roots(args: argparse.Namespace, volume: dict, edition: str) -> None:
    roman = str(volume["roman"])
    volume_repo = args.repos_root / f"lra-volume-{roman}"
    output_dir = args.output_dir / edition / "volumes"
    cmd = [
        sys.executable,
        str(Path(__file__).resolve().parent / "build_volume_docker.py"),
        "--root",
        str(volume_repo),
        "--common-root",
        str(args.common_root),
        "--skip-validate",
        "--skip-image-build",
        "--edition",
        edition,
        "--tex-root",
        f"volume-{roman}.tex",
        "--output-dir",
        str(output_dir),
    ]
    run(cmd, args.repos_root)


def build_book_roots(args: argparse.Namespace, volume: dict, edition: str) -> None:
    roman = str(volume["roman"])
    volume_repo = args.repos_root / f"lra-volume-{roman}"
    output_dir = args.output_dir / edition / "books"
    cmd = [
        sys.executable,
        str(Path(__file__).resolve().parent / "build_volume_docker.py"),
        "--root",
        str(volume_repo),
        "--common-root",
        str(args.common_root),
        "--skip-validate",
        "--skip-image-build",
        "--edition",
        edition,
        "--output-dir",
        str(output_dir),
    ]
    for book in sorted(volume.get("books", []), key=lambda item: int(item.get("order", 0))):
        tex_root = str(book.get("tex_root") or "")
        if not tex_root:
            raise SystemExit(f"missing book tex_root in registry entry: {book!r}")
        cmd.extend(["--tex-root", tex_root])
    run(cmd, args.repos_root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build all series volume and book PDFs.")
    parser.add_argument("--repos-root", type=Path, required=True)
    parser.add_argument("--common-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("pdf-output"))
    parser.add_argument("--edition", action="append", choices=EDITIONS)
    parser.add_argument("--volume", action="append", choices=ROMANS)
    args = parser.parse_args(argv)

    args.repos_root = args.repos_root.expanduser().resolve()
    args.common_root = args.common_root.expanduser().resolve()
    args.output_dir = args.output_dir.expanduser().resolve()

    requested_editions = tuple(args.edition or EDITIONS)
    requested_volumes = set(args.volume or ROMANS)
    volumes = [
        volume
        for volume in registry().get("volumes", [])
        if str(volume.get("roman")) in requested_volumes
    ]
    volumes.sort(key=lambda item: int(item.get("volume_number", 0)))

    for edition in requested_editions:
        for volume in volumes:
            build_volume_roots(args, volume, edition)
            build_book_roots(args, volume, edition)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
