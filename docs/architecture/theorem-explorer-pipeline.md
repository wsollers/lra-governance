# Theorem Explorer Pipeline

Source: `REPOSITORY_STRUCTURE.md`, `docs/workflows/knowledge-extraction.md`, and `lra-knowledge-explorer/README.md`.

## Ownership

`lra-knowledge-explorer` owns the extractor implementation, graph generation,
and explorer UI.

`lra-governance` owns the extraction standards and orchestrates the refresh; the
independent `lra-volume-*` repos are the canonical TeX source.

## Dispatch Model

The rebuild is orchestrated from `lra-governance`, which reads the independent
volume repos directly. There is no monorepo and no fan-in sync, so there is no
mono-side dispatch point; the governance refresh is the single trigger (see
`docs/workflows/knowledge-extraction.md`).

## Extraction Inputs

Extractor runs point at the split `lra-volume-*` clones. The pipeline depends on
stable labels, dependency blocks, and canonical chapter structure.
