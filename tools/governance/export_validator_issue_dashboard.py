#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VOLUME_REPOS = [
    "lra-volume-i",
    "lra-volume-ii",
    "lra-volume-iii",
    "lra-volume-iv",
    "lra-volume-v",
    "lra-volume-vi",
    "lra-volume-vii",
    "lra-volume-viii",
]


def gh_api(endpoint: str) -> Any:
    completed = subprocess.run(["gh", "api", endpoint], text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"gh api failed for {endpoint}: {completed.stderr.strip()}")
    return json.loads(completed.stdout) if completed.stdout.strip() else None


def metadata_from_body(body: str) -> dict[str, Any]:
    for line in (body or "").splitlines():
        match = re.fullmatch(r"\s*<!--\s*lra-validator-metadata:\s*(\{.*\})\s*-->\s*", line)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                return {}
    return {}


def labels_to_names(issue: dict[str, Any]) -> set[str]:
    return {label["name"] for label in issue.get("labels", []) if isinstance(label, dict) and "name" in label}


def fallback_metadata(repo: str, issue: dict[str, Any]) -> dict[str, Any]:
    labels = labels_to_names(issue)
    data: dict[str, Any] = {"repo": repo}
    for label in labels:
        if label.startswith("severity:"):
            data["severity"] = label.split(":", 1)[1]
        elif label.startswith("validator:"):
            data["code"] = label.split(":", 1)[1]
        elif label.startswith("volume:"):
            data["volume"] = label.split(":", 1)[1]
    data["proof_related"] = "lra-proof" in labels
    return data


def normalize_issue(repo: str, issue: dict[str, Any]) -> dict[str, Any]:
    metadata = {**fallback_metadata(repo, issue), **metadata_from_body(issue.get("body") or "")}
    return {
        "repo": repo,
        "number": issue.get("number"),
        "title": issue.get("title"),
        "state": issue.get("state"),
        "url": issue.get("html_url"),
        "created_at": issue.get("created_at"),
        "updated_at": issue.get("updated_at"),
        "fingerprint": metadata.get("fingerprint"),
        "volume": metadata.get("volume", "unknown"),
        "severity": metadata.get("severity", "unknown"),
        "code": metadata.get("code", "unknown"),
        "path": metadata.get("path"),
        "line": metadata.get("line"),
        "message": metadata.get("message"),
        "proof_related": bool(metadata.get("proof_related")),
    }


def list_validator_issues(repo: str, state: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    page = 1
    while True:
        batch = gh_api(f"/repos/{repo}/issues?state={state}&labels=lra-validator&per_page=100&page={page}")
        if not batch:
            break
        issues.extend(item for item in batch if "pull_request" not in item)
        page += 1
    return issues


def aggregate(issues: list[dict[str, Any]]) -> dict[str, Any]:
    by_repo = Counter(issue["repo"] for issue in issues)
    by_volume = Counter(issue["volume"] for issue in issues)
    by_severity = Counter(issue["severity"] for issue in issues)
    by_code = Counter(issue["code"] for issue in issues)
    return {
        "issue_count": len(issues),
        "proof_issue_count": sum(1 for issue in issues if issue["proof_related"]),
        "by_repo": dict(sorted(by_repo.items())),
        "by_volume": dict(sorted(by_volume.items())),
        "by_severity": dict(sorted(by_severity.items())),
        "by_code": dict(sorted(by_code.items())),
    }


def build_dashboard(repos: list[str], state: str) -> dict[str, Any]:
    issues = []
    for repo in repos:
        issues.extend(normalize_issue(repo, issue) for issue in list_validator_issues(repo, state))
    issues.sort(key=lambda issue: (issue["repo"], issue["severity"], issue["code"], str(issue.get("path") or ""), issue["number"] or 0))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "state": state,
        "repos": repos,
        "totals": aggregate(issues),
        "issues": issues,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export LRA validator GitHub issues as dashboard JSON.")
    parser.add_argument("--owner", default=os.environ.get("GITHUB_REPOSITORY_OWNER") or "wsollers")
    parser.add_argument("--repo", dest="repos", action="append", help="Full owner/repo or repo name. May be repeated.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--state", choices=["open", "closed", "all"], default="open")
    args = parser.parse_args(argv)
    repos = args.repos or [f"{args.owner}/{name}" for name in VOLUME_REPOS]
    repos = [repo if "/" in repo else f"{args.owner}/{repo}" for repo in repos]
    dashboard = build_dashboard(repos, args.state)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(dashboard, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {args.output} with {dashboard['totals']['issue_count']} issue(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
