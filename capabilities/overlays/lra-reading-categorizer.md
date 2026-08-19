# Repo Overlay -- lra-reading-categorizer

Repo identity: Reading library categorization UI.

Human-in-the-loop UI and taxonomy tooling for categorizing the local
mathematical PDF collection. Outputs are local reading-library placement and
review artifacts, not direct volume/source-profile integration.

Owned concerns: the categorization UI; the approved reading subject taxonomy
and matching directory scaffold; the recoverable SQLite categorization
queue; review exports summarizing progress; conservative copy-only placement
of PDFs into managed reading folders.

Not owned: original PDF files outside the repository; source-profile
manifests or active-profile exports (`lra-source-profiles`); PDF text
extraction, OCR, or bibliography normalization (`lra-pdf-extractor` /
`lra-source-profiles`); final LRA note content or bibliography shards;
canonical YAML; theorem explorer internals; Lean, NURBS/Vulkan, or
numerical-analysis rules.

## Abilities

Agents may: import a deduplicated categorization queue from reviewed
source-profile data; maintain the taxonomy under `taxonomy/` and its
scaffolds under `subjects/` and `readings/`; update the Python UI under
`src/reading_categorizer/` and operator entrypoints under `scripts/`; export
review/progress CSVs under `review/`; copy PDFs into managed
`readings/<main>/<sub>/` destinations only through the repo's explicit save
workflow. These are local collection-management abilities; they do not
authorize changes to source-profile manifests, extractor outputs, volume
content, bibliography shards, canonical YAML, or explorer data.

## Safety Rules

- Original PDFs outside the repository (including any configured reading
  root or source-profile path) must not be modified, moved, deleted, or
  renamed.
- PDF placement is copy-only unless the user explicitly asks for a move with
  confirmed paths; never overwrite existing managed PDFs silently.
- The SQLite queue under `data/` is recoverable local state; do not commit
  machine-local queue databases unless a task explicitly promotes a fixture
  or review artifact.
- Classifier output and imported source-profile metadata are hints; human
  review in the UI is the authority for final category placement.

## Integration Boundary

Outputs may inform source-profile cleanup, reading-library organization, or
later bibliography work, but integration happens through the owning
repository's normal review path. If categorization work reveals that another
repo needs a change, report the owning repo and required follow-up instead
of applying it from here.

Layout gate:

- `python tools/governance/validate_code_repo_layout.py --root <repo-root> --repo lra-reading-categorizer --governance-root <lra-governance>`

## Success gates

- `python -m unittest discover -s tests`

Use the local `README.md`, `taxonomy/subjects.yaml`, and local tests for
operational details.
