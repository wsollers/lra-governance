from __future__ import annotations

import re
from pathlib import Path

import yaml

from core.finding import Finding, finding
from core.tex import strip_latex_comment
from core.volume import VOLUME_RE, is_ignored, latex_input_path
from validators.chapter_router import validate_chapter_router


_SUBJECT_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def volume_root_for(chapter: Path) -> Path:
    """Return the nearest volume root, falling back to the chapter parent."""
    chapter = chapter.resolve()
    for parent in chapter.parents:
        if VOLUME_RE.fullmatch(parent.name):
            return parent
    return chapter.parent


def _add(
    findings: list[Finding],
    root: Path,
    path: Path,
    code: str,
    message: str,
    line: int = 0,
) -> None:
    findings.append(finding(code, message, path, root, line, "error"))


def _load_manifest(path: Path) -> dict | None:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    return data if isinstance(data, dict) else None


def applies_to(chapter: Path) -> bool:
    """Return whether a chapter carries the deterministic planned-stub shape."""
    manifest = chapter / "chapter.yaml"
    try:
        text = manifest.read_text(encoding="utf-8")
    except OSError:
        return False
    data = _load_manifest(manifest)
    if data is not None:
        return "sections" in data and "dependencies" in data
    return "sections:" in text and "dependencies:" in text


def _registry_checks(
    findings: list[Finding],
    root: Path,
    manifest_path: Path,
    data: dict,
    registry: list[dict],
) -> None:
    subject = data.get("subject")
    matches = [entry for entry in registry if isinstance(entry, dict) and entry.get("subject") == subject]
    if len(matches) != 1:
        _add(
            findings,
            root,
            manifest_path,
            "chapter_stub_registry_membership",
            "Chapter subject must occur exactly once in the supplied chapter registry.",
        )
        return
    match = matches[0]
    if match.get("display_title") and match.get("display_title") != data.get("display_title"):
        _add(
            findings,
            root,
            manifest_path,
            "chapter_stub_registry_title_mismatch",
            "Chapter display_title must match the supplied chapter registry.",
        )
    position = registry.index(match)
    prior = registry[position - 1] if position > 0 else {}
    following = registry[position + 1] if position + 1 < len(registry) else {}
    expected_prior = prior.get("subject", "") if isinstance(prior, dict) else ""
    expected_next = following.get("subject", "") if isinstance(following, dict) else ""
    dependencies = data.get("dependencies")
    if isinstance(dependencies, dict) and (
        dependencies.get("prior", "") != expected_prior
        or dependencies.get("next", "") != expected_next
    ):
        _add(
            findings,
            root,
            manifest_path,
            "chapter_stub_registry_neighbors",
            "dependencies.prior and dependencies.next must match the supplied registry order.",
        )


def _capstone_checks(findings: list[Finding], root: Path, chapter: Path) -> None:
    exercises = chapter / "proofs" / "exercises"
    exercises_index = exercises / "index.tex"
    capstone = exercises / f"capstone-{chapter.name}.tex"
    if exercises.exists() and not exercises.is_dir():
        _add(
            findings,
            root,
            exercises,
            "chapter_stub_invalid_exercises_path",
            "proofs/exercises must be a directory when present.",
        )
        return
    if exercises_index.is_file() != capstone.is_file():
        _add(
            findings,
            root,
            exercises,
            "chapter_stub_capstone_pair",
            "Optional capstone router and capstone file must either both exist or both be absent.",
        )
        return
    if not exercises_index.is_file():
        return
    route = latex_input_path(capstone)
    significant = [
        strip_latex_comment(line).strip()
        for line in exercises_index.read_text(encoding="utf-8", errors="replace").splitlines()
        if strip_latex_comment(line).strip()
    ]
    if significant != [f"\\input{{{route}}}"]:
        _add(
            findings,
            root,
            exercises_index,
            "chapter_stub_capstone_router",
            f"Capstone router must contain only \\input{{{route}}}.",
        )


def validate_chapter(
    chapter: Path,
    *,
    volume_root: Path | None = None,
    chapter_registry: list[dict] | None = None,
) -> list[Finding]:
    """Validate one chapter shell emitted by the canonical stub generator."""
    chapter = chapter.resolve()
    root = (volume_root or volume_root_for(chapter)).resolve()
    findings: list[Finding] = []

    if not chapter.is_dir():
        _add(findings, root, chapter, "chapter_stub_missing_root", "Chapter stub directory does not exist.")
        return findings
    if not _SUBJECT_RE.fullmatch(chapter.name):
        _add(
            findings,
            root,
            chapter,
            "chapter_stub_invalid_subject",
            "Chapter folder name must be lowercase hyphen-separated ASCII.",
        )

    required = {
        "index.tex": chapter / "index.tex",
        "chapter.yaml": chapter / "chapter.yaml",
        "notes/index.tex": chapter / "notes" / "index.tex",
        "proofs/index.tex": chapter / "proofs" / "index.tex",
    }
    for relative, path in required.items():
        if not path.is_file():
            _add(
                findings,
                root,
                path,
                "chapter_stub_missing_path",
                f"Planned chapter stub requires {relative}.",
            )

    manifest_path = required["chapter.yaml"]
    data: dict | None = None
    if manifest_path.is_file():
        try:
            loaded = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            _add(
                findings,
                root,
                manifest_path,
                "chapter_stub_invalid_yaml",
                f"Invalid chapter stub YAML: {exc}",
            )
        else:
            if not isinstance(loaded, dict):
                _add(
                    findings,
                    root,
                    manifest_path,
                    "chapter_stub_invalid_manifest",
                    "Chapter stub manifest must be a mapping.",
                )
            else:
                data = loaded

    if data is not None:
        if data.get("subject") != chapter.name:
            _add(findings, root, manifest_path, "chapter_stub_subject_mismatch", "Manifest subject must equal the chapter directory name.")
        if not isinstance(data.get("display_title"), str) or not data["display_title"].strip():
            _add(findings, root, manifest_path, "chapter_stub_missing_title", "display_title must be non-empty text.")
        if data.get("volume") != root.name:
            _add(findings, root, manifest_path, "chapter_stub_volume_mismatch", "Manifest volume must equal the containing volume directory name.")
        if data.get("path") != latex_input_path(chapter):
            _add(findings, root, manifest_path, "chapter_stub_path_mismatch", "Manifest path must equal the canonical chapter input path.")
        if data.get("status") != "planned":
            _add(findings, root, manifest_path, "chapter_stub_bad_status", "Planned chapter status must be planned.")
        if not isinstance(data.get("sections"), list):
            _add(findings, root, manifest_path, "chapter_stub_invalid_sections", "sections must be an ordered list.")
        dependencies = data.get("dependencies")
        if not isinstance(dependencies, dict) or any(
            not isinstance(dependencies.get(key, ""), str) for key in ("prior", "next")
        ):
            _add(
                findings,
                root,
                manifest_path,
                "chapter_stub_invalid_dependencies",
                "dependencies must map prior and next to subject strings.",
            )
        if chapter_registry:
            _registry_checks(findings, root, manifest_path, data, chapter_registry)

    if required["index.tex"].is_file():
        findings.extend(
            validate_chapter_router(
                root,
                chapter,
                severity="error",
                allow_legacy_breadcrumb=False,
            )
        )
    _capstone_checks(findings, root, chapter)
    return findings


def validate(volume_root: Path, files=None) -> list[Finding]:
    """Validate planned chapter stubs found anywhere under a volume root."""
    findings: list[Finding] = []
    volume_root = volume_root.resolve()
    manifests = sorted(volume_root.rglob("chapter.yaml"))
    for manifest in manifests:
        chapter = manifest.parent
        if chapter == volume_root or is_ignored(manifest, volume_root):
            continue
        if applies_to(chapter):
            findings.extend(validate_chapter(chapter, volume_root=volume_root))
    return findings
