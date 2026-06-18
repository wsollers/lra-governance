#!/usr/bin/env python3
"""Stage 2 data generation for the governance-owned extraction pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GOVERNANCE_TOOL_ROOT = Path(__file__).resolve().parents[1]
if str(GOVERNANCE_TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(GOVERNANCE_TOOL_ROOT))

import dependency_graph  # noqa: E402


def utc_run_id() -> str:
    return "extraction-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, default=lambda item: asdict(item), indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def source_chapter_root(repo: str, file: str) -> str:
    parts = Path(file.replace("\\", "/")).parts
    if len(parts) >= 2 and parts[0].startswith("volume-"):
        return f"{repo}/{parts[0]}/{parts[1]}"
    if parts and parts[0].startswith("volume-"):
        return f"{repo}/{parts[0]}"
    return f"{repo}/<unknown>"


def chapter_manifest(universe: dependency_graph.Universe) -> dict[str, Any]:
    chapters: dict[str, dict[str, Any]] = {}
    for node in universe.nodes:
        chapter = source_chapter_root(node.repo, node.file)
        entry = chapters.setdefault(
            chapter,
            {
                "chapter": chapter,
                "repo": node.repo,
                "formal_count": 0,
                "counts_by_kind": {},
                "files": [],
                "nodes": [],
            },
        )
        entry["formal_count"] += 1
        entry["nodes"].append(
            {
                "label": node.label,
                "type": node.kind,
                "env": node.env,
                "file": node.file,
                "line": node.line,
                "display_title": node.title,
                "source_order": node.source_order,
                "body_hash": node.body_hash,
                "root_kind": node.root_kind,
            }
        )

    for entry in chapters.values():
        kind_counts = Counter(node["type"] for node in entry["nodes"])
        entry["counts_by_kind"] = dict(sorted(kind_counts.items()))
        entry["files"] = sorted({node["file"] for node in entry["nodes"]})
        entry["nodes"].sort(key=lambda node: node["source_order"])

    return {
        "source": "lra-governance/tools/governance/dependency_graph.py",
        "chapter_count": len(chapters),
        "formal_count": len(universe.nodes),
        "chapters": [chapters[key] for key in sorted(chapters)],
    }


def issue_counts(issues: list[Any]) -> dict[str, Any]:
    by_severity = Counter(getattr(issue, "severity", issue.get("severity", "")) for issue in issues)
    by_code = Counter(getattr(issue, "code", issue.get("code", "")) for issue in issues)
    return {
        "total": len(issues),
        "by_severity": dict(sorted(by_severity.items())),
        "by_code": dict(sorted(by_code.items())),
    }


def edge_counts(report: dependency_graph.EdgeReport) -> dict[str, Any]:
    return {
        "edges": len(report.edges),
        "declarations": len(report.declarations),
        "edge_status": dict(sorted(Counter(edge.status for edge in report.edges).items())),
        "declaration_shape": dict(sorted(Counter(item.get("declaration", "missing") for item in report.declarations).items())),
        "issues": issue_counts(report.issues),
    }


def volume_repos(repos_root: Path) -> list[Path]:
    return sorted(
        path
        for path in repos_root.glob("lra-volume-*")
        if path.is_dir() and (path / ".git").exists()
    )


def report_lines(summary: dict[str, Any]) -> list[str]:
    lines = [
        "# Extraction Stage 2 Report",
        "",
        f"- Run id: `{summary['run_id']}`",
        f"- Created: `{summary['created_at_utc']}`",
        f"- Repos root: `{summary['repos_root']}`",
        f"- Output root: `{summary['output_root']}`",
        "",
        "## Universe",
        "",
        f"- Repos scanned: {summary['universe']['repos']}",
        f"- Formal nodes: {summary['universe']['nodes']}",
        f"- Issues: {summary['universe']['issues']['total']}",
        "",
        "## Chapters",
        "",
        f"- Chapters with formal nodes: {summary['chapter_manifest']['chapter_count']}",
        "",
        "## Per-Repo Edges",
        "",
        "| Repo | Edges | Declarations | Issues | Legacy remarks | Missing declarations |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for repo, counts in summary["edges_by_repo"].items():
        decls = counts["declaration_shape"]
        lines.append(
            f"| `{repo}` | {counts['edges']} | {counts['declarations']} | "
            f"{counts['issues']['total']} | {decls.get('dependencies_remark', 0)} | {decls.get('missing', 0)} |"
        )
    lines += [
        "",
        "## Validation",
        "",
        f"- Validation issues: {summary['validation']['issues']['total']}",
    ]
    for severity, count in summary["validation"]["issues"]["by_severity"].items():
        lines.append(f"- `{severity}`: {count}")
    lines += [
        "",
        "## Artifacts",
        "",
    ]
    for name, path in summary["artifacts"].items():
        lines.append(f"- `{name}`: `{path}`")
    return lines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repos-root",
        type=Path,
        default=Path(__file__).resolve().parents[4],
        help="Workspace containing lra-volume-* repos.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "runs",
        help="Directory that receives ignored extraction run outputs.",
    )
    parser.add_argument(
        "--logs-root",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "logs",
        help="Directory that receives ignored extraction logs and reports.",
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "docs" / "governance" / "dependency-root-policy.yaml",
        help="Dependency root policy used by validation.",
    )
    parser.add_argument("--run-id", default="", help="Optional run id. Defaults to extraction-YYYYMMDD-HHMMSS.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_id = args.run_id or utc_run_id()
    repos_root = args.repos_root.resolve()
    output_root = (args.output_root / run_id).resolve()
    logs_root = args.logs_root.resolve()
    log_path = logs_root / f"extraction-log-{run_id.removeprefix('extraction-')}.log"
    report_path = logs_root / f"extraction-report-{run_id.removeprefix('extraction-')}.md"

    if output_root.exists():
        raise SystemExit(f"Run output already exists: {output_root}")

    log: list[str] = []
    log.append(f"run_id={run_id}")
    log.append(f"repos_root={repos_root}")
    log.append(f"output_root={output_root}")

    universe = dependency_graph.build_universe(repos_root, "lra-volume-*")
    universe_path = output_root / "universe.json"
    dependency_graph.write_json(universe_path, universe)
    dependency_graph.write_markdown(output_root / "universe.md", dependency_graph.universe_markdown(universe))
    log.append(f"universe_nodes={len(universe.nodes)}")
    log.append(f"universe_issues={len(universe.issues)}")

    manifest = chapter_manifest(universe)
    chapter_manifest_path = output_root / "chapter-manifest.json"
    write_json(chapter_manifest_path, manifest)

    policy = dependency_graph.load_policy(args.policy)
    edge_reports: list[dependency_graph.EdgeReport] = []
    validation_issues: list[dependency_graph.Issue] = []
    edges_by_repo: dict[str, Any] = {}

    for repo in volume_repos(repos_root):
        edge_report = dependency_graph.extract_edges_from_universe(repo, universe, str(universe_path))
        edge_reports.append(edge_report)
        repo_dir = output_root / "edges" / repo.name
        dependency_graph.write_json(repo_dir / "edges.json", edge_report)
        dependency_graph.write_markdown(repo_dir / "edges.md", dependency_graph.edges_markdown(edge_report))
        repo_validation = dependency_graph.validate_graph(universe, edge_report, policy)
        validation_issues.extend(repo_validation)
        write_json(repo_dir / "validation.json", {"issues": repo_validation})
        dependency_graph.write_markdown(repo_dir / "validation.md", dependency_graph.validation_markdown(repo_validation))
        edges_by_repo[repo.name] = edge_counts(edge_report)
        log.append(
            f"repo={repo.name} edges={len(edge_report.edges)} "
            f"declarations={len(edge_report.declarations)} issues={len(edge_report.issues)} "
            f"validation_issues={len(repo_validation)}"
        )

    combined_edges = [asdict(edge) for report in edge_reports for edge in report.edges]
    combined_declarations = [item for report in edge_reports for item in report.declarations]
    combined_edges_path = output_root / "combined-edges.json"
    write_json(
        combined_edges_path,
        {
            "run_id": run_id,
            "universe": str(universe_path),
            "edges": combined_edges,
            "declarations": combined_declarations,
        },
    )

    validation_path = output_root / "validation.json"
    write_json(validation_path, {"issues": validation_issues})

    summary = {
        "run_id": run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "repos_root": str(repos_root),
        "output_root": str(output_root),
        "universe": {
            "repos": len(universe.repos),
            "nodes": len(universe.nodes),
            "issues": issue_counts(universe.issues),
        },
        "chapter_manifest": {
            "chapter_count": manifest["chapter_count"],
            "formal_count": manifest["formal_count"],
        },
        "edges_by_repo": edges_by_repo,
        "combined": {
            "edges": len(combined_edges),
            "declarations": len(combined_declarations),
        },
        "validation": {"issues": issue_counts(validation_issues)},
        "artifacts": {
            "universe": str(universe_path),
            "chapter_manifest": str(chapter_manifest_path),
            "combined_edges": str(combined_edges_path),
            "validation": str(validation_path),
            "log": str(log_path),
            "report": str(report_path),
        },
    }

    summary_path = output_root / "summary.json"
    write_json(summary_path, summary)
    write_text(log_path, log)
    write_text(report_path, report_lines(summary))
    print(f"Stage 2 generated data: {output_root}")
    print(f"Formal nodes: {len(universe.nodes)}")
    print(f"Combined edges: {len(combined_edges)}")
    print(f"Validation issues: {len(validation_issues)}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

