#!/usr/bin/env python3
"""Index internal LRA TeX and Lean mathematical objects.

The index is designed for fast Lean <-> TeX verification lookup.  It treats
volume TeX and Lean declarations as source-like evidence surfaces while keeping
PDF page anchoring as a downstream enrichment.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml


FORMAL_TEX_ENVS = {
    "definition",
    "theorem",
    "lemma",
    "proposition",
    "corollary",
    "axiom",
}
LEAN_DECL_KINDS = {
    "abbrev",
    "def",
    "theorem",
    "lemma",
    "axiom",
    "structure",
    "class",
    "inductive",
}

TEX_BEGIN_RE = re.compile(
    r"\\begin\{(?P<kind>definition|theorem|lemma|proposition|corollary|axiom)(?P<star>\*)?\}"
    r"(?:\[(?P<title>[^\]]*)\])?",
    re.S,
)
LABEL_RE = re.compile(r"\\label\{(?P<label>[^{}]+)\}")
SECTION_RE = re.compile(r"\\(?P<kind>part|chapter|section|subsection|subsubsection)\*?\{(?P<title>[^{}]+)\}")
LEAN_FORMALIZES_RE = re.compile(
    r"\\LeanFormalizes"
    r"\{(?P<label>(?:def|ax|thm|lem|prop|cor):[^{}]+)\}"
    r"\{(?P<repo>[A-Za-z0-9_.-]+)\}"
    r"\{(?P<module>[A-Za-z][A-Za-z0-9_'.]*(?:\.[A-Za-z][A-Za-z0-9_'.]*)*)\}"
    r"\{(?P<decl>[A-Za-z_][A-Za-z0-9_'.]*)\}"
    r"\{(?P<status>checked|statement|pending|incomplete)\}",
    re.IGNORECASE,
)
LEAN_DECL_RE = re.compile(
    r"^(?P<indent>\s*)(?:(?:noncomputable|private|protected|partial)\s+)*"
    r"(?P<kind>abbrev|def|theorem|lemma|axiom|structure|class|inductive)\s+"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_'.]*)\b(?P<tail>.*)$"
)
LEAN_NAMESPACE_RE = re.compile(r"^\s*namespace\s+(?P<name>[A-Za-z_][A-Za-z0-9_'.]*)\s*$")
LEAN_END_RE = re.compile(r"^\s*end(?:\s+(?P<name>[A-Za-z_][A-Za-z0-9_'.]*))?\s*$")
LEAN_COMMENT_TITLE_RE = re.compile(
    r"\[\s*(?P<role>Definition|Axiom|Theorem|Lemma|Proposition|Corollary)\s*(?:[-—:]+)\s*(?P<name>[^\]]+?)\s*\]",
    re.I,
)

SKIP_DIR_NAMES = {
    ".git",
    ".lake",
    ".pytest_cache",
    "__pycache__",
    "_to_delete",
    "build",
    "dist",
    "lake-packages",
}
MATCH_STOP_TOKENS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "into",
    "onto",
    "are",
    "is",
    "has",
    "have",
    "every",
    "exists",
    "there",
    "such",
    "that",
    "then",
    "real",
    "set",
    "sets",
    "function",
    "functions",
}
VOLUME_MODULE_PART = {
    "volume-i": "VolumeI",
    "volume-ii": "VolumeII",
    "volume-iii": "VolumeIII",
    "volume-iv": "VolumeIV",
    "volume-v": "VolumeV",
    "volume-vi": "VolumeVI",
    "volume-vii": "VolumeVII",
    "volume-viii": "VolumeVIII",
}
STRICT_HIERARCHY_MATCH_VOLUMES = {"volume-ii", "volume-iii", "volume-iv"}
HIERARCHY_STOP_TOKENS = {
    "book",
    "notes",
    "proofs",
    "source",
    "tex",
    "lean",
    "volume",
    "analysis",
    "spaces",
}
TEX_TO_LEAN_HIERARCHY_TOKENS = {
    "volume-i": {
        "axiom-systems": {"logic", "model", "theory"},
        "predicate-logic": {"logic", "first", "order", "predicate"},
        "propositional-logic": {"logic", "propositional"},
        "set-theory": {"set", "zfc"},
        "relations": {"relation"},
        "orderings": {"order", "relation"},
        "functions": {"operation", "set"},
        "functions-and-order": {"operation", "order", "relation"},
        "cardinality": {"cardinality", "set"},
    },
    "volume-ii": {
        "arithmetic-operations-relations": {"basic", "arithmetic"},
        "complex-numbers": {"complex", "number"},
        "constructing-number-systems": {"integer", "natural", "whole", "rational", "real", "complex", "peano"},
        "embedding-number-systems": {"extension", "number", "system"},
        "extended-real-numbers": {"extended", "real", "number"},
        "formalizing-number-systems": {"foundation", "number", "system"},
        "identity-equality-equivalence": {"foundation", "quotient"},
        "integers": {"integer"},
        "natural-numbers": {"natural", "number"},
        "number-lines": {"real", "number"},
        "numbers-summary": {"number", "system"},
        "peano-systems": {"peano", "system"},
        "rationals": {"rational", "number"},
        "reals": {"real", "number"},
        "whole-numbers": {"whole", "number"},
    },
    "volume-iii": {
        "bounding": {"bounding", "bound"},
        "completeness": {"completeness", "complete"},
        "continuity": {"continuity", "continuous"},
        "differentiation": {"differentiation", "derivative"},
        "elementary-functions": {"function"},
        "function-sequences": {"sequence", "function"},
        "functions": {"function"},
        "real-analysis": {"real"},
        "riemann-integration": {"integration", "integral", "riemann"},
        "sequences": {"sequence"},
        "series": {"series"},
        "structure-of-real-line": {"structure", "real", "line", "compactness", "interval"},
    },
    "volume-iv": {
        "algebras-of-sets": {"algebra", "set"},
        "banach-spaces": {"banach"},
        "hilbert-spaces": {"hilbert"},
        "inner-product-spaces": {"inner", "product"},
        "mathematical-spaces": {"mathematical", "space"},
        "measurable-spaces": {"measurable"},
        "measure-spaces": {"measure"},
        "metric-spaces": {"metric"},
        "normed-linear-spaces": {"normed", "linear"},
        "topological-spaces": {"topological", "topology"},
        "vector-spaces": {"vector"},
    },
}
OUT_OF_SCOPE_TEX_HIERARCHY = {
    "volume-i": {"analytical-geometry", "euclidean-geometry", "trigonometry", "proof-techniques"},
    "volume-iii": {"discrete-calculus"},
}


@dataclass
class InternalObject:
    object_id: str
    source_family: str
    kind: str
    name: str
    repo_root: str
    path: str
    line: int
    end_line: int | None = None
    label: str | None = None
    declaration: str | None = None
    module: str | None = None
    volume: str | None = None
    book: str | None = None
    chapter: str | None = None
    topic: str | None = None
    section_path: list[str] = field(default_factory=list)
    statement: str = ""
    search_text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in path.parts)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def relpath(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def stable_slug(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return slug or "object"


def compact_text(text: str) -> str:
    text = re.sub(r"%.*", "", text)
    text = re.sub(r"\\hyperref\[[^\]]+\]\{[^{}]*\}", " ", text)
    text = re.sub(r"\\label\{[^{}]+\}", " ", text)
    text = re.sub(r"\\(?:begin|end)\{[^{}]+\*?\}", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_match_key(text: str) -> str:
    text = re.sub(r"\\[A-Za-z]+\{([^{}]*)\}", r"\1", text)
    text = text.replace("ℝ", "R").replace("ℚ", "Q").replace("ℤ", "Z").replace("ℕ", "N")
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def match_tokens(text: str) -> set[str]:
    return {
        token
        for token in normalize_match_key(text).split()
        if len(token) > 1 and token not in MATCH_STOP_TOKENS
    }


def line_number_at(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def find_matching_tex_end(text: str, env: str, body_start: int) -> re.Match[str] | None:
    end_re = re.compile(r"\\end\{" + re.escape(env) + r"\*?\}")
    return end_re.search(text, body_start)


def section_context_before(text: str, offset: int) -> list[str]:
    context: dict[str, str] = {}
    order = ["part", "chapter", "section", "subsection", "subsubsection"]
    for match in SECTION_RE.finditer(text, 0, offset):
        kind = match.group("kind")
        context[kind] = compact_text(match.group("title"))
        for lower in order[order.index(kind) + 1 :]:
            context.pop(lower, None)
    return [context[kind] for kind in order if kind in context]


def trailing_window_end(text: str, offset: int) -> int:
    next_formal = TEX_BEGIN_RE.search(text, offset)
    next_section = SECTION_RE.search(text, offset)
    candidates = [match.start() for match in (next_formal, next_section) if match]
    return min(candidates) if candidates else len(text)


def lean_formalizes_in_window(text: str, start: int, end: int) -> list[dict[str, str]]:
    links = []
    for match in LEAN_FORMALIZES_RE.finditer(text, start, end):
        links.append(
            {
                "label": match.group("label"),
                "repo": match.group("repo"),
                "module": match.group("module"),
                "declaration": match.group("decl"),
                "status": match.group("status"),
            }
        )
    return links


def infer_volume_path_metadata(path: Path, root: Path) -> dict[str, str | None]:
    parts = Path(relpath(path, root)).parts
    metadata: dict[str, str | None] = {
        "volume": None,
        "book": None,
        "chapter": None,
        "topic": None,
    }
    for idx, part in enumerate(parts):
        if part.startswith("volume-"):
            metadata["volume"] = part
            if idx + 1 < len(parts):
                metadata["book"] = parts[idx + 1]
            if idx + 2 < len(parts):
                metadata["chapter"] = parts[idx + 2]
            for marker in ("notes", "proofs"):
                if marker in parts:
                    marker_idx = parts.index(marker)
                    if marker_idx + 1 < len(parts):
                        metadata["topic"] = parts[marker_idx + 1]
                    break
            break
        if re.fullmatch(r"Volume[IVX]+", part):
            metadata["volume"] = part
            if idx + 1 < len(parts):
                metadata["book"] = parts[idx + 1]
            if idx + 2 < len(parts):
                metadata["chapter"] = parts[idx + 2]
            break
    return metadata


def tex_files(root: Path, artifact_source: str) -> list[Path]:
    files = []
    for path in root.rglob("*.tex"):
        if should_skip(path):
            continue
        rel_parts = Path(relpath(path, root)).parts
        if not rel_parts or not rel_parts[0].startswith("volume-"):
            continue
        if path.name == "corrected.tex" and artifact_source == "source":
            continue
        if path.name == "source.tex" and artifact_source == "corrected":
            continue
        files.append(path)
    return sorted(files)


def index_tex_file(path: Path, root: Path) -> list[InternalObject]:
    records: list[InternalObject] = []
    text = read_text(path)
    path_meta = infer_volume_path_metadata(path, root)
    relative = relpath(path, root)
    for match in TEX_BEGIN_RE.finditer(text):
        kind = match.group("kind")
        end = find_matching_tex_end(text, kind, match.end())
        if not end:
            continue
        raw_block = text[match.start() : end.end()]
        label_match = LABEL_RE.search(raw_block)
        title = compact_text(match.group("title") or "")
        label = label_match.group("label") if label_match else None
        starred = bool(match.group("star"))
        if "YOUR_LABEL" in (label or "") or "TITLE GOES HERE" in title:
            continue
        line = line_number_at(text, match.start())
        end_line = line_number_at(text, end.end())
        name = title or label or f"{path.stem}:{line}"
        object_id = f"tex:{label}" if label else f"tex:{relative}:{line}"
        statement = compact_text(raw_block)
        formalizes = lean_formalizes_in_window(text, end.end(), trailing_window_end(text, end.end()))
        records.append(
            InternalObject(
                object_id=object_id,
                source_family="tex",
                kind=kind,
                name=name,
                repo_root=str(root),
                path=relative,
                line=line,
                end_line=end_line,
                label=label,
                volume=path_meta["volume"],
                book=path_meta["book"],
                chapter=path_meta["chapter"],
                topic=path_meta["topic"],
                section_path=section_context_before(text, match.start()),
                statement=statement,
                search_text=" ".join(item for item in [kind, name, label or "", statement] if item),
                metadata={"artifact_file": path.name, "starred": starred, "lean_formalizes": formalizes},
            )
        )
    return records


def index_tex_root(root: Path, artifact_source: str) -> list[InternalObject]:
    records: list[InternalObject] = []
    for path in tex_files(root, artifact_source):
        records.extend(index_tex_file(path, root))
    return records


def lean_module_name(path: Path, root: Path) -> str:
    relative = Path(relpath(path, root)).with_suffix("")
    return ".".join(relative.parts)


def lean_object_qualified_name(module: str, declaration: str) -> str:
    if declaration.startswith("LRA."):
        return declaration
    return f"{module}.{declaration}"


def declaration_extent(lines: list[str], start_idx: int) -> int:
    for idx in range(start_idx + 1, min(len(lines), start_idx + 80)):
        if LEAN_DECL_RE.match(lines[idx]) and not lines[idx].startswith((" ", "\t")):
            return idx
    return min(len(lines), start_idx + 80)


def declaration_statement(lines: list[str], start_idx: int, end_idx: int) -> str:
    chunk = "\n".join(lines[start_idx:end_idx])
    chunk = re.sub(r"/-.*?-/", " ", chunk, flags=re.S)
    chunk = re.sub(r"--.*", "", chunk)
    stop_patterns = [r"\s:=\s", r"\s:=\n", r"\swhere\b", r"\sby\b"]
    stop = len(chunk)
    for pattern in stop_patterns:
        found = re.search(pattern, chunk)
        if found:
            stop = min(stop, found.start())
    return re.sub(r"\s+", " ", chunk[:stop]).strip()


def compact_lean_comment(text: str) -> str:
    text = re.sub(r"^/-!?", "", text.strip())
    text = re.sub(r"-/$", "", text.strip())
    cleaned = []
    for line in text.splitlines():
        line = re.sub(r"^\s*--\s?", "", line)
        line = re.sub(r"^\s*\*\s?", "", line)
        cleaned.append(line)
    return re.sub(r"\s+", " ", "\n".join(cleaned)).strip()


def lean_comment_title(comment: str) -> dict[str, str]:
    match = LEAN_COMMENT_TITLE_RE.search(comment)
    if not match:
        return {}
    return {
        "role": match.group("role").lower(),
        "name": compact_text(match.group("name")),
    }


def leading_comment(lines: list[str], decl_idx: int) -> str:
    idx = decl_idx - 1
    while idx >= 0 and not lines[idx].strip():
        idx -= 1
    if idx < 0:
        return ""
    if lines[idx].lstrip().startswith("--"):
        start = idx
        while start - 1 >= 0 and lines[start - 1].lstrip().startswith("--"):
            start -= 1
        return compact_lean_comment("\n".join(lines[start : idx + 1]))
    if "-/" not in lines[idx]:
        return ""
    end = idx
    start = idx
    while start >= 0 and "/-" not in lines[start]:
        start -= 1
    if start < 0:
        return ""
    return compact_lean_comment("\n".join(lines[start : end + 1]))


def update_namespace_stack(line: str, stack: list[str]) -> None:
    namespace = LEAN_NAMESPACE_RE.match(line)
    if namespace:
        stack.extend(namespace.group("name").split("."))
        return
    end = LEAN_END_RE.match(line)
    if not end or not stack:
        return
    name = end.group("name")
    if not name:
        stack.pop()
        return
    parts = name.split(".")
    if stack[-len(parts) :] == parts:
        del stack[-len(parts) :]


def lean_files(root: Path) -> list[Path]:
    return sorted(item for item in root.rglob("*.lean") if not should_skip(item))


def index_lean_file(path: Path, root: Path) -> list[InternalObject]:
    records: list[InternalObject] = []
    text = read_text(path)
    lines = text.splitlines()
    namespace_stack: list[str] = []
    module = lean_module_name(path, root)
    relative = relpath(path, root)
    for idx, line in enumerate(lines):
        match = LEAN_DECL_RE.match(line)
        if match and match.group("kind") in LEAN_DECL_KINDS:
            kind = match.group("kind")
            name = match.group("name")
            end_idx = declaration_extent(lines, idx)
            statement = declaration_statement(lines, idx, end_idx)
            comment = leading_comment(lines, idx)
            comment_title = lean_comment_title(comment)
            declaration = ".".join([*namespace_stack, name]) if namespace_stack else name
            qualified_name = lean_object_qualified_name(module, declaration)
            path_meta = infer_volume_path_metadata(path, root)
            records.append(
                InternalObject(
                    object_id=f"lean:{qualified_name}",
                    source_family="lean",
                    kind=kind,
                    name=name,
                    repo_root=str(root),
                    path=relative,
                    line=idx + 1,
                    end_line=end_idx,
                    declaration=declaration,
                    module=module,
                    volume=path_meta["volume"],
                    book=path_meta["book"],
                    chapter=path_meta["chapter"],
                    statement=statement,
                    search_text=" ".join([kind, declaration, module, statement, comment]),
                    metadata={
                        "namespace": list(namespace_stack),
                        "leading_comment": comment,
                        "leading_comment_role": comment_title.get("role"),
                        "leading_comment_name": comment_title.get("name"),
                    },
                )
            )
        update_namespace_stack(line, namespace_stack)
    return records


def index_lean_root(root: Path) -> list[InternalObject]:
    records: list[InternalObject] = []
    for path in lean_files(root):
        records.extend(index_lean_file(path, root))
    return records


def build_index(
    *,
    tex_roots: Iterable[Path],
    lean_roots: Iterable[Path],
    artifact_source: str,
) -> dict[str, Any]:
    records: list[InternalObject] = []
    inputs = {"tex_roots": [], "lean_roots": []}
    for root in tex_roots:
        root = root.resolve()
        inputs["tex_roots"].append(str(root))
        records.extend(index_tex_root(root, artifact_source))
    for root in lean_roots:
        root = root.resolve()
        inputs["lean_roots"].append(str(root))
        records.extend(index_lean_root(root))
    records.sort(key=lambda item: (item.source_family, item.path, item.line, item.object_id))
    return {
        "schema_version": "lra.internal-object-index/1.0",
        "inputs": inputs,
        "counts": {
            "objects": len(records),
            "tex": sum(1 for item in records if item.source_family == "tex"),
            "lean": sum(1 for item in records if item.source_family == "lean"),
        },
        "objects": [asdict(record) for record in records],
    }


def kind_compatible(tex_kind: str, lean_kind: str) -> bool:
    if tex_kind == "definition":
        return lean_kind in {"abbrev", "def", "structure", "class", "inductive"}
    if tex_kind == "axiom":
        return lean_kind in {"axiom", "theorem", "lemma"}
    return lean_kind in {"theorem", "lemma", "axiom"}


def score_candidate(tex: dict[str, Any], lean: dict[str, Any]) -> int:
    if not kind_compatible(str(tex["kind"]), str(lean["kind"])):
        return 0
    tex_key = normalize_match_key(str(tex["name"]))
    lean_name = str(lean.get("declaration") or lean["name"])
    lean_key = normalize_match_key(lean_name.split(".")[-1])
    lean_statement_key = normalize_match_key(str(lean.get("statement") or ""))
    lean_comment = str(lean.get("metadata", {}).get("leading_comment") or "")
    lean_comment_key = normalize_match_key(lean_comment)
    score = 0
    if tex_key and tex_key == lean_key:
        score += 100
    if tex_key and tex_key in lean_statement_key:
        score += 45
    if tex_key and tex_key in lean_comment_key:
        score += 80
    tex_tokens = match_tokens(str(tex["name"]))
    lean_tokens = match_tokens(" ".join([lean_name, str(lean.get("statement") or "")]))
    overlap = tex_tokens & lean_tokens
    if overlap:
        score += len(overlap) * 12
        if tex_tokens and overlap == tex_tokens:
            score += 30
    comment_overlap = tex_tokens & match_tokens(lean_comment)
    if comment_overlap:
        score += len(comment_overlap) * 8
        if tex_tokens and comment_overlap == tex_tokens:
            score += 20
    if str(tex.get("volume") or "").lower().replace("-", "") in str(lean.get("path") or "").lower().replace("-", ""):
        score += 10
    context_tokens = tex_hierarchy_tokens(tex)
    lean_context_tokens = lean_hierarchy_tokens(lean)
    context_overlap = context_tokens & lean_context_tokens
    if context_overlap:
        score += min(len(context_overlap), 4) * 18
    return score


def production_lean(record: dict[str, Any]) -> bool:
    return str(record.get("path") or "").startswith("LRA/")


def tex_volume_module_part(record: dict[str, Any]) -> str | None:
    return VOLUME_MODULE_PART.get(str(record.get("volume") or "").lower())


def tex_hierarchy_key(record: dict[str, Any]) -> str | None:
    path_parts = str(record.get("path") or "").split("/")
    if len(path_parts) >= 3:
        return path_parts[2]
    return str(record.get("chapter") or "") or None


def tex_out_of_scope_for_matching(record: dict[str, Any]) -> bool:
    volume = str(record.get("volume") or "").lower()
    key = tex_hierarchy_key(record)
    return bool(key and key in OUT_OF_SCOPE_TEX_HIERARCHY.get(volume, set()))


def same_volume_lean(tex: dict[str, Any], lean: dict[str, Any]) -> bool:
    volume_part = tex_volume_module_part(tex)
    if not volume_part:
        return True
    module = str(lean.get("module") or "")
    path = str(lean.get("path") or "")
    return module.startswith(f"LRA.{volume_part}.") or path.startswith(f"LRA/{volume_part}/")


def tex_hierarchy_tokens(record: dict[str, Any]) -> set[str]:
    fields = [
        str(record.get("book") or ""),
        str(record.get("chapter") or ""),
        str(record.get("topic") or ""),
        str(record.get("path") or ""),
    ]
    tokens = set(re.findall(r"[a-z0-9]+", normalize_match_key(" ".join(fields))))
    expanded = set(tokens)
    for token in tokens:
        if token.endswith("s") and len(token) > 3:
            expanded.add(token[:-1])
    return {token for token in expanded if len(token) > 1 and token not in HIERARCHY_STOP_TOKENS}


def tex_local_hierarchy_tokens(record: dict[str, Any]) -> set[str]:
    path_parts = str(record.get("path") or "").split("/")
    tail_parts: list[str] = []
    for marker in ("notes", "proofs"):
        if marker in path_parts:
            tail_parts = path_parts[path_parts.index(marker) + 1 :]
            break
    fields = [
        str(record.get("chapter") or ""),
        str(record.get("topic") or ""),
        " ".join(tail_parts),
    ]
    tokens = set(re.findall(r"[a-z0-9]+", normalize_match_key(" ".join(fields))))
    expanded = set(tokens)
    for token in tokens:
        if token.endswith("s") and len(token) > 3:
            expanded.add(token[:-1])
    return {token for token in expanded if len(token) > 1 and token not in HIERARCHY_STOP_TOKENS}


def lean_hierarchy_tokens(record: dict[str, Any]) -> set[str]:
    text = " ".join([str(record.get("module") or ""), str(record.get("path") or "")])
    tokens = set(re.findall(r"[a-z0-9]+", normalize_match_key(text)))
    expanded = set(tokens)
    for token in tokens:
        if token.endswith("s") and len(token) > 3:
            expanded.add(token[:-1])
    return {token for token in expanded if len(token) > 1 and token not in HIERARCHY_STOP_TOKENS}


def expected_lean_hierarchy_tokens(tex: dict[str, Any]) -> set[str]:
    volume = str(tex.get("volume") or "").lower()
    key = tex_hierarchy_key(tex)
    if not key:
        return set()
    return TEX_TO_LEAN_HIERARCHY_TOKENS.get(volume, {}).get(key, set())


def context_compatible(tex: dict[str, Any], lean: dict[str, Any]) -> bool:
    if tex_out_of_scope_for_matching(tex) or not production_lean(lean) or not same_volume_lean(tex, lean):
        return False
    strict_volume = str(tex.get("volume") or "").lower() in STRICT_HIERARCHY_MATCH_VOLUMES
    context_tokens = expected_lean_hierarchy_tokens(tex)
    if not context_tokens:
        context_tokens = tex_local_hierarchy_tokens(tex) if strict_volume else tex_hierarchy_tokens(tex)
    if not context_tokens:
        return True
    lean_context_tokens = lean_hierarchy_tokens(lean)
    if context_tokens & lean_context_tokens:
        return True
    if expected_lean_hierarchy_tokens(tex):
        return False
    if strict_volume:
        return False
    # Folder slugs and Lean module names are not always vocabulary-equivalent;
    # outside structurally aligned volumes, same production volume is still the
    # correct bounded review universe.
    return bool(tex_volume_module_part(tex))


def build_match_report(payload: dict[str, Any], *, limit: int) -> dict[str, Any]:
    tex_records = [item for item in payload["objects"] if item["source_family"] == "tex"]
    lean_records = [
        item for item in payload["objects"] if item["source_family"] == "lean" and production_lean(item)
    ]
    lean_by_token: dict[str, list[dict[str, Any]]] = {}
    lean_by_kind: dict[str, list[dict[str, Any]]] = {}
    for lean in lean_records:
        lean_by_kind.setdefault(str(lean["kind"]), []).append(lean)
        haystack = " ".join(
            [
                str(lean.get("declaration") or lean["name"]),
                str(lean.get("module") or ""),
                str(lean.get("statement") or ""),
                str(lean.get("metadata", {}).get("leading_comment") or ""),
            ]
        )
        for token in match_tokens(haystack):
            lean_by_token.setdefault(token, []).append(lean)
    linked_tex = []
    missing_tex = []
    candidate_matches = []
    linked_declarations = set()
    for tex in tex_records:
        links = tex.get("metadata", {}).get("lean_formalizes") or []
        if links:
            linked_tex.append(tex["object_id"])
            for link in links:
                if link.get("declaration"):
                    linked_declarations.add(str(link["declaration"]))
            continue
        scored = []
        tex_token_set = match_tokens(str(tex["name"]))
        candidates_by_id: dict[str, dict[str, Any]] = {}
        for token in sorted(tex_token_set, key=len, reverse=True)[:8]:
            for lean in lean_by_token.get(token, []):
                candidates_by_id[str(lean["object_id"])] = lean
                if len(candidates_by_id) >= 500:
                    break
            if len(candidates_by_id) >= 500:
                break
        if not candidates_by_id:
            for kind in ("abbrev", "def", "structure", "class", "inductive", "theorem", "lemma", "axiom"):
                for lean in lean_by_kind.get(kind, [])[:200]:
                    candidates_by_id[str(lean["object_id"])] = lean
        for lean in candidates_by_id.values():
            if not context_compatible(tex, lean):
                continue
            score = score_candidate(tex, lean)
            if score > 0:
                scored.append(
                    {
                        "score": score,
                        "lean_object_id": lean["object_id"],
                        "lean_kind": lean["kind"],
                        "declaration": lean.get("declaration"),
                        "module": lean.get("module"),
                        "path": lean["path"],
                        "line": lean["line"],
                        "leading_comment_role": lean.get("metadata", {}).get("leading_comment_role"),
                        "leading_comment_name": lean.get("metadata", {}).get("leading_comment_name"),
                    }
                )
        scored.sort(key=lambda item: (-int(item["score"]), str(item["declaration"])))
        if scored:
            candidate_matches.append(
                {
                    "tex_object_id": tex["object_id"],
                    "tex_label": tex.get("label"),
                    "tex_kind": tex["kind"],
                    "tex_name": tex["name"],
                    "path": tex["path"],
                    "line": tex["line"],
                    "candidates": scored[:limit],
                }
            )
        else:
            missing_tex.append(
                {
                    "tex_object_id": tex["object_id"],
                    "tex_label": tex.get("label"),
                    "tex_kind": tex["kind"],
                    "tex_name": tex["name"],
                    "path": tex["path"],
                    "line": tex["line"],
                }
            )
    unlinked_lean = [
        {
            "lean_object_id": lean["object_id"],
            "lean_kind": lean["kind"],
            "declaration": lean.get("declaration"),
            "module": lean.get("module"),
            "path": lean["path"],
            "line": lean["line"],
        }
        for lean in lean_records
        if str(lean.get("declaration") or lean["name"]) not in linked_declarations
    ]
    return {
        "schema_version": "lra.lean-tex-match-report/1.0",
        "counts": {
            "tex_objects": len(tex_records),
            "lean_objects": len(lean_records),
            "tex_with_leanformalizes": len(linked_tex),
            "tex_without_leanformalizes": len(tex_records) - len(linked_tex),
            "tex_with_candidates": len(candidate_matches),
            "tex_without_candidates": len(missing_tex),
            "lean_without_tex_link": len(unlinked_lean),
        },
        "candidate_matches": candidate_matches,
        "tex_without_candidates": missing_tex,
        "lean_without_tex_link": unlinked_lean,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tex-root", action="append", type=Path, default=[], help="Volume TeX repo/root to scan. May repeat.")
    parser.add_argument("--lean-root", action="append", type=Path, default=[], help="Lean repo/root to scan. May repeat.")
    parser.add_argument(
        "--tex-artifact-source",
        choices=("source", "corrected", "all"),
        default="source",
        help="When artifact directories contain both source.tex and corrected.tex, choose which to index.",
    )
    parser.add_argument("--output", type=Path, help="Output file. Defaults to stdout.")
    parser.add_argument("--format", choices=("yaml", "json", "jsonl"), default="yaml")
    parser.add_argument("--include-match-report", action="store_true", help="Include Lean <-> TeX candidate matches and missing-link counts.")
    parser.add_argument("--candidate-limit", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.tex_root and not args.lean_root:
        print("ERROR: pass at least one --tex-root or --lean-root", file=sys.stderr)
        return 2
    payload = build_index(
        tex_roots=args.tex_root,
        lean_roots=args.lean_root,
        artifact_source=args.tex_artifact_source,
    )
    if args.include_match_report:
        payload["match_report"] = build_match_report(payload, limit=args.candidate_limit)
    if args.format == "json":
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    elif args.format == "jsonl":
        text = "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in payload["objects"])
    else:
        text = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
