# Theorem Explorer Pipeline

Source: `capabilities/extract-knowledge/capability.md` and `lra-knowledge-explorer/README.md`.

## Ownership

`lra-knowledge-explorer` owns the extractor implementation, graph generation,
and explorer UI.

`lra-governance` owns the extraction standards and orchestrates the refresh; the
independent `lra-volume-*` repos are the canonical TeX source.

## Dispatch Model

The rebuild is orchestrated from `lra-governance`, which reads the independent
volume repos directly. There is no monorepo and no fan-in sync, so there is no
mono-side dispatch point; the governance refresh is the single trigger (see
`capabilities/extract-knowledge/capability.md`).

## Extraction Inputs

Extractor runs point at the split `lra-volume-*` clones. The pipeline depends on
stable labels, dependency blocks, and canonical chapter structure.

## Published Explorer

The live explorer is published at
`https://wsollers.github.io/lra-knowledge-explorer/`. Rebuild by running the
governance refresh from `lra-governance`, or trigger
**Actions -> Rebuild Knowledge Explorer -> Run workflow** in
`lra-knowledge-explorer`.
