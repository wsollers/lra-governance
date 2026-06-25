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
    "lean",
    "node_modules",
    "out",
    "output",
    "outputs",
    "proof-techniques",
    "reports",
    "venv",
}

IGNORED_RELATIVE_DIRS = {
    "book-analysis-i/real-analysis",
    "book-discrete-algebraic/integers/notes/mendelson-construction",
    "book-discrete-algebraic/integers/notes/tao-construction",
    "book-discrete-algebraic/integers/proofs/mendelson-construction",
    "book-discrete-algebraic/integers/proofs/tao-construction",
    "volume-iii/book-analysis-i/real-analysis",
    "volume-ii/book-discrete-algebraic/integers/notes/mendelson-construction",
    "volume-ii/book-discrete-algebraic/integers/notes/tao-construction",
    "volume-ii/book-discrete-algebraic/integers/proofs/mendelson-construction",
    "volume-ii/book-discrete-algebraic/integers/proofs/tao-construction",
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


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _parts_for_ignore(path: Path, root: Path | None) -> tuple[str, ...]:
    if root is None:
        return path.parts
    try:
        return path.resolve().relative_to(root.resolve()).parts
    except ValueError:
        return path.parts


def is_ignored(path: Path, root: Path | None = None) -> bool:
    if any(part in IGNORED_DIR_NAMES or part.startswith(".") for part in _parts_for_ignore(path, root)):
        return True
    if root is None:
        return False
    rel = _relative_posix(path, root)
    full = path.resolve().as_posix()
    return any(rel == ignored or rel.startswith(f"{ignored}/") or full.endswith(f"/{ignored}") for ignored in IGNORED_RELATIVE_DIRS)


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
            if not is_ignored(current / name, volume_root)
        ]
        if is_chapter_root(current):
            chapters.append(current.resolve())
            dirnames[:] = [name for name in dirnames if name not in {"notes", "proofs"}]
    return sorted(set(chapters))


def iter_all_tex(root: Path):
    from .file_inventory import all_files

    yield from all_files(root)


def included_tex_files(root: Path) -> set[Path]:
    from .file_inventory import reachable_files

    return reachable_files(root)


def iter_tex(root: Path):
    from .file_inventory import files_to_validate

    yield from files_to_validate([root])


def latex_input_path(path: Path) -> str:
    parts = path.with_suffix("").resolve().parts
    for index, part in enumerate(parts):
        if VOLUME_RE.fullmatch(part):
            return Path(*parts[index:]).as_posix()
    return path.with_suffix("").as_posix()
