#!/usr/bin/env python3
"""Generate book-aware theorem routes for proof-vault synchronization."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GOVERNANCE_TOOL_ROOT = Path(__file__).resolve().parents[1]
if str(GOVERNANCE_TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(GOVERNANCE_TOOL_ROOT))

import dependency_graph  # noqa: E402
from core.file_inventory import files_to_validate  # noqa: E402
from core.volume import resolve_volume  # noqa: E402

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


SCHEMA = "lra.theorem_routes"
SCHEMA_VERSION = 1
ROUTE_VERSION = "leaf-theorem-routes-v2"
PROOF_FOR_RE = re.compile(r"\\LRAProofFor\{(?P<label>(?:thm|lem|prop|cor|def|ax):[^{}]+)\}", re.IGNORECASE)
PROOF_LABEL_RE = re.compile(r"\\label\{(?P<label>prf:[^{}]+)\}")


def rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def git_commit(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def load_book_registry(path: Path) -> dict[str, list[dict[str, Any]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    by_roman: dict[str, list[dict[str, Any]]] = {}
    for volume in data.get("volumes", []):
        roman = str(volume.get("roman") or "").lower()
        books = volume.get("books") if isinstance(volume.get("books"), list) else []
        by_roman[roman] = books
    return by_roman


def book_for_file(file_rel: str, books: list[dict[str, Any]]) -> dict[str, Any]:
    matches = [
        book
        for book in books
        if file_rel == str(book.get("book_dir") or "") or file_rel.startswith(f"{book.get('book_dir')}/")
    ]
    if matches:
        return max(matches, key=lambda item: len(str(item.get("book_dir") or "")))
    return {}


def slug_from_label(label: str) -> str:
    return label.replace(":", "-", 1).lower()


def proof_index(repo_root: Path) -> dict[str, dict[str, str]]:
    volume_root = resolve_volume(repo_root).root
    by_target: dict[str, dict[str, str]] = {}
    for path in files_to_validate(volume_root, only_reachable=True):
        raw = path.read_text(encoding="utf-8", errors="replace")
        text = dependency_graph.strip_comments(raw)
        proof_for = PROOF_FOR_RE.search(text)
        if not proof_for:
            continue
        target = proof_for.group("label").strip()
        proof_label = ""
        label_match = PROOF_LABEL_RE.search(text)
        if label_match:
            proof_label = label_match.group("label").strip()
        by_target[target] = {
            "proof_tex": rel(path, repo_root),
            "proof_label": proof_label,
        }
    return by_target


def route_for_node(
    *,
    node: dependency_graph.Node,
    repo_root: Path,
    volume_root: Path,
    books: list[dict[str, Any]],
    proofs: dict[str, dict[str, str]],
    source_commit: str,
) -> dict[str, Any]:
    file_rel = node.file
    book = book_for_file(file_rel, books)
    book_dir = str(book.get("book_dir") or "")
    book_slug = str(book.get("slug") or "")
    book_title = str(book.get("title") or "")
    book_path_slug = Path(book_dir).name if book_dir else ""

    path_parts = Path(file_rel).parts
    volume = volume_root.name
    chapter = ""
    if book_dir and file_rel.startswith(f"{book_dir}/"):
        remaining = Path(file_rel).relative_to(book_dir).parts
        chapter = remaining[0] if remaining else ""
    elif len(path_parts) >= 2:
        chapter = path_parts[1]

    proof = proofs.get(node.label, {})
    vault_parts = [volume]
    if book_path_slug:
        vault_parts.append(book_path_slug)
    if chapter:
        vault_parts.append(chapter)
    vault_parts.append(slug_from_label(node.label))

    return {
        "theorem_id": node.label,
        "title": node.title,
        "type": node.kind,
        "volume": volume,
        "book": book_path_slug,
        "book_slug": book_slug,
        "book_title": book_title,
        "book_dir": book_dir,
        "chapter": chapter,
        "section": "",
        "subsection": "",
        "theorem_tex": file_rel,
        "proof_tex": proof.get("proof_tex", ""),
        "proof_label": proof.get("proof_label", ""),
        "vault_path": "/".join(vault_parts),
        "tags": [],
        "dependencies": [],
        "source_repo": repo_root.name,
        "source_commit": source_commit,
        "route_version": ROUTE_VERSION,
        "proof_vault_url": "",
    }


def write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_yaml(path: Path, payload: dict[str, Any]) -> None:
    if yaml is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=False, width=100), encoding="utf-8")


def generate_for_repo(repo_root: Path, registry: dict[str, list[dict[str, Any]]], out_dir: Path | None) -> dict[str, Any]:
    volume_root = resolve_volume(repo_root).root
    roman = volume_root.name.removeprefix("volume-")
    books = registry.get(roman, [])
    source_commit = git_commit(repo_root)
    nodes, issues = dependency_graph.extract_nodes(repo_root, repo_root.name)
    proofs = proof_index(repo_root)
    routes = [
        route_for_node(
            node=node,
            repo_root=repo_root,
            volume_root=volume_root,
            books=books,
            proofs=proofs,
            source_commit=source_commit,
        )
        for node in nodes
        if node.kind in dependency_graph.FORMAL_PREFIXES
    ]
    routes.sort(key=lambda item: (item.get("volume", ""), item.get("book", ""), item.get("chapter", ""), item.get("theorem_id", "")))

    payload = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_repo": repo_root.name,
        "source_commit": source_commit,
        "route_version": ROUTE_VERSION,
        "route_count": len(routes),
        "issue_count": len(issues),
        "issues": [asdict(issue) for issue in issues],
        "routes": routes,
    }

    destination = out_dir or repo_root / "build" / "knowledge"
    write_payload(destination / "theorem-routes.json", payload)
    write_yaml(destination / "theorem-routes.yaml", payload)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repos-root", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--repo", type=Path, action="append", default=[])
    parser.add_argument(
        "--book-registry",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "docs" / "architecture" / "book-registry.json",
    )
    parser.add_argument("--out-dir", type=Path, help="Optional single output directory; only valid with one --repo.")
    return parser.parse_args()


def volume_repos(root: Path) -> list[Path]:
    return sorted(path for path in root.glob("lra-volume-*") if path.is_dir() and (path / ".git").exists())


def main() -> int:
    args = parse_args()
    repos = [path.resolve() for path in args.repo] if args.repo else volume_repos(args.repos_root.resolve())
    if args.out_dir and len(repos) != 1:
        raise SystemExit("--out-dir is only valid with exactly one --repo")
    registry = load_book_registry(args.book_registry.resolve())
    total_routes = 0
    total_issues = 0
    for repo in repos:
        payload = generate_for_repo(repo, registry, args.out_dir.resolve() if args.out_dir else None)
        total_routes += int(payload["route_count"])
        total_issues += int(payload["issue_count"])
        print(f"{repo.name}: {payload['route_count']} routes, {payload['issue_count']} issue(s)")
    print(f"total: {total_routes} routes, {total_issues} issue(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
