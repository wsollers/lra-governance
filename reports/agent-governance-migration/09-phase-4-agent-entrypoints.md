# Phase 4: Agent Entrypoints And Wrapper Preview Generation

## Reason

Phase 4 creates the canonical agent instruction source and provider-wrapper
generation design in `lra-governance`. The goal is to make downstream
instruction files derived from one rule flow instead of hand-maintained copies.

The rule flow is:

```text
global governance docs + repo overlay + provider wrapper format -> generated agent instruction files
```

## Files Added

- `AGENTS.md`
- `tools/governance/generate_agent_wrappers.py`
- `tools/governance/merge_repo_overlays.py`
- `tools/governance/validate_repo_rules.py`
- `tools/governance/templates/AGENTS.md.j2`
- `tools/governance/templates/CLAUDE.md.j2`
- `tools/governance/templates/GEMINI.md.j2`
- `tools/governance/templates/copilot-instructions.md.j2`
- `tools/governance/templates/github-instructions.md.j2`

## Files Updated

- `docs/governance/agent-instruction-policy.md`
- `docs/governance/task-scope-limits.md`
- `docs/architecture/generated-file-policy.md`
- `docs/architecture/multi-repo-sync.md`

## Intentionally Not Implemented

- No downstream repo writes.
- No downstream sync.
- No full-replace write mode.
- No drift remediation.
- No dependency on Jinja.
- No generated wrappers committed to target repos.

## Dry-Run Only

The generator writes preview files only under a requested output directory.
This allows template shape, overlay routing, and generated-file headers to be
reviewed before any write mode exists.

## Drift Prevention

Generated files include a source header, source repo, source commit when
available, source document list, and local-edit warning. The validator checks
that preview files contain the generated-file header and that volume previews
do not receive specialist overlays.

## Next Recommended Phase

The next phase should review preview output, refine provider wrapper shape, and
add drift-check reporting. Downstream full-replace sync should remain blocked
until preview validation is stable.

