# Repo Overlay -- lra-governance

Repo identity: Governance, capabilities, validators, and wrapper tooling.

Owned concerns:

- capability resolver, route manifest, and capability docs,
- governance validators, generators, and their tests,
- repo overlays and generated wrapper tooling,
- canonical YAML registries, schemas, and prompts,
- standards, reports, and migration plans.

Success gates:

- `python capabilities/test_resolve.py`
- `python capabilities/generate_task_index.py --check`
- `python tools/governance/audit_governance_context.py`
- run focused validator tests for changed validator code.

Build and validation work in this repo should use the `build-repo` capability.
Do not run LaTeX volume render checks as substitutes for governance tests.
