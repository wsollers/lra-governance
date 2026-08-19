#!/usr/bin/env python3
"""Resolve a repository/task pair to a bounded governance execution packet.

The manifest is the routing authority. The resolver selects one applicable
route, binds its verification commands, validates every local resource, and
returns an explainable packet. Only the entrypoint, one repository overlay, and
the route's eager instructions belong in the initial context.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import string
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


TOKEN_ESTIMATOR = "unicode_chars_div_4_ceil"
ALLOWED_VERIFY_FIELDS = {"root", "chapter", "canonical", "target"}
EXECUTABLE_VERIFY_RE = re.compile(
    r"^(?:python|py|docker|git|lake|latexmk|cmake)(?:\s|$)|^[.]?[\\/]",
    re.IGNORECASE,
)
RESOURCE_FIELDS = (
    "eager_instructions",
    "lazy_references",
    "tools",
    "schemas",
    "examples",
)
POINTER_PREFIXES = ("external:", "nearby:")


def estimate_tokens(text: str) -> int:
    """Return the stable estimator used by governance context budgets."""
    return math.ceil(len(text) / 4)


def _has_manifest(path: Path) -> bool:
    return (path / "capabilities" / "manifest.yaml").is_file()


def _gov_root(start: Path) -> Path | None:
    """Search *start* and its parents for the canonical manifest."""
    start = start.expanduser().resolve()
    if start.is_file():
        start = start.parent
    for candidate in (start, *start.parents):
        if _has_manifest(candidate):
            return candidate
    return None


def _discover_gov_root(
    explicit: str | None = None,
    repo_root: str | None = None,
) -> Path | None:
    """Resolve governance using explicit, environment, script, and checkout roots."""
    if explicit:
        return _gov_root(Path(explicit))

    candidates: list[Path] = []
    configured = os.environ.get("LRA_GOVERNANCE_ROOT")
    if configured:
        candidates.append(Path(configured))

    # Invoking the resolver through a sibling governance checkout should work
    # regardless of the caller's current working directory.
    candidates.append(Path(__file__).resolve().parent)
    if repo_root:
        root = Path(repo_root).expanduser().resolve()
        candidates.extend((root, root.parent / "lra-governance"))
    cwd = Path.cwd().resolve()
    candidates.extend((cwd, cwd.parent / "lra-governance"))

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        found = _gov_root(resolved)
        if found:
            return found
    return None


def _load_yaml_unique(path: Path) -> dict[str, Any]:
    """Load YAML safely while rejecting duplicate mapping keys."""
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - exercised by bootstrap failures
        raise ValueError(
            "PyYAML is required; run scripts/bootstrap_python.py and use .venv Python"
        ) from exc

    class UniqueKeyLoader(yaml.SafeLoader):
        pass

    def construct_mapping(loader, node, deep=False):
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in mapping:
                mark = key_node.start_mark
                raise ValueError(
                    f"{path}:{mark.line + 1}: duplicate YAML key {key!r}"
                )
            mapping[key] = loader.construct_object(value_node, deep=deep)
        return mapping

    UniqueKeyLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping,
    )
    try:
        result = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"failed to parse {path}: {exc}") from exc
    if not isinstance(result, dict):
        raise ValueError(f"{path} must contain a YAML mapping at the document root")
    return result


def _validate_json(instance: dict[str, Any], schema_path: Path, label: str) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:  # pragma: no cover - exercised by bootstrap failures
        raise ValueError(
            "jsonschema is required; run scripts/bootstrap_python.py and use .venv Python"
        ) from exc

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if not errors:
        return
    rendered = []
    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        rendered.append(f"{location}: {error.message}")
    raise ValueError(f"invalid {label}: " + "; ".join(rendered))


def _is_pointer(value: str) -> bool:
    return (
        value.startswith(POINTER_PREFIXES)
        or (":" in value and not Path(value).suffix)
        or ("/" not in value and "\\" not in value and not Path(value).suffix)
    )


def _local_path(gov: Path, value: str) -> Path:
    path = (gov / value).resolve()
    try:
        path.relative_to(gov.resolve())
    except ValueError as exc:
        raise ValueError(f"local governance path escapes the repository: {value}") from exc
    return path


def _validate_verify_template(route_id: str, value: str) -> None:
    fields = {
        field_name
        for _, field_name, _, _ in string.Formatter().parse(value)
        if field_name
    }
    unknown = sorted(fields - ALLOWED_VERIFY_FIELDS)
    if unknown:
        raise ValueError(
            f"{route_id}: unsupported verification placeholders {unknown}; "
            f"allowed: {sorted(ALLOWED_VERIFY_FIELDS)}"
        )


def _validate_executable_verify(route_id: str, value: str) -> None:
    _validate_verify_template(route_id, value)
    if not EXECUTABLE_VERIFY_RE.match(value.strip()):
        raise ValueError(
            f"{route_id}: verification must be an executable command, got {value!r}"
        )


def _validate_manifest_semantics(gov: Path, manifest: dict[str, Any]) -> None:
    routes = manifest["routes"]
    ids = [route["id"] for route in routes]
    duplicates = sorted({route_id for route_id in ids if ids.count(route_id) > 1})
    if duplicates:
        raise ValueError(f"duplicate route ids: {duplicates}")

    trigger_owners: dict[str, list[str]] = {}
    for route in routes:
        for trigger in [route["title"], *route.get("triggers", [])]:
            normalized = str(trigger).strip().lower()
            trigger_owners.setdefault(normalized, []).append(route["id"])
    duplicate_triggers = {
        trigger: sorted(set(owners))
        for trigger, owners in trigger_owners.items()
        if len(set(owners)) > 1
    }
    if duplicate_triggers:
        raise ValueError(f"duplicate route triggers: {duplicate_triggers}")

    entrypoint = _local_path(gov, manifest["entrypoint"])
    if not entrypoint.is_file():
        raise ValueError(f"manifest entrypoint does not exist: {manifest['entrypoint']}")

    local_resources: list[tuple[str, str, str]] = []
    for route in routes:
        route_id = route["id"]
        for verify in route.get("verify", []):
            _validate_verify_template(route_id, verify)
        for field_name in RESOURCE_FIELDS:
            for raw in route.get(field_name, []):
                value = str(raw)
                if not _is_pointer(value):
                    local_resources.append((route_id, field_name, value))

        eager = set(map(str, route.get("eager_instructions", [])))
        pointers = set(map(str, route.get("lazy_references", [])))
        pointers.update(map(str, route.get("tools", [])))
        pointers.update(map(str, route.get("schemas", [])))
        overlap = sorted(eager & pointers)
        if overlap:
            raise ValueError(
                f"{route_id}: resources classified as eager and non-eager: {overlap}"
            )
        for value in eager:
            if Path(value).suffix.lower() not in {".md", ".txt"}:
                raise ValueError(
                    f"{route_id}: eager instruction is not text guidance: {value}"
                )

    for prompt_route in manifest.get("prompt_routes", []):
        owner = str(prompt_route["title"])
        for verify in prompt_route.get("verify", []):
            _validate_executable_verify(owner, str(verify))
        local_resources.append(
            (owner, "prompt", str(prompt_route["prompt"]))
        )
        for raw in prompt_route.get("schemas", []):
            value = str(raw)
            if not _is_pointer(value):
                local_resources.append((owner, "schemas", value))

    for owner, field_name, value in local_resources:
        if not _local_path(gov, value).exists():
            raise ValueError(f"{owner}: missing {field_name} path {value}")

    overlay_config = _load_yaml_unique(gov / "capabilities" / "overlays-config.yaml")
    for record in overlay_config.get("repos", []):
        repo = str(record.get("repo"))
        kind = str(record.get("kind", "volume"))
        defaults = [
            route["id"]
            for route in routes
            if route.get("default") and _applicable(route, kind, repo)
        ]
        if len(defaults) > 1:
            raise ValueError(f"{repo}: multiple applicable default routes {defaults}")


def _load_manifest(gov: Path) -> dict[str, Any]:
    manifest = _load_yaml_unique(gov / "capabilities" / "manifest.yaml")
    _validate_json(
        manifest,
        gov / "constitution" / "schemas" / "capability-manifest.schema.json",
        "capability manifest",
    )
    _validate_manifest_semantics(gov, manifest)
    return manifest


def _repo_record(gov: Path, repo: str) -> dict[str, Any]:
    config = _load_yaml_unique(gov / "capabilities" / "overlays-config.yaml")
    matches = [record for record in config.get("repos", []) if record.get("repo") == repo]
    if not matches:
        known = sorted(str(record.get("repo")) for record in config.get("repos", []))
        raise ValueError(f"unknown repository {repo!r}; registered repositories: {known}")
    if len(matches) > 1:
        raise ValueError(f"duplicate overlay configuration for repository {repo!r}")
    return matches[0]


def _canonical_repo_name(gov: Path, repo: str, root: str | None = None) -> str:
    """Return the registered name denoted by a name or repository-root path."""
    config = _load_yaml_unique(gov / "capabilities" / "overlays-config.yaml")
    registered = [str(record.get("repo")) for record in config.get("repos", [])]
    by_casefold = {name.casefold(): name for name in registered}

    raw = str(repo).strip()
    candidates = [raw]

    # Recognize either platform's separators so a Windows repository path has
    # stable behavior even when resolution is exercised in a Linux container.
    trimmed = raw.rstrip("/\\")
    if trimmed:
        candidates.append(re.split(r"[/\\]+", trimmed)[-1])

    try:
        candidates.append(Path(raw).expanduser().resolve().name)
    except (OSError, RuntimeError):
        pass

    # ``--repo . --root <repo-root>`` is a useful invocation from wrappers that
    # already know the target root but do not carry a separate repository name.
    if raw in {".", "./", ".\\"} and root:
        root_trimmed = str(root).strip().rstrip("/\\")
        if root_trimmed:
            candidates.append(re.split(r"[/\\]+", root_trimmed)[-1])

    for candidate in candidates:
        canonical = by_casefold.get(candidate.casefold())
        if canonical is not None:
            return canonical

    known = sorted(registered)
    raise ValueError(f"unknown repository {repo!r}; registered repositories: {known}")


def _repo_kind(gov: Path, repo: str) -> str:
    return str(_repo_record(gov, repo).get("kind", "volume"))


def _applicable(route: dict[str, Any], kind: str, repo: str) -> bool:
    return kind in route.get("applies_to", ["volume"]) and (
        not route.get("repos") or repo in route["repos"]
    )


@dataclass(frozen=True)
class Match:
    route: dict[str, Any]
    match_type: str
    matched_trigger: str | None


class RouteSelectionNeeded(Exception):
    """Deterministic matching could not pick one route; the caller must choose.

    Raised instead of a fatal error so an LLM agent can read the candidate
    catalog, pick the route whose description matches the task's intent, and
    re-resolve with ``--route <id>``.
    """

    def __init__(self, reason: str, candidates: list[dict[str, Any]]):
        super().__init__(reason)
        self.reason = reason
        self.candidates = candidates


def _catalog(manifest: dict[str, Any], kind: str, repo: str) -> list[dict[str, Any]]:
    """Return the routes applicable to (kind, repo) for selection displays."""
    return [
        route for route in manifest["routes"] if _applicable(route, kind, repo)
    ]


def _catalog_entries(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": route["id"],
            "title": str(route.get("title", "")),
            "description": str(route.get("description", "")),
            "example_triggers": [str(t) for t in route.get("triggers", [])[:3]],
            "default": bool(route.get("default", False)),
        }
        for route in routes
    ]


def _explicit_route(
    route_id: str, manifest: dict[str, Any], kind: str, repo: str
) -> Match:
    by_id = {route["id"]: route for route in manifest["routes"]}
    route = by_id.get(route_id)
    if route is None:
        known = sorted(by_id)
        raise ValueError(f"unknown route {route_id!r}; routes: {known}")
    if not _applicable(route, kind, repo):
        applicable = [r["id"] for r in _catalog(manifest, kind, repo)]
        raise ValueError(
            f"route {route_id!r} does not apply to repo {repo!r} "
            f"(kind {kind!r}); applicable routes: {applicable}"
        )
    return Match(route, "explicit", None)


def _match(task: str, manifest: dict[str, Any], kind: str, repo: str) -> Match:
    lowered = task.lower()
    best: dict[str, Any] | None = None
    best_trigger: str | None = None
    best_len = -1
    ties: list[str] = []

    routes = manifest["routes"]
    for route in routes:
        if not _applicable(route, kind, repo):
            continue
        candidates = [route.get("title", ""), *route.get("triggers", [])]
        for trigger in candidates:
            normalized = str(trigger).strip().lower()
            if not normalized:
                continue
            pattern = r"(?<![\w-])" + re.escape(normalized) + r"(?![\w-])"
            if not re.search(pattern, lowered):
                continue
            if len(normalized) > best_len:
                best = route
                best_trigger = str(trigger)
                best_len = len(normalized)
                ties = [route["id"]]
            elif len(normalized) == best_len and route["id"] not in ties:
                ties.append(route["id"])

    if best is not None:
        if len(ties) > 1:
            tied = [route for route in routes if route["id"] in ties]
            raise RouteSelectionNeeded(
                f"task {task!r} matches routes {ties} equally", tied
            )
        return Match(best, "trigger", best_trigger)

    defaults = [
        route
        for route in routes
        if route.get("default") and _applicable(route, kind, repo)
    ]
    if len(defaults) == 1:
        return Match(defaults[0], "default", None)
    if len(defaults) > 1:
        raise RouteSelectionNeeded(
            f"multiple default routes apply to repo {repo!r}", defaults
        )
    applicable = _catalog(manifest, kind, repo)
    if not applicable:
        raise ValueError(
            f"no routes are defined for repo kind {kind!r}; "
            "add a route to capabilities/manifest.yaml"
        )
    raise RouteSelectionNeeded(
        f"no trigger matched task {task!r} for repo kind {kind!r} "
        "and no default route applies",
        applicable,
    )


@dataclass
class Resolution:
    repo: str
    repo_kind: str
    task: str
    gov_root: Path
    core: Path
    overlay: Path
    route_id: str
    description: str
    match_type: str
    matched_trigger: str | None
    manifest_version: int
    packet_version: int
    token_estimator: str
    eager_instructions: list[Path] = field(default_factory=list)
    lazy_references: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    schemas: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    verify: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    estimated_tokens: int = 0
    token_budget: int = 0


def resolve(gov: Path, repo: str, task: str, args: dict[str, Any]) -> Resolution:
    gov = gov.expanduser().resolve()
    repo = _canonical_repo_name(gov, repo, args.get("root"))
    manifest = _load_manifest(gov)
    entrypoint_value = args.get("entrypoint") or manifest["entrypoint"]
    core = _local_path(gov, str(entrypoint_value))
    if not core.is_file():
        raise FileNotFoundError(f"missing entrypoint {entrypoint_value}")

    kind = _repo_kind(gov, repo)
    overlay = gov / "capabilities" / "overlays" / f"{repo}.md"
    if not overlay.is_file():
        raise FileNotFoundError(
            f"no overlay for repo {repo!r} "
            f"(expected capabilities/overlays/{repo}.md); "
            "create it or run generate_overlays.py"
        )

    explicit = args.get("route")
    if explicit:
        match = _explicit_route(str(explicit), manifest, kind, repo)
    else:
        match = _match(task, manifest, kind, repo)
    route = match.route
    substitutions = {
        "root": args.get("root") or "<root>",
        "chapter": args.get("chapter") or "<chapter>",
        "canonical": args.get("canonical") or "<canonical-dir>",
        "target": args.get("target") or "<file>",
    }
    verify = [value.format(**substitutions) for value in route.get("verify", [])]
    eager = [_local_path(gov, str(value)) for value in route["eager_instructions"]]
    for path in eager:
        if not path.is_file():
            raise FileNotFoundError(f"missing eager instruction {path}")

    budget = int(route.get("token_budget", manifest["default_token_budget"]))
    eager_paths = [core, overlay, *eager]
    estimated = sum(estimate_tokens(path.read_text(encoding="utf-8")) for path in eager_paths)
    if estimated > budget:
        raise ValueError(
            f"{route['id']} eager packet is {estimated} estimated tokens, "
            f"exceeding budget {budget}"
        )

    warnings: list[str] = []
    if match.match_type == "default":
        warnings.append(
            f"no trigger matched; resolved to the default route {route['id']!r}. "
            "If another applicable route's description fits the task better, "
            "re-run with --route <id> (use --list to compare descriptions)."
        )

    return Resolution(
        repo=repo,
        repo_kind=kind,
        task=task,
        gov_root=gov,
        core=core,
        overlay=overlay,
        route_id=route["id"],
        description=str(route.get("description", "")),
        match_type=match.match_type,
        matched_trigger=match.matched_trigger,
        manifest_version=int(manifest["version"]),
        packet_version=int(manifest["packet_version"]),
        token_estimator=str(manifest["token_estimator"]),
        eager_instructions=eager,
        lazy_references=list(route.get("lazy_references", [])),
        tools=list(route.get("tools", [])),
        schemas=list(route.get("schemas", [])),
        examples=list(route.get("examples", [])),
        outputs=list(route.get("outputs", [])),
        verify=verify,
        warnings=warnings,
        estimated_tokens=estimated,
        token_budget=budget,
    )


def _relative(path: Path, gov: Path) -> str:
    return path.relative_to(gov).as_posix()


def _as_dict(resolution: Resolution, gov: Path) -> dict[str, Any]:
    packet = {
        "packet_version": resolution.packet_version,
        "manifest_version": resolution.manifest_version,
        "repo": resolution.repo,
        "repo_kind": resolution.repo_kind,
        "task": resolution.task,
        "route": resolution.route_id,
        "description": resolution.description,
        "match_type": resolution.match_type,
        "matched_trigger": resolution.matched_trigger,
        "governance_root": resolution.gov_root.as_posix(),
        "entrypoint": _relative(resolution.core, gov),
        "token_estimator": resolution.token_estimator,
        "estimated_tokens": resolution.estimated_tokens,
        "token_budget": resolution.token_budget,
        "headroom": resolution.token_budget - resolution.estimated_tokens,
        "eager_instructions": [
            _relative(resolution.core, gov),
            _relative(resolution.overlay, gov),
            *[_relative(path, gov) for path in resolution.eager_instructions],
        ],
        "lazy_references": resolution.lazy_references,
        "tools": resolution.tools,
        "schemas": resolution.schemas,
        "examples": resolution.examples,
        "outputs": resolution.outputs,
        "verify": resolution.verify,
        "warnings": resolution.warnings,
    }
    _validate_json(
        packet,
        gov / "constitution" / "schemas" / "resolution-packet.schema.json",
        "resolution packet",
    )
    return packet


def _print_human(resolution: Resolution, packet: dict[str, Any]) -> None:
    print(f"repo:         {resolution.repo} ({resolution.repo_kind})")
    print(f"task:         {resolution.task!r}")
    print(f"route:        {resolution.route_id}")
    if resolution.description:
        print(f"about:        {resolution.description}")
    if resolution.match_type == "trigger":
        print(f"matched:      {resolution.matched_trigger!r}")
    elif resolution.match_type == "explicit":
        print("matched:      explicit --route selection")
    else:
        print("matched:      default route")
    print(f"entrypoint:   {packet['entrypoint']}")
    print(
        "context:      "
        f"{resolution.estimated_tokens}/{resolution.token_budget} "
        "estimated eager governance tokens"
    )
    print("\neager instructions (load in order):")
    for index, path in enumerate(packet["eager_instructions"], 1):
        print(f"  {index}. {path}")
    for heading, values in (
        ("lazy references (open only for a concrete question)", resolution.lazy_references),
        ("executable tools (run; do not preload source)", resolution.tools),
        ("schemas/data (query or validate; do not preload)", resolution.schemas),
        ("examples (inspect one relevant example)", resolution.examples),
        ("outputs", resolution.outputs),
        ("verification", resolution.verify),
    ):
        print(f"\n{heading}:")
        for value in values:
            prefix = "$ " if heading == "verification" else ""
            print(f"  - {prefix}{value}")
    for warning in resolution.warnings:
        print(f"\nwarning: {warning}")


def _emit(resolution: Resolution, gov: Path) -> None:
    for path in [resolution.core, resolution.overlay, *resolution.eager_instructions]:
        print(f"----- {_relative(path, gov)} -----")
        print(path.read_text(encoding="utf-8"), end="")
        if not path.read_text(encoding="utf-8").endswith("\n"):
            print()


def _print_catalog(
    entries: list[dict[str, Any]], repo: str, reason: str | None, as_json: bool
) -> None:
    """Print applicable routes so an agent can pick one by description."""
    if as_json:
        payload: dict[str, Any] = {"repo": repo, "routes": entries}
        if reason is not None:
            payload["selection_needed"] = True
            payload["reason"] = reason
            payload["next_step"] = (
                "Pick the route whose description matches the task's intent, "
                f"then re-run with: --repo {repo} --route <id> --task \"<user task>\""
            )
        print(json.dumps(payload, indent=2))
        return
    if reason is not None:
        print(f"route selection needed: {reason}")
        print(
            "Pick the route whose description matches the task's intent, then"
        )
        print(
            f"re-run: python capabilities/resolve.py --repo {repo} "
            "--route <id> --task \"<user task>\" --root <repo-root>"
        )
        print()
    print(f"routes for {repo}:")
    for entry in entries:
        marker = " (default)" if entry["default"] else ""
        print(f"  {entry['id']}{marker} — {entry['title']}")
        if entry["description"]:
            print(f"      {entry['description']}")
        if entry["example_triggers"]:
            hints = ", ".join(repr(t) for t in entry["example_triggers"])
            print(f"      e.g. {hints}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Resolve (repo, task) to a bounded governance packet."
    )
    parser.add_argument("--repo", required=True)
    parser.add_argument("--task", help="the user's task; required unless --list")
    parser.add_argument(
        "--route",
        help="explicit route id (from --list or a selection catalog); "
        "skips trigger matching but keeps validation and budgets",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="print the applicable route catalog for --repo and exit",
    )
    parser.add_argument("--gov-root")
    parser.add_argument("--root")
    parser.add_argument("--chapter")
    parser.add_argument("--canonical")
    parser.add_argument("--target")
    parser.add_argument(
        "--entrypoint",
        help="staged local entrypoint path; default comes from the manifest",
    )
    output = parser.add_mutually_exclusive_group()
    output.add_argument(
        "--emit",
        action="store_true",
        help="emit eager instruction content without packet metadata",
    )
    output.add_argument("--json", action="store_true", help="print the packet as JSON")
    args = parser.parse_args(argv)

    gov = _discover_gov_root(args.gov_root, args.root)
    if not gov:
        print(
            "fatal: cannot locate lra-governance from --gov-root, "
            "LRA_GOVERNANCE_ROOT, the resolver path, the repository root, or a sibling checkout",
            file=sys.stderr,
        )
        return 1
    if not args.list and not args.task:
        parser.error("--task is required unless --list is given")
    try:
        if args.list:
            manifest = _load_manifest(gov)
            repo = _canonical_repo_name(gov, args.repo, args.root)
            kind = _repo_kind(gov, repo)
            entries = _catalog_entries(_catalog(manifest, kind, repo))
            _print_catalog(entries, repo, None, args.json)
            return 0
        resolution = resolve(gov, args.repo, args.task, vars(args))
        packet = _as_dict(resolution, gov)
    except RouteSelectionNeeded as exc:
        repo = args.repo
        try:
            repo = _canonical_repo_name(gov, args.repo, args.root)
        except ValueError:
            pass
        _print_catalog(_catalog_entries(exc.candidates), repo, exc.reason, args.json)
        return 2
    except (FileNotFoundError, OSError, ValueError, KeyError) as exc:
        print(f"fatal: {exc}", file=sys.stderr)
        return 1

    if args.emit:
        _emit(resolution, gov)
    elif args.json:
        print(json.dumps(packet, indent=2))
    else:
        _print_human(resolution, packet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
