#!/usr/bin/env python3
"""Plan or perform controlled generated wrapper sync to selected repos."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from collections import Counter
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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan or sync generated agent wrappers to explicitly selected repos."
    )
    parser.add_argument("--root", required=True, help="Repository family root.")
    parser.add_argument("--preview", required=True, help="Generated preview directory.")
    parser.add_argument("--out", required=True, help="Output directory for sync plan reports.")
    parser.add_argument("--repo", nargs="+", action="append", choices=repo_names(), required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Plan only; do not write files.")
    mode.add_argument("--write", action="store_true", help="Write selected generated wrappers.")
    parser.add_argument("--allow-non-main", action="store_true")
    return parser.parse_args(argv)


def selected_repos(repo_args: list[list[str]]) -> list[str]:
    repos: list[str] = []
    for group in repo_args:
        repos.extend(group)
    return repos


def safe_resolve(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def run_git(repo_path: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_path,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def repo_status(repo_path: Path) -> tuple[str, bool]:
    branch = run_git(repo_path, ["branch", "--show-current"]) or "(unknown)"
    status = run_git(repo_path, ["status", "--short"])
    return branch, bool(status)


def classify_file(
    repo_path: Path,
    preview_path: Path,
    target_path: Path,
    target_dirty: bool,
    target_branch: str,
    allow_non_main: bool,
) -> tuple[str, str]:
    if not repo_path.exists() or not repo_path.is_dir():
        return "target_repo_missing", "blocked"
    if not preview_path.exists() or not preview_path.is_file():
        return "missing_preview", "blocked"
    if target_dirty:
        return "blocked_dirty_repo", "blocked"
    if target_branch != "main" and not allow_non_main:
        return "blocked_non_main_branch", "blocked"
    if not target_path.exists():
        return "create", "create"
    if target_path.read_bytes() == preview_path.read_bytes():
        return "identical", "none"
    return "replace", "replace"


def make_records(
    root: Path,
    preview_root: Path,
    repos: list[str],
    allow_non_main: bool,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for repo in repos:
        repo_path = root / repo
        if repo_path.exists() and repo_path.is_dir():
            target_branch, target_dirty = repo_status(repo_path)
        else:
            target_branch, target_dirty = "", False
        for wrapper_file in WRAPPER_FILES:
            preview_path = preview_root / repo / wrapper_file
            target_path = repo_path / wrapper_file
            status, action = classify_file(
                repo_path,
                preview_path,
                target_path,
                target_dirty,
                target_branch,
                allow_non_main,
            )
            records.append(
                {
                    "repo": repo,
                    "file": wrapper_file,
                    "status": status,
                    "preview_path": str(preview_path),
                    "target_path": str(target_path),
                    "target_exists": target_path.exists(),
                    "target_dirty": target_dirty,
                    "target_branch": target_branch,
                    "action": action,
                }
            )
    return records


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    fields = [
        "repo",
        "file",
        "status",
        "preview_path",
        "target_path",
        "target_exists",
        "target_dirty",
        "target_branch",
        "action",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({field: record.get(field, "") for field in fields})


def write_markdown(path: Path, data: dict[str, Any]) -> None:
    records = data["records"]
    status_counts = Counter(record["status"] for record in records)
    action_counts = Counter(record["action"] for record in records)
    blocked = [record for record in records if str(record["status"]).startswith("blocked")]
    lines = [
        "# Wrapper Sync Plan",
        "",
        f"- Mode: {'write' if data['write'] else 'dry-run'}",
        f"- Repos selected: {', '.join(f'`{repo}`' for repo in data['repos'])}",
        f"- Total files considered: {len(records)}",
        f"- Downstream files written: {'yes' if data['written'] else 'no'}",
        "",
        "## Counts By Status",
        "",
    ]
    for status in [
        "create",
        "replace",
        "identical",
        "missing_preview",
        "target_repo_missing",
        "blocked_dirty_repo",
        "blocked_non_main_branch",
    ]:
        lines.append(f"- `{status}`: {status_counts.get(status, 0)}")
    lines.extend(["", "## Counts By Action", ""])
    for action, count in sorted(action_counts.items()):
        lines.append(f"- `{action}`: {count}")
    lines.extend(["", "## Blocked Conditions", ""])
    if blocked:
        for record in blocked:
            lines.append(
                f"- `{record['repo']}/{record['file']}`: {record['status']} "
                f"(branch `{record['target_branch']}`, dirty={record['target_dirty']})"
            )
    else:
        lines.append("- None.")
    lines.extend(["", "## File Plan", ""])
    for record in records:
        lines.append(
            f"- `{record['repo']}/{record['file']}`: {record['status']} -> {record['action']}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_selected_files(records: list[dict[str, Any]]) -> int:
    written = 0
    for record in records:
        if record["action"] not in {"create", "replace"}:
            continue
        preview_path = Path(record["preview_path"])
        target_path = Path(record["target_path"])
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(preview_path, target_path)
        written += 1
    return written


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    write_mode = bool(args.write)
    root = safe_resolve(Path(args.root))
    preview_root = safe_resolve(Path(args.preview))
    out_dir = safe_resolve(Path(args.out))
    governance_root = Path(__file__).resolve().parents[2]
    repos = selected_repos(args.repo)

    if not root.exists() or not root.is_dir():
        print(f"fatal: root directory not found: {root}", file=sys.stderr)
        return 1
    if not preview_root.exists() or not preview_root.is_dir():
        print(f"fatal: preview directory not found: {preview_root}", file=sys.stderr)
        return 1
    if governance_root not in out_dir.parents and out_dir != governance_root:
        print(f"fatal: output directory must be under lra-governance: {out_dir}", file=sys.stderr)
        return 1
    if write_mode and not repos:
        print("fatal: --write requires explicit --repo selection", file=sys.stderr)
        return 1

    records = make_records(root, preview_root, repos, args.allow_non_main)
    blocked = [record for record in records if record["action"] == "blocked"]
    if write_mode and blocked:
        print("fatal: write mode blocked; see wrapper-sync-plan reports", file=sys.stderr)

    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"fatal: could not create output directory: {exc}", file=sys.stderr)
        return 1

    written = 0
    if write_mode:
        if blocked:
            data = {
                "root": str(root),
                "preview": str(preview_root),
                "repos": repos,
                "write": write_mode,
                "written": False,
                "records": records,
            }
            write_json(out_dir / "wrapper-sync-plan.json", data)
            write_csv(out_dir / "wrapper-sync-plan.csv", records)
            write_markdown(out_dir / "wrapper-sync-plan.md", data)
            return 1
        written = write_selected_files(records)

    data = {
        "root": str(root),
        "preview": str(preview_root),
        "repos": repos,
        "write": write_mode,
        "written": bool(written),
        "written_count": written,
        "records": records,
    }
    write_json(out_dir / "wrapper-sync-plan.json", data)
    write_csv(out_dir / "wrapper-sync-plan.csv", records)
    write_markdown(out_dir / "wrapper-sync-plan.md", data)

    print(
        f"wrapper sync plan generated: {len(repos)} repos, {len(records)} files, "
        f"mode={'write' if write_mode else 'dry-run'}, written={written}"
    )
    if not write_mode:
        print("dry-run mode: downstream files were not modified")
    else:
        print("write mode: downstream files were copied but not staged, committed, or pushed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

