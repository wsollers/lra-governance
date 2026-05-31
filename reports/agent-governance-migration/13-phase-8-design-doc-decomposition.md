# Phase 8: DESIGN.md Decomposition Report

## Purpose

Phase 8 decomposes the large root `DESIGN.md` into modular canonical
governance, architecture, and workflow documents so agents can load
task-specific context instead of a monolithic design manual.

## Size Change

- Original `DESIGN.md`: approximately 1,602 lines and 53,053 bytes.
- New `DESIGN.md`: 101 lines and 5,524 bytes.

## Files Created

- `docs/architecture/knowledge-pipeline.md`
- `docs/architecture/latex-build-and-rendering.md`
- `docs/workflows/README.md`
- `docs/workflows/knowledge-extraction.md`
- `docs/workflows/volume-cleanup.md`
- `docs/workflows/generated-wrapper-sync.md`
- `docs/workflows/decoration-audit.md`
- `docs/archive/README.md`

## Files Updated

- `DESIGN.md`
- `docs/governance/README.md`
- `docs/architecture/README.md`
- `docs/governance/task-scope-limits.md`
- `docs/governance/repo-overlays/lra-volume.md`

## Content Moved Or Routed

- Purpose, voice, box, chapter-entry, and layered exposition rules route to
  `docs/governance/authoring-standards.md`.
- Notation, canonical predicate sources, no predicate leakage, and missing
  predicate protocol route to `docs/governance/notation-standards.md` and
  `docs/architecture/canonical-yaml.md`.
- Proof file architecture, `prf:` label semantics, proof navigation, and proof
  lifecycle rules route to `docs/governance/proof-standards.md`.
- Dependency block semantics, `\hyperref[label]{Readable Name}` extraction, and
  graph-edge target rules route to `docs/governance/extraction-standards.md`
  and `docs/architecture/knowledge-pipeline.md`.
- Repository ownership, shared LaTeX infrastructure, canonical YAML, and
  specialist repo boundaries route to `docs/architecture/repository-layout.md`
  and repo overlays.
- Build and rendering architecture routes to
  `docs/architecture/latex-build-and-rendering.md`.
- Knowledge extraction, volume cleanup, generated wrapper sync, and decoration
  audit procedures route to `docs/workflows/`.

## Duplicate Rules Resolved

- Generated files not being canonical already existed in agent-instruction and
  generated-file policy; the router now points there instead of repeating the
  full policy.
- Box-worthiness was already refined in `authoring-standards.md`; the router
  preserves discovery and avoids a second competing box rule.
- Dependency-link semantics were already clarified in proof and extraction
  standards; the knowledge pipeline doc now points to the same convention.
- Controlled wrapper sync rules were already established in Phase 7 policy and
  tooling; the workflow doc records the operational sequence without changing
  the policy.

## Obsolete Or Retired Assumptions

- The old design text treated `DESIGN.md` itself as the full active manual. It
  is now retired as an active policy container and retained as a router only.
- Older governance-sync language that implied broad downstream governance file
  syncing has been superseded by generated wrapper preview, drift, and
  controlled sync workflows.
- Older repository tables that predated `lra-numerical-analysis` and
  `lra-pdf-extractor` are superseded by `docs/architecture/repository-layout.md`.

## Unresolved Questions

- Whether a future archive should preserve the full pre-Phase-8 `DESIGN.md`
  text as a historical snapshot.
- Whether chapter-registry and stub-generation details should become a separate
  workflow if those generators are revived.

## Final Verdict

APPROVE WITH MINOR REVIEW: active policy has modular homes, `DESIGN.md` is now
a lightweight router, and old monolithic-design assumptions are recorded rather
than silently discarded.
