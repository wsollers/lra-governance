#!/usr/bin/env python3
"""Stage 1 repository readiness checks for the extraction pipeline."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class RepoCheck:
    repo: str
    path: str
    exists: bool
    branch: str = ""
    expected_branch: str = ""
    head: str = ""
    upstream: str = ""
    ahead: int = 0
    behind: int = 0
    dirty: bool = False
    status: str = ""
    ok: bool = False
    errors: list[str] | None = None


def git(repo: Path, args: list[str], check: bool = False) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def upstream_counts(repo: Path) -> tuple[str, int, int]:
    upstream = git(repo, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"])
    if not upstream:
        return "", 0, 0
    counts = git(repo, ["rev-list", "--left-right", "--count", f"HEAD...{upstream}"])
    if not counts:
        return upstream, 0, 0
    parts = counts.split()
    if len(parts) != 2:
        return upstream, 0, 0
    return upstream, int(parts[0]), int(parts[1])


def check_repo(path: Path, expected_branch: str, require_even: bool) -> RepoCheck:
    errors: list[str] = []
    if not path.is_dir() or not (path / ".git").exists():
        return RepoCheck(
            repo=path.name,
            path=str(path),
            exists=False,
            expected_branch=expected_branch,
            ok=False,
            errors=[f"Missing git repo: {path}"],
        )

    branch = git(path, ["branch", "--show-current"])
    head = git(path, ["rev-parse", "HEAD"])
    status = git(path, ["status", "--short"])
    upstream, ahead, behind = upstream_counts(path)

    if expected_branch and branch != expected_branch:
        errors.append(f"Expected branch {expected_branch}, found {branch or '<detached>'}.")
    if status:
        errors.append("Working tree is dirty.")
    if require_even:
        if not upstream:
            errors.append("No upstream is configured.")
        elif ahead or behind:
            errors.append(f"Repository is not even with {upstream}: ahead {ahead}, behind {behind}.")

    return RepoCheck(
        repo=path.name,
        path=str(path),
        exists=True,
        branch=branch,
        expected_branch=expected_branch,
        head=head,
        upstream=upstream,
        ahead=ahead,
        behind=behind,
        dirty=bool(status),
        status=status,
        ok=not errors,
        errors=errors,
    )


def volume_repos(repos_root: Path) -> list[Path]:
    return sorted(
        path
        for path in repos_root.glob("lra-volume-*")
        if path.is_dir() and (path / ".git").exists()
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repos-root",
        type=Path,
        default=Path(__file__).resolve().parents[4],
        help="Workspace containing lra-governance, lra-volume-*, and lra-knowledge-explorer.",
    )
    parser.add_argument(
        "--governance",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="Path to lra-governance.",
    )
    parser.add_argument(
        "--knowledge-explorer",
        type=Path,
        default=None,
        help="Path to lra-knowledge-explorer. Defaults to <repos-root>/lra-knowledge-explorer.",
    )
    parser.add_argument(
        "--allow-ahead",
        action="store_true",
        help="Allow repos that are ahead of upstream. Behind repos still fail.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a text report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repos_root = args.repos_root.resolve()
    governance = args.governance.resolve()
    knowledge_explorer = (args.knowledge_explorer or repos_root / "lra-knowledge-explorer").resolve()

    checks = [
        check_repo(governance, "main", require_even=True),
        check_repo(knowledge_explorer, "main", require_even=True),
    ]
    checks.extend(check_repo(repo, "main", require_even=True) for repo in volume_repos(repos_root))

    if args.allow_ahead:
        for check in checks:
            if check.ahead and not check.behind and check.ok:
                continue
            if check.ahead and not check.behind and check.errors:
                check.errors = [
                    error
                    for error in check.errors
                    if not error.startswith("Repository is not even")
                ]
                check.ok = not check.errors

    report = {
        "stage": "prepare-repos",
        "repos_root": str(repos_root),
        "ok": all(check.ok for check in checks),
        "counts": {
            "repos": len(checks),
            "ok": sum(1 for check in checks if check.ok),
            "failed": sum(1 for check in checks if not check.ok),
        },
        "checks": [asdict(check) for check in checks],
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Stage 1 repository preflight: {'ok' if report['ok'] else 'failed'}")
        print(f"Repos checked: {report['counts']['repos']}")
        for check in checks:
            marker = "OK" if check.ok else "FAIL"
            relation = f"ahead {check.ahead}, behind {check.behind}" if check.upstream else "no upstream"
            print(f"- {marker} {check.repo} [{check.branch or '<detached>'}] {relation}")
            for error in check.errors or []:
                print(f"  - {error}")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
