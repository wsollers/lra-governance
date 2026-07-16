# Multi-Repo Integration

Source: `REPOSITORY_STRUCTURE.md` and current GitHub Actions workflows.

## Integration Direction

Repositories are independent. Nothing is fanned out, and there is no
volume-to-monorepo content sync.

- `lra-governance` is consumed directly by agents, wrappers, and the build
  image. It does not fan out governance artifacts into other repos. It also owns
  the canonical YAML vocabulary (`predicates.yaml`, `notation.yaml`,
  `relations.yaml`).
- `lra-common` is consumed directly by builds, normally through the Docker image
  or an explicit checkout. It does not fan out `common/` into other repos.
- `lra-volume-*` build independently and publish PDFs to `lra-volumes-output`.
  They do not sync content into any monorepo.
- `lra-lean` and `lra-nurbs` are independent specialist repos. They do not sync
  into a monorepo.
- The theorem-explorer rebuild is orchestrated from `lra-governance`, reading the
  independent volume repos (see `docs/workflows/knowledge-extraction.md`).
- `Learning-Real-Analysis`, the former assembled monorepo, is retired.
- `lra-pdf-extractor` is an independent tool repo and is not a source of direct
  sync into notes.
- `lra-reading-categorizer` is an independent local collection-management repo
  and is not a source of direct sync into notes, bibliography shards,
  source-profile manifests, extractor outputs, canonical YAML, or
  theorem-explorer data.
- `lra-source-profiles` is an independent profile/staging repo and is not a
  source of direct sync into notes, bibliography shards, canonical YAML, or
  theorem-explorer data.

## Governance Resolution

Governance validator and audit tool implementations are not forked into leaf
repositories. Leaf-local `tools/governance/*.py` files, when present, are thin
wrappers that delegate to the canonical implementation in
`lra-governance/tools/governance/`. Wrappers resolve `lra-governance` through
`LRA_GOVERNANCE_ROOT`, a sibling `../lra-governance` checkout, or the build
Docker image, and fail with an actionable message if none is available.

## Generated Wrapper Policy

Generated wrapper work is local and wrapper-only. It must not copy canonical
governance implementations or shared docs into downstream repos. Wrapper
generation is dry-run by default and full-replace only after review (see
`docs/workflows/generated-wrapper-sync.md`).

## Emergency Local Edits

Emergency downstream edits are temporary. The fix must be ported back to the
owning source repo before the next regeneration.

## lra-pdf-extractor

`lra-pdf-extractor` is a tool/staging repo. It may generate candidate LaTeX,
BibTeX, JSON, and review artifacts, but those outputs are not automatically
synced into downstream repos.

Integration into `lra-common`, `lra-volume-*`, or `lra-knowledge-explorer` must
occur through reviewable PRs in the owning repo.

Generated agent wrappers for this repo, if needed, must delegate to
`lra-governance` instead of copying governance implementations.

## lra-reading-categorizer

`lra-reading-categorizer` is a local reading-library categorization UI. It may
import reviewed source-profile data into a recoverable queue, maintain the
approved reading taxonomy, copy PDFs into managed `readings/` folders through
explicit UI actions, and export categorization progress for review.

Those outputs are not automatically synced into `lra-source-profiles`,
`lra-pdf-extractor`, `lra-volume-*`, or `lra-knowledge-explorer`. Integration
must occur through reviewable changes in the owning repo.

Generated agent wrappers for this repo, if needed, must delegate to
`lra-governance` instead of copying governance implementations.

## lra-source-profiles

`lra-source-profiles` is a source profile and review staging repo. It may
generate source manifests, category placements, active profile selections,
cached Markdown extracts, and stable project attachment exports, but those
outputs are not automatically synced into downstream repos.

Integration into `lra-volume-*`, `lra-knowledge-explorer`, or final bibliography
shards must occur through reviewable changes in the owning repo.

Generated agent wrappers for this repo, if needed, must delegate to
`lra-governance` instead of copying governance implementations.
