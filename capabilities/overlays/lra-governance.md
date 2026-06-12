# Repo Overlay -- lra-governance

Repo identity: Governance, capabilities, validators, and wrapper tooling.

Owned concerns:

- capability resolver and capability docs,
- governance validators and tests,
- repo overlays and generated wrapper tooling,
- standards, reports, and migration plans.

Success gates:

- `python capabilities/test_resolve.py`
- `python -m py_compile capabilities/resolve.py capabilities/build-repo/build_repo.py`
- run focused validator tests for changed validator code.

Build and validation work in this repo should use the `build-repo` capability.
Do not run LaTeX volume render checks as substitutes for governance tests.
