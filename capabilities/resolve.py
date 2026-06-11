#!/usr/bin/env python3
"""(repo, task) resolver -- composes "you are in lra-X, do Y" into a runnable bundle.

Resolution = global core (ENTRYPOINT.md) + exactly one repo overlay (overlays/<repo>.md)
            + exactly one capability (matched from manifest.yaml) + its bound verifier(s).

Capabilities are repo-KIND scoped: the resolver maps repo -> kind via overlays-config.yaml
and only matches capabilities whose `applies_to` includes that kind. So a volume LaTeX
capability will not resolve in a lean/cpp repo, and vice versa.

Matching: the task string is matched against each applicable capability's triggers,
whole-word, longest-trigger-wins. The verifier command(s) are bound by substituting
{root}/{chapter}/{canonical}/{target}.

Usage:
  python resolve.py --repo lra-volume-iii --task "append the lemma" --root . --chapter convergence
  python resolve.py --repo lra-lean --task "formalize addition is commutative" --root .
  python resolve.py --repo lra-volume-iii --task "stub a chapter" --emit   # print bundle content
"""
from __future__ import annotations
import argparse, re, sys
from dataclasses import dataclass, field
from pathlib import Path

def _gov_root(start: Path):
    for up in [start, *start.parents]:
        if (up / "capabilities" / "manifest.yaml").exists():
            return up
    return None

def _load_manifest(gov: Path) -> dict:
    import yaml
    return yaml.safe_load((gov / "capabilities" / "manifest.yaml").read_text(encoding="utf-8"))

def _repo_kind(gov: Path, repo: str) -> str:
    import yaml
    cfg_path = gov / "capabilities" / "overlays-config.yaml"
    if cfg_path.exists():
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        for r in cfg.get("repos", []):
            if r.get("repo") == repo:
                return r.get("kind", "volume")
    return "volume"  # default

def _match(task: str, manifest: dict, kind: str):
    t = task.lower()
    best = None; best_len = -1; ties = []
    for cap in manifest["capabilities"]:
        if kind not in cap.get("applies_to", ["volume"]):
            continue
        for trig in cap["triggers"]:
            if re.search(r"(?<![\w-])" + re.escape(trig.strip().lower()) + r"(?![\w-])", t):
                if len(trig) > best_len:
                    best, best_len, ties = cap, len(trig), [cap["id"]]
                elif len(trig) == best_len and cap["id"] not in ties:
                    ties.append(cap["id"])
    return best, ties

@dataclass
class Resolution:
    repo: str; task: str
    core: Path; overlay: Path; capability_id: str
    reads: list = field(default_factory=list)
    verify: list = field(default_factory=list)

def resolve(gov: Path, repo: str, task: str, args: dict) -> Resolution:
    core = gov / "capabilities" / "ENTRYPOINT.md"
    if not core.exists():
        raise FileNotFoundError("missing capabilities/ENTRYPOINT.md (global core)")
    overlay = gov / "capabilities" / "overlays" / f"{repo}.md"
    if not overlay.exists():
        raise FileNotFoundError(
            f"no overlay for repo '{repo}' (expected capabilities/overlays/{repo}.md). "
            f"Create it or run generate_overlays.py.")
    manifest = _load_manifest(gov)
    kind = _repo_kind(gov, repo)
    cap, ties = _match(task, manifest, kind)
    if cap is None:
        applicable = [c["id"] for c in manifest["capabilities"] if kind in c.get("applies_to", ["volume"])]
        raise ValueError(f"no capability matches task {task!r} for repo kind {kind!r}. "
                         f"Capabilities here: {applicable or 'none defined yet'}")
    if len(ties) > 1:
        raise ValueError(f"ambiguous task {task!r} matches {ties}; be more specific.")
    sub = {"root": args.get("root") or "<root>", "chapter": args.get("chapter") or "<chapter>",
           "canonical": args.get("canonical") or "<canonical-dir>", "target": args.get("target") or "<file>"}
    verify = [v.format(**sub) for v in cap["verify"]]
    reads = [gov / r for r in cap["reads"]]
    return Resolution(repo, task, core, overlay, cap["id"], reads, verify)

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Resolve (repo, task) -> capability bundle + verifier.")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--gov-root", default=".")
    ap.add_argument("--root"); ap.add_argument("--chapter")
    ap.add_argument("--canonical"); ap.add_argument("--target")
    ap.add_argument("--emit", action="store_true", help="print concatenated bundle content")
    a = ap.parse_args(argv)
    gov = _gov_root(Path(a.gov_root).resolve())
    if not gov:
        print("fatal: not inside an lra-governance tree (no capabilities/manifest.yaml found)", file=sys.stderr); return 1
    try:
        r = resolve(gov, a.repo, a.task, vars(a))
    except (FileNotFoundError, ValueError) as e:
        print(f"fatal: {e}", file=sys.stderr); return 1
    print(f"repo:       {r.repo}")
    print(f"task:       {r.task!r}")
    print(f"capability: {r.capability_id}")
    print(f"\nload, in order:")
    print(f"  1. core    {r.core.relative_to(gov)}")
    print(f"  2. overlay {r.overlay.relative_to(gov)}")
    for i, rd in enumerate(r.reads, 3):
        print(f"  {i}. cap     {rd.relative_to(gov)}")
    print(f"\nbound verifier (must exit 0):")
    for v in r.verify:
        print(f"  $ {v}")
    if a.emit:
        print("\n" + "="*60 + " BUNDLE " + "="*60)
        for p in [r.core, r.overlay, *r.reads]:
            if p.suffix == ".md" and p.exists():
                print(f"\n----- {p.relative_to(gov)} -----\n{p.read_text(encoding='utf-8')}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
