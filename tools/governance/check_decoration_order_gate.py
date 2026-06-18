#!/usr/bin/env python3
"""Fail if any volume has out-of-order formal decoration blocks."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core.volume import resolve_volume
from validators import formal_decoration


def volume_repos(root: Path) -> list[Path]:
    if root.name.startswith("lra-volume-"):
        return [root]
    return sorted(path for path in root.glob("lra-volume-*") if path.is_dir())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="A repos root containing lra-volume-* repos, or one volume repo.",
    )
    args = parser.parse_args()

    findings = []
    for repo in volume_repos(args.root.resolve()):
        try:
            volume = resolve_volume(repo)
        except (FileNotFoundError, ValueError) as exc:
            print(f"fatal: {repo}: {exc}", file=sys.stderr)
            return 1
        for finding in formal_decoration.validate(volume.root):
            if finding.code == "decoration_order":
                findings.append((repo.name, finding))

    if not findings:
        print("decoration order gate: clean")
        return 0

    print(f"decoration order gate: {len(findings)} issue(s)")
    for repo, finding in findings:
        print(f"{repo}: {finding.path}:{finding.line} {finding.message}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
