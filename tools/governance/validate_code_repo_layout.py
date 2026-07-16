#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


IGNORED_DIRS = {
    ".git",
    ".github",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "cmake-build-debug",
    "cmake-build-release",
    "dist",
    "htmlcov",
}


def _load_config(governance_root: Path) -> dict[str, dict[str, Any]]:
    import yaml

    cfg = governance_root / "capabilities" / "overlays-config.yaml"
    data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
    return {entry["repo"]: entry for entry in data.get("repos", []) if entry.get("repo")}


def _matches_pattern(path: Path, pattern: str) -> bool:
    parts = path.parts
    pat = Path(pattern).parts
    if len(parts) != len(pat):
        return False
    return all(token == "*" or token == part for token, part in zip(pat, parts))


def _exists_pattern(root: Path, pattern: str) -> bool:
    if "*" not in pattern:
        return (root / pattern).exists()
    return any(_matches_pattern(path.relative_to(root), pattern) for path in root.rglob("*") if path.is_dir())


def _under_declared(path: Path, roots: list[str]) -> bool:
    rel = path.parts
    for root in roots:
        pat = Path(root).parts
        if "*" in pat:
            if len(rel) >= len(pat) and all(token == "*" or token == part for token, part in zip(pat, rel)):
                return True
            continue
        root_parts = Path(root).parts
        if rel[: len(root_parts)] == root_parts:
            return True
    return False


def _walk_files(root: Path, suffixes: tuple[str, ...]) -> list[Path]:
    found: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in suffixes:
            continue
        rel = path.relative_to(root)
        if any(part in IGNORED_DIRS for part in rel.parts):
            continue
        found.append(rel)
    return found


def validate_python(root: Path, layout: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    code_roots = list(layout.get("code_roots") or ["src", "tools"])
    test_roots = list(layout.get("test_roots") or ["tests"])

    if not any((root / item).is_dir() for item in code_roots):
        errors.append(f"missing Python code root; expected one of: {', '.join(code_roots)}")
    if not any(_exists_pattern(root, item) for item in test_roots):
        errors.append(f"missing Python test root; expected one of: {', '.join(test_roots)}")

    allowed = [*code_roots, *test_roots]
    for rel in _walk_files(root, (".py",)):
        if rel.name.startswith("test_") and _under_declared(rel, test_roots):
            continue
        if _under_declared(rel, allowed):
            continue
        errors.append(f"Python file outside declared roots: {rel}")
    return errors


def validate_cpp(root: Path, layout: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required_dirs = list(layout.get("required_dirs") or ["cmake", "tools"])
    code_roots = list(layout.get("code_roots") or ["src", "include", "projects"])
    test_roots = list(layout.get("test_roots") or ["tests", "projects/*/tests"])

    if not (root / "CMakeLists.txt").is_file():
        errors.append("missing CMakeLists.txt")
    for item in required_dirs:
        if not (root / item).is_dir():
            errors.append(f"missing required directory: {item}")
    if not any((root / item).is_dir() for item in code_roots if "*" not in item):
        errors.append(f"missing C++ code root; expected one of: {', '.join(code_roots)}")
    if not any(_exists_pattern(root, item) for item in test_roots):
        errors.append(f"missing C++ test root; expected one of: {', '.join(test_roots)}")

    allowed = [*code_roots, *test_roots]
    for rel in _walk_files(root, (".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx", ".ixx")):
        if _under_declared(rel, allowed):
            continue
        errors.append(f"C/C++ file outside declared roots: {rel}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate specialist code repository layout.")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--governance-root", type=Path, default=Path("."))
    args = parser.parse_args(argv)

    root = args.root.resolve()
    governance_root = args.governance_root.resolve()
    config = _load_config(governance_root)
    entry = config.get(args.repo)
    if not entry:
        print(f"fatal: repo not listed in overlays config: {args.repo}", file=sys.stderr)
        return 2
    layout = entry.get("layout") or {}
    language = layout.get("language")
    if language == "python":
        errors = validate_python(root, layout)
    elif language == "cpp":
        errors = validate_cpp(root, layout)
    else:
        print(f"fatal: no code layout configured for repo {args.repo!r}", file=sys.stderr)
        return 2

    if errors:
        for error in errors:
            print(f"layout error: {error}", file=sys.stderr)
        return 1
    print(f"code layout valid: {args.repo} ({language})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
