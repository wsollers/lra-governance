# Generated Wrapper Workflow

Generated agent wrappers are derived from `lra-governance` and should delegate
back to the canonical checkout.

## Source Flow

The generated-file and local-edit rules live in
`docs/architecture/generated-file-policy.md` and
`docs/governance/agent-instruction-policy.md`.

The generation formula is:

```text
repo name + resolver command + repo-overlay pointer + provider wrapper format
```

Generated wrappers are thin delegates. They must not copy canonical governance
docs or repo overlay bodies into downstream repositories, and must not instruct
agents to preload the generated human task index.

Generated downstream files are not canonical.

## Preview And Validation

Before any write:

1. Generate wrapper previews under a report directory.
2. Validate preview headers, overlay pointers, resolution rules, and
   specialist-rule boundaries.
3. Run wrapper pointer-drift reporting against downstream repos.
4. Review the planned create, replace, identical, and blocked statuses.

Preview and drift outputs are local reports and should not be committed unless
a task explicitly asks for a report artifact.

## Controlled Write

Wrapper generation is dry-run by default. Write mode must be explicit,
repo-selected, and guarded. It must not silently update every repo.

The generation tool writes only generated wrapper files defined by the
generated-file policy and the selected provider wrapper.

Write mode must refuse dirty target repos and non-main target branches unless a
task explicitly authorizes an exception. The tool does not stage, commit, or
push downstream repos. It must not copy canonical governance implementations or
shared docs into downstream repos.

## Review

Downstream generated wrappers should be committed through reviewable PRs or
controlled commits after inspection. Reviewers should check the generated-file
header, source repo, resolver command, overlay pointer, absence of secrets,
and absence of embedded governance or overlay bodies.
