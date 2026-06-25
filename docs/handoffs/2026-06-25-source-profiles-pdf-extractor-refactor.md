# Continuation Prompt: Source Profiles and PDF Extractor Layout Refactor

Use this prompt to continue the Learning Real Analysis refactor in a new Codex chat.

## Starting Point

Work primarily in:

```text
F:\repos\lra-governance
```

Current date of handoff: 2026-06-25.

The multi-repo checkpoint has already been committed locally. The relevant repos are clean except `lra-hold`, which is intentionally a temporary holder and should not be committed unless explicitly requested.

Committed checkpoint heads:

```text
lra-governance     cd2fcee  Checkpoint governance refactor
lra-proof-vault    fede191  Checkpoint proof vault route migration
lra-volume-i       369c6bd  Checkpoint Volume I book layout
lra-volume-ii      e574a9d  Checkpoint Volume II book layout
lra-volume-iii     496cea7  Checkpoint Volume III book layout
lra-volume-iv      c0962df  Checkpoint Volume IV book layout
lra-volume-v       a2ddceb  Checkpoint Volume V book layout
lra-volume-vi      55672ab  Checkpoint Volume VI book layout
lra-volume-vii     701b26f  Checkpoint Volume VII book layout
lra-volume-viii    a4be56f  Checkpoint Volume VIII book layout
```

`lra-governance`, `lra-proof-vault`, and all eight volume repos are ahead of origin by one commit at this handoff. `lra-source-profiles` and `lra-pdf-extractor` are clean on `main`.

## Current Ground Truth

The canonical layout is book-aware and volume-aware. Use the governance registry as the source of truth:

```text
F:\repos\lra-governance\docs\architecture\book-registry.json
```

Supporting architecture docs:

```text
F:\repos\lra-governance\docs\architecture\volume-architecture.md
F:\repos\lra-governance\docs\architecture\frontmatter-and-frontispiece-standard.md
F:\repos\lra-governance\docs\governance\volume-structure.md
F:\repos\lra-governance\docs\governance\volume-structure.schema.json
```

Key layout rules:

- Volume repos no longer carry governance/common sources as local owned content.
- Each volume root is named `volume-<roman>.tex`.
- Each book root is named `volume-<roman>-<book-slug>.tex`.
- Books have independent frontmatter, bibliographies, and TOC validation.
- Image paths are volume-local `images/<slug>.png`, with generated extras archived in governance.
- The build path now expects governance/common to be resolved through the governance tooling/Docker flow.

## Recently Completed

- Volume I through VIII were refactored to volume roots plus book roots.
- Bibliographies were migrated to per-book `.bib` files.
- Book-level TOC validation was added/updated.
- Knowledge explorer and proof-vault route work was started and checkpointed.
- Mathematician frontmatter images were regenerated from ChatGPT contact sheets, normalized to Cantor size, distributed to the volume repos, and archived in governance:

```text
F:\repos\lra-governance\mathemeticians
F:\repos\lra-governance\mathemeticians\lra-primary-series
```

- Live frontispiece image references were audited:
  - all `\includegraphics{images/...}` references resolve,
  - all registry image paths resolve,
  - all distributed volume images are `1365x2048`.

## Next Tasks

Primary task:

Update `lra-source-profiles` and `lra-pdf-extractor` to understand the current volume/book layout.

Start by auditing how those repos currently discover:

- volume repositories,
- root TeX files,
- book roots,
- chapter/section files,
- bibliographies,
- generated PDFs,
- source metadata,
- extraction paths,
- any hard-coded legacy names such as `main.tex`, `*-main.tex`, old volume titles, old volume numbers, or old image/frontmatter assumptions.

Then update them to consume or mirror the current governance registry rather than maintaining stale layout assumptions.

Likely repos:

```text
F:\repos\lra-source-profiles
F:\repos\lra-pdf-extractor
```

Useful initial searches:

```powershell
rg -n "main\.tex|volume-.*-main|book-registry|volume-i|volume-ii|volume-iii|volume-viii|bibliography|root|chapter|pdf|extract" F:\repos\lra-source-profiles F:\repos\lra-pdf-extractor
rg -n "Logic and Foundations|Numerical and Approximation|Computational Mathematics|Topology and Geometry|Algebra and Abstract Structures" F:\repos\lra-source-profiles F:\repos\lra-pdf-extractor
```

Before editing, read the local README/docs/scripts in both repos and identify their expected inputs/outputs. Prefer small, registry-driven changes over duplicating the registry.

## Validation Expectations

After changes:

1. Run the relevant tests or smoke commands in `lra-source-profiles`.
2. Run the relevant tests or smoke commands in `lra-pdf-extractor`.
3. Re-run any governance validator that checks book roots or extracted paths if applicable.
4. Confirm no references remain to the old root naming convention unless they are compatibility notes.
5. Confirm generated/extracted paths include both volume and book identity where needed.

Do not commit `lra-hold` unless the user explicitly asks; it still contains temporary topic folders.

## Status Commands

Use this to re-check the handoff state:

```powershell
Get-ChildItem -Path F:\repos -Directory -Filter lra-* | Where-Object { Test-Path (Join-Path $_.FullName '.git') } | ForEach-Object { Write-Output "===== $($_.Name) ====="; git -C $_.FullName status --short --branch }
```

If asked to push, push the committed repos deliberately; at this handoff they are only committed locally.
