Generated downstream instruction files are not canonical, and there are no
synced governance copies in downstream repos. The former one-way governance
fan-out and volume-to-monorepo sync are retired; repos read `lra-governance` and
`lra-common` directly from a sibling checkout, `LRA_GOVERNANCE_ROOT`, or the
build image.

# lra-governance Agent Router

`lra-governance` is the source of truth for LRA governance docs, architecture
docs, repo overlays, prompts, schemas, governance tools, generators, the
canonical YAML vocabulary, and integration policy.

Detailed rules live under:

- `docs/agent-task-index.md`
- `docs/governance/`
- `docs/architecture/`
- `docs/governance/repo-overlays/`
- `constitution/schema/`
- `tools/governance/`

When working from a local multi-repo checkout such as `F:\repos`, use
`docs/agent-task-index.md` to choose the smallest relevant set of canonical
governance files. Do not read every downstream copy just because it exists.

When working inside an isolated repository checkout without an adjacent
`lra-governance`, resolve governance through `LRA_GOVERNANCE_ROOT`, an explicit
`lra-governance` checkout, or the build Docker image. There are no local synced
governance copies to fall back on; if none resolves, stop and report that
`lra-governance` is not present.

Do not edit downstream generated instruction files by hand except for emergency
repair; any emergency repair must be ported upstream into `lra-governance`.

For agent wrapper generation, combine:

1. global core rules,
2. exactly one repo overlay or repo-family overlay,
3. provider-specific wrapper formatting.

Do not include secrets, credentials, tokens, or machine-local private values in
generated files.

Do not modify mathematical content during governance tasks. The canonical
vocabulary (`predicates.yaml`, `notation.yaml`, `relations.yaml`) lives in
`lra-governance`; do not invent predicates, notation, relations, labels, or
dependencies.

