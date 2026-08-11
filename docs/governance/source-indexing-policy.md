# Source Indexing Policy

This policy governs which personal reading-library PDFs are eligible for the
Learning Real Analysis source index. The machine-readable authority is
`docs/governance/source-indexing-policy.yaml`; tools should consume that file
instead of hard-coding subject folder decisions.

## Responsibility Boundary

`lra-governance` owns the indexability decision: which reading-library folders
are part of the LRA source corpus by default and which are library-only.

`lra-source-profiles` owns implementation: recursive discovery, profile
metadata, cached Markdown, theorem indexes, quality reports, and codesearch
indexes. Its tools should apply this policy by default and may expose an
explicit override for deliberate one-off indexing.

`lra-pdf-extractor` owns extraction mechanics only: text extraction, OCR,
quality signals, and page-level evidence. It should not decide whether a book
belongs in the LRA source corpus.

An optional private `lra-sources` catalog repo may own cross-machine pointer
metadata: where the reviewed source-profile checkout lives, where the local raw
reading library lives, where generated indexes live, and which topic/omnibus
index should be consulted first. It must not own raw PDFs, full extracted book
text, final notes, bibliography shards, canonical YAML, or governance rules.

## Current Reading Library

The default host reading library is `D:\Readings`, with source PDFs organized
under `D:\Readings\Sources`. Generated indexes belong under
`D:\Readings\indexes\lra` so they stay outside Git and inside the backed-up
reading hierarchy.

## Source Catalog Resolution

When a task needs primary-source evidence, agents should resolve source lookup
locations in this order:

1. Use an explicit task path or environment variable when supplied:
   `LRA_SOURCES_ROOT` for the optional private catalog repo,
   `LRA_SOURCE_PROFILES_ROOT` for `lra-source-profiles`, or
   `LRA_READINGS_ROOT` for the host reading library.
2. If an adjacent private `../lra-sources` checkout exists, read its overarching
   catalog index first. The catalog should point to the active
   `lra-source-profiles` checkout, raw reading-library root, generated index
   root, topic source indexes, volume aggregates, and omnibus indexes.
3. If no `lra-sources` catalog is available, use a sibling
   `../lra-source-profiles` checkout and the default `D:\Readings` /
   `D:\Readings\indexes\lra` locations.
4. If neither the catalog nor source-profile/index roots resolve, stop and
   report that primary-source lookup cannot be certified.

The optional catalog is a pointer layer, not a source-data layer. It may contain
small manifests, source IDs, hashes, path templates, profile names, and index
locations. Do not store raw PDFs or full generated Markdown/OCR text in that
repo.

## Primary Source Lookup

Primary mathematical source material is located in the external reading library
under `D:\Readings` (`D:/Readings` in slash-form paths). The source PDFs live
under `D:\Readings\Sources`; generated lookup artifacts live under
`D:\Readings\indexes\lra`.

When adding, normalizing, auditing, or cross-checking theorem-like statements
or definitions, do not guess source wording from memory or web snippets. Look
up primary-source evidence through the reviewed topic indexes and the generated
search indexes:

- an optional private catalog in `[external:lra-sources]`, when present, to
  resolve the active source-profile checkout and generated index roots;
- topic and chapter source indexes in
  `[external:lra-source-profiles] volumes/<volume>/<topic...>/source-index.yaml`;
- volume aggregate source indexes in
  `[external:lra-source-profiles] volumes/<volume>/_sources/source-index.yaml`;
- generated searchable volume caches under
  `D:\Readings\indexes\lra\volumes\<volume>\_sources\`;
- the global omnibus source and theorem indexes under
  `D:\Readings\indexes\lra\omnibus\`.

Use the topic index first when the target volume and topic are known, because
it records the curated local source selection for that subject. Use the omnibus
index when the topic is uncertain, the topic index is sparse, or alternate
terminology may appear in sources assigned elsewhere. For definitions and
theorem-like statements, search both the structured theorem indexes and the
Markdown/codesearch cache, then read the surrounding extracted source text
before treating a hit as evidence.

For open-ended concept queries, use ranked omnibus topic search before raw
codesearch. The ranked search layer strips natural-language filler such as
"theorems related to", scores exact phrase and token overlap across theorem
kind, title, snippet, source title, and volume fields, deduplicates repeated
cache views, and enriches results with source metadata. Raw codesearch remains
the fallback for exact strings, regex patterns, notation variants, and manual
inspection.

Source search should support both global and constrained scopes. Global search
queries the whole generated omnibus corpus. Constrained search may filter by an
explicit author substring, an explicit source ID allow-list, a named profile, a
volume workbench profile, a chapter/topic `source-index.yaml`, or another
curated source-list YAML. By default, source-list constraints should consider
enabled rows only; disabled rows require an explicit override.

For agent lookup spanning primary sources and LRA-authored material, use the
governance facade instead of loading or invoking each index separately:

```powershell
python F:\repos\lra-governance\tools\governance\lra_lookup.py "least upper bound"
python F:\repos\lra-governance\tools\governance\lra_lookup.py "compactness" --scope sources --volume volume-iii
```

`lra_lookup.py` resolves the catalog pointers above, delegates the primary
source lane to `lra-source-profiles/scripts/search_omnibus.py`, and joins only
compact result records from the internal TeX/Lean/C++ and canonical-vocabulary
indexes. It is a query facade, not a new index owner. Use the specialist tools
below for index construction, raw codesearch, or detailed maintenance.

## Volume Source Workbench Profiles

`lra-source-profiles` may maintain volume-level source workbench profiles for
human study and authoring preparation. A volume workbench is the default
preferred source stack for a whole LRA volume; chapter-level source selections
may inherit from or override it when a topic needs a narrower source set.

Volume workbench profiles should be machine-readable and auditable. Each
selected source entry should reference the stable source identity (`source_id`
and, when available, `sha256` or `object_id`) and may record local workflow
metadata such as:

- whether the source is enabled for the current workbench;
- an ordered rank or slot order for preferred-source sorting and Chrome tab
  launch order;
- a review role such as `primary`, `secondary`, `reference`, or `historical`;
- notes explaining local preference, exclusion, or chapter-specific use.

Folder-to-volume mappings are source-profile metadata, not governance facts.
They may seed candidate volume workbenches from reading-library folder
hierarchies, but they must remain reviewable and must not replace source
identity, bibliographic review, or the curated topic and volume source indexes.
Changing a folder-to-volume map must not move, delete, or overwrite original
PDFs.

Chrome tab launchers and attachment-slot exports should consume the enabled
ordered workbench selection. Disabled sources may remain in the profile as
reviewed candidates, but they should not open as active working tabs unless a
tool explicitly requests all candidates.

## Identity Model

The SHA-256 hash of the PDF bytes is the stable source-object identity. File
paths are location metadata and policy context, not source identity.

Hash-keyed derived artifacts should live under
`D:\Readings\indexes\lra\objects\pdf\<sha256>\`. Volume and chapter indexes are
views that reference those objects through `sha256` or `object_id`. If a PDF is
moved or renamed without changing bytes, tools should update path metadata and
reuse existing extraction, OCR, theorem, and chunk artifacts.

By default, recursive index runs include the subject roots listed as
`recursive_scan.indexable_roots` in the YAML policy.

The following roots are library-only by default and should not enter LRA source
indexes during recursive scans:

- `Sources/Calculus`
- `Sources/History`

Housekeeping roots such as `_duplicates`, `duplicates`, `Hold`, `_hold`,
`indexes`, and `lra-source-profiles` are also skipped during recursive scans.
Ordinary staging folders named `processed` remain indexable.

An explicit tool override may index excluded roots for a deliberate local test,
but that override does not change the canonical policy.

## Internal TeX and Lean Indexes

LRA-authored TeX and Lean files are internal source surfaces for verification
work. For Lean <-> TeX linking, tools should index TeX source and Lean source
directly before consulting rendered PDFs.

The canonical deterministic indexer is
`tools/governance/index_internal_objects.py`. It emits source-style records for
TeX definition/theorem-like environments and Lean declarations with stable
object identifiers, file paths, line hints, labels or declaration names,
statement text, and volume/chapter/topic metadata when those can be inferred
from paths.

Runtime discovery uses three independent SQLite FTS5 databases under the
configured LRA index root:

- `internal/sqlite/tex-search.sqlite`;
- `internal/sqlite/lean-search.sqlite`;
- `internal/sqlite/cpp-search.sqlite`.

TeX, Lean, and C/C++ are separate refresh units. The YAML/JSON object payloads
remain useful as deterministic interchange, match-report, and repair artifacts,
but agents must not load them for ordinary lookup.

For ordinary edit loops, use
`tools/governance/update_internal_object_index.py`. The updater preserves the
full indexer as the parsing authority while adding a delta state file: it hashes
current TeX/Lean source files, re-indexes changed files, removes records for
deleted files, and merges unchanged records from the previous index. Use
`--full` when roots, parser behavior, or index health are in doubt. Unless
`--no-sqlite` is explicit, every full or delta run atomically rebuilds the
SQLite database for each family present in the payload. C/C++ indexing follows
the same rule in `tools/governance/index_cpp_objects.py`.

The delta workflow is documented in
`docs/workflows/internal-object-index-delta.md`. After adding or revising a TeX
formal artifact or Lean declaration, rerun the updater before relying on lookup
results. A newly added TeX definition should be searchable by label or display
name in the generated internal object index.

Full-text source lookup is available for active Lean and LaTeX work. Use
ordinary code search, such as `rg`, for raw repository text; use the governed
ranked object search when looking for theorem-like or definition-like objects
by rough name, statement wording, synonym, typo, or mathematical phrase. The
object search queries SQLite candidates and scores phrase, token, synonym,
LaTeX-symbol, and character n-gram overlap without loading the generated object
payload into agent context.

Example:

```powershell
python F:\repos\lra-governance\tools\governance\search_internal_object_index.py `
  --index D:\Readings\indexes\lra\internal\sqlite\tex-search.sqlite `
  --source-family tex `
  --limit 8 `
  "supremum sum at most sum suprema"
```

Point `--index` at `lean-search.sqlite` or `cpp-search.sqlite` for those
families, and use `--format json` when another tool or agent will consume the
results. Search-quality feedback
from proof memorialization and verification tasks should be recorded under the
root `feedback/` folder, including the proof or object sought, the query used,
top results, whether they were suitable, and any better query terms discovered.
This feedback can drive later improvements such as a dedicated skill, a
long-lived search index, or stronger mathematical query expansion.

Every TeX definition, axiom, theorem, lemma, proposition, and corollary
environment must have a bracketed display name, for example
`\begin{definition}[Natural Logarithm]` or
`\begin{proposition}[Fundamental Logarithmic Limit]`. The rendered box title
and the numbered environment title should agree in mathematical name so the
index has a stable human-facing key.

Reviewed TeX-to-Lean links should be recorded immediately after the TeX formal
artifact with:

```tex
\LeanFormalizes{<tex-label>}{lra-lean}{<Lean.module>}{<LeanDeclaration>}{<status>}
```

The allowed statuses are `checked`, `statement`, `pending`, and `incomplete`.
When a new TeX definition or theorem-like artifact has no Lean declaration yet,
create an explicit `lra-lean` follow-up task to add the declaration or record
why it is intentionally absent; do not leave the TeX artifact silently
untracked.

PDF outputs are render artifacts. They may provide page-number or visual QA
evidence after a TeX object is identified, but they should not be the primary
object-discovery surface because labels, environment structure, and source
lineage are more reliable in TeX.

Generated internal indexes belong under ignored build or external index
locations unless a small curated crosswalk is intentionally reviewed and
committed. Do not commit full rendered PDFs, full generated TeX object indexes,
delta state files, or machine-local absolute index paths as canonical
governance data.

## Docker Search Workflow

Use the `lra-source-indexer:latest` image from `lra-source-profiles` for
repeatable source searches. The image contains the same text extraction,
theorem-index, quality-report, and Google codesearch tooling used by local and
GitHub Actions runs.

Refresh the omnibus index after adding, moving, or enriching sources:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\source_indexer.ps1 `
  -Command omnibus `
  -ReadingsRoot D:\Readings
```

Search the generated corpus with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\omnibus_topic_search.ps1 `
  -Query "theorems related to Lipschitz continuity"

powershell -ExecutionPolicy Bypass -File scripts\omnibus_search.ps1 `
  -Query "diameter"
```

`omnibus_topic_search.ps1` queries the generated omnibus SQLite FTS5 index when
available, falls back to the theorem JSON/YAML index, and then falls back to
local codesearch when available. Use `--format json` when a tool or agent will
consume the ranked results.

Use scoped topic search when a result should come from reviewed source stacks:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\omnibus_topic_search.ps1 `
  -Query "lipschitz continuity" `
  -Author "Terence Tao"

powershell -ExecutionPolicy Bypass -File scripts\omnibus_topic_search.ps1 `
  -Query "uniform convergence of a sequence of functions" `
  -Volume volume-iii `
  -Book book-analysis-i `
  -Chapter real-analysis

powershell -ExecutionPolicy Bypass -File scripts\omnibus_topic_search.ps1 `
  -Query "compactness" `
  -Profile general-profile
```

`omnibus_search.ps1` is the raw regex/string lookup tool. It mounts
`D:\Readings` read-only and sets `CSEARCHINDEX` to
`/readings/indexes/lra/omnibus/codesearch/csearchindex`. Its output points to
generated Markdown cache files under
`D:\Readings\indexes\lra\volumes\<volume>\_sources\markdown\`.

For definitions, search both the formal noun phrase and common variants:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\omnibus_topic_search.ps1 -Query "definition of diameter"
powershell -ExecutionPolicy Bypass -File scripts\omnibus_search.ps1 -Query "Definition.*diameter"
powershell -ExecutionPolicy Bypass -File scripts\omnibus_search.ps1 -Query "diameter of a set"
powershell -ExecutionPolicy Bypass -File scripts\omnibus_search.ps1 -Query "bounded set"
```

For theorem-like material, search by statement term, theorem name, and nearby
mathematical action:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\omnibus_topic_search.ps1 -Query "theorems related to compactness"
powershell -ExecutionPolicy Bypass -File scripts\omnibus_search.ps1 -Query "Theorem.*compact"
powershell -ExecutionPolicy Bypass -File scripts\omnibus_search.ps1 -Query "Heine Borel"
powershell -ExecutionPolicy Bypass -File scripts\omnibus_search.ps1 -Query "finite subcover"
```

When a first query is sparse, generate alternate terms before deciding that the
corpus lacks the topic. Use at least these transformations:

- formal term and plain-English term: `distance from a point to a set`,
  `point set distance`;
- singular, plural, and adjectival forms: `compact set`, `compactness`,
  `relatively compact`;
- common synonyms and older terminology: `neighborhood`, `neighbourhood`,
  `open ball`;
- notation-driven variants: `dist(x,A)`, `d(x,A)`, `diam A`, `diameter`;
- theorem-name and conclusion variants: `Bolzano-Weierstrass`, `convergent
  subsequence`;
- weaker and stronger related hypotheses: `complete`, `totally bounded`,
  `compact`.

Prefer a small query family over one broad query. Read the surrounding
generated Markdown before using a result as source evidence, because codesearch
finds strings and the theorem index is intentionally heuristic.
