# Multi-Repo Sync

Source: `REPOSITORY_STRUCTURE.md` and current GitHub Actions workflows.

## Sync Direction

- `lra-governance` syncs governance artifacts outward.
- `lra-common` syncs `common/` and `bibliography/` outward.
- `lra-volume-*` sync volume content into `Learning-Real-Analysis`.
- `lra-lean` syncs into `Learning-Real-Analysis/lean/`.
- `lra-nurbs` syncs into `Learning-Real-Analysis/nurbs_dde/`.
- `Learning-Real-Analysis` dispatches theorem-explorer rebuilds.

## Full-Replace Policy

Existing workflows use `rsync --delete` for full-replace sync. Future
governance generation must include dry-run output and drift checks before any
full replacement.

## Emergency Local Edits

Emergency downstream edits are temporary. The fix must be ported back to the
owning source repo before the next sync.
