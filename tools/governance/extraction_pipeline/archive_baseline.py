#!/usr/bin/env python3
"""Archive current extraction inputs and explorer outputs for comparison.

The archive is a baseline, not a generated run log. It is meant to be committed
when the project needs a stable before/after comparison for pipeline changes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


DEFAULT_EXPLORER_FILES = (
    "knowledge.json",
    "graph-edges.json",
    "graph-edge-errors.json",
    "proof-errors.json",
    "proof-vault-index.json",
)


@dataclass
class ArchivedFile:
    source: str
    archived_as: str
    bytes: int
    sha256: str


@dataclass
class RepoState:
    repo: str
    path: str
    branch: str
    head: str
    status: str


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_file(source: Path, destination: Path) -> ArchivedFile:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return ArchivedFile(
        source=str(source),
        archived_as=destination.as_posix(),
        bytes=destination.stat().st_size,
        sha256=sha256(destination),
    )


def git_value(repo: Path, args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return result.stdout.strip()


def repo_state(repo: Path) -> RepoState:
    return RepoState(
        repo=repo.name,
        path=str(repo),
        branch=git_value(repo, ["branch", "--show-current"]),
        head=git_value(repo, ["rev-parse", "HEAD"]),
        status=git_value(repo, ["status", "--short"]),
    )


def volume_repos(repos_root: Path) -> list[Path]:
    return sorted(
        path
        for path in repos_root.glob("lra-volume-*")
        if path.is_dir() and (path / ".git").exists()
    )


def source_chapter_yamls(repo: Path) -> Iterable[Path]:
    for path in sorted(repo.rglob("chapter.yaml")):
        relative = path.relative_to(repo)
        first = relative.parts[0] if relative.parts else ""
        if first.startswith("volume-"):
            yield path


def archive_chapter_yamls(repos_root: Path, destination_root: Path) -> tuple[list[ArchivedFile], list[RepoState]]:
    archived: list[ArchivedFile] = []
    states: list[RepoState] = []
    for repo in volume_repos(repos_root):
        states.append(repo_state(repo))
        for chapter_yaml in source_chapter_yamls(repo):
            relative = chapter_yaml.relative_to(repo)
            destination = destination_root / "chapter-yamls" / repo.name / relative
            archived.append(copy_file(chapter_yaml, destination))
    return archived, states


def explorer_paths(root: Path) -> Iterable[Path]:
    for name in DEFAULT_EXPLORER_FILES:
        path = root / name
        if path.is_file():
            yield path
    reorder = root / "reorder"
    if reorder.is_dir():
        for path in sorted(reorder.rglob("*")):
            if path.is_file() and path.name != ".gitignore":
                yield path


def archive_explorer(root: Path, destination_root: Path) -> tuple[list[ArchivedFile], RepoState]:
    archived: list[ArchivedFile] = []
    for path in explorer_paths(root):
        destination = destination_root / "knowledge-explorer" / path.relative_to(root)
        archived.append(copy_file(path, destination))
    return archived, repo_state(root)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repos-root",
        type=Path,
        default=Path(__file__).resolve().parents[4],
        help="Workspace containing lra-volume-* and lra-knowledge-explorer repos.",
    )
    parser.add_argument(
        "--knowledge-explorer",
        type=Path,
        default=None,
        help="Path to lra-knowledge-explorer. Defaults to <repos-root>/lra-knowledge-explorer.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "baselines" / "extraction",
        help="Directory that will receive the timestamped baseline archive.",
    )
    parser.add_argument(
        "--run-id",
        default="",
        help="Optional archive id. Defaults to baseline-YYYYMMDD-HHMMSS.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repos_root = args.repos_root.resolve()
    knowledge_explorer = (args.knowledge_explorer or repos_root / "lra-knowledge-explorer").resolve()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_id = args.run_id or f"baseline-{timestamp}"
    output_root = (args.output_root / run_id).resolve()

    if output_root.exists():
        raise SystemExit(f"Archive already exists: {output_root}")
    if not knowledge_explorer.is_dir():
        raise SystemExit(f"Missing lra-knowledge-explorer repo: {knowledge_explorer}")

    chapter_files, volume_states = archive_chapter_yamls(repos_root, output_root)
    explorer_files, explorer_state = archive_explorer(knowledge_explorer, output_root)

    manifest = {
        "run_id": run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "repos_root": str(repos_root),
        "archive_root": str(output_root),
        "counts": {
            "volume_repos": len(volume_states),
            "chapter_yamls": len(chapter_files),
            "explorer_files": len(explorer_files),
            "archived_files": len(chapter_files) + len(explorer_files),
        },
        "repos": {
            "volumes": [asdict(state) for state in volume_states],
            "knowledge_explorer": asdict(explorer_state),
        },
        "files": {
            "chapter_yamls": [asdict(item) for item in chapter_files],
            "knowledge_explorer": [asdict(item) for item in explorer_files],
        },
    }
    manifest_path = output_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Archived baseline: {output_root}")
    print(f"Chapter YAML files: {len(chapter_files)}")
    print(f"Explorer files: {len(explorer_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
