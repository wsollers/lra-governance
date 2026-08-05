#!/usr/bin/env python3
"""Install VS Code devcontainer shims for LRA volume repositories."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def governance_root() -> Path:
    env = os.environ.get("LRA_GOVERNANCE_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


def common_root(gov_root: Path, explicit: Path | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(explicit)
    env = os.environ.get("LRA_COMMON_ROOT")
    if env:
        candidates.append(Path(env))
    candidates.append(gov_root.parent / "lra-common")

    for candidate in candidates:
        resolved = candidate.expanduser().resolve(strict=False)
        if (resolved / "common" / "volume-preamble.tex").exists():
            return resolved
    raise SystemExit(
        "lra-common checkout not found. Pass --common-root, set LRA_COMMON_ROOT, "
        "or place lra-common next to lra-governance."
    )


def is_volume_repo(path: Path) -> bool:
    return path.is_dir() and path.name.startswith("lra-volume-") and any(path.glob("volume-*.tex"))


def rel_for_json(target: Path, base: Path) -> str:
    try:
        rel = target.resolve().relative_to(base.resolve())
    except ValueError:
        rel = Path(os.path.relpath(target.resolve(), base.resolve()))
    return rel.as_posix()


def load_template(name: str, gov_root: Path) -> str:
    path = gov_root / "templates" / "devcontainer" / "lra-volume" / name
    return path.read_text(encoding="utf-8")


def render_devcontainer(volume_root: Path, gov_root: Path, common: Path) -> str:
    dev_dir = volume_root / ".devcontainer"
    dockerfile = gov_root / "docker" / "lra-tex-dev" / "Dockerfile"
    context = dockerfile.parent
    text = load_template("devcontainer.json", gov_root)
    replacements = {
        "__LRA_TEX_DOCKERFILE__": rel_for_json(dockerfile, dev_dir),
        "__LRA_TEX_CONTEXT__": rel_for_json(context, dev_dir),
        "__LRA_GOVERNANCE_ROOT__": gov_root.as_posix(),
        "__LRA_COMMON_ROOT__": common.as_posix(),
    }
    for key, value in replacements.items():
        text = text.replace(key, value)
    json.loads(text)
    return text


def render_tasks(volume_root: Path, gov_root: Path) -> str:
    text = load_template("tasks.json", gov_root)
    roots = sorted(path.name for path in volume_root.glob("volume-*.tex"))
    if roots:
        text = text.replace("volume-iii.tex", roots[0])
    json.loads(text)
    return text


def write_if_changed(path: Path, content: str, write: bool) -> str:
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old == content:
        return "unchanged"
    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        return "updated" if old is not None else "created"
    return "would_update" if old is not None else "would_create"


def install(volume_root: Path, gov_root: Path, common: Path, write: bool) -> list[tuple[Path, str]]:
    if not is_volume_repo(volume_root):
        raise SystemExit(f"not an lra-volume repository root: {volume_root}")
    dev_dir = volume_root / ".devcontainer"
    return [
        (dev_dir / "devcontainer.json", write_if_changed(dev_dir / "devcontainer.json", render_devcontainer(volume_root, gov_root, common), write)),
        (dev_dir / "tasks.json", write_if_changed(dev_dir / "tasks.json", render_tasks(volume_root, gov_root), write)),
    ]


def volume_roots(args: argparse.Namespace) -> list[Path]:
    roots: list[Path] = []
    if args.root:
        roots.extend(path.expanduser().resolve() for path in args.root)
    if args.all_sibling_volumes:
        workspace = args.workspace.expanduser().resolve()
        roots.extend(path.resolve() for path in workspace.glob("lra-volume-*") if is_volume_repo(path))
    unique: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        if root not in seen:
            unique.append(root)
            seen.add(root)
    if not unique:
        raise SystemExit("no target volume repositories selected")
    return unique


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, action="append", help="target lra-volume-* repository root; repeatable")
    parser.add_argument("--workspace", type=Path, default=Path.cwd().parent, help="workspace containing sibling lra-volume-* repos")
    parser.add_argument("--all-sibling-volumes", action="store_true", help="install into every lra-volume-* repo under --workspace")
    parser.add_argument("--common-root", type=Path, help="lra-common checkout root")
    parser.add_argument("--write", action="store_true", help="write files; default is dry-run")
    args = parser.parse_args(argv)

    gov_root = governance_root()
    common = common_root(gov_root, args.common_root)
    for root in volume_roots(args):
        for path, status in install(root, gov_root, common, args.write):
            print(f"{status}: {path}")
    if not args.write:
        print("dry-run only; pass --write to create or update files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
