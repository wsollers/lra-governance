# Agent Instruction Policy

Canonical rules live under `docs/governance/`, `docs/architecture/`, and
`docs/governance/repo-overlays/`.

Agent-specific files are generated artifacts:

- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `.github/copilot-instructions.md`
- `.github/instructions/*.instructions.md`

## Generation Rule

Generated agent files must be assembled from:

1. global core governance rules,
2. exactly one appropriate repo overlay or repo-family overlay,
3. provider-specific wrapper formatting.

## Source Header Rule

Every generated agent file must identify:

- the source repo (`lra-governance`),
- the source documents used,
- whether the file is generated,
- the local-edit policy.

## Secret Rule

Generated instructions may name required secret variables, such as `SYNC_PAT`,
but must never contain token values, credentials, or machine-local secrets.

## Drift Rule

Downstream generated files must not become local sources of truth. Emergency
local repairs must be ported back to `lra-governance` before the next sync.
