# lra-volume Overlay

Stub overlay for `lra-volume-i` through `lra-volume-v`.

Owned concerns:

- volume content only,
- Overleaf-ready volume roots,
- local copies of synced `common/` and `bibliography/`,
- volume-to-monorepo content sync.

This overlay must not contain Lean-specific, C++ / Vulkan / simulation, or
numerical-analysis / benchmark / plotting rules.

## Agent Scope

Volume agents may edit only the owning `volume-N/` content unless a task
explicitly says otherwise. They should not edit synced `common/`,
`bibliography/`, generated governance wrappers, or canonical YAML.

Volume tasks should preserve Overleaf readiness and monorepo sync shape.
