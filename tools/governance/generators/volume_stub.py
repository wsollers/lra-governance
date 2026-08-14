from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

import yaml


_VOLUME_RE = re.compile(r"volume-[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_SUBJECT_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def _required(name: str, value: str) -> str:
    value = (value or "").strip()
    if not value:
        raise ValueError(f"{name} is required")
    return value


def _validate_registry(chapter_registry: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, entry in enumerate(chapter_registry, 1):
        subject = _required(f"chapter_registry[{index}].subject", entry.get("subject", ""))
        title = _required(
            f"chapter_registry[{index}].display_title", entry.get("display_title", "")
        )
        if not _SUBJECT_RE.fullmatch(subject):
            raise ValueError(f"invalid chapter subject: {subject}")
        if subject in seen:
            raise ValueError(f"duplicate chapter subject: {subject}")
        seen.add(subject)
        result.append({"subject": subject, "display_title": title, "status": "planned"})
    return result


def _validate_frontispiece(frontispiece: Mapping[str, str] | None) -> dict[str, str] | None:
    if not frontispiece:
        return None
    result = {
        "mathematician": _required("frontispiece.mathematician", frontispiece.get("mathematician", "")),
        "years": _required("frontispiece.years", frontispiece.get("years", "")),
        "image": _required("frontispiece.image", frontispiece.get("image", "")),
    }
    if not result["image"].startswith("images/") or not result["image"].endswith(".png"):
        raise ValueError("frontispiece.image must be an images/<name>.png path")
    return result


def render_volume_stub(
    volume_identifier: str,
    volume_display_title: str,
    volume_scope: str,
    chapter_registry: Sequence[Mapping[str, str]],
    *,
    frontispiece: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return the two-file planned-volume shell from explicit inputs."""
    volume_identifier = _required("volume_identifier", volume_identifier)
    if not _VOLUME_RE.fullmatch(volume_identifier):
        raise ValueError("volume_identifier must have the form volume-<identifier>")
    volume_display_title = _required("volume_display_title", volume_display_title)
    volume_scope = _required("volume_scope", volume_scope)
    chapters = _validate_registry(chapter_registry)
    frontispiece_data = _validate_frontispiece(frontispiece)

    image_block = ""
    if frontispiece_data:
        image_block = (
            "\\begin{center}\n"
            f"\\includegraphics[width=0.6\\textwidth]{{{frontispiece_data['image']}}}\n"
            "\\end{center}\n\n"
        )
    registry_items = "\n".join(
        f"  \\item {entry['display_title']}" for entry in chapters
    ) or "  \\item TODO: add chapters in dependency order."
    index_tex = (
        f"\\chapter*{{{volume_display_title}}}\n\n"
        f"{image_block}"
        "\\section*{Scope}\n\n"
        f"{volume_scope}\n\n"
        "\\section*{Chapter Registry}\n\n"
        "The following chapters are listed in dependency order.\n\n"
        "\\begin{enumerate}\n"
        f"{registry_items}\n"
        "\\end{enumerate}\n\n"
        "\\section*{Status}\n\n"
        "\\textbf{Status:} Planned\n\n"
        "Chapters will be \\input here as they are created.\n"
    )
    manifest: dict[str, object] = {
        "volume": volume_identifier,
        "display_title": volume_display_title,
        "status": "planned",
    }
    if frontispiece_data:
        manifest["frontispiece"] = frontispiece_data
    manifest["scope"] = volume_scope
    manifest["chapters"] = chapters
    yaml_text = yaml.safe_dump(manifest, sort_keys=False, allow_unicode=False)
    return {
        f"{volume_identifier}/index.tex": index_tex,
        f"{volume_identifier}/chapter.yaml": yaml_text,
    }
