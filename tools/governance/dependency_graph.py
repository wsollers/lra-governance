#!/usr/bin/env python3
"""Extract and validate LRA formal dependency graphs.

This is intentionally read-only. It builds a global formal-artifact universe
across volume repos, extracts immediate dependency edges for a target cleanup
scope, and validates graph mechanics against a root policy.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from core.file_inventory import files_to_validate
from core.volume import resolve_volume


FORMAL_ENVS = {
    "definition": "def",
    "axiom": "ax",
    "theorem": "thm",
    "lemma": "lem",
    "proposition": "prop",
    "corollary": "cor",
}
FORMAL_PREFIXES = set(FORMAL_ENVS.values())
THEOREM_LIKE = {"thm", "lem", "prop", "cor"}
ROOTABLE_KINDS = {"ax", "def"}

BEGIN_FORMAL_RE = re.compile(
    r"\\begin\{(?P<env>definition|axiom|theorem|lemma|proposition|corollary)\}"
    r"(?:\[(?P<title>[^\]]*)\])?",
    re.IGNORECASE,
)
LABEL_RE = re.compile(r"\\label\{(?P<label>[a-z]+:[^{}]+)\}")
HYPERREF_RE = re.compile(r"\\hyperref\[(?P<label>[^\]]+)\](?:\{(?P<text>[^{}]*)\})?")
DEPENDENCY_ITEM_RE = re.compile(r"^[ \t]*\\item\s+(?P<text>[^\n]+)$", re.MULTILINE)
PROOF_FOR_RE = re.compile(r"\\LRAProofFor\{(?P<label>(?:thm|lem|prop|cor):[^{}]+)\}", re.IGNORECASE)
DEPENDENCIES_ENV_RE = re.compile(
    r"\\begin\{dependencies\}(?P<body>[\s\S]*?)\\end\{dependencies\}",
    re.IGNORECASE,
)
DEPENDENCIES_REMARK_RE = re.compile(
    r"\\begin\{remark\*\}\[Dependencies\](?P<body>[\s\S]*?)\\end\{remark\*\}",
    re.IGNORECASE,
)
NO_LOCAL_RE = re.compile(r"\\NoLocalDependencies\b")
DEFINITIONAL_ROOT_RE = re.compile(r"\\DefinitionalRoot\b")
SECTION_RE = re.compile(r"\\(?:chapter|section|subsection|subsubsection)\*?\{")
COMMENT_RE = re.compile(r"(?<!\\)%.*$")


@dataclass
class Node:
    id: str
    label: str
    kind: str
    env: str
    title: str
    repo: str
    file: str
    line: int
    source_order: int
    body_hash: str
    root_kind: str = ""


@dataclass
class Edge:
    source: str
    target: str
    source_id: str | None
    target_id: str | None
    display: str
    repo: str
    file: str
    line: int
    block_kind: str
    status: str = "ok"
    kind: str = "depends_on"


@dataclass
class Issue:
    severity: str
    code: str
    message: str
    repo: str = ""
    file: str = ""
    line: int = 1
    label: str = ""
    target: str = ""


@dataclass
class Universe:
    repos_root: str
    repos: list[str]
    nodes: list[Node]
    issues: list[Issue] = field(default_factory=list)


@dataclass
class EdgeReport:
    root: str
    repo: str
    universe: str
    edges: list[Edge]
    declarations: list[dict[str, Any]]
    issues: list[Issue] = field(default_factory=list)


def strip_comments(text: str) -> str:
    return "\n".join(COMMENT_RE.sub("", line) for line in text.splitlines())


def line_at(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def stable_hash(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def active_tex_files(repo_root: Path) -> list[Path]:
    volume_root = resolve_volume(repo_root).root
    return files_to_validate(volume_root, only_reachable=True)


def formal_blocks(text: str) -> list[tuple[re.Match[str], int]]:
    blocks: list[tuple[re.Match[str], int]] = []
    for match in BEGIN_FORMAL_RE.finditer(text):
        env = match.group("env")
        end_re = re.compile(rf"\\end\{{{re.escape(env)}\}}", re.IGNORECASE)
        end = end_re.search(text, match.end())
        if end:
            blocks.append((match, end.end()))
    return blocks


def extract_nodes(repo_root: Path, repo: str, start_order: int = 0) -> tuple[list[Node], list[Issue]]:
    nodes: list[Node] = []
    issues: list[Issue] = []
    order = start_order
    for path in active_tex_files(repo_root):
        raw = path.read_text(encoding="utf-8", errors="replace")
        text = strip_comments(raw)
        for begin, end_pos in formal_blocks(text):
            env = begin.group("env").lower()
            kind = FORMAL_ENVS[env]
            block_text = text[begin.start() : end_pos]
            labels = LABEL_RE.findall(block_text)
            line = line_at(text, begin.start())
            if not labels:
                issues.append(Issue("error", "missing_formal_label", f"{env} has no label.", repo, rel(path, repo_root), line))
                continue
            formal_labels = [label for label in labels if label.split(":", 1)[0] in FORMAL_PREFIXES]
            if len(formal_labels) != 1:
                issues.append(
                    Issue(
                        "error",
                        "invalid_formal_label_count",
                        f"{env} should have exactly one formal label; found {formal_labels}.",
                        repo,
                        rel(path, repo_root),
                        line,
                    )
                )
                continue
            label = formal_labels[0]
            prefix = label.split(":", 1)[0]
            if prefix != kind:
                issues.append(
                    Issue(
                        "error",
                        "label_kind_mismatch",
                        f"{env} label {label} should use prefix {kind}:.",
                        repo,
                        rel(path, repo_root),
                        line,
                        label,
                    )
                )
            order += 1
            nodes.append(
                Node(
                    id=f"{repo}:{label}",
                    label=label,
                    kind=kind,
                    env=env,
                    title=(begin.group("title") or "").strip(),
                    repo=repo,
                    file=rel(path, repo_root),
                    line=line,
                    source_order=order,
                    body_hash=stable_hash(block_text),
                    root_kind=root_kind_after_block(text, end_pos),
                )
            )
    return nodes, issues


def volume_repos(repos_root: Path, repo_filter: str) -> list[Path]:
    return sorted(path for path in repos_root.iterdir() if path.is_dir() and path.match(repo_filter))


def build_universe(repos_root: Path, repo_filter: str) -> Universe:
    nodes: list[Node] = []
    issues: list[Issue] = []
    repos: list[str] = []
    order = 0
    for repo_root in volume_repos(repos_root, repo_filter):
        repos.append(repo_root.name)
        repo_nodes, repo_issues = extract_nodes(repo_root, repo_root.name, order)
        if repo_nodes:
            order = max(node.source_order for node in repo_nodes)
        nodes.extend(repo_nodes)
        issues.extend(repo_issues)

    by_label: dict[str, list[Node]] = defaultdict(list)
    for node in nodes:
        by_label[node.label].append(node)
    for label, matches in sorted(by_label.items()):
        if len(matches) > 1:
            issues.append(
                Issue(
                    "error",
                    "duplicate_global_label",
                    f"Label {label} appears {len(matches)} times globally.",
                    label=label,
                )
            )
    return Universe(str(repos_root), repos, nodes, issues)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, default=lambda obj: asdict(obj), indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_universe(path: Path) -> Universe:
    data = json.loads(path.read_text(encoding="utf-8"))
    return Universe(
        repos_root=data["repos_root"],
        repos=data["repos"],
        nodes=[Node(**item) for item in data["nodes"]],
        issues=[Issue(**item) for item in data.get("issues", [])],
    )


def label_index(universe: Universe) -> dict[str, list[Node]]:
    by_label: dict[str, list[Node]] = defaultdict(list)
    for node in universe.nodes:
        by_label[node.label].append(node)
    return by_label


def next_boundary(text: str, start: int) -> int:
    formal = BEGIN_FORMAL_RE.search(text, start)
    section = SECTION_RE.search(text, start)
    candidates = [m.start() for m in (formal, section) if m]
    return min(candidates) if candidates else len(text)


def root_kind_after_block(text: str, end_pos: int) -> str:
    window = text[end_pos:next_boundary(text, end_pos)]
    if DEFINITIONAL_ROOT_RE.search(window):
        return "definitional"
    return ""


def dependency_blocks(window: str) -> list[tuple[str, str, int]]:
    blocks: list[tuple[str, str, int]] = []
    for match in DEPENDENCIES_ENV_RE.finditer(window):
        blocks.append(("dependencies_env", match.group("body"), match.start()))
    for match in DEPENDENCIES_REMARK_RE.finditer(window):
        blocks.append(("dependencies_remark", match.group("body"), match.start()))
    for match in NO_LOCAL_RE.finditer(window):
        blocks.append(("no_local", "", match.start()))
    for match in DEFINITIONAL_ROOT_RE.finditer(window):
        blocks.append(("definitional_root", "", match.start()))
    return sorted(blocks, key=lambda item: item[2])


def append_dependency_edges(
    *,
    edges: list[Edge],
    issues: list[Issue],
    body: str,
    text: str,
    root: Path,
    path: Path,
    repo: str,
    source: str,
    source_id: str | None,
    source_line: int,
    block_kind: str,
    block_line: int,
    block_start: int,
    by_label: dict[str, list[Node]],
    edge_kind: str,
) -> None:
    hyperrefs = list(HYPERREF_RE.finditer(body))
    if not hyperrefs and "TODO" not in body:
        issues.append(Issue("error", "dependencies_without_hyperref", f"{source} dependency block has no hyperref targets.", repo, rel(path, root), block_line, source))
    for item in DEPENDENCY_ITEM_RE.finditer(body):
        item_text = item.group("text").strip()
        if "TODO" in item_text or HYPERREF_RE.search(item_text):
            continue
        item_line = line_at(text, block_start + item.start())
        issues.append(
            Issue(
                "error",
                "dependency_item_without_hyperref",
                f"{source} dependency item lacks a hyperref target: {item_text}",
                repo,
                rel(path, root),
                item_line,
                source,
            )
        )
    for ref in hyperrefs:
        target = ref.group("label").strip()
        display = (ref.group("text") or "").strip()
        target_matches = by_label.get(target, [])
        status = "ok"
        target_id = None
        if target.startswith("prf:"):
            status = "invalid_proof_target"
            issues.append(Issue("error", "dependency_targets_proof", f"{source} targets proof label {target}.", repo, rel(path, root), block_line, source, target))
        elif ":" not in target or target.split(":", 1)[0] not in FORMAL_PREFIXES:
            status = "invalid_target_prefix"
            issues.append(Issue("error", "invalid_dependency_target_prefix", f"{source} targets non-formal label {target}.", repo, rel(path, root), block_line, source, target))
        elif len(target_matches) == 0:
            status = "missing_target"
            issues.append(Issue("error", "missing_dependency_target", f"{source} targets unknown label {target}.", repo, rel(path, root), block_line, source, target))
        elif len(target_matches) > 1:
            status = "ambiguous_target"
            issues.append(Issue("error", "ambiguous_dependency_target", f"{source} target {target} has multiple global matches.", repo, rel(path, root), block_line, source, target))
        else:
            target_id = target_matches[0].id
        edges.append(
            Edge(
                source=source,
                target=target,
                source_id=source_id,
                target_id=target_id,
                display=display,
                repo=repo,
                file=rel(path, root),
                line=block_line or source_line,
                block_kind=block_kind,
                status=status,
                kind=edge_kind,
            )
        )


def extract_edges_from_universe(root: Path, universe: Universe, universe_ref: str = "") -> EdgeReport:
    by_label = label_index(universe)
    repo = root.name
    issues: list[Issue] = []
    edges: list[Edge] = []
    declarations: list[dict[str, Any]] = []

    for path in active_tex_files(root):
        raw = path.read_text(encoding="utf-8", errors="replace")
        text = strip_comments(raw)
        blocks = formal_blocks(text)
        for begin, end_pos in blocks:
            block_text = text[begin.start() : end_pos]
            formal_labels = [
                label for label in LABEL_RE.findall(block_text)
                if label.split(":", 1)[0] in FORMAL_PREFIXES
            ]
            if len(formal_labels) != 1:
                continue
            source = formal_labels[0]
            source_matches = by_label.get(source, [])
            source_id = source_matches[0].id if len(source_matches) == 1 else None
            line = line_at(text, begin.start())
            window_start = end_pos
            window_end = next_boundary(text, window_start)
            window = text[window_start:window_end]
            dep_blocks = dependency_blocks(window)
            declaration = {
                "source": source,
                "source_id": source_id,
                "repo": repo,
                "file": rel(path, root),
                "line": line,
                "dependency_block_count": len(dep_blocks),
                "declaration": "missing",
            }
            if not dep_blocks:
                issues.append(Issue("warning", "missing_dependency_declaration", f"{source} has no dependency declaration.", repo, rel(path, root), line, source))
                declarations.append(declaration)
                continue
            if len(dep_blocks) > 1:
                issues.append(Issue("warning", "multiple_dependency_declarations", f"{source} has multiple dependency declarations.", repo, rel(path, root), line, source))
            block_kind, body, block_offset = dep_blocks[-1]
            declaration["declaration"] = block_kind
            declaration["dependency_line"] = line_at(text, window_start + block_offset)
            if block_kind == "dependencies_remark":
                issues.append(Issue("warning", "legacy_dependency_remark", f"{source} uses remark*[Dependencies] instead of dependencies environment.", repo, rel(path, root), int(declaration["dependency_line"]), source))
            if block_kind in {"no_local", "definitional_root"}:
                declarations.append(declaration)
                continue
            append_dependency_edges(
                edges=edges,
                issues=issues,
                body=body,
                text=text,
                root=root,
                path=path,
                repo=repo,
                source=source,
                source_id=source_id,
                source_line=line,
                block_kind=block_kind,
                block_line=int(declaration["dependency_line"]),
                block_start=window_start + block_offset,
                by_label=by_label,
                edge_kind="depends_on",
            )
            declarations.append(declaration)

        proof_fors = list(PROOF_FOR_RE.finditer(text))
        if len(proof_fors) > 1:
            issues.append(Issue("warning", "multiple_proof_for_declarations", f"{rel(path, root)} has multiple LRAProofFor declarations.", repo, rel(path, root), line_at(text, proof_fors[1].start())))
        for proof_for in proof_fors:
            source = proof_for.group("label").strip()
            source_matches = by_label.get(source, [])
            source_id = source_matches[0].id if len(source_matches) == 1 else None
            line = line_at(text, proof_for.start())
            if len(source_matches) == 0:
                issues.append(Issue("error", "missing_proof_target", f"Proof targets unknown formal label {source}.", repo, rel(path, root), line, source))
            elif len(source_matches) > 1:
                issues.append(Issue("error", "ambiguous_proof_target", f"Proof target {source} has multiple global matches.", repo, rel(path, root), line, source))

            dep_blocks = [block for block in dependency_blocks(text[proof_for.end():]) if block[0] in {"dependencies_env", "dependencies_remark", "no_local"}]
            declaration = {
                "source": source,
                "source_id": source_id,
                "repo": repo,
                "file": rel(path, root),
                "line": line,
                "dependency_scope": "proof",
                "dependency_block_count": len(dep_blocks),
                "declaration": "missing",
            }
            if not dep_blocks:
                declarations.append(declaration)
                continue
            if len(dep_blocks) > 1:
                issues.append(Issue("warning", "multiple_proof_dependency_declarations", f"{source} proof has multiple dependency declarations.", repo, rel(path, root), line, source))
            block_kind, body, block_offset = dep_blocks[-1]
            declaration["declaration"] = f"proof_{block_kind}"
            declaration["dependency_line"] = line_at(text, proof_for.end() + block_offset)
            if block_kind == "dependencies_remark":
                issues.append(Issue("warning", "legacy_proof_dependency_remark", f"{source} proof uses remark*[Dependencies] instead of dependencies environment.", repo, rel(path, root), int(declaration["dependency_line"]), source))
            if block_kind == "no_local":
                declarations.append(declaration)
                continue
            append_dependency_edges(
                edges=edges,
                issues=issues,
                body=body,
                text=text,
                root=root,
                path=path,
                repo=repo,
                source=source,
                source_id=source_id,
                source_line=line,
                block_kind=f"proof_{block_kind}",
                block_line=int(declaration["dependency_line"]),
                block_start=proof_for.end() + block_offset,
                by_label=by_label,
                edge_kind="proof_depends_on",
            )
            declarations.append(declaration)

    return EdgeReport(str(root), repo, universe_ref, edges, declarations, issues)


def extract_edges(root: Path, universe_path: Path) -> EdgeReport:
    universe = load_universe(universe_path)
    return extract_edges_from_universe(root, universe, str(universe_path))


def load_policy(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {"primitive_definitions": [], "external_assumptions": []}
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_edges(path: Path) -> EdgeReport:
    data = json.loads(path.read_text(encoding="utf-8"))
    return EdgeReport(
        root=data["root"],
        repo=data["repo"],
        universe=data["universe"],
        edges=[Edge(**item) for item in data["edges"]],
        declarations=data.get("declarations", []),
        issues=[Issue(**item) for item in data.get("issues", [])],
    )


def allowed_root(node: Node, policy: dict[str, Any]) -> bool:
    if node.kind == "ax":
        return True
    if node.root_kind == "definitional":
        return True
    primitives = set(policy.get("primitive_definitions") or [])
    if node.label in primitives or node.id in primitives:
        return True
    return False


def definitional_root_ids(edge_report: EdgeReport) -> set[str]:
    return {
        str(item.get("source_id"))
        for item in edge_report.declarations
        if item.get("source_id") and item.get("declaration") == "definitional_root"
    }


def excluded_path_patterns(policy: dict[str, Any]) -> list[str]:
    return [str(pattern).replace("\\", "/") for pattern in policy.get("excluded_paths") or []]


def is_excluded_path(repo: str, file: str, policy: dict[str, Any]) -> bool:
    path = f"{repo}/{file}".replace("\\", "/")
    repo_file = file.replace("\\", "/")
    return any(fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(repo_file, pattern) for pattern in excluded_path_patterns(policy))


def issue_in_excluded_path(issue: Issue, policy: dict[str, Any]) -> bool:
    return bool(issue.repo and issue.file and is_excluded_path(issue.repo, issue.file, policy))


def validate_graph(universe: Universe, edge_report: EdgeReport, policy: dict[str, Any]) -> list[Issue]:
    issues = [
        issue for issue in list(universe.issues) + list(edge_report.issues)
        if not issue_in_excluded_path(issue, policy)
    ]
    node_by_id = {node.id: node for node in universe.nodes}
    ids_in_scope = {
        node.id for node in universe.nodes
        if node.repo == edge_report.repo and not is_excluded_path(node.repo, node.file, policy)
    }

    adjacency: dict[str, list[str]] = defaultdict(list)
    indegree: dict[str, int] = defaultdict(int)
    for edge in edge_report.edges:
        if edge.kind != "depends_on":
            continue
        if is_excluded_path(edge.repo, edge.file, policy):
            continue
        if edge.status != "ok" or not edge.source_id or not edge.target_id:
            continue
        adjacency[edge.source_id].append(edge.target_id)
        indegree.setdefault(edge.source_id, indegree.get(edge.source_id, 0))
        indegree[edge.target_id] += 1

    graph_nodes = set(adjacency)
    for targets in adjacency.values():
        graph_nodes.update(targets)

    queue = deque(sorted(node_id for node_id in graph_nodes if indegree.get(node_id, 0) == 0))
    seen: list[str] = []
    while queue:
        node_id = queue.popleft()
        seen.append(node_id)
        for target in adjacency.get(node_id, []):
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if len(seen) != len(graph_nodes):
        issues.append(Issue("error", "dependency_cycle", "Dependency graph contains at least one cycle in extracted edges."))

    missing_decls = {
        item.get("source_id")
        for item in edge_report.declarations
        if item.get("declaration") == "missing" and item.get("dependency_scope", "statement") != "proof"
    }
    definitional_roots = definitional_root_ids(edge_report)
    for node in universe.nodes:
        if node.id not in ids_in_scope or node.kind not in THEOREM_LIKE:
            continue
        if node.id in missing_decls:
            continue
        bad_leaf = first_bad_leaf(node.id, adjacency, node_by_id, policy, definitional_roots)
        if bad_leaf:
            leaf = node_by_id[bad_leaf]
            issues.append(
                Issue(
                    "warning",
                    "closure_leaf_not_allowed_root",
                    f"{node.label} dependency closure reaches non-root leaf {leaf.label}.",
                    leaf.repo,
                    leaf.file,
                    leaf.line,
                    node.label,
                    leaf.label,
                )
            )

    return issues


def first_bad_leaf(start: str, adjacency: dict[str, list[str]], node_by_id: dict[str, Node], policy: dict[str, Any], definitional_roots: set[str] | None = None) -> str | None:
    definitional_roots = definitional_roots or set()
    stack = [start]
    visited: set[str] = set()
    while stack:
        node_id = stack.pop()
        if node_id in visited:
            continue
        visited.add(node_id)
        targets = adjacency.get(node_id, [])
        if not targets:
            node = node_by_id.get(node_id)
            if node and node_id not in definitional_roots and not allowed_root(node, policy):
                return node_id
        stack.extend(targets)
    return None


def universe_markdown(universe: Universe) -> list[str]:
    by_repo: dict[str, list[Node]] = defaultdict(list)
    for node in universe.nodes:
        by_repo[node.repo].append(node)
    lines = [
        "# Formal Universe",
        "",
        f"- Repos root: `{universe.repos_root}`",
        f"- Repos scanned: {len(universe.repos)}",
        f"- Formal nodes: {len(universe.nodes)}",
        f"- Issues: {len(universe.issues)}",
        "",
        "## Counts",
        "",
        "| Repo | def | ax | thm | lem | prop | cor | total |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for repo, nodes in sorted(by_repo.items()):
        counts = {kind: sum(1 for node in nodes if node.kind == kind) for kind in ["def", "ax", "thm", "lem", "prop", "cor"]}
        lines.append(f"| `{repo}` | {counts['def']} | {counts['ax']} | {counts['thm']} | {counts['lem']} | {counts['prop']} | {counts['cor']} | {len(nodes)} |")
    if universe.issues:
        lines += ["", "## Issues", ""]
        for issue in universe.issues[:500]:
            loc = f"{issue.repo}/{issue.file}:{issue.line}" if issue.file else issue.repo
            lines.append(f"- **{issue.severity}** `{issue.code}` {loc} {issue.message}")
    return lines


def edges_markdown(report: EdgeReport) -> list[str]:
    counts = defaultdict(int)
    kind_counts = defaultdict(int)
    for edge in report.edges:
        counts[edge.status] += 1
        kind_counts[edge.kind] += 1
    decl_counts = defaultdict(int)
    for decl in report.declarations:
        decl_counts[decl.get("declaration", "missing")] += 1
    lines = [
        "# Dependency Edge Report",
        "",
        f"- Root: `{report.root}`",
        f"- Repo: `{report.repo}`",
        f"- Universe: `{report.universe}`",
        f"- Declarations: {len(report.declarations)}",
        f"- Edges: {len(report.edges)}",
        f"- Issues: {len(report.issues)}",
        "",
        "## Declaration Counts",
        "",
    ]
    for name, count in sorted(decl_counts.items()):
        lines.append(f"- `{name}`: {count}")
    lines += ["", "## Edge Status Counts", ""]
    for name, count in sorted(counts.items()):
        lines.append(f"- `{name}`: {count}")
    lines += ["", "## Edge Kind Counts", ""]
    for name, count in sorted(kind_counts.items()):
        lines.append(f"- `{name}`: {count}")
    if report.issues:
        lines += ["", "## Issues", ""]
        for issue in report.issues[:500]:
            loc = f"{issue.repo}/{issue.file}:{issue.line}" if issue.file else issue.repo
            target = f" target=`{issue.target}`" if issue.target else ""
            label = f" label=`{issue.label}`" if issue.label else ""
            lines.append(f"- **{issue.severity}** `{issue.code}` {loc}{label}{target}: {issue.message}")
    return lines


def validation_markdown(issues: list[Issue]) -> list[str]:
    by_code = defaultdict(int)
    by_severity = defaultdict(int)
    for issue in issues:
        by_code[issue.code] += 1
        by_severity[issue.severity] += 1
    lines = [
        "# Dependency Graph Validation",
        "",
        f"- Issues: {len(issues)}",
        f"- Errors: {by_severity['error']}",
        f"- Warnings: {by_severity['warning']}",
        "",
        "## Issue Counts",
        "",
    ]
    for code, count in sorted(by_code.items()):
        lines.append(f"- `{code}`: {count}")
    if issues:
        lines += ["", "## Issues", ""]
        for issue in issues[:800]:
            loc = f"{issue.repo}/{issue.file}:{issue.line}" if issue.file else issue.repo
            target = f" target=`{issue.target}`" if issue.target else ""
            label = f" label=`{issue.label}`" if issue.label else ""
            lines.append(f"- **{issue.severity}** `{issue.code}` {loc}{label}{target}: {issue.message}")
    return lines


def cmd_universe(args: argparse.Namespace) -> int:
    universe = build_universe(args.repos_root.resolve(), args.repo_filter)
    write_json(args.out, universe)
    if args.markdown:
        write_markdown(args.markdown, universe_markdown(universe))
    print(f"universe: {len(universe.nodes)} nodes, {len(universe.issues)} issue(s), {args.out}")
    return 1 if any(issue.severity == "error" for issue in universe.issues) and args.strict else 0


def cmd_edges(args: argparse.Namespace) -> int:
    report = extract_edges(args.root.resolve(), args.universe.resolve())
    write_json(args.out, report)
    if args.markdown:
        write_markdown(args.markdown, edges_markdown(report))
    print(f"edges: {len(report.edges)} edges, {len(report.issues)} issue(s), {args.out}")
    return 1 if any(issue.severity == "error" for issue in report.issues) and args.strict else 0


def cmd_validate(args: argparse.Namespace) -> int:
    universe = load_universe(args.universe.resolve())
    edge_report = load_edges(args.edges.resolve())
    policy = load_policy(args.policy)
    issues = validate_graph(universe, edge_report, policy)
    payload = {"universe": str(args.universe), "edges": str(args.edges), "policy": str(args.policy) if args.policy else "", "issues": [asdict(issue) for issue in issues]}
    write_json(args.out, payload)
    if args.markdown:
        write_markdown(args.markdown, validation_markdown(issues))
    errors = sum(1 for issue in issues if issue.severity == "error")
    warnings = sum(1 for issue in issues if issue.severity == "warning")
    print(f"validate: {errors} error(s), {warnings} warning(s), {args.out}")
    return 1 if errors and args.strict else 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract and validate LRA dependency graph data.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("universe", help="Extract global formal-artifact universe.")
    p.add_argument("--repos-root", type=Path, required=True)
    p.add_argument("--repo-filter", default="lra-volume-*")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--markdown", type=Path)
    p.add_argument("--strict", action="store_true")
    p.set_defaults(func=cmd_universe)

    p = sub.add_parser("edges", help="Extract immediate dependency edges for one cleanup root.")
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--universe", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--markdown", type=Path)
    p.add_argument("--strict", action="store_true")
    p.set_defaults(func=cmd_edges)

    p = sub.add_parser("validate", help="Validate extracted graph mechanics.")
    p.add_argument("--universe", type=Path, required=True)
    p.add_argument("--edges", type=Path, required=True)
    p.add_argument("--policy", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--markdown", type=Path)
    p.add_argument("--strict", action="store_true")
    p.set_defaults(func=cmd_validate)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"fatal: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
