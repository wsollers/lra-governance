#!/usr/bin/env python3
"""Resolve (repository, task) to a bounded governance execution packet.

Initial context = ENTRYPOINT.md + exactly one repo overlay + the route's
``eager_instructions``. Lazy references, executable tools, schemas, and examples
are returned as pointers and are not emitted into context.

Routes are repo-kind scoped. If no explicit trigger matches, the one applicable
default route is selected.

Matching: the task string is matched against each applicable route's triggers,
whole-word, longest-trigger-wins. The verifier command(s) are bound by substituting
{root}/{chapter}/{canonical}/{target}.

Usage:
  python resolve.py --repo lra-volume-iii --task "append the lemma" --root . --chapter convergence
  python resolve.py --repo lra-lean --task "formalize addition is commutative" --root .
  python resolve.py --repo lra-volume-iii --task "stub a chapter" --emit   # print bundle content
"""
from __future__ import annotations
import argparse, json, re, sys
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

def _applicable(route: dict, kind: str, repo: str) -> bool:
    return kind in route.get("applies_to", ["volume"]) and (
        not route.get("repos") or repo in route["repos"]
    )


def _match(task: str, manifest: dict, kind: str, repo: str):
    t = task.lower()
    best = None; best_len = -1; ties = []
    routes = manifest["routes"]
    for cap in routes:
        if not _applicable(cap, kind, repo):
            continue
        for trig in [cap.get("title", ""), *cap.get("triggers", [])]:
            if re.search(r"(?<![\w-])" + re.escape(trig.strip().lower()) + r"(?![\w-])", t):
                if len(trig) > best_len:
                    best, best_len, ties = cap, len(trig), [cap["id"]]
                elif len(trig) == best_len and cap["id"] not in ties:
                    ties.append(cap["id"])
    if best is not None:
        return best, ties
    defaults = [route for route in routes if route.get("default") and _applicable(route, kind, repo)]
    if len(defaults) == 1:
        return defaults[0], [defaults[0]["id"]]
    return None, [route["id"] for route in defaults]

@dataclass
class Resolution:
    repo: str; task: str
    core: Path; overlay: Path; route_id: str
    eager_instructions: list = field(default_factory=list)
    lazy_references: list = field(default_factory=list)
    tools: list = field(default_factory=list)
    schemas: list = field(default_factory=list)
    examples: list = field(default_factory=list)
    outputs: list = field(default_factory=list)
    verify: list = field(default_factory=list)
    token_budget: int = 0

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
    cap, ties = _match(task, manifest, kind, repo)
    if cap is None:
        applicable = [c["id"] for c in manifest["routes"] if _applicable(c, kind, repo)]
        suffix = f" Ambiguous defaults: {ties}." if ties else ""
        raise ValueError(f"no route matches task {task!r} for repo kind {kind!r}. "
                         f"Routes here: {applicable or 'none defined yet'}.{suffix}")
    if len(ties) > 1:
        raise ValueError(f"ambiguous task {task!r} matches {ties}; be more specific.")
    sub = {"root": args.get("root") or "<root>", "chapter": args.get("chapter") or "<chapter>",
           "canonical": args.get("canonical") or "<canonical-dir>", "target": args.get("target") or "<file>"}
    verify = [v.format(**sub) for v in cap.get("verify", [])]
    eager = [gov / r for r in cap.get("eager_instructions", [])]
    return Resolution(
        repo=repo,
        task=task,
        core=core,
        overlay=overlay,
        route_id=cap["id"],
        eager_instructions=eager,
        lazy_references=cap.get("lazy_references", []),
        tools=cap.get("tools", []),
        schemas=cap.get("schemas", []),
        examples=cap.get("examples", []),
        outputs=cap.get("outputs", []),
        verify=verify,
        token_budget=int(cap.get("token_budget", manifest.get("default_token_budget", 0))),
    )


def _relative(path: Path, gov: Path) -> str:
    return path.relative_to(gov).as_posix()


def _as_dict(r: Resolution, gov: Path) -> dict:
    return {
        "repo": r.repo,
        "task": r.task,
        "route": r.route_id,
        "token_budget": r.token_budget,
        "eager_instructions": [_relative(r.core, gov), _relative(r.overlay, gov), *[_relative(p, gov) for p in r.eager_instructions]],
        "lazy_references": r.lazy_references,
        "tools": r.tools,
        "schemas": r.schemas,
        "examples": r.examples,
        "outputs": r.outputs,
        "verify": r.verify,
    }

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Resolve (repo, task) to a bounded governance packet.")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--gov-root", default=".")
    ap.add_argument("--root"); ap.add_argument("--chapter")
    ap.add_argument("--canonical"); ap.add_argument("--target")
    ap.add_argument("--emit", action="store_true", help="emit eager instruction content only")
    ap.add_argument("--json", action="store_true", help="print the resolution packet as JSON")
    a = ap.parse_args(argv)
    gov = _gov_root(Path(a.gov_root).resolve())
    if not gov:
        print("fatal: not inside an lra-governance tree (no capabilities/manifest.yaml found)", file=sys.stderr); return 1
    try:
        r = resolve(gov, a.repo, a.task, vars(a))
    except (FileNotFoundError, ValueError) as e:
        print(f"fatal: {e}", file=sys.stderr); return 1
    packet = _as_dict(r, gov)
    if a.json:
        print(json.dumps(packet, indent=2))
    else:
        print(f"repo:         {r.repo}")
        print(f"task:         {r.task!r}")
        print(f"route:        {r.route_id}")
        print(f"context budget: {r.token_budget} estimated governance tokens")
        print("\neager instructions (load in order):")
        for i, path in enumerate(packet["eager_instructions"], 1):
            print(f"  {i}. {path}")
        for heading, values in (
            ("lazy references (open only for a concrete question)", r.lazy_references),
            ("executable tools (run; do not preload source)", r.tools),
            ("schemas/data (query or validate; do not preload)", r.schemas),
            ("examples (inspect one relevant example)", r.examples),
            ("outputs", r.outputs),
            ("verification", r.verify),
        ):
            print(f"\n{heading}:")
            for value in values:
                prefix = "$ " if heading == "verification" else ""
                print(f"  - {prefix}{value}")
    if a.emit:
        print("\n" + "="*60 + " EAGER CONTEXT " + "="*60)
        for p in [r.core, r.overlay, *r.eager_instructions]:
            print(f"\n----- {_relative(p, gov)} -----\n{p.read_text(encoding='utf-8')}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
