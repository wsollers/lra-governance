# Repo Overlays

Repo overlays are additive rule layers. They clarify how global governance
applies to one repository or repository class.

They must not become divergent forks of global rules.

Specialist rule placement:

- Lean-specific proof implementation rules belong only in `lra-lean.md`.
- C++ / Vulkan / simulation rules belong only in `lra-nurbs.md`.
- Numerical-analysis / benchmark / plotting rules belong only in
  `lra-numerical-analysis.md`.
- PDF/source ingestion, bibliography extraction, local-model cleanup, and
  candidate staging rules belong only in `lra-pdf-extractor.md`.
- Reading-library PDF categorization UI, taxonomy, queue state, and managed
  reading-folder placement rules belong only in `lra-reading-categorizer.md`.
- Source-profile selection, source classification, active-profile export, and
  project attachment staging rules belong only in `lra-source-profiles.md`.
- Volume repos receive only volume-content guidance, except where a named
  volume overlay records cross-repository metadata contracts.
- Digital/print edition behavior and breadcrumb/footer chrome are global volume
  standards. Volume overlays should reference those standards instead of
  restating them.

Specialist overlays now include:

- `lra-lean.md`
- `lra-nurbs.md`
- `lra-knowledge-explorer.md`
- `lra-numerical-analysis.md`
- `lra-pdf-extractor.md`
- `lra-reading-categorizer.md`
- `lra-proof-vault.md`
- `lra-source-profiles.md`

Volume-class overlays now include:

- `lra-volume.md`
- `lra-volume-ii.md`

Each generated downstream wrapper should combine the global rules with exactly
the matching overlay. Overlays should link to local README or workflow files
for operational details instead of copying large local technical manuals.

## Specialist Repo Routing Matrix

Use this matrix when deciding which governance docs to load for specialist repo
work. Do not combine specialist overlays unless the task explicitly crosses the
integration boundary.

| Repository | Overlay | Required governance / architecture docs | Local docs | Validation entrypoint |
| --- | --- | --- | --- | --- |
| `lra-source-profiles` | `docs/governance/repo-overlays/lra-source-profiles.md` | `docs/architecture/repository-layout.md`, `docs/architecture/multi-repo-sync.md`, `docs/architecture/knowledge-pipeline.md` when exports feed explorer or authoring work | `[external:lra-source-profiles] README.md`, relevant `workflows/` docs | `python scripts\validate_source_indexes.py`, `python -m pytest tests` |
| `lra-pdf-extractor` | `docs/governance/repo-overlays/lra-pdf-extractor.md` | `docs/architecture/repository-layout.md`, `docs/architecture/multi-repo-sync.md`, `docs/governance/authoring-standards.md` only for candidate-output shape, `docs/architecture/knowledge-pipeline.md` only for explorer handoff | `[external:lra-pdf-extractor] README.md`, relevant `docs/` files | `python -m pytest tests` |
| `lra-reading-categorizer` | `docs/governance/repo-overlays/lra-reading-categorizer.md` | `docs/governance/code-repo-standards.md`, `docs/architecture/repository-layout.md`, `docs/architecture/multi-repo-sync.md`, `docs/governance/repo-overlays/lra-source-profiles.md` only for imported queue data | `[external:lra-reading-categorizer] README.md`, `taxonomy/subjects.yaml`, local tests | `python -m pytest tests` |
| `lra-lean` | `docs/governance/repo-overlays/lra-lean.md` | `docs/architecture/lra-lean-architecture.md`, `docs/architecture/semantic-artifact-record.md` when mapping Lean declarations to semantic artifacts | `[external:lra-lean] README.md`, nearest Lean module | `.\build.ps1 docker-build`, `.\build.ps1 build-all` on Windows; Docker/Lake gates from the overlay otherwise |
| `lra-knowledge-explorer` | `docs/governance/repo-overlays/lra-knowledge-explorer.md` | `docs/architecture/knowledge-pipeline.md`, `docs/architecture/theorem-explorer-pipeline.md`, `docs/workflows/knowledge-extraction.md`, `docs/governance/extraction-standards.md` | `[external:lra-knowledge-explorer] README.md`, `PIPELINE.md` | `python -m pytest tests`; extraction smoke commands only when graph output changes |

Generated capability overlays under `capabilities/overlays/` are resolver
summaries derived from `capabilities/overlays-config.yaml`. They must include
all specialist repos so `build-repo` can route validation, but they do not
replace the canonical overlays above.

The Python-based specialist repos currently use the shared resolver kind
`python_tool`: `lra-knowledge-explorer`, `lra-pdf-extractor`, and
`lra-reading-categorizer`, and `lra-source-profiles`. They all enter validation
through `build-repo` and declare repo-local success gates in
`capabilities/overlays-config.yaml`. Do not infer validation from whether a repo
happens to have `scripts/`, `tools/`, or `src/`; read the configured gates and
the repo-local README.

Shared code layout and style rules live in
`docs/governance/code-repo-standards.md` and are enforced by
`tools/governance/validate_code_repo_layout.py`.
