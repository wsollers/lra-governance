# LRA Governance

This repository is the canonical source for project-wide governance,
architecture, prompts, schemas, validators, generators, and the canonical
mathematical vocabulary used across the Learning Real Analysis multi-repo
workspace.

## Source Of Truth

- `DESIGN.md`
- `REPOSITORY_STRUCTURE.md`
- `AGENTS.md`
- `.gitignore`
- `constitution/`
- `docs/`
- `tools/`
- canonical YAML: `predicates.yaml`, `notation.yaml`, `relations.yaml`

These files are consumed in place. They are **not** copied or synced into the
other repositories.

## How Repos Reach Governance

`lra-governance` is no longer fanned out into downstream repos. Each repo reads
it directly from a sibling checkout in a shared multi-repo workspace:

```text
<workspace>/
  lra-governance/     <- this repo (canonical)
  lra-common/         <- shared LaTeX infrastructure (canonical)
  lra-volume-i/
  lra-volume-ii/
  ...
```

From any repo at `<workspace>/<repo>`, governance resolves as
`<repo>/../lra-governance` and shared LaTeX infrastructure as
`<repo>/../lra-common`.

Resolution order used by the local wrapper scripts:

1. `LRA_GOVERNANCE_ROOT` (and the equivalent for common) when set;
2. a sibling `../lra-governance` / `../lra-common` checkout;
3. the path baked into the build Docker image.

If none resolve, the wrappers **hard-error** with an actionable setup message
instead of silently degrading. There are no local synced copies to fall back
on.

## Independence (No More Sync)

The previous one-way governance/common fan-out sync and the volume-to-monorepo
content sync are both retired:

- governance and common are read directly, never copied downstream;
- each `lra-volume-*` repo is self-contained and builds its own PDFs
  independently, checking out `lra-governance` and `lra-common` at build time in
  a Docker container (see `templates/volume-validate-and-compile.yml`);
- there is no assembled monorepo. `Learning-Real-Analysis` is retired.

## Per-Repo Overlays

Each repo may carry a local overlay document that adds repo-specific context on
top of the canonical governance. Overlays are additive: they refine the global
rules for that repo's owned work and must not fork or weaken them. The canonical
overlay sources live in `docs/governance/repo-overlays/`.

## Where To Edit

Make every governance change here, in the smallest applicable document. Do not
treat a downstream repo's generated wrappers or local overlay as a source of
truth; those are generated or additive artifacts. See `DESIGN.md` for the task
router.
