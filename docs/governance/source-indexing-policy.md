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

## Current Reading Library

The default host reading library is `D:\Readings`, with source PDFs organized
under `D:\Readings\Sources`. Generated indexes belong under
`D:\Readings\indexes\lra` so they stay outside Git and inside the backed-up
reading hierarchy.

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
powershell -ExecutionPolicy Bypass -File scripts\omnibus_search.ps1 `
  -Query "diameter"
```

`omnibus_search.ps1` mounts `D:\Readings` read-only and sets `CSEARCHINDEX` to
`/readings/indexes/lra/omnibus/codesearch/csearchindex`. Search output points
to generated Markdown cache files under
`D:\Readings\indexes\lra\volumes\<volume>\_sources\markdown\`.

For definitions, search both the formal noun phrase and common variants:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\omnibus_search.ps1 -Query "Definition.*diameter"
powershell -ExecutionPolicy Bypass -File scripts\omnibus_search.ps1 -Query "diameter of a set"
powershell -ExecutionPolicy Bypass -File scripts\omnibus_search.ps1 -Query "bounded set"
```

For theorem-like material, search by statement term, theorem name, and nearby
mathematical action:

```powershell
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
