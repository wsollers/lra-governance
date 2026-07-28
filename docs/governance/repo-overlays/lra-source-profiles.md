# lra-source-profiles Overlay

This overlay applies to `lra-source-profiles`.

## Owned Concerns

`lra-source-profiles` owns tooling and metadata for:

- dynamic source profiles for Learning Real Analysis,
- candidate mathematical source classification,
- proposed category placement,
- reviewable folder-to-volume mappings used to seed volume source candidates,
- volume-level source workbench profiles with ordered enabled selections,
- volume/chapter source indexes,
- chapter-level source selection overrides when a topic needs a narrower or
  different stack than the volume workbench,
- reusable named source profiles,
- active source selections,
- stable active-profile exports for project attachment slots,
- Chrome/PDF tab launch order derived from active enabled source selections,
- cached Markdown extracts derived from reviewed source metadata,
- conservative PDF import, scan, move, and review workflows,
- source manifest validation and profile audit workflows.

## Non-Owned Concerns

`lra-source-profiles` does not own:

- final LRA note content,
- final volume-owned bibliography shards,
- canonical predicate / notation / relation YAML,
- shared LaTeX infrastructure,
- theorem explorer internals or generated graph data,
- global governance standards,
- Lean formalization rules,
- NURBS / Vulkan / simulation rules,
- numerical-analysis benchmark rules,
- PDF-extractor implementation rules.

## Project Overlay Abilities

Agents working in this repo may use its project-local tools to:

- scan configured reading roots and copy PDFs into local working folders,
- apply `docs/governance/source-indexing-policy.yaml` when recursively
  discovering indexable PDFs,
- classify candidate sources into proposed categories,
- maintain auditable folder-to-volume maps that seed candidate source stacks
  without moving or deleting original PDFs,
- maintain volume-level workbench profiles whose enabled sources are ordered by
  reviewed preference for study, authoring preparation, attachment export, and
  Chrome tab launch,
- maintain chapter-level overrides only where the volume workbench is too broad
  or misses topic-specific sources,
- maintain `volumes/<volume>/<chapter>/source-index.yaml` metadata,
- write approved selections to `active-sources.yaml`,
- maintain `misplaced-sources.yaml` and the misplaced review queue,
- generate and validate source indexes,
- export active profiles into stable `active-profile/sourceNN.md` slots,
- export named profiles into the same stable attachment-slot shape,
- import new PDFs with optional known Google Drive URLs,
- generate or refresh per-source Markdown cache files.

These abilities are staging and review abilities. They do not authorize direct
writes into volume notes, final bibliography shards, canonical YAML, or theorem
explorer generated data.

## Safety Rules

Original PDFs outside the repository, including configured reading roots such
as `D:\readings`, must not be modified.

Do not delete original files, overwrite existing source files silently, or
invent bibliographic data. Uncertain metadata must remain marked for review
with confidence and notes.

Recursive source-index scans must honor the canonical source indexing policy in
`docs/governance/source-indexing-policy.yaml` by default. Excluded library-only
roots may be indexed only by an explicit local override.

Local copied PDFs and generated scratch artifacts should remain untracked unless
a task explicitly promotes a specific artifact to reviewed source material.

When moving sources between categories or chapters, preserve source IDs, hash
metadata, review notes, and duplicate-status information unless an explicit
cleanup task says otherwise.

## Integration Boundary

Outputs from `lra-source-profiles` may inform authoring, bibliography, and
source-review work in other repos, but integration must happen through the
owning repository's normal review path.

If source-profile work reveals that final note content, bibliography entries,
canonical YAML, or extraction records need changes, report the owning repo and
required follow-up rather than applying those changes from this repo.

## Governance Doc Set

Load these governance documents for source-profile work:

- `docs/governance/repo-overlays/lra-source-profiles.md`;
- `docs/governance/source-indexing-policy.md` when scanning or indexing the
  external reading library;
- `docs/architecture/repository-layout.md`;
- `docs/architecture/multi-repo-sync.md`;
- `docs/architecture/knowledge-pipeline.md` only when active-profile exports
  feed authoring or explorer work;
- `docs/governance/repo-overlays/lra-pdf-extractor.md` only when coordinating
  PDF ingestion and Markdown extraction boundaries.

Use the local `[external:lra-source-profiles] README.md`, `workflows/`, source
indexes, and scripts for operational details.
Shared Python layout and code-style rules live in
`docs/governance/code-repo-standards.md` and are enforced by
`tools/governance/validate_code_repo_layout.py` through the shared
`build-repo` path.
