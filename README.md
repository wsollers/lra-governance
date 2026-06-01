# LRA Governance

This repository is the canonical source for project-wide governance files used
by the Learning Real Analysis split-repo workspace.

## Source Of Truth

- `DESIGN.md`
- `REPOSITORY_STRUCTURE.md`
- `.gitignore`
- `constitution/`

These files are synced one-way into the monorepo, volume repos, and shared
common repo so local work in any repo has the same project rules available at
the repository root.

## Sync Direction

```text
lra-governance -> Learning-Real-Analysis
lra-governance -> lra-common
lra-governance -> lra-volume-i
lra-governance -> lra-volume-ii
lra-governance -> lra-volume-iii
lra-governance -> lra-volume-iv
lra-governance -> lra-volume-v
lra-governance -> lra-volume-vi
lra-governance -> lra-volume-vii
lra-governance -> lra-volume-viii
```

Do not edit synced governance files in downstream repos. Make changes here and
let the workflow distribute them.
