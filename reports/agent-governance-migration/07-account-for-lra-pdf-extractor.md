# Phase 3 Follow-Up: Account for lra-pdf-extractor

## Reason

`lra-pdf-extractor` was added to the LRA repository family after its bootstrap
PR merged. The governance refactor now needs an explicit overlay and
architecture references so future generated agent instructions can route the
right rules to the repo.

The repo is an acceleration and staging tool for PDF/source ingestion,
bibliography metadata extraction and normalization, local-model-assisted
candidate extraction/decorating, and reviewable LaTeX/BibTeX/JSON outputs.

## Files Updated

- `docs/governance/repo-overlays/lra-pdf-extractor.md`
- `docs/governance/repo-overlays/README.md`
- `docs/architecture/repository-layout.md`
- `docs/architecture/multi-repo-sync.md`
- `reports/agent-governance-migration/07-account-for-lra-pdf-extractor.md`

## Scope Boundaries

`lra-pdf-extractor` owns extraction and staging tooling. It does not own final
LRA notes, canonical YAML, shared LaTeX infrastructure, theorem explorer
internals, or global governance rules.

Generated candidates from `lra-pdf-extractor` must be reviewed and applied
through PRs in the owning repository. They must not be directly synced into
notes, bibliography, canonical YAML, theorem explorer data, or governance
files.

## Implementation Status

Implementation work on PDF extraction, GUI workflows, and local-model
integration is intentionally tabled until the governance refactor is complete.

