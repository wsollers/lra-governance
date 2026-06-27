from __future__ import annotations

import json
import re
from pathlib import Path

from core.file_inventory import all_files
from core.finding import Finding, finding
from core.tex import INPUT_RE, read_text, strip_latex_comments


IMAGE_PATH_RE = re.compile(r"^images/[A-Za-z0-9._-]+\.png$")
FRONTMATTER_CALL_RE = re.compile(
    r"\\LRAFrontMatterPage"
    r"\{([^{}]*)\}"
    r"\{([^{}]*)\}"
    r"\{([^{}]*)\}"
    r"\{([^{}]*)\}"
    r"\{([^{}]*)\}"
    r"\{([^{}]*)\}"
)
PART_RE = re.compile(r"\\part(?:\[[^\]]*\])?\{([^}]+)\}")
LRAMETA_SERIES_RE = re.compile(r"series\s*=\s*\{([^{}]+)\}")


def validate(volume_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    registry = _registry_for(volume_root)
    if registry is None:
        return findings

    _validate_registry_record(volume_root, registry, findings)
    _validate_frontmatter_renderer(volume_root, findings)
    _validate_volume_root(volume_root, registry, findings)
    for book in registry.get("books", []):
        _validate_book_root(volume_root, registry, book, findings)
    _validate_volume_index(volume_root, registry, findings)
    _validate_lrameta_series(volume_root, registry, findings)
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


def _validate_registry_record(volume_root: Path, registry: dict, findings: list[Finding]) -> None:
    required = {
        "display_title": "volume display title",
        "series_title": "series title",
        "frontmatter_mathematician": "frontmatter mathematician",
        "mathematician_lifespan": "mathematician lifespan",
        "image_path": "frontmatter image path",
    }
    for key, label in required.items():
        if not isinstance(registry.get(key), str) or not registry.get(key):
            findings.append(
                finding(
                    "frontmatter_registry_missing_field",
                    f"Book registry volume record is missing {label} ({key}).",
                    volume_root,
                    volume_root,
                )
            )
    _validate_registry_image_path(volume_root, volume_root, registry.get("image_path"), findings)
    for book in registry.get("books", []):
        if book.get("image_path"):
            _validate_registry_image_path(volume_root, volume_root, book.get("image_path"), findings)


def _validate_registry_image_path(volume_root: Path, path: Path, image_path: object, findings: list[Finding]) -> None:
    if isinstance(image_path, str) and image_path and IMAGE_PATH_RE.fullmatch(image_path):
        return
    findings.append(
        finding(
            "frontmatter_registry_bad_image_path",
            f"Frontmatter image_path must use images/<filename>.png, found {image_path!r}.",
            path,
            volume_root,
        )
    )


def _validate_frontmatter_renderer(volume_root: Path, findings: list[Finding]) -> None:
    renderer = volume_root / "frontmatter.tex"
    if not renderer.is_file():
        findings.append(
            finding(
                "missing_frontmatter_renderer",
                "Volume must define volume-local frontmatter renderer at frontmatter.tex.",
                renderer,
                volume_root,
            )
        )
        return
    text = strip_latex_comments(read_text(renderer))
    if r"\newcommand{\LRAFrontMatterPage}[6]" not in text:
        findings.append(
            finding(
                "frontmatter_renderer_missing_macro",
                "frontmatter.tex must define \\LRAFrontMatterPage with six arguments.",
                renderer,
                volume_root,
            )
        )
    if r"\includegraphics" not in text:
        findings.append(
            finding(
                "frontmatter_renderer_missing_image",
                "frontmatter.tex must render the frontmatter image argument.",
                renderer,
                volume_root,
            )
        )


def _validate_volume_root(volume_root: Path, registry: dict, findings: list[Finding]) -> None:
    root = volume_root.parent / f"{volume_root.name}.tex"
    expected = (
        registry.get("series_title", ""),
        registry.get("display_title", ""),
        "",
        registry.get("frontmatter_mathematician", ""),
        registry.get("mathematician_lifespan", ""),
        registry.get("image_path", ""),
    )
    _validate_root_frontmatter(volume_root, root, expected, findings)


def _validate_book_root(volume_root: Path, registry: dict, book: dict, findings: list[Finding]) -> None:
    root_name = book.get("tex_root")
    if not isinstance(root_name, str):
        return
    root = volume_root.parent / root_name
    expected = (
        registry.get("series_title", ""),
        registry.get("display_title", ""),
        book.get("title", ""),
        book.get("frontmatter_mathematician") or registry.get("frontmatter_mathematician", ""),
        book.get("mathematician_lifespan") or registry.get("mathematician_lifespan", ""),
        book.get("image_path") or registry.get("image_path", ""),
    )
    _validate_root_frontmatter(volume_root, root, expected, findings)


def _validate_root_frontmatter(
    volume_root: Path,
    root: Path,
    expected: tuple[str, str, str, str, str, str],
    findings: list[Finding],
) -> None:
    if not root.is_file():
        return
    text = strip_latex_comments(read_text(root))
    inputs = _inputs(text)
    expected_input = f"{volume_root.name}/frontmatter"
    if expected_input not in inputs:
        findings.append(
            finding(
                "root_missing_frontmatter_input",
                f"{root.name} must input {expected_input}.",
                root,
                volume_root,
            )
        )
    if r"\begin{titlepage}" in text:
        findings.append(
            finding(
                "root_inline_frontmatter",
                "PDF roots must use volume-local frontmatter.tex instead of inline titlepage/frontmatter blocks.",
                root,
                volume_root,
            )
        )
    match = FRONTMATTER_CALL_RE.search(text)
    if not match:
        findings.append(
            finding(
                "root_missing_frontmatter_call",
                f"{root.name} must call \\LRAFrontMatterPage with series, volume, book, mathematician, lifespan, and image path.",
                root,
                volume_root,
            )
        )
        return
    actual = tuple(item.strip() for item in match.groups())
    if actual != expected:
        findings.append(
            finding(
                "root_frontmatter_metadata_mismatch",
                f"{root.name} frontmatter metadata must be {expected!r}; found {actual!r}.",
                root,
                volume_root,
                _line_for_pos(text, match.start()),
            )
        )
    image_path = actual[5]
    if not IMAGE_PATH_RE.fullmatch(image_path):
        findings.append(
            finding(
                "frontmatter_bad_image_path",
                f"Frontmatter image path must use images/<filename>.png, found {image_path!r}.",
                root,
                volume_root,
                _line_for_pos(text, match.start()),
            )
        )
    elif not (volume_root.parent / image_path).is_file():
        findings.append(
            finding(
                "frontmatter_missing_image_file",
                f"Frontmatter image file is missing: {image_path}.",
                root,
                volume_root,
                _line_for_pos(text, match.start()),
            )
        )


def _validate_volume_index(volume_root: Path, registry: dict, findings: list[Finding]) -> None:
    path = volume_root / "index.tex"
    if not path.is_file():
        return
    text = strip_latex_comments(read_text(path))
    display_title = registry.get("display_title", "")
    part_titles = PART_RE.findall(text)
    if display_title and display_title not in text:
        findings.append(
            finding(
                "volume_index_display_title_mismatch",
                f"Volume index must carry registry title {display_title!r} in its comment/title context.",
                path,
                volume_root,
            )
        )
    if display_title and part_titles and display_title not in part_titles:
        findings.append(
            finding(
                "part_title_mismatch",
                f"\\part title must match registry display title {display_title!r}; found {part_titles!r}.",
                path,
                volume_root,
                _line_for_text(text, r"\part"),
            )
        )


def _validate_lrameta_series(volume_root: Path, registry: dict, findings: list[Finding]) -> None:
    expected = registry.get("series_title")
    if not expected:
        return
    for path in all_files(volume_root, suffixes=(".tex",)):
        text = strip_latex_comments(read_text(path))
        for match in LRAMETA_SERIES_RE.finditer(text):
            actual = match.group(1).strip()
            if actual != expected:
                findings.append(
                    finding(
                        "metadata_series_title_mismatch",
                        f"Metadata series title must be {expected!r}; found {actual!r}.",
                        path,
                        volume_root,
                        _line_for_pos(text, match.start()),
                    )
                )


def _inputs(text: str) -> set[str]:
    return {
        match.group(1).replace("\\", "/").removesuffix(".tex")
        for match in INPUT_RE.finditer(text)
    }


def _line_for_text(text: str, needle: str) -> int:
    pos = text.find(needle)
    return _line_for_pos(text, pos) if pos >= 0 else 0


def _line_for_pos(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1
