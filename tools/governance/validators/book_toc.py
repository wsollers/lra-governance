from __future__ import annotations

import json
import re
from pathlib import Path

from core.finding import Finding, finding
from core.tex import INPUT_RE, read_text, strip_latex_comments


BOOK_DIR_RE = re.compile(r"^volume-(i|ii|iii|iv|v|vi|vii|viii)/book-[a-z0-9]+(?:-[a-z0-9]+)*$")
BOOK_ROOT_RE = re.compile(r"^volume-(i|ii|iii|iv|v|vi|vii|viii)-[a-z0-9]+(?:-[a-z0-9]+)*\.tex$")


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
    books = registry.get("books", [])
    _validate_registry_shape(volume_root, registry, findings)
    if (repo_root / "main.tex").is_file() or (volume_root / "main.tex").is_file():
        return findings
    _validate_registered_book_dirs(repo_root, volume_root, books, findings)
    _validate_volume_index_routes_books(volume_root, books, findings)
    for book in books:
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


def _validate_registry_shape(volume_root: Path, registry: dict, findings: list[Finding]) -> None:
    books = registry.get("books", [])
    seen_slugs: dict[str, str] = {}
    seen_orders: dict[int, str] = {}
    for book in books:
        title = book.get("title") or book.get("slug") or book.get("book_dir") or "book"
        slug = book.get("slug")
        order = book.get("order")
        root_name = book.get("tex_root")
        book_dir = book.get("book_dir")

        if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            findings.append(
                finding(
                    "book_registry_bad_slug",
                    f"Book registry entry has a noncanonical slug for {title}: {slug!r}.",
                    volume_root,
                    volume_root,
                )
            )
        elif slug in seen_slugs:
            findings.append(
                finding(
                    "book_registry_duplicate_slug",
                    f"Book registry repeats slug {slug!r}: {seen_slugs[slug]} and {title}.",
                    volume_root,
                    volume_root,
                )
            )
        else:
            seen_slugs[slug] = str(title)

        if not isinstance(order, int):
            findings.append(
                finding(
                    "book_registry_bad_order",
                    f"Book registry entry has a non-integer order for {title}: {order!r}.",
                    volume_root,
                    volume_root,
                )
            )
        elif order in seen_orders:
            findings.append(
                finding(
                    "book_registry_duplicate_order",
                    f"Book registry repeats order {order}: {seen_orders[order]} and {title}.",
                    volume_root,
                    volume_root,
                )
            )
        else:
            seen_orders[order] = str(title)

        if not isinstance(book_dir, str) or not BOOK_DIR_RE.fullmatch(book_dir):
            findings.append(
                finding(
                    "book_registry_bad_book_dir",
                    f"Book registry entry for {title} has noncanonical book_dir: {book_dir!r}.",
                    volume_root,
                    volume_root,
                )
            )
        if not isinstance(root_name, str) or not BOOK_ROOT_RE.fullmatch(root_name):
            findings.append(
                finding(
                    "book_registry_bad_tex_root",
                    f"Book registry entry for {title} has noncanonical tex_root: {root_name!r}.",
                    volume_root,
                    volume_root,
                )
            )


def _validate_registered_book_dirs(repo_root: Path, volume_root: Path, books: list[dict], findings: list[Finding]) -> None:
    registered = {book.get("book_dir") for book in books if isinstance(book.get("book_dir"), str)}
    for path in sorted(volume_root.glob("book-*")):
        if not path.is_dir():
            continue
        rel = path.relative_to(repo_root).as_posix()
        if rel not in registered:
            findings.append(
                finding(
                    "unregistered_book_dir",
                    f"Book directory is not registered in docs/architecture/book-registry.json: {rel}.",
                    path,
                    volume_root,
                )
            )


def _validate_volume_index_routes_books(volume_root: Path, books: list[dict], findings: list[Finding]) -> None:
    index = volume_root / "index.tex"
    if not index.is_file():
        return
    inputs = _inputs(index)
    for book in books:
        book_dir = book.get("book_dir")
        title = book.get("title") or book_dir or "book"
        if not isinstance(book_dir, str):
            continue
        expected = f"{book_dir}/index"
        if expected not in inputs:
            findings.append(
                finding(
                    "book_not_routed_from_volume_index",
                    f"Volume index must route {title} through {expected}.",
                    index,
                    volume_root,
                )
            )


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

    if root_name:
        bib = repo_root / "bibliography" / f"{Path(root_name).stem}.bib"
        if not bib.is_file():
            findings.append(
                finding(
                    "missing_book_bibliography_shard",
                    f"Missing bibliography shard for {title}: bibliography/{Path(root_name).stem}.bib.",
                    bib,
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
