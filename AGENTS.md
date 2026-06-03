# lra-governance Agent Router

`lra-governance` is the source of truth for LRA governance docs, architecture
docs, repo overlays, prompts, schemas, generators, and sync policy.

Detailed rules live under:

- `docs/agent-task-index.md`
- `docs/governance/`
- `docs/architecture/`
- `docs/governance/repo-overlays/`

When working from a local multi-repo checkout such as `F:\repos`, use
`docs/agent-task-index.md` to choose the smallest relevant set of canonical
governance files. Do not read every synced downstream copy just because it
exists.

When working inside an isolated repository checkout without adjacent
`lra-governance`, use that repo's local synced `docs/` copies.

Generated downstream instruction files are not canonical. Do not edit
downstream generated instruction files by hand except for emergency repair; any
emergency repair must be ported upstream into `lra-governance`.

For agent wrapper generation, combine:

1. global core rules,
2. exactly one repo overlay or repo-family overlay,
3. provider-specific wrapper formatting.

Do not include secrets, credentials, tokens, or machine-local private values in
generated files.

Do not modify mathematical content during governance tasks.

Do not touch `Learning-Real-Analysis/scripts/`.

