from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools" / "governance"
sys.path.insert(0, str(TOOLS))

import analyze_task_history as history  # noqa: E402


def write_jsonl(path: Path, rows: list[dict[str, str]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def test_router_corpus_routes_common_user_tasks(tmp_path: Path) -> None:
    corpus = tmp_path / "prompts.jsonl"
    write_jsonl(
        corpus,
        [
            {
                "repo": "lra-volume-i",
                "prompt": "append the lemma for finite unions",
                "expected_family": "generation",
                "expected_capability": "author-statement",
            },
            {
                "repo": "lra-volume-ii",
                "prompt": "generate the definition of convergence",
                "expected_family": "generation",
                "expected_capability": "author-definition",
            },
            {
                "repo": "lra-governance",
                "prompt": "validate repo",
                "expected_family": "build",
                "expected_capability": "build-repo",
            },
            {
                "repo": "lra-lean",
                "prompt": "formalize this theorem in Lean",
                "expected_family": "generation",
                "expected_capability": "author-lean-theorem",
            },
            {
                "repo": "lra-source-profiles",
                "prompt": "check repository source index validation",
                "expected_family": "build",
                "expected_capability": "build-repo",
            },
        ],
    )

    known_repos = history.load_known_repos(ROOT)
    records = history.load_jsonl(corpus, known_repos, "lra-governance")
    report = history.analyze(records, ROOT)

    assert report.total == 5
    assert report.unmatched == 0
    assert not report.expectation_failures
    assert report.family_counts["generation"] == 3
    assert report.capability_counts["build-repo"] == 2


def test_router_corpus_keeps_unmatched_prompts_for_bucket_design(tmp_path: Path) -> None:
    corpus = tmp_path / "prompts.jsonl"
    write_jsonl(
        corpus,
        [
            {
                "repo": "lra-governance",
                "prompt": "slim the governance router into task-family packs",
                "expected_family": "governance-audit",
            }
        ],
    )

    records = history.load_jsonl(corpus, history.load_known_repos(ROOT), "lra-governance")
    report = history.analyze(records, ROOT)

    assert report.total == 1
    assert report.unmatched == 1
    assert report.unmatched_tasks[0].family == "governance-audit"
    assert not report.expectation_failures


def test_repo_can_be_inferred_from_prompt_text(tmp_path: Path) -> None:
    corpus = tmp_path / "prompts.jsonl"
    write_jsonl(
        corpus,
        [
            {
                "prompt": "for lra-numerical-analysis implement the next solver task",
                "expected_family": "code-quality",
                "expected_capability": "cpp-build-task",
            }
        ],
    )

    records = history.load_jsonl(corpus, history.load_known_repos(ROOT), "lra-governance")
    report = history.analyze(records, ROOT)

    assert records[0].repo == "lra-numerical-analysis"
    assert report.unmatched == 0
    assert report.capability_counts["cpp-build-task"] == 1
