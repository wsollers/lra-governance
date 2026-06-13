from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

from .tex import INPUT_RE, read_text, strip_latex_comments
from .volume import VOLUME_RE, is_ignored


DEFAULT_SUFFIXES = (".tex",)


def files_to_validate(
    volumes: Iterable[Path | str] | Path | str,
    *,
    only_reachable: bool = True,
    excluded: bool = False,
    include_excluded: bool | None = None,
    suffixes: tuple[str, ...] = DEFAULT_SUFFIXES,
) -> list[Path]:
    """Return the canonical sorted file inventory for validators and tools.

    By default this returns reachable files and omits excluded paths. The
    ``excluded`` flag means "include excluded paths"; ``include_excluded`` is
    accepted as a more explicit alias for callers that prefer it.
    """
    include_excluded = excluded if include_excluded is None else include_excluded
    files: set[Path] = set()
    for volume in _as_roots(volumes):
        root = Path(volume).resolve()
        if only_reachable:
            candidates = reachable_files(root, include_excluded=include_excluded, suffixes=suffixes)
        else:
            candidates = all_files(root, include_excluded=include_excluded, suffixes=suffixes)
        files.update(candidates)
    return sorted(files)


def reachable_files(
    root: Path | str,
    *,
    include_excluded: bool = False,
    suffixes: tuple[str, ...] = DEFAULT_SUFFIXES,
) -> set[Path]:
    root = Path(root).resolve()
    volume_root = enclosing_volume_root(root)
    if root.is_file():
        if _has_suffix(root, suffixes) and (include_excluded or not is_ignored(root, volume_root)):
            return {root}
        return set()

    entry = root / "index.tex"
    if not entry.exists():
        return set(all_files(root, include_excluded=include_excluded, suffixes=suffixes))

    included: set[Path] = set()
    pending = [entry.resolve()]
    while pending:
        current = pending.pop()
        if current in included:
            continue
        if not include_excluded and is_ignored(current, volume_root):
            continue
        try:
            current.relative_to(volume_root)
        except ValueError:
            continue
        if not current.exists() or not current.is_file() or not _has_suffix(current, suffixes):
            continue
        included.add(current)
        for target in input_paths(current, volume_root, include_excluded=include_excluded):
            if target not in included:
                pending.append(target)
    return included


def all_files(
    root: Path | str,
    *,
    include_excluded: bool = False,
    suffixes: tuple[str, ...] = DEFAULT_SUFFIXES,
) -> list[Path]:
    root = Path(root).resolve()
    volume_root = enclosing_volume_root(root)
    if root.is_file():
        if _has_suffix(root, suffixes) and (include_excluded or not is_ignored(root, volume_root)):
            return [root]
        return []

    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        if not include_excluded:
            dirnames[:] = [
                name
                for name in dirnames
                if not is_ignored(current / name, volume_root)
            ]
        for filename in filenames:
            path = current / filename
            if _has_suffix(path, suffixes) and (include_excluded or not is_ignored(path, volume_root)):
                files.append(path.resolve())
    return sorted(files)


def input_paths(
    source: Path,
    volume_root: Path,
    *,
    include_excluded: bool = False,
) -> list[Path]:
    text = strip_latex_comments(read_text(source))
    paths: list[Path] = []
    for match in INPUT_RE.finditer(text):
        target = match.group(1).replace("\\", "/").removesuffix(".tex")
        candidates = input_candidates(target, source, volume_root)
        for candidate in candidates:
            resolved = candidate.resolve()
            if candidate.exists() and candidate.is_file() and (include_excluded or not is_ignored(resolved, volume_root)):
                paths.append(resolved)
                break
    return paths


def input_candidates(target: str, source: Path, volume_root: Path) -> list[Path]:
    target_path = Path(target)
    bases: list[Path] = []
    if target.startswith(f"{volume_root.name}/"):
        bases.append(volume_root.parent / target_path)
    else:
        bases.extend([volume_root / target_path, source.parent / target_path])

    candidates: list[Path] = []
    for base in bases:
        candidates.append(base.with_suffix(".tex"))
        candidates.append(base / "index.tex")
    return candidates


def enclosing_volume_root(path: Path | str) -> Path:
    path = Path(path).resolve()
    current = path if path.is_dir() else path.parent
    for candidate in [current, *current.parents]:
        if VOLUME_RE.fullmatch(candidate.name):
            return candidate.resolve()
    return path


def _has_suffix(path: Path, suffixes: tuple[str, ...]) -> bool:
    return not suffixes or path.suffix in suffixes


def _as_roots(volumes: Iterable[Path | str] | Path | str) -> Iterable[Path | str]:
    if isinstance(volumes, (str, Path)):
        return [volumes]
    return volumes
