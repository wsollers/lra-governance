from __future__ import annotations

import json
from pathlib import Path

from core.finding import Finding, finding
from core.tex import INPUT_RE, read_text, strip_latex_comments


def validate(volume_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    registry = _registry_for(volume_root)
    if registry is None:
        findings.append(
            finding(
                "missing_book_toc_registry",
                "Book TOC registry does not contain this volume.",
                volume_root,
                volume_root,
            )
        )
        return findings

    repo_root = volume_root.parent
    for book in registry.get("books", []):
        _validate_book(repo_root, volume_root, book, findings)
    return findings


def _registry_for(volume_root: Path) -> dict | None:
    path = Path(__file__).resolve().parents[3] / "docs" / "architecture" / "book-registry.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    roman = volume_root.name.removeprefix("volume-")
    for volume in data.get("volumes", []):
        if volume.get("roman") == roman:
            return volume
    return None


def _validate_book(repo_root: Path, volume_root: Path, book: dict, findings: list[Finding]) -> None:
    root_name = book.get("tex_root")
    book_dir = book.get("book_dir")
    title = book.get("title", root_name or book_dir or "book")
    if not root_name or not book_dir:
        findings.append(
            finding(
                "book_toc_registry_incomplete",
                f"Book registry entry is missing tex_root or book_dir for {title}.",
                volume_root,
                volume_root,
            )
        )
        return

    tex_root = repo_root / root_name
    expected_book_input = f"{book_dir}/index"
    if not tex_root.is_file():
        if (repo_root / "main.tex").is_file() or (volume_root / "main.tex").is_file():
            return
        findings.append(
            finding(
                "missing_book_tex_root",
                f"Missing canonical book root for {title}: {root_name}.",
                tex_root,
                volume_root,
            )
        )
    else:
        root_inputs = _inputs(tex_root)
        if expected_book_input not in root_inputs:
            findings.append(
                finding(
                    "book_root_wrong_input",
                    f"{root_name} must route {expected_book_input}.",
                    tex_root,
                    volume_root,
                )
            )

    book_index = repo_root / book_dir / "index.tex"
    if not book_index.is_file():
        findings.append(
            finding(
                "missing_book_index",
                f"Missing book index for {title}: {book_dir}/index.tex.",
                book_index,
                volume_root,
            )
        )
        return

    expected_toc = book.get("expected_toc", [])
    expected_chapters = [entry.get("chapter") for entry in expected_toc]
    actual_chapter_inputs = [
        item
        for item in _inputs(book_index)
        if item.startswith(f"{book_dir}/") and item.endswith("/index")
    ]
    actual_chapters = [Path(item.removesuffix("/index")).name for item in actual_chapter_inputs]
    if actual_chapters != expected_chapters:
        findings.append(
            finding(
                "book_chapter_toc_mismatch",
                f"{title} chapter TOC mismatch. Expected {expected_chapters}; found {actual_chapters}.",
                book_index,
                volume_root,
            )
        )

    for entry in expected_toc:
        chapter = entry.get("chapter")
        if not chapter:
            continue
        _validate_chapter_notes(repo_root, volume_root, book_dir, title, chapter, entry.get("notes", []), findings)


def _validate_chapter_notes(
    repo_root: Path,
    volume_root: Path,
    book_dir: str,
    title: str,
    chapter: str,
    expected_notes: list[str],
    findings: list[Finding],
) -> None:
    notes_index = repo_root / book_dir / chapter / "notes" / "index.tex"
    if not notes_index.is_file():
        findings.append(
            finding(
                "missing_chapter_notes_index",
                f"{title}/{chapter} is missing notes/index.tex.",
                notes_index,
                volume_root,
            )
        )
        return

    prefix = f"{book_dir}/{chapter}/notes/"
    actual_notes = [
        Path(item.removesuffix("/index")).name
        for item in _inputs(notes_index)
        if item.startswith(prefix) and item.endswith("/index")
    ]
    if actual_notes != expected_notes:
        findings.append(
            finding(
                "book_notes_toc_mismatch",
                f"{title}/{chapter} notes TOC mismatch. Expected {expected_notes}; found {actual_notes}.",
                notes_index,
                volume_root,
            )
        )


def _inputs(path: Path) -> list[str]:
    text = strip_latex_comments(read_text(path))
    return [
        match.group(1).replace("\\", "/").removesuffix(".tex")
        for match in INPUT_RE.finditer(text)
    ]
