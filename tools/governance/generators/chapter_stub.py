from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.volume import VOLUME_RE, latex_input_path
from generators.section_stub import append_once, slugify, stub_section, write_new


GOVERNANCE_ROOT = Path(__file__).resolve().parents[3]
BOOK_REGISTRY = GOVERNANCE_ROOT / "docs" / "architecture" / "book-registry.json"


@dataclass(frozen=True)
class ChapterParentContext:
    root: Path
    volume: str
    book: str

    @property
    def registry_book_dir(self) -> str:
        parts = [self.volume]
        if self.book:
            parts.append(self.book)
        return Path(*parts).as_posix()


def _tex(value: str) -> str:
    return (value or "").replace("\\", r"\textbackslash{}").replace("{", r"\{").replace("}", r"\}")


def _neighbors(subject: str, registry: list[dict]):
    subjects = [entry["subject"] for entry in registry]
    titles = [entry["display_title"] for entry in registry]
    if subject in subjects:
        index = subjects.index(subject)
        return (
            titles[index - 1] if index > 0 else "",
            subjects[index - 1] if index > 0 else "",
            titles[index + 1] if index < len(titles) - 1 else "",
            subjects[index + 1] if index < len(titles) - 1 else "",
        )
    return ("", "", "", "")


def _root_context(chapter_parent: Path) -> ChapterParentContext:
    root = Path(chapter_parent)
    parts = root.resolve().parts
    volume_index = next(
        (index for index, part in enumerate(parts) if VOLUME_RE.fullmatch(part)),
        None,
    )
    if volume_index is None:
        volume = root.name
        book = ""
    else:
        volume = parts[volume_index]
        book = (
            parts[volume_index + 1]
            if len(parts) > volume_index + 1 and parts[volume_index + 1].startswith("book-")
            else ""
        )
    return ChapterParentContext(root=root, volume=volume, book=book)


def _book_registry() -> dict:
    if not BOOK_REGISTRY.exists():
        return {}
    return json.loads(BOOK_REGISTRY.read_text(encoding="utf-8"))


def _roman_to_number(roman: str) -> int | None:
    values = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8}
    return values.get(roman)


def _number_to_roman(value: int | None) -> str:
    values = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII"}
    return values.get(value or 0, str(value or ""))


def _matching_registry_book(context: ChapterParentContext) -> tuple[dict, dict] | tuple[None, None]:
    data = _book_registry()
    roman = context.volume.removeprefix("volume-")
    for volume in data.get("volumes", []):
        if volume.get("roman") != roman:
            continue
        for book in volume.get("books", []):
            if book.get("book_dir") == context.registry_book_dir:
                return volume, book
    return None, None


def _registry_for_context(context: ChapterParentContext) -> list[dict]:
    _volume, book = _matching_registry_book(context)
    if not book:
        return []
    return [
        {"subject": entry.get("chapter"), "display_title": entry.get("chapter", "")}
        for entry in book.get("expected_toc", [])
        if entry.get("chapter")
    ]


def _metadata_from_registry(chapter_parent: Path, subject: str, display_title: str, registry: list[dict]) -> dict[str, str]:
    context = _root_context(chapter_parent)
    data = _book_registry()
    roman = context.volume.removeprefix("volume-")
    volume_number = _roman_to_number(roman)
    metadata = {
        "series": data.get("naming", {}).get("default_series_title", "From Cantor to Ito"),
        "volume": f"Volume {roman.upper()}" if roman else "",
        "book": "",
        "chapter": f"Chapter: {display_title}",
    }

    volume, book = _matching_registry_book(context)
    if volume:
        metadata["series"] = volume.get("series_title") or metadata["series"]
        if volume_number:
            metadata["volume"] = f"Volume {roman.upper()}: {volume.get('display_title', '').strip()}".rstrip(": ")
        if book:
            metadata["book"] = f"Book {_number_to_roman(book.get('order'))}: {book.get('title')}"
            for index, entry in enumerate(book.get("expected_toc", []), 1):
                if entry.get("chapter") == subject:
                    metadata["chapter"] = f"Chapter {index}: {display_title}"
                    return metadata

    if registry:
        subjects = [entry["subject"] for entry in registry]
        if subject in subjects:
            metadata["chapter"] = f"Chapter {subjects.index(subject) + 1}: {display_title}"
    return metadata


def render_lrameta(volume_root: Path, subject: str, display_title: str, registry: list[dict], overrides: dict[str, str] | None = None) -> str:
    metadata = _metadata_from_registry(volume_root, subject, display_title, registry)
    for key, value in (overrides or {}).items():
        if value:
            metadata[key] = value
    return (
        "\\lrameta{\n"
        f"  series = {{{_tex(metadata['series'])}}},\n"
        f"  volume = {{{_tex(metadata['volume'])}}},\n"
        f"  book = {{{_tex(metadata['book'])}}},\n"
        f"  chapter = {{{_tex(metadata['chapter'])}}},\n"
        "  current = chapter,\n"
        "}\n"
        "\\LraBreadcrumb"
    )


def _capstone_stub(subject: str, display_title: str) -> str:
    return (
        "\\phantomsection\n"
        f"\\label{{cap:{subject}}}\n\n"
        "\\begin{tcolorbox}[\n"
        "  colback=gray!6,\n"
        "  colframe=gray!40,\n"
        "  arc=2pt,\n"
        "  left=8pt, right=8pt, top=6pt, bottom=6pt,\n"
        "  title={\\small\\textbf{Capstone Theorem}},\n"
        "  fonttitle=\\small\\bfseries\n"
        "]\n"
        "\\textbf{Theorem.}\n"
        f"TODO: state the theorem-shaped capstone target for {display_title}.\n"
        "\\end{tcolorbox}\n\n"
        "\\begin{remark*}[Dependencies to state]\n"
        "List only the prior labels needed to parse the capstone statement.\n"
        "\\end{remark*}\n\n"
        "\\begin{remark*}[Dependencies to prove]\n"
        "List the prior labels needed to prove the capstone theorem.\n"
        "\\end{remark*}\n\n"
        "\\begin{remark*}[Dependency ceiling]\n"
        "The capstone may use only results routed at or before this chapter.\n"
        "\\end{remark*}\n\n"
        "\\begin{dependencies}\n"
        "\\begin{itemize}\n"
        "  \\item TODO\n"
        "\\end{itemize}\n"
        "\\end{dependencies}\n\n"
        "\\clearpage\n"
    )


def _yaml_quote(value: str) -> str:
    return json.dumps(value)


def stub_chapter(
    volume_root,
    subject,
    display_title,
    registry,
    section_titles,
    metadata: dict[str, str] | None = None,
    *,
    include_capstone: bool = True,
):
    volume_root = Path(volume_root)
    context = _root_context(volume_root)
    if not registry:
        registry = _registry_for_context(context)
    chapter = volume_root / subject
    if chapter.exists() and any(chapter.iterdir()):
        raise FileExistsError(f"refusing to overwrite existing chapter: {chapter}")

    (chapter / "notes").mkdir(parents=True, exist_ok=True)
    (chapter / "proofs").mkdir(parents=True, exist_ok=True)
    if include_capstone:
        (chapter / "proofs" / "exercises").mkdir(parents=True, exist_ok=True)

    _prior_title, prior_subject, _next_title, next_subject = _neighbors(subject, registry)
    breadcrumb = render_lrameta(volume_root, subject, display_title, registry, metadata)
    chapter_route = latex_input_path(chapter / "index.tex").removesuffix("/index")
    capstone_route = ""
    if include_capstone:
        capstone_route = (
            "\n"
            "\\section*{Capstone}\n"
            f"\\input{{{chapter_route}/proofs/exercises/index}}\n"
        )
    write_new(
        chapter / "index.tex",
        "% =========================================================\n"
        f"% Chapter: {display_title}\n"
        "% =========================================================\n"
        f"\\chapter{{{display_title}}}\n"
        f"\\label{{ch:{subject}}}\n\n"
        f"{breadcrumb}\n\n"
        f"\\input{{{chapter_route}/notes/index}}\n\n"
        "\\LRAExcludeFromPrintEditionBegin\n"
        "\\section*{Proofs}\n"
        f"\\input{{{chapter_route}/proofs/index}}\n\n"
        f"{capstone_route}"
        "\\LRAExcludeFromPrintEditionEnd\n",
    )

    if section_titles:
        sections = "sections:\n" + "".join(
            f"  - subject: {slugify(title)}\n    display_title: \"{title}\"\n"
            for title in section_titles
        )
    else:
        sections = "sections: []\n"
    book_line = f"book: {context.book}\n" if context.book else ""
    write_new(
        chapter / "chapter.yaml",
        f"subject: {subject}\n"
        f"display_title: {_yaml_quote(display_title)}\n"
        f"volume: {context.volume}\n"
        f"{book_line}"
        f"path: {latex_input_path(chapter)}\n"
        f"status: planned\n{sections}dependencies:\n  prior: {prior_subject}\n  next: {next_subject}\n",
    )
    write_new(
        chapter / "notes" / "index.tex",
        f"% Notes index for chapter: {display_title}\n"
        "% Topic routers are \\section + \\input here in dependency order.\n",
    )
    write_new(
        chapter / "proofs" / "index.tex",
        f"% Proofs index for chapter: {display_title}\n% Proof topics \\input here, matching notes sections in dependency order.\n",
    )
    if include_capstone:
        write_new(
            chapter / "proofs" / "exercises" / "index.tex",
            f"% Exercise proofs index for chapter: {display_title}\n"
            f"\\input{{{chapter_route}/proofs/exercises/capstone-{subject}}}\n",
        )
        write_new(
            chapter / "proofs" / "exercises" / f"capstone-{subject}.tex",
            _capstone_stub(subject, display_title),
        )

    for router in ("index.tex", "main.tex"):
        path = volume_root / router
        if path.exists():
            append_once(path, f"\\input{{{latex_input_path(chapter / 'index.tex')}}}")

    created = [stub_section(chapter, title) for title in section_titles]
    return {"chapter": str(chapter), "sections": created}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Scaffold a canonical stub chapter.")
    root = parser.add_mutually_exclusive_group(required=True)
    root.add_argument("--volume-root")
    root.add_argument("--book-root")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--sections", default="", help="section titles in order, ';'-separated")
    parser.add_argument("--registry", help="JSON list of {subject, display_title} in dependency order")
    parser.add_argument("--series-title", help="override breadcrumb series metadata")
    parser.add_argument("--volume-title", help="override breadcrumb volume metadata")
    parser.add_argument("--book-title", help="override breadcrumb book metadata")
    parser.add_argument("--chapter-title", help="override breadcrumb chapter metadata")
    parser.add_argument("--no-capstone", action="store_true")
    args = parser.parse_args(argv)
    registry = json.loads(Path(args.registry).read_text()) if args.registry else []
    section_titles = [title.strip() for title in args.sections.split(";") if title.strip()]
    metadata = {
        "series": args.series_title,
        "volume": args.volume_title,
        "book": args.book_title,
        "chapter": args.chapter_title,
    }
    result = stub_chapter(
        args.book_root or args.volume_root,
        args.subject,
        args.title,
        registry,
        section_titles,
        metadata,
        include_capstone=not args.no_capstone,
    )
    print("created chapter:", result["chapter"])
    for section in result["sections"]:
        print("  section:", section["slug"])


if __name__ == "__main__":
    main()
