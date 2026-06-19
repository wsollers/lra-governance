#!/usr/bin/env python3
"""Export a governance extraction run to lra-knowledge-explorer JSON artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GOVERNANCE_TOOL_ROOT = Path(__file__).resolve().parents[1]
if str(GOVERNANCE_TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(GOVERNANCE_TOOL_ROOT))

import dependency_graph  # noqa: E402


KIND_DISPLAY = {
    "def": "Definition",
    "ax": "Axiom",
    "thm": "Theorem",
    "lem": "Lemma",
    "prop": "Proposition",
    "cor": "Corollary",
}

CHAPTER_WRAPPERS = {"analysis", "algebra"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def chapter_from_file(file: str) -> str:
    parts = Path(file.replace("\\", "/")).parts
    if len(parts) < 2:
        return "_unknown"
    if len(parts) >= 3 and parts[1] in CHAPTER_WRAPPERS:
        return parts[2]
    return parts[1]


def volume_from_repo(repo: str) -> str:
    if repo.startswith("lra-volume-"):
        return repo[len("lra-volume-") :]
    if repo.startswith("volume-"):
        return repo[len("volume-") :]
    return repo


def source_from_file(file: str) -> str:
    parts = Path(file.replace("\\", "/")).parts
    if len(parts) < 3:
        return file.replace("\\", "/")
    if len(parts) >= 4 and parts[1] in CHAPTER_WRAPPERS:
        return Path(*parts[3:]).as_posix()
    return Path(*parts[2:]).as_posix()


def section_from_file(file: str) -> str:
    source = source_from_file(file)
    parts = Path(source).parts
    if len(parts) >= 2 and parts[0] == "notes":
        return parts[1]
    return parts[0] if parts else ""


HYPERREF_RE = re.compile(r"\\hyperref\[([^\]]+)\]\{((?:[^{}]|\{[^{}]*\})*)\}", re.DOTALL)


def strip_statement_navigation(text: str) -> str:
    def replace_ref(match: re.Match[str]) -> str:
        target = match.group(1)
        display = match.group(2)
        plain = re.sub(r"\\(?:textit|emph|textbf)\{([^{}]*)\}", r"\1", display)
        if re.search(r"\bGo to .*proof\.?|\bReturn to (?:Theorem|theorem|Proof|proof)\b", plain, re.IGNORECASE):
            return ""
        if target.startswith("prf:"):
            return plain
        return match.group(0)

    text = HYPERREF_RE.sub(replace_ref, text)
    text = re.sub(r"\\texorpdfstring\{([^{}]*)\}\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\(?:smallskip|medskip|bigskip|noindent)\b", "", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_formal_environment_wrapper(block: str, env: str) -> str:
    begin = re.match(rf"^\\begin\{{{re.escape(env)}\}}", block, flags=re.IGNORECASE)
    if begin:
        block = block[begin.end() :].lstrip()
        if block.startswith("["):
            brace_depth = 0
            for index, char in enumerate(block[1:], start=1):
                prev = block[index - 1] if index else ""
                if char == "{" and prev != "\\":
                    brace_depth += 1
                elif char == "}" and prev != "\\" and brace_depth:
                    brace_depth -= 1
                elif char == "]" and brace_depth == 0:
                    block = block[index + 1 :].lstrip()
                    break
    block = re.sub(rf"\s*\\end\{{{re.escape(env)}\}}\s*$", "", block, flags=re.IGNORECASE)
    return block


def title_from_label(label: str) -> str:
    slug = label.split(":", 1)[-1]
    return " ".join(part.capitalize() for part in slug.split("-") if part)


def statement_for_node(repos_root: Path, node: dict[str, Any]) -> str:
    path = repos_root / node["repo"] / node["file"]
    text = dependency_graph.strip_comments(path.read_text(encoding="utf-8", errors="replace"))
    for begin, end_pos in dependency_graph.formal_blocks(text):
        block = text[begin.start() : end_pos]
        labels = dependency_graph.LABEL_RE.findall(block)
        if node["label"] not in labels:
            continue
        env = begin.group("env")
        block = strip_formal_environment_wrapper(block, env)
        block = re.sub(r"\\label\{[^{}]+\}\s*", "", block)
        return strip_statement_navigation(block)
    return node.get("title") or node["label"]


def title_for(node: dict[str, Any]) -> str:
    title = strip_statement_navigation(node.get("title") or node["label"])
    if r"\hyperref[" in title or r"\texorpdfstring" in title:
        return title_from_label(node["label"])
    return title


def build_export(run_dir: Path, repos_root: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    universe = load_json(run_dir / "universe.json")
    combined = load_json(run_dir / "combined-edges.json")
    nodes = universe["nodes"]
    by_label = {node["label"]: node for node in nodes}

    depends_on: dict[str, list[str]] = defaultdict(list)
    used_by: dict[str, list[str]] = defaultdict(list)
    graph_edges: list[dict[str, str]] = []
    seen_edges: set[tuple[str, str, str]] = set()
    for edge in combined["edges"]:
        key = (edge["source"], edge["target"], "depends_on")
        if key in seen_edges:
            continue
        seen_edges.add(key)
        graph_edges.append({"from": edge["source"], "to": edge["target"], "kind": "depends_on"})
        depends_on[edge["source"]].append(edge["target"])
        used_by[edge["target"]].append(edge["source"])

    exported_nodes: list[dict[str, Any]] = []
    chapter_order: list[str] = []
    seen_chapters: set[str] = set()

    for node in sorted(nodes, key=lambda item: item["source_order"]):
        label = node["label"]
        chapter = chapter_from_file(node["file"])
        volume = volume_from_repo(node.get("repo", ""))
        if chapter not in seen_chapters:
            seen_chapters.add(chapter)
            chapter_order.append(chapter)

        deps = depends_on.get(label, [])
        users = used_by.get(label, [])
        statement = statement_for_node(repos_root, node)
        kind = KIND_DISPLAY.get(node["kind"], node["kind"])
        name = title_for(node)
        exported_nodes.append(
            {
                "id": label,
                "kind": kind,
                "name": name,
                "deck": "",
                "chapter": chapter,
                "volume": volume,
                "source": source_from_file(node["file"]),
                "statement_display": statement,
                "statement_tex": statement,
                "source_text": statement,
                "section": section_from_file(node["file"]),
                "depends_on_ids": deps,
                "used_by_ids": users,
                "prereq_ids": [],
                "equivalent_to_ids": [],
                "implies_ids": [],
                "depends_on_titles": [title_for(by_label[target]) for target in deps if target in by_label],
                "used_by_titles": [title_for(by_label[source]) for source in users if source in by_label],
                "dependencies": deps,
                "ignored": False,
                "is_theorem_like": kind in {"Theorem", "Lemma", "Proposition", "Corollary"},
                "definitional_root": node.get("root_kind") == "definitional",
                "is_root": bool(node.get("root_kind")) or kind == "Axiom",
                "root_kind": node.get("root_kind") or ("axiom" if kind == "Axiom" else ""),
                "env_name": node.get("env", ""),
                "text_preview": re.sub(r"\s+", " ", statement)[:240],
            }
        )

    knowledge = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "chapters": chapter_order,
            "node_count": len(exported_nodes),
            "edge_count": len(graph_edges),
            "error_count": 0,
            "schema_version": "governance-export-1",
            "script": "lra-governance/tools/governance/extraction_pipeline/export_knowledge_explorer.py",
            "source_run": str(run_dir),
        },
        "nodes": exported_nodes,
        "edges": graph_edges,
    }
    return knowledge, graph_edges


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path, help="Governance extraction run directory.")
    parser.add_argument(
        "--repos-root",
        type=Path,
        default=Path(__file__).resolve().parents[4],
        help="Workspace containing lra-volume-* repos.",
    )
    parser.add_argument(
        "--knowledge-explorer",
        type=Path,
        default=Path(__file__).resolve().parents[4] / "lra-knowledge-explorer",
        help="lra-knowledge-explorer repo to receive generated artifacts.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = args.run_dir.resolve()
    repos_root = args.repos_root.resolve()
    explorer = args.knowledge_explorer.resolve()
    if not (run_dir / "universe.json").exists() or not (run_dir / "combined-edges.json").exists():
        raise SystemExit(f"Missing extraction artifacts in {run_dir}")
    if not (explorer / ".git").exists():
        raise SystemExit(f"Missing lra-knowledge-explorer repo: {explorer}")

    knowledge, graph_edges = build_export(run_dir, repos_root)
    write_json(explorer / "knowledge.json", knowledge)
    write_json(explorer / "graph-edges.json", graph_edges)
    write_json(
        explorer / "proof-errors.json",
        {"generated_at": knowledge["metadata"]["generated_at"], "chapters": knowledge["metadata"]["chapters"], "error_count": 0, "errors": []},
    )
    write_json(
        explorer / "graph-edge-errors.json",
        {"generated_at": knowledge["metadata"]["generated_at"], "chapters": knowledge["metadata"]["chapters"], "error_count": 0, "errors": []},
    )
    print(f"Wrote {len(knowledge['nodes'])} nodes and {len(graph_edges)} edges to {explorer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
