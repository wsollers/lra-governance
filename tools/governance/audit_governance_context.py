#!/usr/bin/env python3
"""Deterministically audit route governance context and token budgets."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
RESOURCE_CLASSES = (
    "eager_instructions",
    "lazy_references",
    "tools",
    "schemas",
    "examples",
)


def estimate_tokens(text: str) -> int:
    """Stable proxy used for budgets; deliberately independent of model tokenizer."""
    return math.ceil(len(text) / 4)


def _is_pointer(value: str) -> bool:
    return (
        value.startswith(("external:", "nearby:"))
        or (":" in value and not Path(value).suffix)
        or ("/" not in value and "\\" not in value and not Path(value).suffix)
    )


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _render_wrappers(repo: str) -> dict[str, str]:
    if repo == "lra-governance":
        return {"AGENTS.md": _load_text(ROOT / "AGENTS.md")}
    from generate_agent_wrappers import (
        generated_header,
        governance_resolution,
        provider_notes,
        render_template,
    )
    from merge_repo_overlays import overlay_for_repo

    overlay_name = overlay_for_repo(repo)
    values = {
            "GENERATED_HEADER": generated_header(overlay_name),
            "REPO_NAME": repo,
            "OVERLAY_PATH": f"capabilities/overlays/{overlay_name}",
            "GOVERNANCE_RESOLUTION": governance_resolution(),
    }
    template_dir = ROOT / "tools" / "governance" / "templates"
    rendered: dict[str, str] = {}
    for template_name in (
        "AGENTS.md.j2",
        "CLAUDE.md.j2",
        "GEMINI.md.j2",
        "copilot-instructions.md.j2",
        "github-instructions.md.j2",
    ):
        template = _load_text(template_dir / template_name)
        wrapper_values = {**values, "PROVIDER_NOTES": provider_notes(template_name)}
        rendered[template_name.removesuffix(".j2")] = render_template(template, wrapper_values)
    agents = rendered["AGENTS.md"]
    for name in list(rendered):
        if name != "AGENTS.md":
            rendered[name] = rendered[name] + "\n" + agents
    return rendered


def _generated_index_is_current(manifest: dict) -> bool:
    sys.path.insert(0, str(ROOT / "capabilities"))
    try:
        from generate_task_index import render
    finally:
        sys.path.pop(0)
    path = ROOT / "docs" / "agent-task-index.md"
    return path.exists() and _load_text(path) == render(manifest)


def audit() -> dict:
    manifest_path = ROOT / "capabilities" / "manifest.yaml"
    errors: list[str] = []
    warnings: list[str] = []

    sys.path.insert(0, str(ROOT / "capabilities"))
    try:
        from resolve import _load_manifest

        manifest = _load_manifest(ROOT)
    except (OSError, ValueError) as exc:
        return {
            "ok": False,
            "estimator": "ceil(unicode_characters / 4)",
            "route_count": 0,
            "prompt_route_count": 0,
            "local_resource_count": 0,
            "max_context": None,
            "contexts": [],
            "warnings": [],
            "errors": [str(exc)],
        }
    finally:
        sys.path.pop(0)

    if manifest.get("version") != 4:
        errors.append("manifest version must be 4")
    if manifest.get("token_estimator") != "unicode_chars_div_4_ceil":
        errors.append("token_estimator must be unicode_chars_div_4_ceil")

    routes = manifest.get("routes") or []
    ids = [route.get("id") for route in routes]
    duplicates = sorted({route_id for route_id in ids if ids.count(route_id) > 1})
    if duplicates:
        errors.append(f"duplicate route ids: {duplicates}")

    required = {"id", "title", "applies_to", "triggers", *RESOURCE_CLASSES, "outputs", "verify", "token_budget"}
    local_paths: set[str] = set()
    for route in routes:
        route_id = route.get("id", "<missing-id>")
        missing = sorted(required - set(route))
        if missing:
            errors.append(f"{route_id}: missing fields {missing}")
        for field in RESOURCE_CLASSES:
            values = route.get(field, [])
            if not isinstance(values, list):
                errors.append(f"{route_id}: {field} must be a list")
                continue
            for raw in values:
                value = str(raw)
                if _is_pointer(value):
                    continue
                path = ROOT / value
                local_paths.add(value)
                if not path.exists():
                    errors.append(f"{route_id}: missing {field} path {value}")
        eager = set(map(str, route.get("eager_instructions", [])))
        non_eager = set(map(str, route.get("lazy_references", []))) | set(map(str, route.get("tools", []))) | set(map(str, route.get("schemas", [])))
        overlap = sorted(eager & non_eager)
        if overlap:
            errors.append(f"{route_id}: resources classified as both eager and non-eager: {overlap}")
        for value in eager:
            suffix = Path(value).suffix.lower()
            if suffix not in {".md", ".txt"}:
                errors.append(f"{route_id}: eager instruction is not text guidance: {value}")
        typed_resources = {
            str(value).rstrip("/")
            for field in RESOURCE_CLASSES
            for value in route.get(field, [])
        }
        transitive_pattern = re.compile(
            r"`((?:docs|capabilities|constitution|tools)/[^`\s]+)`"
        )
        for value in eager:
            path = ROOT / value
            if not path.is_file():
                continue
            text = _load_text(path)
            for reference in sorted(set(transitive_pattern.findall(text))):
                if reference.rstrip("/") not in typed_resources:
                    errors.append(
                        f"{route_id}: eager guidance points to unclassified resource {reference}"
                    )
            lowered = text.lower()
            if (
                "read `docs/agent-task-index.md`" in lowered
                or "load `docs/agent-task-index.md`" in lowered
                or "read the canonical task router" in lowered
            ):
                errors.append(f"{route_id}: eager guidance preloads the generated task index")

    config = yaml.safe_load(_load_text(ROOT / "capabilities" / "overlays-config.yaml"))
    repo_records = config.get("repos", [])
    contexts: list[dict] = []
    defaults: dict[tuple[str, str], list[str]] = {}
    core_path = ROOT / str(manifest["entrypoint"])
    core_tokens = estimate_tokens(_load_text(core_path))

    for route in routes:
        for repo_record in repo_records:
            repo = repo_record["repo"]
            kind = repo_record.get("kind", "volume")
            if kind not in route.get("applies_to", ["volume"]):
                continue
            if route.get("repos") and repo not in route["repos"]:
                continue
            if route.get("default"):
                defaults.setdefault((repo, kind), []).append(route["id"])

            overlay_path = ROOT / "capabilities" / "overlays" / f"{repo}.md"
            if not overlay_path.exists():
                errors.append(f"{route['id']}: missing resolver overlay for {repo}")
                continue
            wrapper_profiles = {
                name: estimate_tokens(text)
                for name, text in _render_wrappers(repo).items()
            }
            wrapper_profile, wrapper_tokens = max(
                wrapper_profiles.items(), key=lambda item: (item[1], item[0])
            )
            eager_tokens = core_tokens + estimate_tokens(_load_text(overlay_path))
            for value in route.get("eager_instructions", []):
                path = ROOT / str(value)
                if path.exists() and path.is_file():
                    eager_tokens += estimate_tokens(_load_text(path))
            total_tokens = wrapper_tokens + eager_tokens
            budget = int(route.get("token_budget", manifest.get("default_token_budget", 0)))
            record = {
                "route": route["id"],
                "repo": repo,
                "wrapper_tokens": wrapper_tokens,
                "wrapper_profile": wrapper_profile,
                "eager_packet_tokens": eager_tokens,
                "governance_context_tokens": total_tokens,
                "budget": budget,
                "headroom": budget - total_tokens,
            }
            contexts.append(record)
            if total_tokens > budget:
                errors.append(
                    f"{route['id']} on {repo}: governance context {total_tokens} exceeds budget {budget}"
                )

    for (repo, _kind), route_ids in sorted(defaults.items()):
        if len(route_ids) > 1:
            errors.append(f"{repo}: multiple default routes {route_ids}")
    for repo_record in repo_records:
        repo = repo_record["repo"]
        kind = repo_record.get("kind", "volume")
        if (repo, kind) not in defaults:
            warnings.append(f"{repo}: no default route; unmatched tasks fail closed")

    if not _generated_index_is_current(manifest):
        errors.append("docs/agent-task-index.md is stale; run capabilities/generate_task_index.py")

    for name in ("AGENTS.md.j2", "CLAUDE.md.j2", "GEMINI.md.j2", "copilot-instructions.md.j2", "github-instructions.md.j2"):
        text = _load_text(ROOT / "tools" / "governance" / "templates" / name)
        if "Canonical route resolver:" not in text or "--task \"<user task>\"" not in text:
            errors.append(f"{name}: missing resolver command")
        if "Canonical task router:" in text or "read the canonical task router" in text.lower():
            errors.append(f"{name}: still instructs agents to preload the human task index")

    contexts.sort(key=lambda item: (-item["governance_context_tokens"], item["route"], item["repo"]))
    return {
        "ok": not errors,
        "estimator": "ceil(unicode_characters / 4)",
        "route_count": len(routes),
        "prompt_route_count": len(manifest.get("prompt_routes", [])),
        "local_resource_count": len(local_paths),
        "max_context": contexts[0] if contexts else None,
        "contexts": contexts,
        "warnings": warnings,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    result = audit()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        state = "PASS" if result["ok"] else "FAIL"
        print(f"governance context audit: {state}")
        print(f"routes: {result['route_count']}; prompt routes: {result['prompt_route_count']}; local resources: {result['local_resource_count']}")
        if result["max_context"]:
            item = result["max_context"]
            print(
                "largest context: "
                f"{item['governance_context_tokens']} tokens "
                f"({item['route']} on {item['repo']}; "
                f"wrapper {item['wrapper_profile']}; budget {item['budget']})"
            )
        if args.verbose:
            for item in result["contexts"]:
                print(
                    f"  {item['route']} / {item['repo']}: "
                    f"wrapper={item['wrapper_tokens']}[{item['wrapper_profile']}] "
                    f"eager={item['eager_packet_tokens']} "
                    f"total={item['governance_context_tokens']} budget={item['budget']}"
                )
        for warning in result["warnings"]:
            print(f"warning: {warning}")
        for error in result["errors"]:
            print(f"error: {error}", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
