# Agent Instruction Policy

Canonical rules live under `docs/governance/`, `docs/architecture/`, and
`capabilities/overlays/`.

## Canonical Sources

Canonical agent-instruction sources are:

- `docs/governance/*.md`
- `docs/architecture/*.md`
- `capabilities/overlays/*.md`

The root `AGENTS.md` in `lra-governance` is the local router for agents working
in this source repo. It points to canonical source directories rather than
replacing them.

Agent-specific files are generated artifacts:

- downstream `AGENTS.md`
- downstream `CLAUDE.md`
- downstream `GEMINI.md`
- downstream `.github/copilot-instructions.md`
- downstream `.github/instructions/*.instructions.md`
- downstream compatibility wrappers, if any

## Generation Rule

Generated agent files must be thin pointer wrappers that identify:

1. the canonical route resolver command,
2. exactly one appropriate repo overlay or repo-family overlay,
3. the canonical governance resolution order,
4. provider-specific wrapper formatting.

Generation formula:

```text
repo name + resolver command + repo overlay pointer + provider wrapper = generated instruction file
```

Generated wrappers must not embed global governance docs or repo overlay bodies.
They may point to the generated human task index as a lazy reference, but must
not instruct agents to preload it.
Governance updates belong in `lra-governance`, not in downstream generated
snapshots.

## Provider Rule

- Codex uses `AGENTS.md`.
- Claude uses `CLAUDE.md`, which should import or point to `AGENTS.md` where
  supported.
- Copilot uses `.github/copilot-instructions.md` and optionally
  `.github/instructions/*.instructions.md`.
- Gemini uses `GEMINI.md`.

## Source Header Rule

Every generated agent file must identify:

- the source repo (`lra-governance`),
- the source documents used,
- whether the file is generated,
- the local-edit policy.

## Secret Rule

Generated instructions must never contain token values, credentials, or
machine-local secrets.

## Drift Rule

Downstream generated files must not become local sources of truth. Emergency
local repairs must be ported back to `lra-governance`.

## User Todo Issue Rule

When the user asks an agent to create, add, record, or remember a todo, the
agent must create a GitHub issue in the current repository unless the user
explicitly names another repository or asks for a different tracking system.

The issue title should be concise and action-oriented. The issue body should
preserve the user's requested todo, include any relevant repository context, and
note that the issue was created from a user todo request. Apply existing repo
labels only when their meaning is clear.

This rule does not apply to the agent's private execution plan, transient
checklists, or requests to add literal `TODO` comments in source files. If the
current repository has no GitHub remote, GitHub is unavailable, or issue
creation fails, the agent must report the blocker and provide the issue title
and body that would have been created.

## Local Edit Rule

Generated files are local wrappers or instructions, not synced governance
copies. Emergency downstream edits are allowed only as temporary repair and
must be ported upstream into `lra-governance` before regeneration.
