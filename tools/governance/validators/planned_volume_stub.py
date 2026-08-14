from __future__ import annotations

import re
from pathlib import Path

import yaml

from core.finding import Finding, finding
from core.tex import read_text


_VOLUME_RE = re.compile(r"volume-[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_SUBJECT_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def applies_to(volume_root: Path) -> bool:
    """Return whether the root carries the planned-volume stub manifest."""
    return (volume_root / "chapter.yaml").is_file()


def _add(findings: list[Finding], root: Path, path: Path, code: str, message: str) -> None:
    findings.append(finding(code, message, path, root, 0, "error"))


def validate(volume_root: Path, files=None) -> list[Finding]:
    """Validate the two-file shell emitted by ``render_volume_stub``.

    Completed volume repositories normally do not have ``chapter.yaml`` at the
    volume root, so this validator is intentionally inactive for them.
    """
    manifest_path = volume_root / "chapter.yaml"
    if not applies_to(volume_root):
        return []

    findings: list[Finding] = []
    index_path = volume_root / "index.tex"
    if not index_path.is_file():
        _add(findings, volume_root, index_path, "planned_volume_stub_missing_index", "Planned volume stub requires index.tex.")
        return findings
    try:
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        _add(findings, volume_root, manifest_path, "planned_volume_stub_invalid_yaml", f"Invalid planned-volume YAML: {exc}")
        return findings
    if not isinstance(data, dict):
        _add(findings, volume_root, manifest_path, "planned_volume_stub_invalid_manifest", "Planned-volume manifest must be a mapping.")
        return findings

    volume_id = data.get("volume")
    if volume_id != volume_root.name or not _VOLUME_RE.fullmatch(str(volume_id or "")):
        _add(findings, volume_root, manifest_path, "planned_volume_stub_volume_mismatch", "Manifest volume must equal the volume directory name.")
    title = data.get("display_title")
    scope = data.get("scope")
    if not isinstance(title, str) or not title.strip():
        _add(findings, volume_root, manifest_path, "planned_volume_stub_missing_title", "display_title must be non-empty text.")
    if not isinstance(scope, str) or not scope.strip():
        _add(findings, volume_root, manifest_path, "planned_volume_stub_missing_scope", "scope must be non-empty text.")
    if data.get("status") != "planned":
        _add(findings, volume_root, manifest_path, "planned_volume_stub_bad_status", "Planned volume status must be planned.")

    chapters = data.get("chapters")
    if not isinstance(chapters, list):
        _add(findings, volume_root, manifest_path, "planned_volume_stub_invalid_chapters", "chapters must be an ordered list.")
        chapters = []
    seen: set[str] = set()
    ordered_titles: list[str] = []
    for position, chapter in enumerate(chapters, 1):
        if not isinstance(chapter, dict):
            _add(findings, volume_root, manifest_path, "planned_volume_stub_invalid_chapter", f"Chapter {position} must be a mapping.")
            continue
        subject = chapter.get("subject")
        chapter_title = chapter.get("display_title")
        if not isinstance(subject, str) or not _SUBJECT_RE.fullmatch(subject):
            _add(findings, volume_root, manifest_path, "planned_volume_stub_invalid_subject", f"Chapter {position} has an invalid subject.")
        elif subject in seen:
            _add(findings, volume_root, manifest_path, "planned_volume_stub_duplicate_subject", f"Duplicate chapter subject: {subject}.")
        else:
            seen.add(subject)
        if not isinstance(chapter_title, str) or not chapter_title.strip():
            _add(findings, volume_root, manifest_path, "planned_volume_stub_missing_chapter_title", f"Chapter {position} requires display_title.")
        else:
            ordered_titles.append(chapter_title)
        if chapter.get("status") != "planned":
            _add(findings, volume_root, manifest_path, "planned_volume_stub_bad_chapter_status", f"Chapter {position} status must be planned.")

    frontispiece = data.get("frontispiece")
    if frontispiece is not None:
        if not isinstance(frontispiece, dict):
            _add(findings, volume_root, manifest_path, "planned_volume_stub_invalid_frontispiece", "frontispiece must be a mapping.")
        else:
            for key in ("mathematician", "years", "image"):
                if not isinstance(frontispiece.get(key), str) or not frontispiece[key].strip():
                    _add(findings, volume_root, manifest_path, "planned_volume_stub_incomplete_frontispiece", f"frontispiece.{key} is required.")
            image = frontispiece.get("image", "")
            if isinstance(image, str) and (not image.startswith("images/") or not image.endswith(".png")):
                _add(findings, volume_root, manifest_path, "planned_volume_stub_invalid_image", "frontispiece.image must use images/<name>.png.")

    index = read_text(index_path)
    for heading in (r"\section*{Scope}", r"\section*{Chapter Registry}", r"\section*{Status}"):
        if heading not in index:
            _add(findings, volume_root, index_path, "planned_volume_stub_missing_heading", f"Missing required heading {heading}.")
    if isinstance(title, str) and f"\\chapter*{{{title}}}" not in index:
        _add(findings, volume_root, index_path, "planned_volume_stub_title_mismatch", "index.tex title does not match the manifest.")
    if isinstance(scope, str) and scope not in index:
        _add(findings, volume_root, index_path, "planned_volume_stub_scope_mismatch", "index.tex scope does not match the manifest.")
    positions = [index.find(chapter_title) for chapter_title in ordered_titles]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        _add(findings, volume_root, index_path, "planned_volume_stub_chapter_order_mismatch", "Chapter titles must appear in manifest order.")
    if isinstance(frontispiece, dict) and isinstance(frontispiece.get("image"), str):
        if frontispiece["image"] not in index:
            _add(findings, volume_root, index_path, "planned_volume_stub_image_mismatch", "index.tex does not reference the manifest frontispiece image.")
    return findings
