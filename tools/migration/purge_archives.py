#!/usr/bin/env python3
"""Recursively find and purge `archive/` directories under a root.

Dry-run by default: prints a manifest (path, file count, total bytes) of every
archive dir that WOULD be deleted. Pass --apply to actually delete (shutil.rmtree).

Safety:
  * --root is required; the tool only deletes directories literally named
    'archive' (override with --name) found beneath it -- never the root itself.
  * docs/archive directories are SKIPPED by default (they are a documented
    convention with READMEs); pass --include-docs to purge them too.
  * .git is never traversed. Nested archives inside an archive are not double
    counted (the whole tree is removed once).
  * These are git-tracked repos: a purge of the working tree remains recoverable
    from git history until you commit and garbage-collect.
"""
from __future__ import annotations
import argparse, os, shutil
from pathlib import Path

def human(n: int) -> str:
    f = float(n)
    for u in ("B", "KB", "MB", "GB", "TB"):
        if f < 1024 or u == "TB":
            return f"{f:.0f}{u}" if u == "B" else f"{f:.1f}{u}"
        f /= 1024

def dir_stats(path: Path):
    files = total = 0
    for dp, _, fns in os.walk(path):
        for fn in fns:
            try:
                total += (Path(dp) / fn).stat().st_size
                files += 1
            except OSError:
                pass
    return files, total

def find_archives(root: Path, name: str, include_docs: bool, excludes: tuple[str, ...]):
    found = []
    for dirpath, dirnames, _ in os.walk(root, topdown=True):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        keep = []
        for d in dirnames:
            p = Path(dirpath) / d
            is_archive = (d == name)
            skip_docs = (not include_docs and Path(dirpath).name == "docs")
            excluded = any(x in p.as_posix() for x in excludes)
            if is_archive and not skip_docs and not excluded:
                found.append(p)          # prune: don't descend into a doomed tree
            else:
                keep.append(d)
        dirnames[:] = keep
    return sorted(set(found))

def main():
    ap = argparse.ArgumentParser(description="Find and purge archive/ directories.")
    ap.add_argument("--root", required=True)
    ap.add_argument("--name", default="archive", help="Directory name to purge (default: archive).")
    ap.add_argument("--include-docs", action="store_true", help="Also purge docs/archive (skipped by default).")
    ap.add_argument("--exclude", action="append", default=[], help="Substring(s) of paths to skip (repeatable).")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    archives = find_archives(root, a.name, a.include_docs, tuple(a.exclude))
    if not archives:
        print(f"No '{a.name}' directories under {root}"); return
    grand_files = grand_bytes = 0
    print(f"root: {root}\n")
    for p in archives:
        files, total = dir_stats(p)
        grand_files += files; grand_bytes += total
        verb = "DELETE" if a.apply else "WOULD DELETE"
        print(f"  {verb}  {p.relative_to(root).as_posix()}   ({files} files, {human(total)})")
        if a.apply:
            shutil.rmtree(p)
    print(f"\n{'PURGED' if a.apply else 'DRY-RUN'}: {len(archives)} archive dir(s), "
          f"{grand_files} files, {human(grand_bytes)} total"
          + ("" if a.apply else "  -- re-run with --apply to delete"))

if __name__ == "__main__":
    raise SystemExit(main())
