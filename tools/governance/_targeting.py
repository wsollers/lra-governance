"""Shared target discovery for LRA governance validators."""

from __future__ import annotations

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
    "volume-iii/analysis/real-analysis",
    "volume-iv/algebra/index.tex",
    "volume-iv/algebra/algebraic-structures",
}


@dataclass(frozen=True)
class Target:
    scope: str
    root: Path
    volume: Path | None = None
    chapter: Path | None = None
    section: str | None = None
    notes_dir: Path | None = None
    proofs_dir: Path | None = None


def is_volume_root(path: Path) -> bool:
    return path.is_dir() and VOLUME_RE.match(path.name) is not None and (path / "index.tex").exists()


def is_chapter_root(path: Path) -> bool:
    return path.is_dir() and (path / "notes").is_dir() and (path / "proofs").is_dir()


def relative_posix(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def is_ignored_path(path: Path, root: Path | None = None) -> bool:
    if any(part in IGNORED_DIR_NAMES for part in path.parts):
        return True
    if root is None:
        return False
    rel = relative_posix(path, root)
    full = path.resolve().as_posix()
    return any(
        rel == ignored
        or rel.startswith(f"{ignored}/")
        or full.endswith("/" + ignored)
        or f"/{ignored}/" in full
        for ignored in IGNORED_RELATIVE_DIRS
    )


def volume_roots(root: Path) -> list[Path]:
    root = root.resolve()
    if is_volume_root(root):
        return [root]
    if not root.is_dir():
        return []
    direct = [path for path in root.iterdir() if not is_ignored_path(path, root) and is_volume_root(path)]
    if direct:
        return sorted(path.resolve() for path in direct)
    return sorted(
        path.resolve()
        for path in root.rglob("volume-*")
        if not is_ignored_path(path, root) and is_volume_root(path)
    )


def chapter_roots(root: Path, volume: Path | None = None) -> list[Path]:
    root = root.resolve()
    if is_chapter_root(root):
        return [root]
    roots: list[Path] = []
    volumes = [volume.resolve()] if volume else volume_roots(root)
    for volume_root in volumes:
        if not volume_root.is_dir():
            continue
        roots.extend(
            path.resolve()
            for path in volume_root.iterdir()
            if path.is_dir() and not is_ignored_path(path, root) and is_chapter_root(path)
        )
    return sorted(set(roots))


def _absolute_or_under(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def _matches(path: Path, value: str | Path, root: Path) -> bool:
    text = str(value).replace("\\", "/").removesuffix("/")
    if not text:
        return False
    candidate = _absolute_or_under(root, value)
    try:
        rel = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        rel = path.resolve().as_posix()
    return path.resolve() == candidate or path.name == text or rel == text or rel.endswith(f"/{text}")


def resolve_volume(root: Path, value: str | Path | None) -> Path | None:
    if value is None:
        return None
    roots = [path for path in volume_roots(root) if _matches(path, value, root)]
    if len(roots) == 1:
        return roots[0]
    if not roots:
        raise ValueError(f"No volume target matches {value!s}.")
    raise ValueError(f"Volume target {value!s} is ambiguous: {', '.join(path.name for path in roots)}.")


def resolve_chapter(root: Path, value: str | Path | None, volume_value: str | Path | None = None) -> Path | None:
    if value is None:
        return None
    volume = resolve_volume(root, volume_value)
    roots = [path for path in chapter_roots(root, volume) if _matches(path, value, root)]
    if len(roots) == 1:
        return roots[0]
    if not roots:
        raise ValueError(f"No chapter target matches {value!s}.")
    names = ", ".join(path.as_posix() for path in roots)
    raise ValueError(f"Chapter target {value!s} is ambiguous: {names}.")


def section_names(chapter: Path) -> set[str]:
    names: set[str] = set()
    for parent_name in ("notes", "proofs"):
        parent = chapter / parent_name
        if not parent.is_dir():
            continue
        names.update(
            path.name
            for path in parent.iterdir()
            if path.is_dir()
            and not path.name.startswith(".")
            and path.name not in {"exercises", "notes"}
            and not is_ignored_path(path)
        )
    return names


def _section_name_from_path(path: Path) -> str | None:
    parts = path.parts
    for anchor in ("notes", "proofs"):
        if anchor in parts:
            index = parts.index(anchor)
            if index + 1 < len(parts):
                return parts[index + 1]
    return path.name if path.suffix == "" else path.stem


def resolve_section(
    root: Path,
    value: str | Path | None,
    chapter_value: str | Path | None = None,
    volume_value: str | Path | None = None,
) -> Target | None:
    if value is None:
        return None
    root = root.resolve()
    explicit_chapter = resolve_chapter(root, chapter_value, volume_value)
    candidates = chapter_roots(root, resolve_volume(root, volume_value)) if explicit_chapter is None else [explicit_chapter]
    possible_path = _absolute_or_under(root, value)
    raw_name = _section_name_from_path(Path(str(value).replace("\\", "/")))
    matches: list[Target] = []
    for chapter in candidates:
        for section in sorted(section_names(chapter)):
            notes_dir = chapter / "notes" / section
            proofs_dir = chapter / "proofs" / section
            section_paths = [path for path in (notes_dir, proofs_dir) if path.exists()]
            if (
                raw_name == section
                or any(path.resolve() == possible_path for path in section_paths)
                or any(_matches(path, value, root) for path in section_paths)
            ):
                matches.append(
                    Target(
                        scope="section",
                        root=root,
                        volume=chapter.parent,
                        chapter=chapter,
                        section=section,
                        notes_dir=notes_dir if notes_dir.exists() else None,
                        proofs_dir=proofs_dir if proofs_dir.exists() else None,
                    )
                )
    unique = {(target.chapter, target.section): target for target in matches}
    matches = list(unique.values())
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise ValueError(f"No section target matches {value!s}.")
    names = ", ".join(f"{target.chapter.name}/{target.section}" for target in matches if target.chapter)
    raise ValueError(f"Section target {value!s} is ambiguous: {names}. Pass --chapter to disambiguate.")


def resolve_target(
    root: Path,
    volume: str | Path | None = None,
    chapter: str | Path | None = None,
    section: str | Path | None = None,
) -> Target:
    root = root.resolve()
    section_target = resolve_section(root, section, chapter, volume)
    if section_target:
        return section_target
    chapter_path = resolve_chapter(root, chapter, volume)
    if chapter_path:
        return Target(scope="chapter", root=root, volume=chapter_path.parent, chapter=chapter_path)
    volume_path = resolve_volume(root, volume)
    if volume_path:
        return Target(scope="volume", root=root, volume=volume_path)
    return Target(scope="repo", root=root)


def target_chapters(target: Target) -> list[Path]:
    if target.chapter:
        return [target.chapter]
    if target.volume:
        return chapter_roots(target.root, target.volume)
    return chapter_roots(target.root)


def note_validation_paths(target: Target) -> list[Path]:
    if target.scope == "section":
        return [target.notes_dir] if target.notes_dir else []
    chapters = target_chapters(target)
    return [chapter / "notes" for chapter in chapters if (chapter / "notes").is_dir()]


def proof_validation_paths(target: Target) -> list[Path]:
    if target.scope == "section":
        return [target.proofs_dir] if target.proofs_dir else []
    chapters = target_chapters(target)
    return [chapter / "proofs" for chapter in chapters if (chapter / "proofs").is_dir()]


def discovery_lines(root: Path) -> list[str]:
    root = root.resolve()
    lines = [f"root: {root}"]
    for volume in volume_roots(root):
        lines.append(f"volume: {volume.name}")
        for chapter in chapter_roots(root, volume):
            lines.append(f"  chapter: {chapter.name}")
            for section in sorted(section_names(chapter)):
                notes = "notes" if (chapter / "notes" / section).exists() else ""
                proofs = "proofs" if (chapter / "proofs" / section).exists() else ""
                suffix = ", ".join(part for part in (notes, proofs) if part)
                lines.append(f"    section: {section}" + (f" ({suffix})" if suffix else ""))
    return lines
