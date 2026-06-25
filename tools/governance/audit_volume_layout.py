#!/usr/bin/env python3
"""Audit LRA volume/chapter/topic filesystem and router layout."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from _targeting import discovery_lines, is_ignored_path, resolve_target, target_chapters


INPUT_RE = re.compile(r"\\(?:input|include)\{([^}]+)\}")
VOLUME_RE = re.compile(r"^volume-(?:i|ii|iii|iv|v|vi|vii|viii)$")


@dataclass
class Finding:
    severity: str
    code: str
    message: str


@dataclass
class ChapterAudit:
    chapter: str
    path: str
    status: str
    notes_topics: list[str] = field(default_factory=list)
    proofs_topics: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)


@dataclass
class LayoutSummary:
    root: str
    refactor_mode: bool
    chapters: int = 0
    compliant_chapters: int = 0
    non_compliant_chapters: int = 0
    warnings: int = 0
    errors: int = 0
    audits: list[ChapterAudit] = field(default_factory=list)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit LRA volume/chapter/topic layout.")
    parser.add_argument("--root", required=True, help="Leaf repo, volume root, or chapter root.")
    parser.add_argument("--volume", help="Audit a discovered volume, such as volume-ii.")
    parser.add_argument("--chapter", help="Audit a discovered chapter, such as whole-numbers.")
    parser.add_argument(
        "--section",
        help="Audit the chapter containing a discovered section. Use --chapter if ambiguous.",
    )
    parser.add_argument(
        "--list-targets",
        action="store_true",
        help="List discovered volumes, chapters, and sections, then exit.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--strict", action="store_true", help="Fail if any chapter is non-compliant.")
    parser.add_argument(
        "--refactor-mode",
        action="store_true",
        help="Treat legacy flat notes/proofs layouts as transitional warnings.",
    )
    return parser.parse_args(argv)


def relpath(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def add(audit: ChapterAudit, severity: str, code: str, message: str) -> None:
    audit.findings.append(Finding(severity, code, message))


def is_volume_root(path: Path) -> bool:
    return path.is_dir() and VOLUME_RE.match(path.name) is not None and (path / "index.tex").exists()


def find_volume_roots(root: Path) -> list[Path]:
    root = root.resolve()
    if is_volume_root(root):
        return [root]
    direct = [path for path in root.iterdir() if not is_ignored_path(path, root) and is_volume_root(path)] if root.is_dir() else []
    if direct:
        return sorted(direct)
    return sorted(path for path in root.rglob("volume-*") if not is_ignored_path(path, root) and is_volume_root(path))


def find_chapter_roots(root: Path) -> list[Path]:
    root = root.resolve()
    if (root / "notes").is_dir() and (root / "proofs").is_dir():
        return [root]
    chapters: list[Path] = []
    for volume in find_volume_roots(root):
        # Descend through any intermediate tier (e.g. book-*/) to find chapter
        # roots, identified by having both notes/ and proofs/. Single-tier
        # chapters that are direct children of the volume are still found.
        for dirpath, dirnames, _filenames in os.walk(volume):
            current = Path(dirpath)
            dirnames[:] = [
                name for name in dirnames
                if not is_ignored_path(current / name, root)
            ]
            if (current / "notes").is_dir() and (current / "proofs").is_dir():
                chapters.append(current)
                dirnames[:] = [name for name in dirnames if name not in {"notes", "proofs"}]
    return sorted(set(path.resolve() for path in chapters))


def input_targets(index_path: Path, chapter_root: Path) -> set[str]:
    if not index_path.exists():
        return set()
    text = index_path.read_text(encoding="utf-8", errors="ignore")
    targets = set()
    for match in INPUT_RE.finditer(text):
        target = match.group(1).replace("\\", "/").removesuffix(".tex")
        targets.add(target)
        targets.add(Path(target).name)
        try:
            targets.add((chapter_root / target).resolve().relative_to(chapter_root.resolve()).as_posix())
        except ValueError:
            pass
    return targets


def is_routed(index_path: Path, target: Path, chapter_root: Path) -> bool:
    targets = input_targets(index_path, chapter_root)
    if not targets:
        return False
    rel = target.relative_to(chapter_root).as_posix().removesuffix(".tex")
    variants = {
        rel,
        rel.removesuffix("/index"),
        target.name,
        target.stem,
        target.parent.name,
    }
    return bool(variants.intersection(targets))


def topic_dirs(parent: Path) -> set[str]:
    if not parent.exists():
        return set()
    return {
        path.name
        for path in parent.iterdir()
        if path.is_dir()
        and not path.name.startswith(".")
        and path.name != "exercises"
        and not is_ignored_path(path)
    }


def legacy_notes_files(chapter: Path) -> list[Path]:
    notes = chapter / "notes"
    if not notes.exists():
        return []
    return sorted(path for path in notes.glob("*.tex") if path.name != "index.tex")


def legacy_proofs_notes(chapter: Path) -> Path | None:
    path = chapter / "proofs" / "notes"
    return path if path.exists() else None


def audit_chapter(chapter: Path, root: Path, refactor_mode: bool) -> ChapterAudit:
    audit = ChapterAudit(chapter=chapter.name, path=relpath(chapter, root), status="non_compliant")

    for relative in ("index.tex", "chapter.yaml", "notes/index.tex", "proofs/index.tex"):
        if not (chapter / relative).exists():
            add(audit, "error", f"missing_{relative.replace('/', '_').replace('.', '_')}", f"Missing {relative}.")

    for relative in ("notes", "proofs", "proofs/exercises"):
        if not (chapter / relative).is_dir():
            add(audit, "error", f"missing_{relative.replace('/', '_')}", f"Missing directory {relative}/.")

    notes_topics = topic_dirs(chapter / "notes")
    proofs_topics = topic_dirs(chapter / "proofs")
    audit.notes_topics = sorted(notes_topics)
    audit.proofs_topics = sorted(topic for topic in proofs_topics if topic != "notes")

    for path in legacy_notes_files(chapter):
        severity = "warning" if refactor_mode else "error"
        add(audit, severity, "legacy_flat_notes_file", f"Legacy flat notes file: {path.relative_to(chapter).as_posix()}.")

    legacy = legacy_proofs_notes(chapter)
    if legacy is not None:
        severity = "warning" if refactor_mode else "error"
        add(audit, severity, "legacy_proofs_notes_directory", "Legacy proofs/notes/ directory is transitional only.")

    for topic in sorted(notes_topics - proofs_topics):
        severity = "warning" if refactor_mode else "error"
        add(audit, severity, "missing_proofs_topic", f"notes/{topic}/ has no matching proofs/{topic}/.")
    for topic in sorted((proofs_topics - notes_topics) - {"notes"}):
        severity = "warning" if refactor_mode else "error"
        add(audit, severity, "orphan_proofs_topic", f"proofs/{topic}/ has no matching notes/{topic}/.")

    notes_index = chapter / "notes" / "index.tex"
    proofs_index = chapter / "proofs" / "index.tex"
    chapter_index = chapter / "index.tex"
    if (chapter / "notes" / "index.tex").exists() and not is_routed(chapter_index, chapter / "notes" / "index.tex", chapter):
        add(audit, "warning", "notes_index_not_in_chapter_index", "notes/index.tex is not visibly routed from chapter index.tex.")
    if (chapter / "proofs" / "index.tex").exists() and not is_routed(chapter_index, chapter / "proofs" / "index.tex", chapter):
        add(audit, "warning", "proofs_index_not_in_chapter_index", "proofs/index.tex is not visibly routed from chapter index.tex.")

    for topic in sorted(notes_topics):
        topic_index = chapter / "notes" / topic / "index.tex"
        if not topic_index.exists():
            add(audit, "error", "missing_notes_topic_index", f"Missing notes/{topic}/index.tex.")
        elif not is_routed(notes_index, topic_index, chapter):
            add(audit, "error", "unrouted_notes_topic", f"notes/{topic}/index.tex is not routed from notes/index.tex.")

    for topic in sorted(proofs_topics - {"notes"}):
        topic_index = chapter / "proofs" / topic / "index.tex"
        if not topic_index.exists():
            add(audit, "error", "missing_proofs_topic_index", f"Missing proofs/{topic}/index.tex.")
        elif not is_routed(proofs_index, topic_index, chapter):
            add(audit, "error", "unrouted_proofs_topic", f"proofs/{topic}/index.tex is not routed from proofs/index.tex.")

    if not any(finding.severity == "error" for finding in audit.findings):
        audit.status = "compliant"
    return audit


def audit_root(root: Path, refactor_mode: bool, chapters: list[Path] | None = None) -> LayoutSummary:
    root = root.resolve()
    summary = LayoutSummary(root=str(root), refactor_mode=refactor_mode)
    for chapter in chapters if chapters is not None else find_chapter_roots(root):
        audit = audit_chapter(chapter, root, refactor_mode)
        summary.audits.append(audit)
        summary.chapters += 1
        if audit.status == "compliant":
            summary.compliant_chapters += 1
        else:
            summary.non_compliant_chapters += 1
        summary.errors += sum(1 for finding in audit.findings if finding.severity == "error")
        summary.warnings += sum(1 for finding in audit.findings if finding.severity == "warning")
    return summary


def print_text(summary: LayoutSummary) -> None:
    print(f"root: {summary.root}")
    print(f"refactor_mode: {summary.refactor_mode}")
    print(f"chapters: {summary.chapters}")
    print(f"compliant_chapters: {summary.compliant_chapters}")
    print(f"non_compliant_chapters: {summary.non_compliant_chapters}")
    print(f"warnings: {summary.warnings}")
    print(f"errors: {summary.errors}")
    for audit in summary.audits:
        if audit.status == "compliant":
            continue
        print(f"\nNON-COMPLIANT {audit.path}")
        for finding in audit.findings:
            print(f"- {finding.severity}: {finding.code}: {finding.message}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if args.list_targets:
        print("\n".join(discovery_lines(root)))
        return 0
    try:
        target = resolve_target(root, args.volume, args.chapter, args.section)
    except ValueError as exc:
        print(f"ERROR target_resolution - {exc}", file=sys.stderr)
        return 2
    summary = audit_root(root, args.refactor_mode, target_chapters(target))
    if args.format == "json":
        print(json.dumps(asdict(summary), indent=2))
    else:
        print_text(summary)
    if args.strict and summary.non_compliant_chapters:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
