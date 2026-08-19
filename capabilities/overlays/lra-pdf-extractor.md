# Repo Overlay -- lra-pdf-extractor

Repo identity: PDF/source ingestion and candidate extraction tooling.

PDF/source ingestion, bibliography normalization, candidate extraction,
OCR/cleanup assistance, and staged review outputs.

Owned concerns: PDF and source-file ingestion; text extraction and cleanup;
bibliography metadata extraction, normalization, and duplicate detection;
candidate `.bib` entry generation; candidate mathematical artifact
extraction; note decoration assistance; local-model-assisted cleanup and
classification; Python GUI review workflows; staged LaTeX, BibTeX, JSON, and
review-queue outputs.

Not owned: final LRA note content; canonical predicate/notation/relation
YAML; shared LaTeX infrastructure; theorem explorer internals; global
governance standards; generated agent wrappers; Lean, NURBS/Vulkan,
numerical-analysis, or volume-specific authoring rules.

## Integration Boundary

Candidate artifacts for other repos must be reviewed and applied through
normal PRs in the owning repository. Never directly overwrite volume note
files, volume-owned `.bib` shards under `lra-volume-*/bibliography/`,
canonical YAML, theorem-explorer generated data, or governance files.

## Local Model Use

Local models may assist with OCR cleanup, hyphenation and ligature repair,
source metadata extraction, candidate classification, low-risk
summarization, and draft decoration suggestions. They must not be treated as
authorities for final mathematical rewrites, invented predicates or labels,
direct note insertion, silent bulk edits, or volume-owned bibliography
updates.

Layout gate:

- `python tools/governance/validate_code_repo_layout.py --root <repo-root> --repo lra-pdf-extractor --governance-root <lra-governance>`

## Success gates

- `python -m pytest tests`

Use the local `README.md`, `pyproject.toml`, `src/`, `tests/`, and local
docs for implementation details.
