# Agent Instruction Policy

This stub will define how generated agent instruction files are produced and
maintained.

Current Phase 2 policy:

- Canonical rules live under `docs/governance/`, `docs/architecture/`, and
  `docs/governance/repo-overlays/`.
- Agent-specific files are generated artifacts.
- Generated artifacts must not contain secrets.
- Generated artifacts must identify their source documents.
- Downstream generated files must not be edited as canonical source.
