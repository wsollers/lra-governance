# lra-pdf-extractor Overlay

This overlay applies to `lra-pdf-extractor`.

## Owned Concerns

`lra-pdf-extractor` owns tooling for:

- PDF and source-file ingestion,
- text extraction and cleanup,
- bibliography metadata extraction and normalization,
- duplicate bibliography detection,
- candidate `.bib` entry generation,
- candidate mathematical artifact extraction,
- note decoration assistance,
- local-model-assisted cleanup and classification,
- Python GUI workflows for reviewing and organizing extracted candidates,
- staged LaTeX, BibTeX, JSON, and review-queue outputs.

## Non-Owned Concerns

`lra-pdf-extractor` does not own:

- final LRA note content,
- canonical predicate / notation / relation YAML,
- shared LaTeX infrastructure,
- theorem explorer internals,
- global governance standards,
- generated agent instruction wrappers,
- Lean formalization rules,
- NURBS / Vulkan / simulation rules,
- numerical-analysis benchmark rules,
- volume-specific authoring rules.

## Integration Boundary

`lra-pdf-extractor` may produce candidate artifacts for other repos, but those
artifacts must be reviewed and applied through normal PRs in the owning
repository.

It must not directly overwrite:

- volume note files,
- the volume-owned `.bib` shards under `lra-volume-*/bibliography/`,
- canonical YAML files,
- theorem explorer generated data,
- governance files.

## Local Model Use

Local models may assist with:

- OCR cleanup suggestions,
- hyphenation and ligature repair suggestions,
- source metadata extraction,
- candidate artifact classification,
- low-risk summarization,
- draft decoration suggestions.

Local models must not be treated as authorities for:

- final mathematical rewrites,
- invented predicates,
- invented labels,
- direct note insertion,
- silent bulk edits,
- volume-owned bibliography updates.

## Generated Agent Rules

Generated agent wrappers for this repo receive:

- global safety and ownership rules,
- this `lra-pdf-extractor` overlay,
- Python tooling guidance,
- GUI workflow guidance,
- local-model safety guidance.

It should not receive Lean, NURBS/Vulkan, volume-only, or
numerical-analysis-specific overlays.

## Governance Doc Set

Load these governance documents for PDF-extractor work:

- `docs/governance/repo-overlays/lra-pdf-extractor.md`;
- `docs/architecture/repository-layout.md`;
- `docs/architecture/multi-repo-sync.md`;
- `docs/governance/authoring-standards.md` only when checking staged
  candidate LaTeX shape;
- `docs/architecture/knowledge-pipeline.md` only when producing or handing off
  explorer-facing candidate data.

Use the local `[external:lra-pdf-extractor] README.md`, `pyproject.toml`,
`src/`, `tests/`, and relevant local docs for implementation details.
Shared Python layout and code-style rules live in
`docs/governance/code-repo-standards.md` and are enforced by
`tools/governance/validate_code_repo_layout.py` through the shared
`build-repo` path.

