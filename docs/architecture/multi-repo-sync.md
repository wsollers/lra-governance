# Multi-Repo Integration

Source: `REPOSITORY_STRUCTURE.md` and current GitHub Actions workflows.

## Integration Direction

- `lra-governance` is consumed directly by agents, wrappers, and the build
  image; it does not fan-out sync governance artifacts into other repos.
- `lra-common` is consumed directly by builds, normally through the Docker image
  or an explicit checkout; it does not fan-out sync `common/` into other repos.
- `lra-volume-*` sync volume content into `Learning-Real-Analysis`.
- `lra-lean` syncs into `Learning-Real-Analysis/lean/`.
- `lra-nurbs` syncs into `Learning-Real-Analysis/nurbs_dde/`.
- `Learning-Real-Analysis` dispatches theorem-explorer rebuilds.
- `lra-pdf-extractor` is an independent tool repo and is not currently a
  source of direct sync into notes.
- `lra-source-profiles` is an independent profile/staging repo and is not
  currently a source of direct sync into notes, bibliography shards, canonical
  YAML, or theorem-explorer data.

Governance validator and audit tool implementations are not forked into leaf
repositories. Leaf-local `tools/governance/*.py` files, when present, are
wrappers that delegate to the canonical implementation in
`lra-governance/tools/governance/` and fail if that canonical checkout is not
available.

## Full-Replace Policy

Existing content-integration workflows may use `rsync --delete` for
full-replace content sync. Governance and common fan-out syncs are disabled.

Generated wrapper work is local and wrapper-only. It must not copy canonical
governance implementations into downstream repos.

## Emergency Local Edits

Emergency downstream edits are temporary. The fix must be ported back to the
owning source repo.

## lra-pdf-extractor

`lra-pdf-extractor` is a tool/staging repo. It may generate candidate LaTeX,
BibTeX, JSON, and review artifacts, but those outputs are not automatically
synced into downstream repos.

Integration into `lra-common`, `Learning-Real-Analysis`, `lra-volume-*`, or
`lra-knowledge-explorer` must occur through reviewable PRs in the owning repo.

Generated agent wrappers for this repo, if needed, must delegate to
`lra-governance` instead of copying governance implementations.

## lra-source-profiles

`lra-source-profiles` is a source profile and review staging repo. It may
generate source manifests, category placements, active profile selections,
cached Markdown extracts, and stable project attachment exports, but those
outputs are not automatically synced into downstream repos.

Integration into `Learning-Real-Analysis`, `lra-volume-*`,
`lra-knowledge-explorer`, or final bibliography shards must occur through
reviewable changes in the owning repo.

Generated agent wrappers for this repo, if needed, must delegate to
`lra-governance` instead of copying governance implementations.
