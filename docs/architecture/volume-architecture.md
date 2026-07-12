# Volume And Book Architecture

This document records the stable architecture for LRA volume repositories. It
is a router, not the canonical inventory of every volume, book, chapter, or
frontmatter asset.

## Authorities

| Concern | Authority |
| --- | --- |
| Book and volume registry data, root names, expected TOC, migration aliases | `docs/architecture/book-registry.json` |
| Volume, book, chapter, topic, proof, capstone, and breadcrumb shape | `docs/governance/volume-structure.md` |
| Integrated volume-shape validator schema | `docs/governance/volume-structure.schema.json` |
| Broader constitutional layout/proof/stub schema | `constitution/schema/file-schema.yaml` |
| Frontmatter, frontispiece, title, image, and dedication rules | `docs/architecture/frontmatter-and-frontispiece-standard.md` and `docs/architecture/dedication-page-standard.md` |
| Build and render behavior | `docs/architecture/latex-build-and-rendering.md` |

## Architecture

Each `lra-volume-*` repository is an independent Overleaf-ready source repo. A
volume is the broad shelf title. A book is a named subject partition inside a
volume. Each volume builds from a full-volume root named `volume-{roman}.tex`;
each book builds from a book root named `volume-{roman}-{book-slug}.tex`.

Source content is routed through:

```text
volume-{roman}/
  index.tex
  book-{slug}/
    index.tex
    {chapter}/
      index.tex
      chapter.yaml
      notes/
      proofs/
```

Legacy roots such as `volume-{roman}-{book-slug}-main.tex`,
`main-book-*.tex`, and transitional `main.tex` are accepted only during
migration. New work should use the canonical full-volume and book-root naming
recorded in `book-registry.json`.

## Ownership

Volume repos own their volume content, chapter-local bibliography shards, and
render assets needed by that volume. They do not own shared LaTeX
infrastructure, governance rules, canonical YAML, Lean formalization,
C++/Vulkan simulation, numerical benchmark workflows, PDF extraction tooling,
or source-profile staging.

Shared LaTeX infrastructure is supplied by `lra-common`. Governance and
validation tools are supplied by `lra-governance`. There is no assembled
monorepo and no volume-to-monorepo sync.

## Validation

Run `tools/governance/validate_volume.py` through the local volume wrapper or
the governance Docker/build helpers as the acceptance gate. The first validator,
`volume_shape`, uses `docs/governance/volume-structure.schema.json`; broader
layout, proof, stub, and capstone contracts are documented in
`constitution/schema/file-schema.yaml`.

Use `tools/governance/audit_volume_layout.py` only for focused migration or
layout reports. After moving theorem or proof source paths, regenerate and
validate theorem-route artifacts before syncing route-dependent consumers such
as the proof vault.

## Migration Rule

Volume and book migrations should proceed in small reviewable steps. Preserve
theorem labels, proof labels, citations, cross-references, and router
reachability. Leave archives untouched unless a task explicitly authorizes
archive maintenance. Validate the affected source and build roots before
pushing.
