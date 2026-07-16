#!/usr/bin/env python3
"""Inventory routed formal artifacts in an LRA volume repository."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "tools" / "governance") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools" / "governance"))

from core.file_inventory import input_paths  # noqa: E402
from core.tex import read_text, strip_latex_comments  # noqa: E402
from core.volume import VOLUME_RE, is_ignored  # noqa: E402


FORMAL_ENV_RE = re.compile(
    r"\\begin\{(?P<env>definition|axiom|theorem|lemma|proposition|corollary)\}"
    r"(?:\[(?P<title>[^\]]+)\])?",
    re.IGNORECASE,
)
FORMAL_BEGIN_OR_BOX_RE = re.compile(
    r"\\begin\{(?:definition|axiom|theorem|lemma|proposition|corollary)(?:box)?\}",
    re.IGNORECASE,
)
FORMAL_PREFIX_RE = re.compile(r"^(def|ax|thm|lem|prop|cor):")
LABEL_RE = re.compile(r"\\label\{(?P<label>[^{}]+)\}")
LRA_META_RE = re.compile(r"(?P<key>series|volume|book|chapter)\s*=\s*\{(?P<value>[^{}]+)\}")
VOLUME_NAMES = {
    "i": "lra-volume-i",
    "ii": "lra-volume-ii",
    "iii": "lra-volume-iii",
    "iv": "lra-volume-iv",
    "v": "lra-volume-v",
    "vi": "lra-volume-vi",
    "vii": "lra-volume-vii",
    "viii": "lra-volume-viii",
}


@dataclass(frozen=True)
class RoutedFormal:
    label: str
    kind: str
    title: str | None
    source_file: Path
    line_start: int
    line_end: int
    text: str
    book_root: Path
    book: str | None
    chapter: str | None
    section: str | None

    def as_json(self, repo_root: Path) -> dict[str, Any]:
        return {
            "label": self.label,
            "kind": self.kind,
            "title": self.title,
            "book": self.book,
            "chapter": self.chapter,
            "section": self.section,
            "book_root": self.book_root.relative_to(repo_root).as_posix(),
            "source_file": self.source_file.relative_to(repo_root).as_posix(),
            "source_line_start": self.line_start,
            "source_line_end": self.line_end,
            "artifact_package": artifact_package_for(self, repo_root),
        }


def resolve_repo_root(repos_root: Path | None, volume_root: Path | None, volume: str | None) -> Path:
    if volume_root is not None:
        root = volume_root.resolve()
        if VOLUME_RE.fullmatch(root.name):
            return root.parent
        return root
    if repos_root is None or volume is None:
        raise ValueError("either --volume-root or both --repos-root and --volume are required")
    repo_name = VOLUME_NAMES.get(volume)
    if not repo_name:
        raise ValueError(f"unknown volume {volume!r}")
    root = (repos_root / repo_name).resolve()
    if not root.exists():
        raise FileNotFoundError(root)
    return root


def resolve_volume_source(repo_root: Path, volume: str | None) -> Path:
    candidates = [child for child in repo_root.iterdir() if child.is_dir() and VOLUME_RE.fullmatch(child.name)]
    if volume:
        expected = f"volume-{volume}"
        candidates = [child for child in candidates if child.name == expected]
    if len(candidates) != 1:
        raise ValueError(f"could not resolve one volume source under {repo_root}")
    return candidates[0].resolve()


def book_roots(repo_root: Path, volume_source: Path) -> list[Path]:
    prefix = f"{volume_source.name}-"
    roots = [
        path.resolve()
        for path in repo_root.glob(f"{prefix}*.tex")
        if path.name != f"{volume_source.name}.tex" and path.is_file()
    ]
    return sorted(roots)


def line_for_offset(text: str, offset: int) -> int:
    return text[:offset].count("\n") + 1


def ordered_reachable_files(entry: Path, volume_source: Path) -> list[Path]:
    ordered: list[Path] = []
    seen: set[Path] = set()

    def visit(path: Path) -> None:
        resolved = path.resolve()
        if resolved in seen:
            return
        seen.add(resolved)
        if not resolved.exists() or not resolved.is_file() or resolved.suffix != ".tex":
            return
        if resolved != entry.resolve():
            try:
                resolved.relative_to(volume_source)
            except ValueError:
                return
            if is_ignored(resolved, volume_source):
                return
        ordered.append(resolved)
        for target in input_paths(resolved, volume_source):
            visit(target)

    visit(entry)
    return ordered


def file_context(path: Path, volume_source: Path) -> tuple[str | None, str | None, str | None]:
    book = chapter = section = None
    try:
        rel = path.relative_to(volume_source).parts
    except ValueError:
        rel = ()
    if len(rel) >= 1:
        book = rel[0]
    if len(rel) >= 2:
        chapter = rel[1]
    if "notes" in rel:
        index = rel.index("notes")
        if len(rel) > index + 1:
            section = rel[index + 1] if rel[index + 1] != "index.tex" else None
    if "proofs" in rel:
        index = rel.index("proofs")
        if len(rel) > index + 1:
            section = rel[index + 1] if rel[index + 1] != "index.tex" else section

    if path.name == "index.tex":
        meta = dict(LRA_META_RE.findall(strip_latex_comments(read_text(path))))
        chapter_text = meta.get("chapter")
        if chapter_text and ":" in chapter_text:
            chapter = chapter or path.parent.name
    return book, chapter, section


def formal_blocks_in_file(path: Path, book_root: Path, volume_source: Path) -> list[RoutedFormal]:
    text = read_text(path)
    starts = list(FORMAL_BEGIN_OR_BOX_RE.finditer(text))
    book, chapter, section = file_context(path, volume_source)
    blocks: list[RoutedFormal] = []
    for index, start in enumerate(starts):
        next_start = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        block = text[start.start() : next_start]
        env_match = FORMAL_ENV_RE.search(block)
        label_match = LABEL_RE.search(block)
        if not env_match or not label_match:
            continue
        label = label_match.group("label")
        if not FORMAL_PREFIX_RE.match(label):
            continue
        blocks.append(
            RoutedFormal(
                label=label,
                kind=env_match.group("env").lower(),
                title=env_match.group("title"),
                source_file=path,
                line_start=line_for_offset(text, start.start()),
                line_end=line_for_offset(text, next_start),
                text=block,
                book_root=book_root,
                book=book,
                chapter=chapter,
                section=section,
            )
        )
    return blocks


def normalized(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")


def matches_filter(item: RoutedFormal, args: argparse.Namespace, repo_root: Path) -> bool:
    if args.book:
        book_value = normalized(args.book)
        book_root_value = normalized(item.book_root.stem)
        if book_value not in {normalized(item.book), book_root_value}:
            return False
    if args.chapter and normalized(args.chapter) not in {normalized(item.chapter), normalized(Path(item.source_file).parent.name)}:
        return False
    if args.section and normalized(args.section) != normalized(item.section):
        return False
    if args.label and args.label != item.label:
        return False
    if args.target:
        target = (repo_root / args.target).resolve() if not args.target.is_absolute() else args.target.resolve()
        try:
            item.source_file.resolve().relative_to(target)
        except ValueError:
            return False
    return True


def artifact_package_for(item: RoutedFormal, repo_root: Path) -> dict[str, Any]:
    slug = item.label.replace(":", "-")
    section_dir = item.source_file.parent
    package_dir = section_dir / slug
    artifact = package_dir / "artifact.yaml"
    corrected = package_dir / "corrected.tex"
    return {
        "directory": package_dir.relative_to(repo_root).as_posix(),
        "artifact": artifact.relative_to(repo_root).as_posix(),
        "corrected_tex": corrected.relative_to(repo_root).as_posix(),
        "exists": artifact.exists() and corrected.exists(),
    }


def routed_formals(args: argparse.Namespace) -> tuple[Path, Path, list[Path], list[RoutedFormal]]:
    repo_root = resolve_repo_root(args.repos_root, args.volume_root, args.volume)
    volume_source = resolve_volume_source(repo_root, args.volume)
    items: list[RoutedFormal] = []
    roots = book_roots(repo_root, volume_source)
    for root in roots:
        for path in ordered_reachable_files(root, volume_source):
            if path == root:
                continue
            items.extend(formal_blocks_in_file(path, root, volume_source))
    filtered = [item for item in items if matches_filter(item, args, repo_root)]
    return repo_root, volume_source, roots, filtered


def inventory(args: argparse.Namespace) -> dict[str, Any]:
    repo_root, volume_source, roots, filtered = routed_formals(args)
    return {
        "schema_version": "lra.semantic-artifact-inventory/1.0",
        "repo_root": str(repo_root),
        "volume_source": volume_source.relative_to(repo_root).as_posix(),
        "filters": {
            "volume": args.volume,
            "book": args.book,
            "chapter": args.chapter,
            "section": args.section,
            "label": args.label,
            "target": args.target.as_posix() if args.target else None,
        },
        "book_roots": [root.relative_to(repo_root).as_posix() for root in roots],
        "count": len(filtered),
        "items": [item.as_json(repo_root) for item in filtered],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="List routed formal artifacts for semantic validation/generation.")
    parser.add_argument("--repos-root", type=Path)
    parser.add_argument("--volume-root", type=Path)
    parser.add_argument("--volume", choices=tuple(VOLUME_NAMES))
    parser.add_argument("--book")
    parser.add_argument("--chapter")
    parser.add_argument("--section")
    parser.add_argument("--label")
    parser.add_argument("--target", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=("yaml", "json"), default="yaml")
    args = parser.parse_args()

    try:
        payload = inventory(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
