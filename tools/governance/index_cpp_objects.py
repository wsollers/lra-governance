#!/usr/bin/env python3
"""Index C/C++ source objects in LRA specialist code repositories."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

try:
    from internal_object_sqlite import build_family_databases
except ModuleNotFoundError:
    from tools.governance.internal_object_sqlite import build_family_databases


CPP_EXTENSIONS = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx", ".ixx"}
SKIP_DIR_NAMES = {
    ".git",
    ".idea",
    ".vs",
    "build",
    "cmake-build-debug",
    "cmake-build-release",
    "out",
    "dist",
    "__pycache__",
}
NAMESPACE_RE = re.compile(r"^\s*namespace\s+(?P<name>[A-Za-z_][A-Za-z0-9_:]*)\s*\{")
TYPE_RE = re.compile(
    r"^\s*(?P<kind>class|struct|enum(?:\s+class)?)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\b"
)
FUNCTION_RE = re.compile(
    r"^\s*(?P<prefix>(?:template\s*<[^;{}]+>\s*)?(?:(?:inline|static|constexpr|consteval|constinit|virtual|explicit|friend|extern)\s+)*)"
    r"(?P<head>(?:[A-Za-z_][A-Za-z0-9_:<>,~*&\[\]\s]+\s+)?[A-Za-z_~][A-Za-z0-9_:~]*)"
    r"\s*\((?P<params>[^;{}]*)\)\s*(?P<suffix>const\b|noexcept\b|override\b|final\b|->\s*[^;{]+|\s)*\s*(?:\{|;)$"
)
CONTROL_WORDS = {"if", "for", "while", "switch", "catch", "return", "requires"}


@dataclass
class CppObject:
    object_id: str
    source_family: str
    kind: str
    name: str
    repo_root: str
    path: str
    line: int
    end_line: int | None = None
    declaration: str | None = None
    namespace: str | None = None
    signature: str = ""
    statement: str = ""
    search_text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in path.parts)


def cpp_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in CPP_EXTENSIONS and not should_skip(path)
    )


def relpath(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def stable_slug(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return slug or "object"


def compact_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def preceding_comment(lines: list[str], index: int) -> str:
    comments: list[str] = []
    cursor = index - 1
    in_block = False
    while cursor >= 0:
        raw = lines[cursor].rstrip()
        stripped = raw.strip()
        if not stripped:
            if comments:
                break
            cursor -= 1
            continue
        if stripped.startswith("//"):
            comments.append(stripped.removeprefix("//").strip())
            cursor -= 1
            continue
        if stripped.endswith("*/") or in_block:
            in_block = True
            comments.append(re.sub(r"^\s*/?\*+/?", "", stripped).strip("*/ "))
            if stripped.startswith("/*") or stripped.startswith("/**"):
                break
            cursor -= 1
            continue
        break
    return compact_text(" ".join(reversed([item for item in comments if item])))


def namespace_stack_for_line(lines: list[str], target_index: int) -> list[str]:
    stack: list[tuple[str, int]] = []
    brace_depth = 0
    for index, line in enumerate(lines[:target_index]):
        namespace_match = NAMESPACE_RE.match(line)
        if namespace_match:
            stack.append((namespace_match.group("name"), brace_depth))
        brace_depth += line.count("{") - line.count("}")
        while stack and brace_depth <= stack[-1][1]:
            stack.pop()
    return [item[0] for item in stack]


def balanced_signature(lines: list[str], start: int) -> str:
    parts = []
    paren_depth = 0
    for line in lines[start : min(len(lines), start + 8)]:
        stripped = line.strip()
        parts.append(stripped)
        paren_depth += stripped.count("(") - stripped.count(")")
        if paren_depth <= 0 and (";" in stripped or "{" in stripped):
            break
    return compact_text(" ".join(parts))


def classify_function_name(signature: str) -> str | None:
    before_paren = signature.split("(", 1)[0].strip()
    if not before_paren:
        return None
    name = before_paren.split()[-1].strip("*&")
    terminal = name.split("::")[-1]
    if terminal in CONTROL_WORDS or not re.match(r"~?[A-Za-z_][A-Za-z0-9_]*$", terminal):
        return None
    return name


def index_cpp_file(path: Path, root: Path) -> list[CppObject]:
    text = read_text(path)
    lines = text.splitlines()
    objects: list[CppObject] = []
    for index, line in enumerate(lines):
        stripped_line = line.strip()
        if not stripped_line or stripped_line[0] in {"{", "}", ")", ";"}:
            continue
        namespace_match = NAMESPACE_RE.match(line)
        if namespace_match:
            name = namespace_match.group("name")
            declaration = "::".join(namespace_stack_for_line(lines, index) + [name])
            objects.append(
                make_object(
                    root,
                    path,
                    index,
                    "namespace",
                    name,
                    declaration,
                    line.strip(),
                    preceding_comment(lines, index),
                )
            )
            continue
        type_match = TYPE_RE.match(line)
        if type_match:
            kind = "enum" if type_match.group("kind").startswith("enum") else type_match.group("kind")
            name = type_match.group("name")
            declaration = "::".join(namespace_stack_for_line(lines, index) + [name])
            signature = balanced_signature(lines, index)
            objects.append(make_object(root, path, index, kind, name, declaration, signature, preceding_comment(lines, index)))
            continue
        signature = balanced_signature(lines, index)
        signature_for_match = re.sub(r"^\s*(?:\[\[[^\]]+\]\]\s*)+", "", signature)
        function_match = FUNCTION_RE.match(signature_for_match)
        if function_match:
            name = classify_function_name(signature_for_match)
            if not name:
                continue
            namespace = namespace_stack_for_line(lines, index)
            declaration = name if "::" in name else "::".join(namespace + [name])
            kind = "method" if "::" in name else "function"
            objects.append(make_object(root, path, index, kind, name.split("::")[-1], declaration, signature, preceding_comment(lines, index)))
    return objects


def make_object(root: Path, path: Path, index: int, kind: str, name: str, declaration: str, signature: str, comment: str) -> CppObject:
    relative = relpath(path, root)
    object_id = f"cpp:{stable_slug(str(root.name))}:{stable_slug(relative)}:{index + 1}:{stable_slug(declaration)}"
    namespace = "::".join(declaration.split("::")[:-1]) or None
    search_text = " ".join(item for item in [kind, name, declaration, signature, comment, relative] if item)
    return CppObject(
        object_id=object_id,
        source_family="cpp",
        kind=kind,
        name=name,
        repo_root=str(root.resolve()),
        path=relative,
        line=index + 1,
        declaration=declaration,
        namespace=namespace,
        signature=signature,
        statement=comment,
        search_text=search_text,
        metadata={"leading_comment": comment} if comment else {},
    )


def build_index(cpp_roots: list[Path]) -> dict[str, Any]:
    objects: list[dict[str, Any]] = []
    inputs = []
    file_count = 0
    for root in cpp_roots:
        root = root.resolve()
        inputs.append(str(root))
        files = cpp_files(root)
        file_count += len(files)
        for path in files:
            objects.extend(asdict(item) for item in index_cpp_file(path, root))
    objects.sort(key=lambda item: (str(item["repo_root"]), str(item["path"]), int(item["line"]), str(item["object_id"])))
    counts_by_kind: dict[str, int] = {}
    for item in objects:
        counts_by_kind[str(item["kind"])] = counts_by_kind.get(str(item["kind"]), 0) + 1
    return {
        "schema_version": "lra.cpp-object-index/1.0",
        "inputs": {"cpp_roots": inputs},
        "counts": {"objects": len(objects), "files": file_count, "by_kind": counts_by_kind},
        "objects": objects,
    }


def write_payload(payload: dict[str, Any], output: Path, fmt: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "json":
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    else:
        text = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    output.write_text(text, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpp-root", type=Path, action="append", default=[], help="C/C++ repo root to scan. May repeat.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--format", choices=["yaml", "json"], default="yaml")
    parser.add_argument("--sqlite-dir", type=Path, help="Directory for the C/C++ SQLite index. Defaults to <output-dir>/sqlite.")
    parser.add_argument("--no-sqlite", action="store_true", help="Do not build the SQLite index.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.cpp_root:
        raise SystemExit("at least one --cpp-root is required")
    payload = build_index(args.cpp_root)
    write_payload(payload, args.output, args.format)
    if not args.no_sqlite:
        sqlite_dir = args.sqlite_dir or args.output.parent / "sqlite"
        result = build_family_databases(
            payload["objects"], families=("cpp",), sqlite_dir=sqlite_dir, source_path=args.output
        )[0]
        print(f"cpp SQLite index written: objects={result['objects']} database={result['database']}")
    counts = payload["counts"]
    print(f"cpp object index written: objects={counts['objects']} files={counts['files']} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
