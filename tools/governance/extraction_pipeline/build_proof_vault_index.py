#!/usr/bin/env python3
"""Build the proof-vault index consumed by lra-knowledge-explorer."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required: pip install pyyaml") from exc


SCHEMA = "lra.proof_vault_index"
SCHEMA_VERSION = 2
GITHUB_BLOB_BASE = "https://github.com/wsollers/lra-proof-vault/blob/master"
GITHUB_TREE_BASE = "https://github.com/wsollers/lra-proof-vault/tree/master"

LABEL_RE = re.compile(r"Canonical theorem label:\s*`([^`]+)`", re.IGNORECASE)
STATUS_RE = re.compile(r"Status:\s*`([^`]+)`", re.IGNORECASE)
HEADING_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
TRANSCRIPTION_RE = re.compile(r"^##\s+Transcription\s*$([\s\S]*?)(?=^##\s+|\Z)", re.MULTILINE)


def rel_posix(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def title_from_path(path: Path) -> str:
    return " ".join(part.capitalize() for part in path.name.split("-") if part)


def markdown_title(text: str, md_path: Path) -> str:
    match = HEADING_RE.search(text)
    if match:
        return match.group(1).strip()
    return title_from_path(md_path.parent)


def markdown_body(text: str) -> str:
    match = TRANSCRIPTION_RE.search(text)
    if match:
        return match.group(1).strip()
    return text.strip()


def vault_blob_url(path: Path, vault_root: Path) -> str:
    return f"{GITHUB_BLOB_BASE}/{rel_posix(path, vault_root)}"


def vault_tree_url(path: Path, vault_root: Path) -> str:
    return f"{GITHUB_TREE_BASE}/{rel_posix(path, vault_root)}"


def resolve_attempt_path(folder: Path, value: str) -> Path:
    candidate = Path(value.replace("\\", "/"))
    if candidate.is_absolute():
        return candidate
    return folder / candidate


def read_optional_text(folder: Path, attempt: dict[str, Any], key: str, warnings: list[dict[str, str]], metadata_path: Path, vault_root: Path) -> str:
    value = str(attempt.get(key) or "").strip()
    if not value:
        return ""
    path = resolve_attempt_path(folder, value)
    if not path.exists():
        warnings.append(
            {
                "type": "missing_attempt_text_file",
                "metadata": rel_posix(metadata_path, vault_root),
                "attempt_id": str(attempt.get("attempt_id") or "proof-attempt"),
                "field": key,
                "path": value,
            }
        )
        return ""
    return path.read_text(encoding="utf-8", errors="replace").strip()


def attempt_record(
    metadata_path: Path,
    metadata: dict[str, Any],
    attempt: dict[str, Any],
    vault_root: Path,
    warnings: list[dict[str, str]],
) -> dict[str, Any]:
    folder = metadata_path.parent
    theorem_title = str(metadata.get("theorem_title") or title_from_path(folder))
    attempt_id = str(attempt.get("attempt_id") or "proof-attempt")
    source_path = str(attempt.get("source_path") or "")
    image_links: list[str] = []

    if source_path:
        image_path = resolve_attempt_path(folder, source_path)
        if image_path.exists():
            image_links.append(vault_blob_url(image_path, vault_root))
        else:
            warnings.append(
                {
                    "type": "missing_attempt_file",
                    "metadata": rel_posix(metadata_path, vault_root),
                    "attempt_id": attempt_id,
                    "source_path": source_path,
                }
            )

    rendered_html = str(attempt.get("rendered_html") or "")
    path = rel_posix(metadata_path, vault_root)
    if rendered_html:
        rendered_path = resolve_attempt_path(folder, rendered_html)
        if rendered_path.exists():
            path = rel_posix(rendered_path, vault_root)

    notes = str(attempt.get("notes") or "").strip()
    tags = attempt.get("tags")
    tag_text = ""
    if isinstance(tags, list) and tags:
        tag_text = "\n\nTags: " + ", ".join(str(tag) for tag in tags)

    ocr_text = read_optional_text(folder, attempt, "ocr_text_path", warnings, metadata_path, vault_root)
    markdown = read_optional_text(folder, attempt, "markdown_path", warnings, metadata_path, vault_root)
    tex = read_optional_text(folder, attempt, "tex_path", warnings, metadata_path, vault_root)

    return {
        "title": f"{theorem_title} ({attempt_id})",
        "path": path,
        "vault_record": rel_posix(folder, vault_root),
        "vault_url": vault_tree_url(folder, vault_root),
        "theorem_id": str(metadata.get("theorem_id") or metadata.get("theorem_label") or ""),
        "source_repo": str(metadata.get("source_repo") or ""),
        "volume": str(metadata.get("volume") or ""),
        "book": str(metadata.get("book") or ""),
        "book_slug": str(metadata.get("book_slug") or ""),
        "book_title": str(metadata.get("book_title") or ""),
        "book_dir": str(metadata.get("book_dir") or ""),
        "chapter": str(metadata.get("chapter") or ""),
        "section": str(metadata.get("section") or ""),
        "subsection": str(metadata.get("subsection") or ""),
        "theorem_tex": str(metadata.get("theorem_tex") or ""),
        "proof_tex": str(metadata.get("proof_tex") or ""),
        "proof_label": str(metadata.get("proof_label") or ""),
        "vault_path": str(metadata.get("vault_path") or ""),
        "route_confidence": str(metadata.get("route_confidence") or ""),
        "attempt_id": attempt_id,
        "review_status": str(attempt.get("review_status") or ""),
        "images": image_links,
        "body": notes + tag_text,
        "ocr_text": ocr_text,
        "markdown": markdown,
        "tex": tex,
        "text_source": str(attempt.get("text_source") or ""),
        "text_review_status": str(attempt.get("text_review_status") or ""),
    }


def add_metadata_records(records: dict[str, list[dict[str, Any]]], vault_root: Path, warnings: list[dict[str, str]]) -> None:
    for metadata_path in sorted(vault_root.glob("volume-*/**/metadata.yaml")):
        metadata = read_yaml(metadata_path)
        label = metadata.get("theorem_id") or metadata.get("theorem_label")
        attempts = metadata.get("attempts")
        if not isinstance(label, str) or not label.strip() or not isinstance(attempts, list):
            continue
        for attempt in attempts:
            if isinstance(attempt, dict):
                records.setdefault(label.strip(), []).append(
                    attempt_record(metadata_path, metadata, attempt, vault_root, warnings)
                )


def add_markdown_records(records: dict[str, list[dict[str, Any]]], vault_root: Path) -> None:
    md_paths = [
        path
        for path in vault_root.rglob("proof-*.md")
        if ".git" not in path.parts and path.is_file() and not path.name.endswith(".proof.md")
    ]

    for md_path in sorted(md_paths):
        text = md_path.read_text(encoding="utf-8")
        label_match = LABEL_RE.search(text)
        if not label_match:
            continue

        label = label_match.group(1).strip()
        attempt_dir = md_path.parent
        image_paths = sorted(attempt_dir.glob("proof-*.jpg")) + sorted(attempt_dir.glob("proof-*.png"))
        status_match = STATUS_RE.search(text)
        records.setdefault(label, []).append(
            {
                "title": markdown_title(text, md_path),
                "path": rel_posix(md_path, vault_root),
                "vault_record": rel_posix(attempt_dir, vault_root),
                "vault_url": vault_tree_url(attempt_dir, vault_root),
                "review_status": status_match.group(1).strip() if status_match else "",
                "images": [vault_blob_url(image_path, vault_root) for image_path in image_paths],
                "body": markdown_body(text),
            }
        )


def build_index(vault_root: Path, generated_at: str | None = None) -> dict[str, Any]:
    warnings: list[dict[str, str]] = []
    records: dict[str, list[dict[str, Any]]] = {}
    add_metadata_records(records, vault_root, warnings)
    add_markdown_records(records, vault_root)

    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "source": "lra-proof-vault",
        "record_count": sum(len(items) for items in records.values()),
        "warning_count": len(warnings),
        "warnings": warnings,
        "records": dict(sorted(records.items())),
    }


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--proof-vault",
        type=Path,
        default=Path(__file__).resolve().parents[4] / "lra-proof-vault",
        help="Path to lra-proof-vault.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parents[4] / "lra-knowledge-explorer" / "proof-vault-index.json",
        help="Output proof-vault-index.json path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    vault_root = args.proof_vault.resolve()
    if not (vault_root / ".git").exists():
        raise SystemExit(f"Missing lra-proof-vault repo: {vault_root}")
    index = build_index(vault_root)
    write_json(args.out.resolve(), index)
    print(f"Wrote {args.out.resolve()} with {index['record_count']} records.")
    if index["warning_count"]:
        print(f"Warnings: {index['warning_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
