#!/usr/bin/env python3
"""Regression tests for (repo, task) -> capability routing in resolve.py.

Locks consolidated typed mathematical authoring, separate full-proof authoring,
and cross-kind isolation. Run: python test_resolve.py
"""
from __future__ import annotations
import contextlib
import copy
import io
import json
import sys
from pathlib import Path

import resolve as R

GOV = R._gov_root(Path(__file__).resolve().parent)


def route(repo: str, task: str) -> str:
    """Return the resolved capability id, or 'FATAL:<msg>' if resolution fails."""
    try:
        return R.resolve(GOV, repo, task, {}).route_id
    except (ValueError, FileNotFoundError) as e:
        return f"FATAL:{e}"


def expect(repo, task, cap):
    got = route(repo, task)
    assert got == cap, f"route({repo!r}, {task!r}) = {got!r}, expected {cap!r}"


# --- ordinary mathematical kinds share one typed authoring route ---
def test_add_definition_routes_to_author_mathematics():
    expect("lra-volume-i", "add definition of continuity", "author-mathematics")


def test_generate_the_definition_routes_to_author_mathematics():
    expect("lra-volume-i", "generate the definition for continuity", "author-mathematics")


def test_write_the_definition_routes_to_author_mathematics():
    expect("lra-volume-i", "write the definition for a Cauchy sequence", "author-mathematics")


def test_bare_define_falls_to_volume_default_with_reroute_warning():
    resolved = R.resolve(GOV, "lra-volume-i", "define X", {})
    assert resolved.route_id == "work-leaf-volume"
    assert resolved.match_type == "default"
    assert resolved.warnings and "--route" in resolved.warnings[0]


def test_noun_phrase_falls_to_volume_default_with_reroute_warning():
    resolved = R.resolve(GOV, "lra-volume-i", "append the lemma", {})
    assert resolved.route_id == "work-leaf-volume"
    assert resolved.match_type == "default"
    assert resolved.warnings


def test_the_theorem_routes_to_author_mathematics():
    expect("lra-volume-i", "author statement for the theorem", "author-mathematics")


def test_generate_theorem_statement_routes_to_author_mathematics():
    expect("lra-volume-i", "generate a theorem statement", "author-mathematics")


def test_generate_full_proof_routes_to_full_proof_capability():
    expect("lra-volume-i", "generate full proof", "author-full-proof")


def test_generate_theorem_full_proof_does_not_route_to_statement_authoring():
    expect("lra-volume-i", "generate a theorem full proof", "author-full-proof")


def test_populate_theorem_stub_routes_only_to_full_proof_capability():
    expect(
        "lra-volume-i",
        "populate a deterministic theorem proof stub with a full proof",
        "author-full-proof",
    )


def test_create_theorem_stub_routes_to_mathematics_capability():
    expect("lra-volume-i", "create a theorem proof stub", "author-mathematics")


def test_generate_full_capstone_routes_to_author_capstone():
    expect("lra-volume-i", "generate full capstone", "author-capstone")


def test_stub_volume_routes_to_deterministic_volume_capability():
    expect("lra-governance", "scaffold a volume", "author-stub-volume")


def test_stub_chapter_routes_to_deterministic_chapter_capability():
    expect("lra-volume-i", "stub a chapter", "author-stub-chapter")


def test_the_axiom_noun_phrase_falls_to_volume_default():
    expect("lra-volume-i", "the axiom of completeness", "work-leaf-volume")


def test_example_routes_to_author_mathematics():
    expect("lra-volume-i", "generate an example of a convergent sequence", "author-mathematics")


def test_exposition_routes_to_author_mathematics():
    expect("lra-volume-i", "write motivation for compactness", "author-mathematics")


def test_model_theory_routes_to_author_mathematics_with_lazy_specialization():
    expect("lra-volume-viii", "author mathematics for a first-order structure", "author-mathematics")


def test_model_theory_subject_phrase_falls_to_volume_default():
    expect("lra-volume-vii", "author model theory L-structure mathematics", "work-leaf-volume")


# --- semantic audit routing ---
def test_lra_audit_topic_routes_to_topic_semantic_audit():
    expect("lra-volume-iii", "LRA audit topic bounds-extremals", "audit-semantic-topic")


def test_single_artifact_calibration_still_routes_separately():
    expect("lra-volume-iii", "calibrate semantic artifact", "calibrate-semantic-artifact")


def test_chapter_symbol_audit_routes_to_deterministic_scanner():
    expect("lra-volume-iii", "audit chapter symbols", "audit-chapter-symbols")


def test_statement_audit_routes_to_deterministic_preflight_capability():
    expect("lra-volume-iii", "audit a statement", "audit-statement")


def test_proof_audit_routes_to_deterministic_twelve_layer_capability():
    expect("lra-volume-iii", "audit a proof", "audit-proof")


def test_proof_layout_audit_remains_the_more_specific_route():
    expect("lra-volume-iii", "audit proof layout", "audit-proof-layout")


def test_toolkit_planning_routes_to_deterministic_planner():
    expect("lra-volume-iii", "plan toolkits", "plan-toolkits")


# --- a definition task in a non-volume kind must NOT select a volume authoring
#     route. It falls back to the repo's lean route instead. ---
def test_define_does_not_leak_into_lean():
    expect("lra-lean", "define X", "author-lean-theorem")


def test_lean_routes_to_lean_capability():
    expect("lra-lean", "formalize addition commutativity", "author-lean-theorem")


def test_numerical_analysis_routes_to_cpp_capability():
    expect("lra-numerical-analysis", "implement the solver", "cpp-build-task")


def test_nurbs_routes_to_cpp_capability():
    expect("lra-nurbs", "implement surface evaluation", "cpp-build-task")


def test_volume_build_routes_to_build_repo():
    expect("lra-volume-viii", "build repo", "build-repo")


def test_lean_workflow_monitor_routes_to_build_repo():
    expect("lra-lean", "monitor workflows", "build-repo")


def test_cpp_build_repo_routes_to_build_repo():
    expect("lra-numerical-analysis", "build repository", "build-repo")


def test_governance_validate_routes_to_build_repo():
    expect("lra-governance", "validate repo", "build-repo")


def test_source_lookup_routes_from_volume():
    expect("lra-volume-iii", "look up this theorem in sources", "lookup-lra")


def test_code_lookup_routes_from_lean():
    expect("lra-lean", "search our code for least upper bound", "lookup-lra")


def test_definition_lookup_beats_author_mathematics_trigger():
    expect("lra-volume-iii", "look up definition of compactness", "lookup-lra")


def test_pdf_extractor_build_routes_to_build_repo():
    expect("lra-pdf-extractor", "validate repo", "build-repo")


def test_source_profiles_build_routes_to_build_repo():
    expect("lra-source-profiles", "check repository", "build-repo")


def test_reading_categorizer_build_routes_to_build_repo():
    expect("lra-reading-categorizer", "validate repo", "build-repo")


def test_exercises_bare_build_falls_to_exercises_default():
    expect("lra-exercises", "build pdf", "work-lra-exercises")


def test_trigger_and_explicit_resolutions_carry_no_warnings():
    triggered = R.resolve(GOV, "lra-volume-i", "add theorem", {})
    assert triggered.match_type == "trigger" and not triggered.warnings
    explicit = R.resolve(
        GOV, "lra-volume-i", "anything", {"route": "author-mathematics"}
    )
    assert explicit.match_type == "explicit" and not explicit.warnings


def test_statement_does_not_leak_into_exercises():
    expect("lra-exercises", "append the theorem", "work-lra-exercises")


def test_definition_does_not_leak_into_pdf_extractor():
    expect("lra-pdf-extractor", "define X", "work-pdf-extractor")


def test_statement_does_not_leak_into_reading_categorizer():
    expect("lra-reading-categorizer", "append the theorem", "work-reading-categorizer")


def test_statement_does_not_leak_into_source_profiles():
    expect("lra-source-profiles", "append the theorem", "work-source-profiles")


# --- catalog and web kinds ---
def test_sources_catalog_default_route():
    resolved = R.resolve(GOV, "lra-sources", "add the new halmos source record", {})
    assert resolved.route_id == "work-lra-sources"
    assert resolved.match_type == "default"


def test_dashboard_web_default_route():
    resolved = R.resolve(GOV, "lra-dashboard", "improve the progress charts", {})
    assert resolved.route_id == "work-lra-dashboard"


def test_sources_lookup_routes_to_lookup_capability():
    expect("lra-sources", "lookup lra sources for tao", "lookup-lra")


def test_dashboard_build_routes_to_build_repo():
    expect("lra-dashboard", "validate repo", "build-repo")


# --- resolver contract and migration safety ---
def test_unknown_repository_fails_closed():
    got = route("lra-not-registered", "build repo")
    assert got.startswith("FATAL:unknown repository"), got


def test_repository_root_path_resolves_to_registered_name():
    resolved = R.resolve(GOV, str(GOV), "audit governance", {"root": str(GOV)})
    assert resolved.repo == "lra-governance"
    assert resolved.route_id == "audit-governance"


def test_windows_repository_path_resolves_by_final_directory_name():
    resolved = R.resolve(
        GOV,
        "F:\\repos\\lra-lean\\",
        "formalize an upper-bound pilot",
        {"root": r"F:\repos\lra-lean"},
    )
    assert resolved.repo == "lra-lean"
    assert resolved.route_id == "author-lean-theorem"


def test_dot_repository_reference_uses_root_identity():
    resolved = R.resolve(GOV, ".", "audit governance", {"root": str(GOV)})
    assert resolved.repo == "lra-governance"
    assert resolved.route_id == "audit-governance"


def test_resolution_reports_match_and_measured_context():
    resolved = R.resolve(GOV, "lra-governance", "audit governance", {})
    assert resolved.repo_kind == "governance"
    assert resolved.match_type == "trigger"
    assert resolved.matched_trigger == "Audit governance"
    assert 0 < resolved.estimated_tokens <= resolved.token_budget
    assert resolved.manifest_version == 4
    assert resolved.packet_version == 1


def test_manifest_selects_canonical_execution_contract():
    resolved = R.resolve(GOV, "lra-governance", "audit governance", {})
    assert resolved.core == GOV / "capabilities" / "ENTRYPOINT.md"
    assert resolved.core.read_text(encoding="utf-8").startswith(
        "# LRA Agent Execution Contract"
    )
    assert R._load_manifest(GOV)["entrypoint"] == "capabilities/ENTRYPOINT.md"


def test_json_output_is_a_versioned_packet():
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = R.main(
            [
                "--repo",
                "lra-governance",
                "--task",
                "audit governance",
                "--root",
                str(GOV),
                "--json",
            ]
        )
    assert code == 0
    packet = json.loads(output.getvalue())
    assert packet["packet_version"] == 1
    assert packet["manifest_version"] == 4
    assert packet["route"] == "audit-governance"
    assert packet["estimated_tokens"] <= packet["token_budget"]
    assert packet["headroom"] == packet["token_budget"] - packet["estimated_tokens"]


def test_emit_mode_outputs_only_eager_files():
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = R.main(
            [
                "--repo",
                "lra-governance",
                "--task",
                "audit governance",
                "--root",
                str(GOV),
                "--emit",
            ]
        )
    text = output.getvalue()
    assert code == 0
    assert text.startswith("----- capabilities/ENTRYPOINT.md -----")
    assert "repo:         " not in text


# --- LLM-facing selection surface: --list, --route, and selection catalogs ---
def test_list_flag_prints_catalog_with_descriptions():
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = R.main(["--repo", "lra-governance", "--list", "--root", str(GOV)])
    text = output.getvalue()
    assert code == 0
    assert "routes for lra-governance:" in text
    assert "audit-governance (default)" in text
    assert "Audit, shrink, or deduplicate the governance corpus" in text


def test_list_json_catalog_is_structured():
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = R.main(["--repo", "lra-lean", "--list", "--json", "--root", str(GOV)])
    assert code == 0
    payload = json.loads(output.getvalue())
    assert payload["repo"] == "lra-lean"
    ids = {entry["id"] for entry in payload["routes"]}
    assert "author-lean-theorem" in ids
    assert all(entry["description"] for entry in payload["routes"])


def test_explicit_route_selection_bypasses_trigger_matching():
    resolved = R.resolve(
        GOV,
        "lra-volume-i",
        "flesh out the missing pieces in chapter three",
        {"route": "author-full-proof"},
    )
    assert resolved.route_id == "author-full-proof"
    assert resolved.match_type == "explicit"
    assert resolved.matched_trigger is None


def test_explicit_route_json_packet_reports_explicit_match():
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = R.main(
            [
                "--repo",
                "lra-governance",
                "--task",
                "tidy the manifest",
                "--route",
                "audit-governance",
                "--root",
                str(GOV),
                "--json",
            ]
        )
    assert code == 0
    packet = json.loads(output.getvalue())
    assert packet["route"] == "audit-governance"
    assert packet["match_type"] == "explicit"
    assert packet["description"]


def test_explicit_route_rejects_inapplicable_repo_kind():
    try:
        R.resolve(GOV, "lra-lean", "do the thing", {"route": "author-mathematics"})
    except ValueError as exc:
        assert "does not apply" in str(exc)
        assert "applicable routes" in str(exc)
    else:
        raise AssertionError("explicit route accepted an inapplicable repo kind")


def test_explicit_unknown_route_lists_known_ids():
    try:
        R.resolve(GOV, "lra-lean", "do the thing", {"route": "no-such-route"})
    except ValueError as exc:
        assert "unknown route" in str(exc)
    else:
        raise AssertionError("explicit route accepted an unknown id")


def _synthetic_manifest() -> dict:
    return {
        "routes": [
            {
                "id": "alpha",
                "title": "Alpha",
                "description": "First synthetic route.",
                "applies_to": ["volume"],
                "triggers": ["run alpha"],
            },
            {
                "id": "beta",
                "title": "Beta",
                "description": "Second synthetic route.",
                "applies_to": ["volume"],
                "triggers": ["run  beta"],
            },
        ]
    }


def test_trigger_tie_raises_selection_needed_with_candidates():
    manifest = _synthetic_manifest()
    # both 9-char triggers appear in the task -> equal-length tie
    try:
        R._match("please run alpha and run  beta", manifest, "volume", "lra-volume-i")
    except R.RouteSelectionNeeded as exc:
        assert {route["id"] for route in exc.candidates} == {"alpha", "beta"}
    else:
        raise AssertionError("equal-length trigger tie did not request selection")


def test_no_match_without_default_raises_selection_needed_with_catalog():
    manifest = _synthetic_manifest()
    try:
        R._match("something unrelated", manifest, "volume", "lra-volume-i")
    except R.RouteSelectionNeeded as exc:
        assert "no trigger matched" in exc.reason
        assert {route["id"] for route in exc.candidates} == {"alpha", "beta"}
    else:
        raise AssertionError("unmatched task without default did not request selection")


def test_selection_needed_exits_2_with_actionable_catalog():
    original = R._match

    def force_selection(task, manifest, kind, repo):
        raise R.RouteSelectionNeeded(
            "synthetic", R._catalog(manifest, kind, repo)
        )

    R._match = force_selection
    try:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = R.main(
                ["--repo", "lra-lean", "--task", "mystery work", "--root", str(GOV)]
            )
    finally:
        R._match = original
    text = output.getvalue()
    assert code == 2
    assert "route selection needed" in text
    assert "--route <id>" in text
    assert "author-lean-theorem" in text


def test_every_route_has_a_distinct_description():
    manifest = R._load_manifest(GOV)
    descriptions = [route["description"] for route in manifest["routes"]]
    assert all(descriptions)
    assert len(set(descriptions)) == len(descriptions)


def test_manifest_schema_requires_description():
    manifest = copy.deepcopy(R._load_manifest(GOV))
    del manifest["routes"][0]["description"]
    schema = GOV / "constitution" / "schemas" / "capability-manifest.schema.json"
    try:
        R._validate_json(manifest, schema, "test manifest")
    except ValueError as exc:
        assert "description" in str(exc)
    else:
        raise AssertionError("manifest schema accepted a route without description")


def test_manifest_schema_rejects_unknown_fields():
    manifest = copy.deepcopy(R._load_manifest(GOV))
    manifest["unexpected"] = True
    schema = GOV / "constitution" / "schemas" / "capability-manifest.schema.json"
    try:
        R._validate_json(manifest, schema, "test manifest")
    except ValueError as exc:
        assert "Additional properties are not allowed" in str(exc)
    else:
        raise AssertionError("manifest schema accepted an unknown field")


def test_prompt_routes_use_executable_verification_commands():
    manifest = R._load_manifest(GOV)
    for prompt_route in manifest["prompt_routes"]:
        assert prompt_route["verify"], prompt_route["title"]
        for command in prompt_route["verify"]:
            R._validate_executable_verify(prompt_route["title"], command)


def test_prompt_route_rejects_descriptive_verification_phrase():
    manifest = copy.deepcopy(R._load_manifest(GOV))
    manifest["prompt_routes"] = [
        {
            "title": "Synthetic legacy prompt route",
            "prompt": "constitution/prompts/generate-capstone.md",
            "schemas": ["constitution/schema/file-schema.yaml"],
            "verify": ["proof layout audit"],
        }
    ]
    try:
        R._validate_manifest_semantics(GOV, manifest)
    except ValueError as exc:
        assert "verification must be an executable command" in str(exc)
    else:
        raise AssertionError("prompt route accepted a descriptive verification phrase")


def test_one_time_logical_block_migration_is_not_a_prompt_route():
    manifest = R._load_manifest(GOV)
    prompts = {route["prompt"] for route in manifest["prompt_routes"]}
    titles = {route["title"] for route in manifest["prompt_routes"]}
    assert "constitution/prompts/fix-logical-block-gaps.md" not in prompts
    assert "Fix logical block gaps" not in titles


def test_statement_semantic_prompt_is_lazy_under_capability_route():
    manifest = R._load_manifest(GOV)
    prompt_routes = {route["prompt"] for route in manifest["prompt_routes"]}
    statement_route = next(route for route in manifest["routes"] if route["id"] == "audit-statement")
    assert "constitution/prompts/audit-statement.md" not in prompt_routes
    assert "constitution/prompts/audit-statement.md" in statement_route["lazy_references"]


def test_proof_semantic_prompt_is_lazy_under_capability_route():
    manifest = R._load_manifest(GOV)
    prompt_routes = {route["prompt"] for route in manifest["prompt_routes"]}
    proof_route = next(route for route in manifest["routes"] if route["id"] == "audit-proof")
    assert "constitution/prompts/audit-proof.md" not in prompt_routes
    assert "constitution/prompts/audit-proof.md" in proof_route["lazy_references"]


def test_mathematical_authoring_uses_typed_schema_without_generation_prompt():
    manifest = R._load_manifest(GOV)
    prompt_routes = {route["prompt"] for route in manifest["prompt_routes"]}
    author_route = next(route for route in manifest["routes"] if route["id"] == "author-mathematics")
    assert "constitution/prompts/generate-statement.md" not in prompt_routes
    assert "constitution/prompts/generate-statement.md" not in author_route["lazy_references"]
    assert "constitution/schemas/mathematical-content.schema.json" in author_route["schemas"]
    assert "tools/governance/generators/mathematical_tex.py" in author_route["tools"]


def test_full_proof_route_uses_typed_renderer_without_generation_prompt():
    manifest = R._load_manifest(GOV)
    prompt_routes = {route["prompt"] for route in manifest["prompt_routes"]}
    author_route = next(route for route in manifest["routes"] if route["id"] == "author-full-proof")
    assert "constitution/prompts/generate-proof.md" not in prompt_routes
    assert "constitution/prompts/generate-proof.md" not in author_route["lazy_references"]
    assert "tools/governance/generators/proof_stub.py" not in author_route["tools"]


def test_full_capstone_prompt_is_lazy_under_authoring_capability():
    manifest = R._load_manifest(GOV)
    prompt_routes = {route["prompt"] for route in manifest["prompt_routes"]}
    author_route = next(route for route in manifest["routes"] if route["id"] == "author-capstone")
    assert "constitution/prompts/generate-capstone.md" not in prompt_routes
    assert "constitution/prompts/generate-capstone.md" in author_route["lazy_references"]


def test_permanent_prompt_route_inventory_is_empty():
    assert R._load_manifest(GOV)["prompt_routes"] == []


if __name__ == "__main__":
    tests = [
        v
        for k, v in sorted(globals().items())
        if k.startswith("test_") and callable(v)
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {t.__name__}: {e}")
    print(f"\n{len(tests)-failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
