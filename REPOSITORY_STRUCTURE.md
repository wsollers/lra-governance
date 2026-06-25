# LRA Repository Structure

This file is the canonical map for the Learning Real Analysis multi-repo
workspace. `DESIGN.md` contains the writing and artifact rules; this file
contains repository ownership, layout, and integration rules.

## Source Of Truth Map

| Repository | Canonical ownership |
|---|---|
| `lra-governance` | `DESIGN.md`, `REPOSITORY_STRUCTURE.md`, `AGENTS.md`, `.gitignore`, `constitution/`, `docs/`, `tools/`, generators, schemas, prompts, and the canonical YAML (`predicates.yaml`, `notation.yaml`, `relations.yaml`) |
| `lra-common` | shared LaTeX infrastructure: `common/` |
| `lra-volume-i` through `lra-volume-viii` | volume content under `volume-N/`; self-contained, Overleaf-ready, independently built |
| `lra-lean` | Lean 4 formalization workspace; independent |
| `lra-nurbs` | NURBS/DDE C++ / Vulkan / geometry / simulation engine; independent |
| `lra-knowledge-explorer` | extraction pipeline, HTML theorem graph, GitHub Pages site |
| `lra-numerical-analysis` | numerical methods, experiments, benchmarks, plots, numerical reports; independent |
| `lra-pdf-extractor` | PDF/source ingestion, bibliography extraction, candidate staging; independent tool repo, reviewable candidates only |
| `lra-source-profiles` | dynamic source profiles, classification, active source indexes, attachment exports; independent profile/staging repo |
| `lra-volumes-output` | published digital and print PDFs from independent volume builds |

`Learning-Real-Analysis`, the former assembled monorepo, is **retired**. There
is no omnibus assembly target and no volume-to-monorepo sync; each volume builds
independently. The canonical YAML formerly owned there now lives in
`lra-governance`.

## Integration Model

Repositories are independent. There is no governance/common fan-out sync and no
volume-to-monorepo content sync.

- `lra-governance` and `lra-common` are read directly, never copied downstream.
- Each repo resolves them via `LRA_GOVERNANCE_ROOT` (and the common equivalent),
  a sibling `../lra-governance` / `../lra-common` checkout, or the build Docker
  image, in that order.
- Local wrapper scripts hard-error if neither resolves. There are no synced
  local copies to fall back on.
- Each `lra-volume-*` repo builds its own digital and print PDFs in a Docker
  container that checks out `lra-governance` and `lra-common` at build time
  (`templates/volume-validate-and-compile.yml`) and publishes the results to
  `lra-volumes-output`.

## Governance Repo Layout

```text
lra-governance/
  AGENTS.md
  DESIGN.md
  REPOSITORY_STRUCTURE.md
  README.md
  .gitignore
  predicates.yaml             canonical vocabulary (moved from the retired monorepo)
  notation.yaml
  relations.yaml
  constitution/
    master.md
    prompts/
    schema/
    schemas/
  docs/
    agent-task-index.md
    architecture/
    governance/
      repo-overlays/
    workflows/
  tools/
    governance/
  templates/
    volume-validate-and-compile.yml    independent per-volume build
  scripts/
```

Governance files are edited here and consumed in place. Downstream repos do not
carry synced copies.

## Common Repo Layout

```text
lra-common/
  common/
    preamble.tex
    colors.tex
    environments.tex
    macros.tex
    boxes.tex
    exercise-format.tex
    volume-preamble.tex
  bibliography/
    README.md                 retired mirror note; not a sync source
```

`common/` is owned by `lra-common` and consumed directly by builds through the
Docker image or an explicit checkout. It is not copied into volume repos.
Bibliography entries are edited in the owning `lra-volume-*` shard.

## Volume Repo Layout

Each volume repo is self-contained, Overleaf-ready, and independently built.

```text
lra-volume-N/
  main.tex                    Overleaf / Docker build root
  .latexmkrc                  local build config
  bibliography/               volume-owned bibliography shard
  volume-N/
    index.tex
    <chapter>/
      index.tex
      chapter.yaml
      notes/
      proofs/
```

At build time the volume checks out `lra-common` (for `common/`) and
`lra-governance` (for validators and canonical YAML). These are supplied by the
build environment, not stored as synced copies in the volume repo. `main.tex`
inputs the volume preamble and `volume-N/index`.

## Canonical Chapter Layout

```text
<chapter>/
  index.tex
  chapter.yaml
  notes/
    index.tex
    <section>/
      notes-<section>.tex
      figure-<n>.tex
  proofs/
    index.tex
    notes/
      index.tex
      prf-<result-id>.tex
    exercises/
      index.tex
      capstone-<chapter>.tex
```

The chapter `index.tex` is the only file that inputs `proofs/index.tex`.
`proofs/notes/index.tex` inputs proof files in dependency order. Exercise and
capstone material lives under `proofs/exercises/`.

## Integration Rules

- Governance and shared LaTeX infrastructure are read directly from
  `lra-governance` and `lra-common`; nothing is fanned out.
- Bibliography shards are owned by each volume repo.
- Canonical YAML lives in `lra-governance`. Tools resolve it the same way they
  resolve the rest of governance; it is not duplicated into volume repos.
- Volume builds are independent and publish PDFs to `lra-volumes-output`.

---

## Knowledge Explorer Pipeline

The knowledge explorer at `lra-knowledge-explorer` is rebuilt from the
independent volume repositories through a governance-orchestrated refresh, not
from an assembled monorepo. The refresh is run from `lra-governance` (see
`docs/workflows/knowledge-extraction.md`).

```text
lra-volume-i ... lra-volume-viii      canonical TeX source
        |
        v
lra-governance refresh                preflight, extract, validate, combine
        |
        v
lra-knowledge-explorer                knowledge.json, graph-edges.json
        |
        v
GitHub Pages explorer
```

The live explorer is published at:

```text
https://wsollers.github.io/lra-knowledge-explorer/
```

### Source rule

Extraction reads the split volume repos directly. The retired monorepo is not an
extraction source. Missing volume repos, chapter directories, `notes/index.tex`,
or `proofs/index.tex` are hard errors.

### Manual rebuild

Run the governance refresh from `lra-governance`, or trigger
**Actions -> Rebuild Knowledge Explorer -> Run workflow** in
`lra-knowledge-explorer`.
