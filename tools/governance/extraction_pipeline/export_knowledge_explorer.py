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
from extraction_pipeline.build_proof_vault_index import build_index as build_proof_vault_index  # noqa: E402


KIND_DISPLAY = {
    "def": "Definition",
    "ax": "Axiom",
    "thm": "Theorem",
    "lem": "Lemma",
    "prop": "Proposition",
    "cor": "Corollary",
}

CHAPTER_WRAPPERS = {"analysis", "algebra"}
WORKED_EXAMPLE_RE = re.compile(
    r"\\begin\{workedexample\}(?:\[(?P<title>[^\]]*)\])?(?P<body>[\s\S]*?)\\end\{workedexample\}",
    re.IGNORECASE,
)
WORKED_EXAMPLE_FOR_RE = re.compile(r"\\LRAWorkedExampleFor\{(?P<labels>[^{}]*)\}", re.IGNORECASE)
WORKED_EXAMPLE_USES_RE = re.compile(r"\\LRAWorkedExampleUses\{(?P<labels>[^{}]*)\}", re.IGNORECASE)
WORKED_EXAMPLE_TAGS_RE = re.compile(r"\\LRAWorkedExampleTags\{(?P<tags>[^{}]*)\}", re.IGNORECASE)
WORKED_EXAMPLE_METADATA_RE = re.compile(
    r"\\LRAWorkedExample(?:For|Uses|Tags)\{[^{}]*\}\s*",
    re.IGNORECASE,
)
INPUT_RE = re.compile(r"\\input\{(?P<path>[^{}]+)\}")
CHAPTER_RE = re.compile(r"\\chapter\*?\{(?P<title>(?:[^{}]|\{[^{}]*\})*)\}", re.DOTALL)
SECTION_RE = re.compile(r"\\section\*?\{(?P<title>(?:[^{}]|\{[^{}]*\})*)\}", re.DOTALL)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[,;\n]+", value or "") if item.strip()]


def next_version(explorer: Path, generated_at: str) -> dict[str, Any]:
    path = explorer / "knowledge-version.json"
    if path.exists():
        current = load_json(path)
        version_id = int(current.get("version_id", 0)) + 1
    else:
        version_id = 1
    payload = {
        "version_id": version_id,
        "updated_at": generated_at,
        "source": "lra-governance/tools/governance/extraction_pipeline/export_knowledge_explorer.py",
    }
    write_json(path, payload)
    return payload


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


def read_tex(path: Path) -> str:
    if not path.exists():
        return ""
    return dependency_graph.strip_comments(path.read_text(encoding="utf-8", errors="replace"))


def input_path(root: Path, raw: str) -> Path:
    raw = raw.strip()
    path = root / raw
    if path.suffix:
        return path
    return path.with_suffix(".tex")


def first_tex_title(path: Path, pattern: re.Pattern[str], fallback: str = "") -> str:
    text = read_tex(path)
    match = pattern.search(text)
    if not match:
        return title_from_slug(fallback) if fallback else ""
    return re.sub(r"\s+", " ", match.group("title")).strip()


def title_from_slug(slug: str) -> str:
    specials = {
        "r": r"$\mathbb{R}$",
        "q": r"$\mathbb{Q}$",
        "z": r"$\mathbb{Z}$",
        "w": r"$\mathbb{W}$",
        "n": r"$\mathbb{N}$",
        "c": r"$\mathbb{C}$",
    }
    words = []
    for part in slug.split("-"):
        words.append(specials.get(part, part.capitalize()))
    return " ".join(words)


def toc_for_repo(repo_root: Path) -> dict[str, Any]:
    repo_name = repo_root.name
    volume = volume_from_repo(repo_name)
    volume_dir = repo_root / f"volume-{volume}"
    volume_index = volume_dir / "index.tex"
    chapters: list[dict[str, Any]] = []

    def chapter_inputs(path: Path, depth: int = 0) -> list[str]:
        if depth > 4:
            return []
        text = read_tex(path)
        if CHAPTER_RE.search(text):
            rel_path = path.resolve().relative_to(repo_root.resolve()).with_suffix("").as_posix()
            return [rel_path]
        out: list[str] = []
        for input_match in INPUT_RE.finditer(text):
            child = input_path(repo_root, input_match.group("path").replace("\\", "/"))
            out.extend(chapter_inputs(child, depth + 1))
        return out

    for raw in chapter_inputs(volume_index):
        parts = Path(raw).parts
        if len(parts) < 2 or parts[0] != f"volume-{volume}":
            continue
        chapter_key = parts[2] if len(parts) >= 3 and parts[1] in CHAPTER_WRAPPERS else parts[1]
        if chapter_key in {chapter["id"] for chapter in chapters}:
            continue
        chapter_index = input_path(repo_root, raw)
        chapter_title = first_tex_title(chapter_index, CHAPTER_RE)
        if not chapter_title:
            continue
        notes_index = chapter_index.parent / "notes" / "index.tex"
        sections: list[dict[str, str]] = []
        for section_match in INPUT_RE.finditer(read_tex(notes_index)):
            section_raw = section_match.group("path").replace("\\", "/")
            section_parts = Path(section_raw).parts
            if len(section_parts) < 4 or section_parts[0] != f"volume-{volume}":
                continue
            try:
                notes_index_part = section_parts.index("notes")
            except ValueError:
                continue
            if notes_index_part + 1 >= len(section_parts):
                continue
            section_key = section_parts[notes_index_part + 1]
            if section_key in {section["id"] for section in sections}:
                continue
            section_index = input_path(repo_root, section_raw)
            section_title = first_tex_title(section_index, SECTION_RE, section_key)
            sections.append({"id": section_key, "title": section_title})
        chapters.append({"id": chapter_key, "title": chapter_title, "sections": sections})
    return {"id": volume, "repo": repo_name, "chapters": chapters}


def build_toc(repos_root: Path) -> list[dict[str, Any]]:
    def key(path: Path) -> int:
        value = volume_from_repo(path.name)
        roman = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8}
        return roman.get(value, 999)

    volumes = []
    for repo_root in sorted(repos_root.glob("lra-volume-*"), key=key):
        if (repo_root / ".git").exists():
            volumes.append(toc_for_repo(repo_root))
    return volumes


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


def collect_worked_examples(repos_root: Path, nodes: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    files = sorted({(node["repo"], node["file"]) for node in nodes})
    for repo, file in files:
        path = repos_root / repo / file
        if not path.exists():
            continue
        text = dependency_graph.strip_comments(path.read_text(encoding="utf-8", errors="replace"))
        for index, match in enumerate(WORKED_EXAMPLE_RE.finditer(text), start=1):
            body = match.group("body").strip()
            target_match = WORKED_EXAMPLE_FOR_RE.search(body)
            if not target_match:
                continue
            title = (match.group("title") or f"Example {index}").strip()
            uses_match = WORKED_EXAMPLE_USES_RE.search(body)
            tags_match = WORKED_EXAMPLE_TAGS_RE.search(body)
            cleaned_body = WORKED_EXAMPLE_METADATA_RE.sub("", body).strip()
            line = text.count("\n", 0, match.start()) + 1
            record = {
                "label": title,
                "title": title,
                "body_tex": cleaned_body,
                "uses": split_csv(uses_match.group("labels") if uses_match else ""),
                "tags": split_csv(tags_match.group("tags") if tags_match else ""),
                "source": source_from_file(file),
                "source_line": line,
            }
            for target in split_csv(target_match.group("labels")):
                examples[target].append(record)
    return examples


def title_for(node: dict[str, Any]) -> str:
    title = strip_statement_navigation(node.get("title") or node["label"])
    if r"\hyperref[" in title or r"\texorpdfstring" in title:
        return title_from_label(node["label"])
    return title


def build_export(run_dir: Path, repos_root: Path, version: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    universe = load_json(run_dir / "universe.json")
    combined = load_json(run_dir / "combined-edges.json")
    nodes = universe["nodes"]
    by_label = {node["label"]: node for node in nodes}

    depends_on: dict[str, list[str]] = defaultdict(list)
    used_by: dict[str, list[str]] = defaultdict(list)
    proof_depends_on: dict[str, list[str]] = defaultdict(list)
    proof_used_by: dict[str, list[str]] = defaultdict(list)
    graph_edges: list[dict[str, str]] = []
    seen_edges: set[tuple[str, str, str]] = set()
    for edge in combined["edges"]:
        kind = edge.get("kind") or "depends_on"
        key = (edge["source"], edge["target"], kind)
        if key in seen_edges:
            continue
        seen_edges.add(key)
        graph_edges.append({"from": edge["source"], "to": edge["target"], "kind": kind})
        if kind == "proof_depends_on":
            proof_depends_on[edge["source"]].append(edge["target"])
            proof_used_by[edge["target"]].append(edge["source"])
        else:
            depends_on[edge["source"]].append(edge["target"])
            used_by[edge["target"]].append(edge["source"])

    exported_nodes: list[dict[str, Any]] = []
    chapter_order: list[str] = []
    seen_chapters: set[str] = set()
    examples_by_label = collect_worked_examples(repos_root, nodes)
    toc = build_toc(repos_root)
    chapter_titles = {
        (volume["id"], chapter["id"]): chapter["title"]
        for volume in toc
        for chapter in volume.get("chapters", [])
    }
    section_titles = {
        (volume["id"], chapter["id"], section["id"]): section["title"]
        for volume in toc
        for chapter in volume.get("chapters", [])
        for section in chapter.get("sections", [])
    }

    for node in sorted(nodes, key=lambda item: item["source_order"]):
        label = node["label"]
        chapter = chapter_from_file(node["file"])
        volume = volume_from_repo(node.get("repo", ""))
        section = section_from_file(node["file"])
        if chapter not in seen_chapters:
            seen_chapters.add(chapter)
            chapter_order.append(chapter)

        deps = depends_on.get(label, [])
        users = used_by.get(label, [])
        proof_deps = proof_depends_on.get(label, [])
        proof_users = proof_used_by.get(label, [])
        statement = statement_for_node(repos_root, node)
        kind = KIND_DISPLAY.get(node["kind"], node["kind"])
        name = title_for(node)
        exported = {
            "id": label,
            "kind": kind,
            "name": name,
            "deck": "",
            "chapter": chapter,
            "chapter_title": chapter_titles.get((volume, chapter), title_from_slug(chapter)),
            "volume": volume,
            "source": source_from_file(node["file"]),
            "statement_display": statement,
            "statement_tex": statement,
            "source_text": statement,
            "section": section,
            "section_title": section_titles.get((volume, chapter, section), title_from_slug(section)),
            "depends_on_ids": deps,
            "used_by_ids": users,
            "proof_depends_on_ids": proof_deps,
            "proof_used_by_ids": proof_users,
            "prereq_ids": [],
            "equivalent_to_ids": [],
            "implies_ids": [],
            "depends_on_titles": [title_for(by_label[target]) for target in deps if target in by_label],
            "used_by_titles": [title_for(by_label[source]) for source in users if source in by_label],
            "proof_depends_on_titles": [title_for(by_label[target]) for target in proof_deps if target in by_label],
            "proof_used_by_titles": [title_for(by_label[source]) for source in proof_users if source in by_label],
            "dependencies": deps,
            "proof_dependencies": proof_deps,
            "ignored": False,
            "is_theorem_like": kind in {"Theorem", "Lemma", "Proposition", "Corollary"},
            "definitional_root": node.get("root_kind") == "definitional",
            "is_root": bool(node.get("root_kind")) or kind == "Axiom",
            "root_kind": node.get("root_kind") or ("axiom" if kind == "Axiom" else ""),
            "env_name": node.get("env", ""),
            "text_preview": re.sub(r"\s+", " ", statement)[:240],
        }
        if examples_by_label.get(label):
            exported["examples"] = examples_by_label[label]
        exported_nodes.append(exported)

    knowledge = {
        "metadata": {
            "generated_at": version["updated_at"],
            "version_id": version["version_id"],
            "chapters": chapter_order,
            "node_count": len(exported_nodes),
            "edge_count": len(graph_edges),
            "error_count": 0,
            "schema_version": "governance-export-1",
            "script": "lra-governance/tools/governance/extraction_pipeline/export_knowledge_explorer.py",
            "source_run": str(run_dir),
            "toc": toc,
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
    parser.add_argument(
        "--proof-vault",
        type=Path,
        default=Path(__file__).resolve().parents[4] / "lra-proof-vault",
        help="lra-proof-vault repo used to build proof-vault-index.json.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = args.run_dir.resolve()
    repos_root = args.repos_root.resolve()
    explorer = args.knowledge_explorer.resolve()
    proof_vault = args.proof_vault.resolve()
    if not (run_dir / "universe.json").exists() or not (run_dir / "combined-edges.json").exists():
        raise SystemExit(f"Missing extraction artifacts in {run_dir}")
    if not (explorer / ".git").exists():
        raise SystemExit(f"Missing lra-knowledge-explorer repo: {explorer}")
    if not (proof_vault / ".git").exists():
        raise SystemExit(f"Missing lra-proof-vault repo: {proof_vault}")

    generated_at = datetime.now(timezone.utc).isoformat()
    version = next_version(explorer, generated_at)
    knowledge, graph_edges = build_export(run_dir, repos_root, version)
    proof_vault_index = build_proof_vault_index(proof_vault, generated_at=generated_at)
    write_json(explorer / "knowledge.json", knowledge)
    write_json(explorer / "graph-edges.json", graph_edges)
    write_json(explorer / "proof-vault-index.json", proof_vault_index)
    write_json(
        explorer / "proof-errors.json",
        {"generated_at": knowledge["metadata"]["generated_at"], "chapters": knowledge["metadata"]["chapters"], "error_count": 0, "errors": []},
    )
    write_json(
        explorer / "graph-edge-errors.json",
        {"generated_at": knowledge["metadata"]["generated_at"], "chapters": knowledge["metadata"]["chapters"], "error_count": 0, "errors": []},
    )
    print(
        f"Wrote {len(knowledge['nodes'])} nodes, {len(graph_edges)} edges, "
        f"and {proof_vault_index['record_count']} proof-vault records to {explorer}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
