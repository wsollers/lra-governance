# Retired Workflows

These workflow files implemented the old multi-repo sync model and are retired.
They are kept here for historical reference only and are not active (they no
longer live under `.github/workflows/`). They are safe to `git rm` once you no
longer want the history inline.

| File | Why retired |
| --- | --- |
| `sync-governance.yml` | Governance is no longer fanned out into downstream repos. Repos read `lra-governance` directly via `LRA_GOVERNANCE_ROOT`, a sibling `../lra-governance` checkout, or the build Docker image. |
| `sync-to-monorepo-volume.yml` | The assembled monorepo (`Learning-Real-Analysis`) is retired, so there is no volume-to-monorepo content sync. Each `lra-volume-*` repo builds independently (`templates/volume-validate-and-compile.yml`). |

The current integration model is documented in `REPOSITORY_STRUCTURE.md` and
`docs/architecture/multi-repo-sync.md`.
