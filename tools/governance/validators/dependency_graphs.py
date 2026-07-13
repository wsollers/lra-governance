from __future__ import annotations

from pathlib import Path
from core.finding import Finding, finding

import dependency_graph


ERROR_CODES = {
    "dependency_cycle",
    "invalid_formal_label_count",
    "ambiguous_source_variant_target",
    "missing_source_variant_target",
}


def validate(volume_root: Path, files) -> list[Finding]:
    repo_root = volume_root.parent
    repos_root = repo_root.parent
    policy = dependency_graph.load_policy(_policy_path(repo_root))
    findings: list[Finding] = []
    universe = dependency_graph.build_universe(repos_root, "lra-volume-*")
    edge_reports = [
        dependency_graph.extract_edges_from_universe(repos_root / repo, universe, "in-memory")
        for repo in universe.repos
    ]
    target_edges = next((report for report in edge_reports if report.repo == repo_root.name), None)
    if target_edges is None:
        target_edges = dependency_graph.extract_edges_from_universe(repo_root, universe, "in-memory")
        edge_reports.append(target_edges)
    merged_edges = dependency_graph.merge_edge_reports(target_edges, edge_reports)
    issues = dependency_graph.validate_graph(universe, merged_edges, policy)
    for issue in issues:
        path = repo_root / issue.file if issue.file else repo_root
        severity = "error" if issue.code in ERROR_CODES else "warning"
        findings.append(
            finding(
                issue.code,
                issue.message,
                path,
                volume_root,
                issue.line,
                severity,
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
