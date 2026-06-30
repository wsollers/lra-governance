from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from generators.chapter_stub import stub_chapter
from generators.section_stub import stub_section


def _section_titles(args: argparse.Namespace) -> list[str]:
    titles: list[str] = []
    for value in args.section or []:
        titles.extend(part.strip() for part in value.split(";") if part.strip())
    titles.extend(part.strip() for part in (args.sections or "").split(";") if part.strip())
    return titles


def _load_registry(path: str | None) -> list[dict]:
    if not path:
        return []
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _print_result(result: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    if "chapter" in result:
        print(f"created chapter: {result['chapter']}")
        for section in result.get("sections", []):
            print(f"  section: {section['slug']}")
    else:
        print(f"created section: {result['slug']}")


def _cmd_chapter(args: argparse.Namespace) -> int:
    result = stub_chapter(
        args.volume_root,
        args.subject,
        args.title,
        _load_registry(args.registry),
        _section_titles(args),
        {
            "series": args.series_title,
            "volume": args.volume_title,
            "book": args.book_title,
            "chapter": args.chapter_title,
        },
    )
    _print_result(result, args.json)
    return 0


def _cmd_section(args: argparse.Namespace) -> int:
    results = [stub_section(Path(args.chapter_root), title) for title in _section_titles(args)]
    if args.json:
        print(json.dumps({"sections": results}, indent=2, sort_keys=True))
    else:
        for result in results:
            print(f"created section: {result['slug']}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scaffold canonical LRA stub chapters or sections.")
    parser.add_argument("--json", action="store_true", help="print machine-readable output")
    subparsers = parser.add_subparsers(dest="command", required=True)

    chapter = subparsers.add_parser("chapter", help="scaffold a canonical stub chapter")
    chapter.add_argument("--volume-root", required=True, help="path to the owning volume-* directory")
    chapter.add_argument("--subject", required=True, help="chapter slug")
    chapter.add_argument("--title", required=True, help="chapter display title")
    chapter.add_argument("--section", action="append", help="section title; repeat or separate multiple titles with ';'")
    chapter.add_argument("--sections", default="", help="section titles in order, ';'-separated")
    chapter.add_argument("--registry", help="JSON list of {subject, display_title} in dependency order")
    chapter.add_argument("--series-title", help="override breadcrumb series metadata")
    chapter.add_argument("--volume-title", help="override breadcrumb volume metadata")
    chapter.add_argument("--book-title", help="override breadcrumb book metadata")
    chapter.add_argument("--chapter-title", help="override breadcrumb chapter metadata")
    chapter.set_defaults(func=_cmd_chapter)

    section = subparsers.add_parser("section", help="scaffold one or more canonical stub sections")
    section.add_argument("--chapter-root", required=True, help="path to the owning chapter directory")
    section.add_argument("--section", action="append", help="section title; repeat or separate multiple titles with ';'")
    section.add_argument("--sections", default="", help="section titles in order, ';'-separated")
    section.set_defaults(func=_cmd_section)

    args = parser.parse_args(argv)
    if args.command == "section" and not _section_titles(args):
        parser.error("section requires --section or --sections")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
