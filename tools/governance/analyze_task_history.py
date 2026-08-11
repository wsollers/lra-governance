#!/usr/bin/env python3
"""Analyze task prompt history against the LRA capability router.

Input is JSONL so the corpus can come from Codex exports, hand curation, or
future app tooling. Each row should contain at least a prompt-like field:

    {"repo": "lra-volume-i", "prompt": "append the lemma ..."}

Accepted prompt fields are `prompt`, `task`, `message`, `text`, and `title`.
Accepted repo fields are `repo`, `project`, `projectName`, `project_name`, and
`repository`. If no repo is present, the analyzer searches the prompt for a
known repo name and otherwise uses `--default-repo`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


PROMPT_FIELDS = ("prompt", "task", "message", "text", "title")
REPO_FIELDS = ("repo", "project", "projectName", "project_name", "repository")


CAPABILITY_FAMILIES = {
    "build-repo": "build",
    "author-statement": "generation",
    "author-definition": "generation",
    "author-stub-chapter": "generation",
    "author-stub-section": "generation",
    "author-lean-theorem": "generation",
    "audit-semantic-topic": "semantic-artifacts",
    "calibrate-semantic-artifact": "semantic-artifacts",
    "cpp-build-task": "code-quality",
}


FAMILY_KEYWORDS = {
    "build": (
        "build",
        "compile",
        "ci",
        "workflow",
        "github action",
        "docker",
        "render",
    ),
    "validation": (
        "validate",
        "validator",
        "audit",
        "check",
        "gate",
        "schema",
        "proof layout",
    ),
    "generation": (
        "generate",
        "author",
        "write",
        "append",
        "stub",
        "scaffold",
        "definition",
        "theorem",
        "lemma",
        "proposition",
        "corollary",
    ),
    "semantic-artifacts": (
        "semantic",
        "artifact",
        "ast",
        "external review",
        "calibrate",
        "formal reading",
    ),
    "code-quality": (
        "refactor",
        "implement",
        "test",
        "pytest",
        "unittest",
        "lint",
        "bug",
        "fix",
    ),
    "repo-management": (
        "wrapper",
        "overlay",
        "agents.md",
        "governance root",
        "lra_governance_root",
        "task creation",
        "thread",
        "worktree",
    ),
    "source-profile-extraction": (
        "source profile",
        "source index",
        "pdf extractor",
        "reading categorizer",
        "bibliography",
        "ocr",
        "markdown cache",
    ),
    "governance-audit": (
        "governance audit",
        "bloat",
        "thin",
        "router",
        "capability",
        "skills",
        "yagni",
        "kiss",
        "dry",
    ),
}


@dataclass
class TaskRecord:
    prompt: str
    repo: str
    source_index: int
    expected_capability: str | None = None
    expected_family: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutedTask:
    prompt: str
    repo: str
    source_index: int
    family: str
    capability: str | None = None
    expected_family: str | None = None
    expected_capability: str | None = None
    status: str = "ok"
    error: str | None = None


@dataclass
class AnalysisReport:
    total: int
    routed: int
    unmatched: int
    family_counts: dict[str, int]
    capability_counts: dict[str, int]
    repo_counts: dict[str, int]
    expectation_failures: list[RoutedTask]
    unmatched_tasks: list[RoutedTask]
    tasks: list[RoutedTask]


def governance_root(start: Path) -> Path:
    for path in [start.resolve(), *start.resolve().parents]:
        if (path / "capabilities" / "manifest.yaml").exists():
            return path
    raise FileNotFoundError("could not find lra-governance root with capabilities/manifest.yaml")


def load_known_repos(gov_root: Path) -> list[str]:
    config = gov_root / "capabilities" / "overlays-config.yaml"
    data = yaml.safe_load(config.read_text(encoding="utf-8")) or {}
    return [entry["repo"] for entry in data.get("repos", []) if entry.get("repo")]


def first_string(data: dict[str, Any], fields: tuple[str, ...]) -> str | None:
    for field_name in fields:
        value = data.get(field_name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def infer_repo(text: str, explicit: str | None, known_repos: list[str], default_repo: str) -> str:
    if explicit:
        return explicit
    lowered = text.lower()
    matches = [repo for repo in known_repos if repo.lower() in lowered]
    if matches:
        return max(matches, key=len)
    return default_repo


def load_jsonl(path: Path, known_repos: list[str], default_repo: str, limit: int | None = None) -> list[TaskRecord]:
    records: list[TaskRecord] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if limit is not None and len(records) >= limit:
            break
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        raw = json.loads(stripped)
        if not isinstance(raw, dict):
            raise ValueError(f"{path}:{index}: expected a JSON object")
        prompt = first_string(raw, PROMPT_FIELDS)
        if not prompt:
            raise ValueError(f"{path}:{index}: missing one of prompt fields {PROMPT_FIELDS}")
        repo = infer_repo(prompt, first_string(raw, REPO_FIELDS), known_repos, default_repo)
        metadata = {key: value for key, value in raw.items() if key not in {*PROMPT_FIELDS, *REPO_FIELDS}}
        records.append(
            TaskRecord(
                prompt=prompt,
                repo=repo,
                source_index=index,
                expected_capability=raw.get("expected_capability"),
                expected_family=raw.get("expected_family"),
                metadata=metadata,
            )
        )
    return records


def import_resolver(gov_root: Path):
    capabilities_dir = gov_root / "capabilities"
    sys.path.insert(0, str(capabilities_dir))
    try:
        import resolve  # type: ignore

        return resolve
    finally:
        try:
            sys.path.remove(str(capabilities_dir))
        except ValueError:
            pass


def keyword_family(prompt: str) -> str:
    lowered = prompt.lower()
    hits: Counter[str] = Counter()
    for family, keywords in FAMILY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in lowered:
                hits[family] += len(keyword)
    if hits:
        return hits.most_common(1)[0][0]
    return "unclassified"


def route_record(record: TaskRecord, gov_root: Path, resolver: Any) -> RoutedTask:
    try:
        resolution = resolver.resolve(gov_root, record.repo, record.prompt, {})
    except (FileNotFoundError, ValueError) as exc:
        return RoutedTask(
            prompt=record.prompt,
            repo=record.repo,
            source_index=record.source_index,
            family=keyword_family(record.prompt),
            expected_family=record.expected_family,
            expected_capability=record.expected_capability,
            status="unmatched",
            error=str(exc),
        )

    capability = resolution.route_id
    return RoutedTask(
        prompt=record.prompt,
        repo=record.repo,
        source_index=record.source_index,
        family=CAPABILITY_FAMILIES.get(capability, keyword_family(record.prompt)),
        capability=capability,
        expected_family=record.expected_family,
        expected_capability=record.expected_capability,
    )


def expectation_failed(task: RoutedTask) -> bool:
    if task.expected_family and task.expected_family != task.family:
        return True
    if task.expected_capability and task.expected_capability != task.capability:
        return True
    return False


def analyze(records: list[TaskRecord], gov_root: Path) -> AnalysisReport:
    resolver = import_resolver(gov_root)
    tasks = [route_record(record, gov_root, resolver) for record in records]
    family_counts = Counter(task.family for task in tasks)
    capability_counts = Counter(task.capability for task in tasks if task.capability)
    repo_counts = Counter(task.repo for task in tasks)
    unmatched_tasks = [task for task in tasks if task.status == "unmatched"]
    expectation_failures = [task for task in tasks if expectation_failed(task)]
    return AnalysisReport(
        total=len(tasks),
        routed=len(tasks) - len(unmatched_tasks),
        unmatched=len(unmatched_tasks),
        family_counts=dict(family_counts.most_common()),
        capability_counts=dict(capability_counts.most_common()),
        repo_counts=dict(repo_counts.most_common()),
        expectation_failures=expectation_failures,
        unmatched_tasks=unmatched_tasks,
        tasks=tasks,
    )


def print_text_report(report: AnalysisReport) -> None:
    print(f"tasks: {report.total}")
    print(f"routed: {report.routed}")
    print(f"unmatched: {report.unmatched}")
    print()
    print("families:")
    for family, count in report.family_counts.items():
        print(f"  {family}: {count}")
    print()
    print("capabilities:")
    for capability, count in report.capability_counts.items():
        print(f"  {capability}: {count}")
    print()
    print("repos:")
    for repo, count in report.repo_counts.items():
        print(f"  {repo}: {count}")
    if report.expectation_failures:
        print()
        print("expectation failures:")
        for task in report.expectation_failures[:20]:
            print(
                f"  line {task.source_index}: expected "
                f"{task.expected_family or task.expected_capability}, got "
                f"{task.family}/{task.capability or '-'}"
            )
    if report.unmatched_tasks:
        print()
        print("unmatched samples:")
        for task in report.unmatched_tasks[:20]:
            print(f"  line {task.source_index} [{task.repo}] {task.family}: {task.prompt}")
            print(f"    {task.error}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSONL task prompt corpus")
    parser.add_argument("--gov-root", type=Path, default=Path("."))
    parser.add_argument("--default-repo", default="lra-governance")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--output", type=Path, help="Optional JSON report path")
    parser.add_argument(
        "--fail-on-expectation-mismatch",
        action="store_true",
        help="Exit nonzero when expected_family or expected_capability mismatches.",
    )
    parser.add_argument(
        "--fail-on-unmatched",
        action="store_true",
        help="Exit nonzero when any prompt cannot resolve to a capability.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    gov_root = governance_root(args.gov_root)
    known_repos = load_known_repos(gov_root)
    records = load_jsonl(args.input, known_repos, args.default_repo, args.limit)
    report = analyze(records, gov_root)
    report_json = json.dumps(asdict(report), indent=2, sort_keys=True)

    if args.output:
        args.output.write_text(report_json + "\n", encoding="utf-8")
    if args.format == "json":
        print(report_json)
    else:
        print_text_report(report)

    if args.fail_on_unmatched and report.unmatched_tasks:
        return 1
    if args.fail_on_expectation_mismatch and report.expectation_failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
