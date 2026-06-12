from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path


VOLUME_RE = re.compile(r"^volume-(?:i|ii|iii|iv|v|vi|vii|viii)$")

IGNORED_DIR_NAMES = {
    ".git",
    ".history",
    ".venv",
    "__pycache__",
    "archive",
    "build",
    "common",
    "dist",
    "node_modules",
    "out",
    "output",
    "outputs",
    "reports",
    "venv",
}


@dataclass(frozen=True)
class Volume:
    root: Path
    source: Path


def resolve_volume(value: str | Path) -> Volume:
    root = Path(value).resolve()
    if not root.exists():
        raise FileNotFoundError(root)
    if root.is_dir() and VOLUME_RE.fullmatch(root.name):
        return Volume(root=root, source=root)
    if root.is_dir():
        children = [child for child in root.iterdir() if child.is_dir() and VOLUME_RE.fullmatch(child.name)]
        if len(children) == 1:
            return Volume(root=children[0].resolve(), source=root)
    raise ValueError(f"Could not resolve a single volume-* directory from {root}")


def is_ignored(path: Path) -> bool:
    return any(part in IGNORED_DIR_NAMES or part.startswith(".") for part in path.parts)


def is_chapter_root(path: Path) -> bool:
    return path.is_dir() and (path / "notes").is_dir() and (path / "proofs").is_dir()


def chapter_roots(volume_root: Path) -> list[Path]:
    volume_root = volume_root.resolve()
    chapters: list[Path] = []
    for dirpath, dirnames, _filenames in os.walk(volume_root):
        current = Path(dirpath)
        dirnames[:] = [
            name
            for name in dirnames
            if name not in IGNORED_DIR_NAMES and not name.startswith(".")
        ]
        if is_chapter_root(current):
            chapters.append(current.resolve())
            dirnames[:] = [name for name in dirnames if name not in {"notes", "proofs"}]
    return sorted(set(chapters))


def iter_tex(root: Path):
    if root.is_file() and root.suffix == ".tex":
        yield root
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            name
            for name in dirnames
            if name not in IGNORED_DIR_NAMES and not name.startswith(".")
        ]
        for filename in filenames:
            if filename.endswith(".tex"):
                yield Path(dirpath) / filename


def latex_input_path(path: Path) -> str:
    parts = path.with_suffix("").resolve().parts
    for index, part in enumerate(parts):
        if VOLUME_RE.fullmatch(part):
            return Path(*parts[index:]).as_posix()
    return path.with_suffix("").as_posix()
