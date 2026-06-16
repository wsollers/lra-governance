from __future__ import annotations

from pathlib import Path
from core.finding import Finding, finding

import dependency_graph


def validate(volume_root: Path) -> list[Finding]:
    repo_root = volume_root.parent
    repos_root = repo_root.parent
    policy = dependency_graph.load_policy(_policy_path(repo_root))
    findings: list[Finding] = []
    universe = dependency_graph.build_universe(repos_root, "lra-volume-*")
    edges = dependency_graph.extract_edges_from_universe(repo_root, universe, "in-memory")
    issues = dependency_graph.validate_graph(universe, edges, policy)
    for issue in issues:
        path = repo_root / issue.file if issue.file else repo_root
        findings.append(
            finding(
                issue.code,
                issue.message,
                path,
                volume_root,
                issue.line,
                "warning",
            )
        )
    return findings


def _policy_path(repo_root: Path) -> Path | None:
    local = repo_root / "docs" / "governance" / "dependency-root-policy.yaml"
    if local.exists():
        return local
    governance = repo_root.parent / "lra-governance" / "docs" / "governance" / "dependency-root-policy.yaml"
    if governance.exists():
        return governance
    return None
