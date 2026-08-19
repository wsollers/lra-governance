# Repo Overlay -- lra-source-profiles

Repo identity: Source profiles, source indexes, and active profile exports.

Source-profile metadata, active source selections, volume/chapter source
indexes, cached Markdown extracts, and attachment-slot exports. Outputs are
staging/review inputs for owning repos.

Owned concerns: dynamic source profiles; candidate source classification and
proposed category placement; reviewable folder-to-volume mappings;
volume-level source workbench profiles with ordered enabled selections;
volume/chapter source indexes and chapter-level overrides; reusable named
profiles; active source selections and stable active-profile exports for
project attachment slots; Chrome/PDF tab launch order; cached Markdown
extracts; conservative PDF import, scan, move, and review workflows; source
manifest validation and profile audit workflows.

Not owned: final LRA note content; final volume-owned bibliography shards;
canonical YAML; shared LaTeX infrastructure; theorem explorer internals;
global governance standards; Lean, NURBS/Vulkan, numerical-analysis, or
PDF-extractor implementation rules.

## Abilities

Agents may use the repo's project-local tools to: scan configured reading
roots and copy PDFs into local working folders; apply the canonical
source-indexing policy when recursively discovering indexable PDFs; classify
candidate sources; maintain auditable folder-to-volume maps without moving
or deleting original PDFs; maintain volume workbench profiles and
chapter-level overrides (overrides only where the volume workbench is too
broad or misses topic-specific sources); maintain
`volumes/<volume>/<chapter>/source-index.yaml`; write approved selections to
`active-sources.yaml`; maintain `misplaced-sources.yaml` and its review
queue; generate and validate source indexes; export active and named
profiles into stable `active-profile/sourceNN.md` slots; import new PDFs
with optional known Google Drive URLs; generate or refresh per-source
Markdown caches; query the omnibus theorem and Markdown indexes with ranked
topic search before raw codesearch; recover a source TOC from existing
extraction, frontmatter/evidence packets, or OCR when the TOC record is
missing or stale.

These are staging and review abilities; they do not authorize direct writes
into volume notes, final bibliography shards, canonical YAML, or explorer
data.

## Safety Rules

- No source ever remains outside the source tree: raw files scanned,
  acquired, imported, or discovered under the reading-library root move
  under the normal `Sources/` tree as soon as placement can be determined;
  temporary out-of-tree staging is allowed only while placement is genuinely
  unknown, with the review queue preserving the obligation to move it.
- Original PDFs outside the repository (including configured reading roots
  such as `D:\readings`) must not be modified.
- Do not delete original files, overwrite existing source files silently, or
  invent bibliographic data; uncertain metadata stays marked for review with
  confidence and notes.
- Recursive source-index scans honor the canonical source-indexing policy by
  default; excluded library-only roots may be indexed only by an explicit
  local override.
- Local copied PDFs and generated scratch artifacts stay untracked unless a
  task explicitly promotes a specific artifact.
- When moving sources between categories or chapters, preserve source IDs,
  hash metadata, review notes, and duplicate-status information unless an
  explicit cleanup task says otherwise.

## Integration Boundary

Outputs may inform authoring, bibliography, and source-review work in other
repos, but integration happens through the owning repository's normal review
path. If source-profile work reveals that final note content, bibliography
entries, canonical YAML, or extraction records need changes, report the
owning repo and required follow-up rather than applying them from here.

Layout gate:

- `python tools/governance/validate_code_repo_layout.py --root <repo-root> --repo lra-source-profiles --governance-root <lra-governance>`

## Success gates

- `python scripts/validate_source_indexes.py`
- `python -m pytest tests`

Use the local `README.md`, `workflows/`, source indexes, and scripts for
operational details.
