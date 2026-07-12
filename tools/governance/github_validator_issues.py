#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FINGERPRINT_PREFIX = "lra-validator-fingerprint:"
METADATA_PREFIX = "lra-validator-metadata:"
BASE_LABELS = ["lra-validator"]
PROOF_CODES = {
    "missing_matching_proofs_topic",
    "proof_file_missing_proof_for",
    "proof_file_missing_restatement",
    "proof_file_missing_return",
    "proof_file_missing_standard_proof",
    "proof_file_missing_learning_proof",
    "proof_targets_missing",
}


@dataclass(frozen=True)
class ValidatorIssue:
    fingerprint: str
    title: str
    body: str
    labels: list[str]
    metadata: dict[str, Any]


def volume_from_report(report: dict[str, Any], repo: str) -> str:
    root = Path(str(report.get("volume_root", "")))
    for part in reversed(root.parts):
        match = re.fullmatch(r"volume-([ivxlcdm]+)", part, re.IGNORECASE)
        if match:
            return match.group(1).lower()
    match = re.search(r"lra-volume-([ivxlcdm]+)", repo, re.IGNORECASE)
    return match.group(1).lower() if match else "unknown"


def is_proof_related(record: dict[str, Any]) -> bool:
    path = str(record.get("path", "")).replace("\\", "/")
    code = str(record.get("code", ""))
    return "/proofs/" in f"/{path}" or code.startswith("proof_") or code in PROOF_CODES


def issue_fingerprint(repo: str, volume: str, record: dict[str, Any]) -> str:
    stable = {
        "repo": repo,
        "volume": volume,
        "path": str(record.get("path", "")),
        "line": record.get("line"),
        "code": str(record.get("code", "")),
    }
    payload = json.dumps(stable, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def github_label(value: str) -> str:
    label = re.sub(r"[^A-Za-z0-9_.:-]+", "-", value.strip()).strip("-")
    return label[:50] or "unknown"


def build_issue(report: dict[str, Any], repo: str, record: dict[str, Any], run_url: str | None, commit: str | None) -> ValidatorIssue:
    volume = volume_from_report(report, repo)
    severity = str(record.get("severity", "unknown"))
    code = str(record.get("code", "unknown"))
    path = str(record.get("path", ""))
    line = record.get("line")
    message = str(record.get("message", "")).strip()
    proof_related = is_proof_related(record)
    fingerprint = issue_fingerprint(repo, volume, record)
    location = f"{path}:{line}" if line else path
    title = f"[validator][{severity}] {code} in {location}"
    metadata = {
        "fingerprint": fingerprint,
        "repo": repo,
        "volume": volume,
        "severity": severity,
        "code": code,
        "path": path,
        "line": line,
        "message": message,
        "proof_related": proof_related,
        "run_url": run_url,
        "commit": commit,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    body_lines = [
        f"<!-- {FINGERPRINT_PREFIX} {fingerprint} -->",
        f"<!-- {METADATA_PREFIX} {json.dumps(metadata, sort_keys=True)} -->",
        "",
        "A nightly LRA governance validator run found this issue.",
        "",
        f"- Repo: `{repo}`",
        f"- Volume: `{volume}`",
        f"- Severity: `{severity}`",
        f"- Code: `{code}`",
        f"- Location: `{location}`",
        f"- Proof related: `{'yes' if proof_related else 'no'}`",
    ]
    if commit:
        body_lines.append(f"- Commit: `{commit}`")
    if run_url:
        body_lines.append(f"- Run: {run_url}")
    body_lines.extend(["", "Message:", "", message or "(no message)"])
    labels = [
        *BASE_LABELS,
        github_label(f"severity:{severity}"),
        github_label(f"validator:{code}"),
        github_label(f"volume:{volume}"),
    ]
    if proof_related:
        labels.append("lra-proof")
    return ValidatorIssue(fingerprint, title[:256], "\n".join(body_lines) + "\n", labels, metadata)


def load_issues(report_path: Path, repo: str, run_url: str | None, commit: str | None) -> list[ValidatorIssue]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    return [build_issue(report, repo, record, run_url, commit) for record in report.get("records", [])]


def extract_fingerprint(body: str) -> str | None:
    match = re.search(r"<!--\s*lra-validator-fingerprint:\s*([0-9a-f]+)\s*-->", body)
    return match.group(1) if match else None


def gh_api(repo: str, endpoint: str, method: str = "GET", payload: dict[str, Any] | None = None) -> Any:
    cmd = ["gh", "api", endpoint, "--method", method]
    if payload is not None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
            json.dump(payload, handle)
            tmp_name = handle.name
        try:
            completed = subprocess.run([*cmd, "--input", tmp_name], text=True, capture_output=True, check=False)
        finally:
            Path(tmp_name).unlink(missing_ok=True)
    else:
        completed = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"gh api failed for {repo} {endpoint}: {completed.stderr.strip()}")
    if not completed.stdout.strip():
        return None
    return json.loads(completed.stdout)


def ensure_labels(repo: str, labels: set[str]) -> None:
    colors = {
        "lra-validator": "5319e7",
        "lra-proof": "0e8a16",
    }
    for label in sorted(labels):
        payload = {"name": label, "color": colors.get(label, "ededed")}
        subprocess.run(["gh", "api", f"/repos/{repo}/labels", "--method", "POST", "-f", f"name={payload['name']}", "-f", f"color={payload['color']}"], text=True, capture_output=True, check=False)


def find_open_issue(repo: str, fingerprint: str) -> dict[str, Any] | None:
    query = f'repo:{repo} is:issue is:open "{FINGERPRINT_PREFIX} {fingerprint}" in:body'
    result = gh_api(repo, f"/search/issues?q={urllib.parse.quote(query)}")
    items = result.get("items", []) if isinstance(result, dict) else []
    return items[0] if items else None


def list_open_validator_issues(repo: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    page = 1
    while True:
        batch = gh_api(repo, f"/repos/{repo}/issues?state=open&labels=lra-validator&per_page=100&page={page}")
        if not batch:
            break
        issues.extend(item for item in batch if "pull_request" not in item)
        page += 1
    return issues


def sync_issues(repo: str, issues: list[ValidatorIssue], close_stale: bool, dry_run: bool) -> dict[str, int]:
    counts = {"created": 0, "updated": 0, "closed": 0, "unchanged": 0}
    if dry_run:
        for issue in issues:
            print(f"would sync {issue.fingerprint}: {issue.title}")
        return counts
    ensure_labels(repo, {label for issue in issues for label in issue.labels})
    current_fingerprints = {issue.fingerprint for issue in issues}
    for issue in issues:
        existing = find_open_issue(repo, issue.fingerprint)
        payload = {"title": issue.title, "body": issue.body, "labels": issue.labels}
        if existing:
            gh_api(repo, f"/repos/{repo}/issues/{existing['number']}", "PATCH", payload)
            counts["updated"] += 1
        else:
            gh_api(repo, f"/repos/{repo}/issues", "POST", payload)
            counts["created"] += 1
    if close_stale:
        for existing in list_open_validator_issues(repo):
            fingerprint = extract_fingerprint(existing.get("body") or "")
            if fingerprint and fingerprint not in current_fingerprints:
                gh_api(repo, f"/repos/{repo}/issues/{existing['number']}", "PATCH", {"state": "closed"})
                counts["closed"] += 1
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync LRA validator JSON findings into GitHub issues.")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--run-url", default=os.environ.get("RUN_URL"))
    parser.add_argument("--commit", default=os.environ.get("GITHUB_SHA"))
    parser.add_argument("--close-stale", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if not args.repo:
        print("fatal: --repo or GITHUB_REPOSITORY is required", file=sys.stderr)
        return 2
    issues = load_issues(args.report, args.repo, args.run_url, args.commit)
    counts = sync_issues(args.repo, issues, args.close_stale, args.dry_run)
    print(json.dumps({"repo": args.repo, "issues": len(issues), **counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
