#!/usr/bin/env python3
"""Report drift between generated wrapper previews and downstream files."""

from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from merge_repo_overlays import repo_names


WRAPPER_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".github/copilot-instructions.md",
    ".github/instructions/lra.instructions.md",
]
DRIFT_STATUSES = {"missing_downstream", "different"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare generated wrapper previews against downstream repo files."
    )
    parser.add_argument("--root", required=True, help="Repository family root.")
    parser.add_argument("--preview", required=True, help="Generated preview directory.")
    parser.add_argument("--out", required=True, help="Output directory for drift reports.")
    parser.add_argument("--repo", nargs="+", action="append", choices=repo_names())
    parser.add_argument("--fail-on-drift", action="store_true")
    return parser.parse_args(argv)


def selected_repos(repo_args: list[list[str]] | None) -> list[str]:
    if not repo_args:
        return repo_names()
    repos: list[str] = []
    for group in repo_args:
        repos.extend(group)
    return repos


def safe_resolve(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def ensure_output_under_governance(out_dir: Path, governance_root: Path) -> None:
    if governance_root not in out_dir.parents and out_dir != governance_root:
        raise ValueError(f"output directory must be under lra-governance: {out_dir}")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def line_count_bytes(data: bytes) -> int:
    if not data:
        return 0
    text = data.decode("utf-8", errors="replace")
    return len(text.splitlines())


def read_bytes_if_file(path: Path) -> bytes | None:
    if path.is_symlink():
        return None
    if not path.exists() or not path.is_file():
        return None
    return path.read_bytes()


def diff_stat(preview_data: bytes | None, downstream_data: bytes | None) -> tuple[int, int]:
    if preview_data is None or downstream_data is None:
        return 0, 0
    preview_lines = preview_data.decode("utf-8", errors="replace").splitlines()
    downstream_lines = downstream_data.decode("utf-8", errors="replace").splitlines()
    added = 0
    removed = 0
    for line in difflib.unified_diff(downstream_lines, preview_lines, lineterm=""):
        if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
            continue
        if line.startswith("+"):
            added += 1
        elif line.startswith("-"):
            removed += 1
    return added, removed


def classify(
    repo_path: Path,
    preview_path: Path,
    downstream_path: Path,
    preview_data: bytes | None,
    downstream_data: bytes | None,
) -> str:
    if not repo_path.exists() or not repo_path.is_dir():
        return "downstream_repo_missing"
    if preview_data is None:
        return "missing_preview"
    if downstream_data is None:
        return "missing_downstream"
    if preview_data == downstream_data:
        return "identical"
    return "different"


def make_record(root: Path, preview_root: Path, repo: str, wrapper_file: str) -> dict[str, Any]:
    repo_path = root / repo
    preview_path = preview_root / repo / wrapper_file
    downstream_path = repo_path / wrapper_file
    preview_data = read_bytes_if_file(preview_path)
    downstream_data = read_bytes_if_file(downstream_path)
    status = classify(repo_path, preview_path, downstream_path, preview_data, downstream_data)
    added, removed = diff_stat(preview_data, downstream_data)
    return {
        "repo": repo,
        "file": wrapper_file,
        "status": status,
        "preview_path": str(preview_path),
        "downstream_path": str(downstream_path),
        "preview_sha256": sha256_bytes(preview_data) if preview_data is not None else "",
        "downstream_sha256": sha256_bytes(downstream_data) if downstream_data is not None else "",
        "preview_bytes": len(preview_data) if preview_data is not None else 0,
        "downstream_bytes": len(downstream_data) if downstream_data is not None else 0,
        "preview_lines": line_count_bytes(preview_data or b""),
        "downstream_lines": line_count_bytes(downstream_data or b""),
        "added_lines": added,
        "removed_lines": removed,
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    fields = [
        "repo",
        "file",
        "status",
        "preview_path",
        "downstream_path",
        "preview_sha256",
        "downstream_sha256",
        "preview_bytes",
        "downstream_bytes",
        "added_lines",
        "removed_lines",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({field: record.get(field, "") for field in fields})


def write_markdown(path: Path, data: dict[str, Any]) -> None:
    records = data["records"]
    status_counts = Counter(record["status"] for record in records)
    missing_by_repo: dict[str, list[str]] = defaultdict(list)
    different_by_repo: dict[str, list[str]] = defaultdict(list)
    identical_files: list[str] = []
    for record in records:
        key = f"{record['repo']}/{record['file']}"
        if record["status"] in {"missing_downstream", "downstream_repo_missing"}:
            missing_by_repo[record["repo"]].append(record["file"])
        elif record["status"] == "different":
            different_by_repo[record["repo"]].append(record["file"])
        elif record["status"] == "identical":
            identical_files.append(key)

    lines = [
        "# Wrapper Drift Report",
        "",
        f"- Total repos checked: {data['total_repos_checked']}",
        f"- Total wrapper files checked: {len(records)}",
        "- Downstream files modified: no",
        "",
        "## Counts By Status",
        "",
    ]
    for status in [
        "missing_downstream",
        "identical",
        "different",
        "missing_preview",
        "downstream_repo_missing",
    ]:
        lines.append(f"- `{status}`: {status_counts.get(status, 0)}")

    lines.extend(["", "## Repos With Missing Downstream Wrappers", ""])
    if missing_by_repo:
        for repo, files in sorted(missing_by_repo.items()):
            lines.append(f"- `{repo}`: {', '.join(f'`{file}`' for file in files)}")
    else:
        lines.append("- None.")

    lines.extend(["", "## Repos With Different Wrappers", ""])
    if different_by_repo:
        for repo, files in sorted(different_by_repo.items()):
            lines.append(f"- `{repo}`: {', '.join(f'`{file}`' for file in files)}")
    else:
        lines.append("- None.")

    lines.extend(["", "## Files Identical", ""])
    if identical_files:
        for filename in identical_files:
            lines.append(f"- `{filename}`")
    else:
        lines.append("- None.")

    lines.extend(
        [
            "",
            "## Recommended Next Action",
            "",
        ]
    )
    if status_counts.get("different") or status_counts.get("missing_downstream"):
        lines.append(
            "- Review drift results before designing any controlled downstream write or sync mode."
        )
        lines.append("- Treat missing downstream wrappers as expected until write mode exists.")
    elif status_counts.get("missing_preview") or status_counts.get("downstream_repo_missing"):
        lines.append("- Fix missing preview or repository setup before planning write mode.")
    else:
        lines.append("- No wrapper drift found; continue with write-mode design review.")

    lines.extend(
        [
            "",
            "This report was produced by read-only downstream inspection. No downstream files were modified.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    governance_root = Path(__file__).resolve().parents[2]
    root = safe_resolve(Path(args.root))
    preview_root = safe_resolve(Path(args.preview))
    out_dir = safe_resolve(Path(args.out))
    repos = selected_repos(args.repo)

    if not root.exists() or not root.is_dir():
        print(f"fatal: root directory not found: {root}", file=sys.stderr)
        return 1
    if not preview_root.exists() or not preview_root.is_dir():
        print(f"fatal: preview directory not found: {preview_root}", file=sys.stderr)
        return 1
    try:
        ensure_output_under_governance(out_dir, governance_root)
        out_dir.mkdir(parents=True, exist_ok=True)
    except (OSError, ValueError) as exc:
        print(f"fatal: {exc}", file=sys.stderr)
        return 1

    records = [
        make_record(root, preview_root, repo, wrapper_file)
        for repo in repos
        for wrapper_file in WRAPPER_FILES
    ]
    status_counts = Counter(record["status"] for record in records)
    data = {
        "root": str(root),
        "preview": str(preview_root),
        "out": str(out_dir),
        "repos": repos,
        "total_repos_checked": len(repos),
        "status_counts": dict(status_counts),
        "records": records,
    }
    write_json(out_dir / "wrapper-drift.json", data)
    write_csv(out_dir / "wrapper-drift.csv", records)
    write_markdown(out_dir / "wrapper-drift.md", data)

    drift_count = sum(status_counts.get(status, 0) for status in DRIFT_STATUSES)
    print(
        f"drift report generated: {len(repos)} repos, {len(records)} files, "
        f"{drift_count} drift records"
    )
    print("downstream repos were inspected read-only and not modified")
    if args.fail_on_drift and drift_count:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

