# Repository Layout

Source: `REPOSITORY_STRUCTURE.md`.

## Source Of Truth Map

Repositories are independent. There is no fan-out sync and no volume-to-monorepo
content sync; the "ownership" column below is authority, not a copy direction.

| Repository | Canonical ownership |
| --- | --- |
| `lra-governance` | Governance docs, architecture docs, repo overlays, prompts, schemas, constitution files, generators, governance tools, and the canonical YAML vocabulary (`predicates.yaml`, `structures.yaml`, `notation.yaml`, `relations.yaml`). Consumed directly; never fanned out. |
| `lra-common` | Shared LaTeX infrastructure: `common/`. Consumed directly by builds through the Docker image or an explicit checkout. |
| `lra-volume-i` through `lra-volume-viii` | Volume content under `volume-N/`. Self-contained, Overleaf-ready, independently built; publishes PDFs to `lra-volumes-output`. |
| `lra-lean` | Lean 4 formalization workspace. Independent. |
| `lra-nurbs` | C++ / Vulkan / geometry / simulation workspace. Independent. |
| `lra-knowledge-explorer` | Extraction pipeline and HTML theorem explorer. Rebuilt by the governance-orchestrated refresh over the volume repos. |
| `lra-numerical-analysis` | Numerical methods, experiments, benchmarks, plots, numerical reports. Independent. |
| `lra-pdf-extractor` | PDF/source ingestion, bibliography extraction and normalization, candidate extraction, review workflow, staged outputs. Independent tool repo; reviewable candidates only. |
| `lra-reading-categorizer` | Human-in-the-loop UI, taxonomy, queue state, review exports, and managed reading-folder scaffold for categorizing a local mathematical PDF collection. Independent collection-management repo. |
| `lra-source-profiles` | Dynamic source profiles, candidate classification, active source indexes, attachment exports, source review workflow. Independent profile/staging repo; reviewed artifacts only. |
| `lra-volumes-output` | Published digital and print PDFs from independent volume builds. |

`Learning-Real-Analysis`, the former assembled monorepo, is retired. There is no
omnibus assembly target; canonical YAML formerly owned there now lives in
`lra-governance`.

`lra-pdf-extractor` is an acceleration and staging tool. It does not own
downstream notes, bibliography, canonical YAML, theorem explorer internals, or
governance rules.

`lra-source-profiles` is a source selection and profile staging tool. It does
not own final LRA note content, final bibliography shards, canonical YAML,
theorem explorer internals, or governance rules.

`lra-reading-categorizer` is a local collection-management UI for assigning
PDFs to the approved reading taxonomy. It does not own source-profile manifests,
extractor outputs, final LRA note content, final bibliography shards, canonical
YAML, theorem explorer internals, or governance rules.

## Governance And Common Resolution

Downstream repos do not carry synced governance or common copies. Governance
docs are read from `lra-governance` directly; shared LaTeX infrastructure is read
from `lra-common` directly.

Governance tool implementations remain canonical in
`lra-governance/tools/governance/`. Downstream leaf repositories may contain thin
wrappers at matching paths so local commands keep working, but those wrappers
resolve `lra-governance` through `LRA_GOVERNANCE_ROOT`, a sibling
`../lra-governance` checkout, or the build Docker image, and fail when none is
available.
