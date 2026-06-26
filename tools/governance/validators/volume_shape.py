from __future__ import annotations

import json
import re
from pathlib import Path

from core.finding import Finding, finding
from core.file_inventory import reachable_files
from core.tex import read_text, strip_latex_comments
from core.volume import chapter_roots, is_ignored, latex_input_path


DEFAULT_SCHEMA = {
    "required_volume_files": ["index.tex"],
    "required_volume_entry_files": [],
    "required_volume_entry_patterns": ["volume-*.tex", "volume-*-*-main.tex", "main-book-*.tex", "main.tex"],
    "canonical_volume_entry_pattern": r"^volume-(i|ii|iii|iv|v|vi|vii|viii)(?:-[a-z0-9]+(?:-[a-z0-9]+)*)?\.tex$",
    "legacy_volume_entry_patterns": ["volume-*-*-main.tex", "main-book-*.tex", "main.tex"],
    "required_chapter_files": ["index.tex", "chapter.yaml", "notes/index.tex", "proofs/index.tex"],
    "required_chapter_dirs": ["notes", "proofs"],
    "note_only_topics": ["notation"],
    "topic_name_pattern": r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    "proof_file_pattern": r"^prf-[a-z0-9]+(?:-[a-z0-9]+)*\.tex$",
    "proof_topic_required_envs": ["theorem", "lemma", "proposition", "corollary"],
    "capstone_pattern": "proofs/exercises/capstone-{chapter}.tex",
    "exercises_allowed_files": ["index.tex", "capstone-{chapter}.tex"],
    "legacy_chapter_paths": ["capstone.tex", "exercises"],
}


def _schema() -> dict:
    root = Path(__file__).resolve().parents[3]
    path = root / "docs" / "governance" / "volume-structure.schema.json"
    if not path.exists():
        return DEFAULT_SCHEMA
    data = json.loads(path.read_text(encoding="utf-8"))
    return {**DEFAULT_SCHEMA, **data}


def _add(
    findings: list[Finding],
    root: Path,
    path: Path,
    code: str,
    message: str,
    severity: str = "error",
) -> None:
    findings.append(finding(code, message, path, root, 0, severity))


def _required_file(findings: list[Finding], root: Path, path: Path, label: str) -> None:
    if not path.exists():
        _add(findings, root, path, "missing_volume_shape_file", f"Missing required {label}.")
    elif not path.is_file():
        _add(findings, root, path, "volume_shape_not_file", f"{label} must be a file.")


def _required_dir(findings: list[Finding], root: Path, path: Path, label: str) -> None:
    if not path.exists():
        _add(findings, root, path, "missing_volume_shape_directory", f"Missing required {label}/.")
    elif not path.is_dir():
        _add(findings, root, path, "volume_shape_not_directory", f"{label} must be a directory.")


def validate(volume_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    schema = _schema()
    for relative in schema["required_volume_files"]:
        _required_file(findings, volume_root, volume_root / relative, f"volume {relative}")
    _validate_entry_roots(volume_root, findings, schema)

    chapters = chapter_roots(volume_root)
    if not chapters:
        _add(findings, volume_root, volume_root, "missing_chapters", "Volume contains no canonical chapter roots.")
        return findings

    for chapter in chapters:
        _validate_chapter(volume_root, chapter, findings, schema)
    _validate_chapter_reachability(volume_root, chapters, findings)
    return findings


def _validate_entry_roots(volume_root: Path, findings: list[Finding], schema: dict) -> None:
    patterns = schema.get("required_volume_entry_patterns")
    if patterns:
        matches = []
        for pattern in patterns:
            matches.extend(path for path in volume_root.glob(pattern) if path.is_file())
            matches.extend(path for path in volume_root.parent.glob(pattern) if path.is_file())
        if not matches:
            expected = ", ".join(patterns)
            _add(
                findings,
                volume_root,
                volume_root / "volume-{roman}.tex",
                "missing_volume_shape_file",
                f"Missing volume entry root. Expected one or more of: {expected}.",
            )
        return

    for relative in schema["required_volume_entry_files"]:
        candidates = [volume_root / relative, volume_root.parent / relative]
        if not any(path.is_file() for path in candidates):
            _add(findings, volume_root, volume_root / relative, "missing_volume_shape_file", f"Missing required volume entry {relative}.")


def _volume_index_inputs(volume_root: Path) -> set[str]:
    index = volume_root / "index.tex"
    if not index.is_file():
        return set()
    text = strip_latex_comments(read_text(index))
    return {
        match.group(1)
        for match in re.finditer(r"\\input\{([^}]+)\}", text)
    }


def _validate_chapter_reachability(volume_root: Path, chapters: list[Path], findings: list[Finding]) -> None:
    # Book-aware: a chapter is correctly routed if its index.tex is reachable from
    # the volume index through the router chain (volume -> book -> chapter). This
    # follows \input chains, so it accepts both single-tier (volume -> chapter)
    # and book-tier (volume -> book -> chapter) layouts.
    reachable = reachable_files(volume_root)
    for chapter in chapters:
        if (chapter / "index.tex").resolve() not in reachable:
            _add(
                findings,
                volume_root,
                chapter / "index.tex",
                "chapter_not_in_volume_index",
                f"Canonical chapter root is not reachable from {volume_root.name}/index.tex "
                f"through the router chain (volume -> book -> chapter).",
            )


def _validate_chapter(volume_root: Path, chapter: Path, findings: list[Finding], schema: dict) -> None:
    included = reachable_files(chapter)
    for relative in schema["required_chapter_dirs"]:
        _required_dir(findings, volume_root, chapter / relative, relative)
    for relative in schema["required_chapter_files"]:
        _required_file(findings, volume_root, chapter / relative, relative)

    for relative in schema["legacy_chapter_paths"]:
        legacy = chapter / relative
        if legacy.exists():
            _add(findings, volume_root, legacy, "legacy_chapter_path", f"Legacy chapter path is not canonical: {relative}.")

    _validate_notes_shape(volume_root, chapter, findings, schema, included)
    _validate_proofs_shape(volume_root, chapter, findings, schema, included)


def _validate_notes_shape(volume_root: Path, chapter: Path, findings: list[Finding], schema: dict, included: set[Path]) -> None:
    notes_root = chapter / "notes"
    if not notes_root.is_dir():
        return
    topic_re = re.compile(schema["topic_name_pattern"])
    for child in notes_root.iterdir():
        if is_ignored(child, notes_root) or child.name == "index.tex":
            continue
        if child.is_file() and child.suffix == ".tex":
            if child.resolve() not in included:
                continue
            _add(findings, volume_root, child, "flat_note_body", "Note body files must live under notes/{topic}/, not directly under notes/.")
        elif child.is_dir():
            if not _active_tree(child, included):
                continue
            if not topic_re.fullmatch(child.name):
                _add(findings, volume_root, child, "noncanonical_topic_name", "Topic directory names must be lowercase kebab-case.")
            _required_file(findings, volume_root, child / "index.tex", f"notes/{child.name}/index.tex")


def _validate_proofs_shape(volume_root: Path, chapter: Path, findings: list[Finding], schema: dict, included: set[Path]) -> None:
    proofs_root = chapter / "proofs"
    if not proofs_root.is_dir():
        return
    topic_re = re.compile(schema["topic_name_pattern"])
    proof_file_re = re.compile(schema["proof_file_pattern"])
    for child in proofs_root.iterdir():
        if is_ignored(child, proofs_root) or child.name == "index.tex":
            continue
        if child.is_file() and child.suffix == ".tex":
            if child.resolve() not in included:
                continue
            _add(findings, volume_root, child, "flat_proof_file", "Proof files must live under proofs/{topic}/, not directly under proofs/.")
        elif child.is_dir() and child.name != "exercises":
            if not _active_tree(child, included):
                continue
            if not topic_re.fullmatch(child.name):
                _add(findings, volume_root, child, "noncanonical_topic_name", "Topic directory names must be lowercase kebab-case.")
            _required_file(findings, volume_root, child / "index.tex", f"proofs/{child.name}/index.tex")
            for proof_file in child.glob("*.tex"):
                if proof_file.resolve() not in included:
                    continue
                if proof_file.name != "index.tex" and not proof_file_re.fullmatch(proof_file.name):
                    _add(findings, volume_root, proof_file, "noncanonical_proof_filename", "Proof files must be named prf-{slug}.tex.")

    notes_topics = _topic_dirs(chapter / "notes", included)
    proof_topics = _topic_dirs(proofs_root, included)
    note_only_topics = set(schema["note_only_topics"])
    for topic in sorted((notes_topics - proof_topics) - note_only_topics):
        notes_topic = chapter / "notes" / topic
        if _note_topic_requires_proofs(notes_topic, schema, included):
            _add(findings, volume_root, notes_topic, "missing_matching_proofs_topic", f"notes/{topic}/ has proof-bearing statements but no matching proofs/{topic}/.")
    for topic in sorted(proof_topics - notes_topics):
        _add(findings, volume_root, proofs_root / topic, "orphan_proofs_topic", f"proofs/{topic}/ has no matching notes/{topic}/.")

    exercises_root = proofs_root / "exercises"
    exercises_index = exercises_root / "index.tex"
    if exercises_root.is_dir() and exercises_index.resolve() in included:
        allowed = {
            item.format(chapter=chapter.name)
            for item in schema.get("exercises_allowed_files", DEFAULT_SCHEMA["exercises_allowed_files"])
        }
        for child in exercises_root.iterdir():
            if is_ignored(child, exercises_root):
                continue
            if not _active_tree(child, included):
                continue
            if child.is_dir():
                _add(findings, volume_root, child, "noncanonical_exercises_path", "proofs/exercises/ may contain only index.tex and the canonical capstone file.")
            elif child.is_file() and child.name not in allowed:
                _add(findings, volume_root, child, "noncanonical_exercises_path", "proofs/exercises/ may contain only index.tex and the canonical capstone file.")


def _topic_dirs(parent: Path, included: set[Path]) -> set[str]:
    if not parent.is_dir():
        return set()
    return {
        child.name
        for child in parent.iterdir()
        if child.is_dir()
        and not is_ignored(child, parent)
        and child.name != "exercises"
        and _active_tree(child, included)
    }


def _active_tree(path: Path, included: set[Path]) -> bool:
    resolved = path.resolve()
    if path.is_file():
        return resolved in included
    return any(item == resolved or resolved in item.parents for item in included)


def _note_topic_requires_proofs(topic_root: Path, schema: dict, included: set[Path]) -> bool:
    envs = "|".join(re.escape(env) for env in schema.get("proof_topic_required_envs", DEFAULT_SCHEMA["proof_topic_required_envs"]))
    if not envs:
        return False
    proof_bearing_re = re.compile(rf"\\begin\{{(?:{envs})\}}(?:\[[^\]]*\])?", re.IGNORECASE)
    for tex in sorted(topic_root.glob("*.tex")):
        if tex.resolve() not in included:
            continue
        if not tex.is_file():
            continue
        text = strip_latex_comments(read_text(tex))
        if proof_bearing_re.search(text):
            return True
    return False
