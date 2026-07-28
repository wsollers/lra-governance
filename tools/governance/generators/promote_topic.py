from __future__ import annotations

import json
import shutil
from pathlib import Path

from core.volume import latex_input_path
from generators.chapter_stub import BOOK_REGISTRY, _root_context, stub_chapter
from generators.section_stub import append_once


def _input(route: str) -> str:
    return f"\\input{{{route}}}"


def _remove_input(path: Path, route: str) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    old_lines = text.splitlines(keepends=True)
    target = _input(route)
    new_lines = [line for line in old_lines if line.strip() != target]
    if new_lines == old_lines:
        return False
    path.write_text("".join(new_lines), encoding="utf-8")
    return True


def _rewrite_moved_paths(root: Path, old_prefix: str, new_prefix: str) -> list[str]:
    changed: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in {".tex", ".yaml", ".yml"}:
            continue
        text = path.read_text(encoding="utf-8")
        updated = text.replace(old_prefix, new_prefix)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            changed.append(str(path))
    return changed


def _registry_patch_report(
    source_chapter: Path,
    source_topic: str,
    destination_chapter: str,
    destination_topic: str,
) -> dict:
    context = _root_context(source_chapter.parent)
    return {
        "book_dir": context.registry_book_dir,
        "remove_topic": {
            "chapter": source_chapter.name,
            "topic": source_topic,
        },
        "insert_chapter_after": source_chapter.name,
        "insert_chapter": {
            "chapter": destination_chapter,
            "notes": [destination_topic],
        },
    }


def _update_book_registry(
    source_chapter: Path,
    source_topic: str,
    destination_chapter: str,
    destination_topic: str,
    registry_path: Path = BOOK_REGISTRY,
) -> bool:
    context = _root_context(source_chapter.parent)
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    changed = False
    for volume in data.get("volumes", []):
        for book in volume.get("books", []):
            if book.get("book_dir") != context.registry_book_dir:
                continue
            toc = book.get("expected_toc", [])
            source_index = None
            for index, entry in enumerate(toc):
                if entry.get("chapter") == source_chapter.name:
                    source_index = index
                    notes = entry.get("notes", [])
                    if source_topic in notes:
                        entry["notes"] = [topic for topic in notes if topic != source_topic]
                        changed = True
                if entry.get("chapter") == destination_chapter:
                    entry["notes"] = [destination_topic]
                    changed = True
                    break
            else:
                if source_index is not None:
                    toc.insert(source_index + 1, {"chapter": destination_chapter, "notes": [destination_topic]})
                    changed = True
            if changed:
                registry_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            return changed
    raise ValueError(f"book directory is not registered: {context.registry_book_dir}")


def promote_topic_to_chapter(
    source_chapter_root: Path,
    topic: str,
    destination_chapter: str,
    display_title: str,
    *,
    destination_topic: str | None = None,
    include_capstone: bool = False,
    update_registry: bool = False,
) -> dict:
    source_chapter = Path(source_chapter_root)
    if not source_chapter.exists():
        raise FileNotFoundError(source_chapter)
    if destination_topic is None:
        destination_topic = topic

    book_root = source_chapter.parent
    destination_root = book_root / destination_chapter
    existing_topic_roots = [
        source_chapter / kind / topic
        for kind in ("notes", "proofs")
        if (source_chapter / kind / topic).exists()
    ]
    if not existing_topic_roots:
        raise FileNotFoundError(f"topic not found in notes/ or proofs/: {topic}")

    result = stub_chapter(
        book_root,
        destination_chapter,
        display_title,
        [],
        [],
        include_capstone=include_capstone,
    )

    moved: list[dict[str, str]] = []
    rewritten: list[str] = []
    routers_updated: list[str] = []
    for kind in ("notes", "proofs"):
        source_topic = source_chapter / kind / topic
        destination_topic_root = destination_root / kind / destination_topic
        if not source_topic.exists():
            continue
        if destination_topic_root.exists():
            raise FileExistsError(destination_topic_root)
        destination_topic_root.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_topic), str(destination_topic_root))
        moved.append({"from": str(source_topic), "to": str(destination_topic_root)})

        old_route = latex_input_path(source_topic / "index.tex")
        new_route = latex_input_path(destination_topic_root / "index.tex")
        if _remove_input(source_chapter / kind / "index.tex", old_route):
            routers_updated.append(str(source_chapter / kind / "index.tex"))
        if append_once(destination_root / kind / "index.tex", _input(new_route)):
            routers_updated.append(str(destination_root / kind / "index.tex"))
        rewritten.extend(
            _rewrite_moved_paths(
                destination_topic_root,
                old_route.removesuffix("/index"),
                new_route.removesuffix("/index"),
            )
        )

    registry_report = _registry_patch_report(
        source_chapter,
        topic,
        destination_chapter,
        destination_topic,
    )
    registry_updated = False
    if update_registry:
        registry_updated = _update_book_registry(
            source_chapter,
            topic,
            destination_chapter,
            destination_topic,
        )

    return {
        "chapter": result["chapter"],
        "moved": moved,
        "routers_updated": sorted(set(routers_updated)),
        "paths_rewritten": sorted(set(rewritten)),
        "registry_updated": registry_updated,
        "registry_patch": registry_report,
    }
