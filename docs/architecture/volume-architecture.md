# Eight-Volume Architecture

This document defines the canonical target volume and book architecture for
Learning Real Analysis. A volume is the broad shelf title. A book is a
named subject partition inside a volume and has its own
`volume-{roman}-{book-slug}-main.tex` entry root.

## Target Volumes

| Volume | Roman | Repository | Display title | Frontispiece | Lifespan | Image path | Status |
|---:|---|---|---|---|---|---|---|
| 1 | I | `wsollers/lra-volume-i` | `Logic, Sets, and Proof` | Georg Cantor | 1845-1918 | `images/cantor.png` | active |
| 2 | II | `wsollers/lra-volume-ii` | `Origins of Numbers` | Giuseppe Peano | 1858-1932 | `images/peano.png` | active |
| 3 | III | `wsollers/lra-volume-iii` | `Classical Analysis` | Augustin-Louis Cauchy | 1789-1857 | `images/cauchy.png` | active |
| 4 | IV | `wsollers/lra-volume-iv` | `Mathematical Spaces` | Emmy Noether | 1882-1935 | `images/noether.png` | active |
| 5 | V | `wsollers/lra-volume-v` | `Modern Analysis` | Henri Poincare | 1854-1912 | `images/poincare.png` | active |
| 6 | VI | `wsollers/lra-volume-vi` | `Algebra` | Leonhard Euler | 1707-1783 | `images/euler.png` | active |
| 7 | VII | `wsollers/lra-volume-vii` | `Advanced Logic` | David Hilbert | 1862-1943 | `images/hilbert.png` | active |
| 8 | VIII | `wsollers/lra-volume-viii` | `Applied and Computational Mathematics` | Isaac Newton | 1643-1727 | `images/newton.png` | active |

## Canonical Book Naming Table

This table summarizes the book-level display titles. The machine-readable
registry for exact TeX root names, output names, and migration aliases is
`docs/architecture/book-registry.json`. Book titles must not be confused with
volume titles.

| Volume | Volume title | Canonical book title | Current root slug | Notes |
|---|---|---|---|---|
| I | Logic, Sets, and Proof | Mathematical Logic and Proof | `book-logic` | Introductory formal logic, proof systems, and axiom-system tooling. |
| I | Logic, Sets, and Proof | Set Theory | `book-sets` | Set-theoretic foundations. |
| I | Logic, Sets, and Proof | Foundational Geometry | `book-geometry` | Euclidean, trigonometric, and analytic geometry foundations. |
| II | Origins of Numbers | Discrete Number Systems | `book-discrete-algebraic` | Formalizing number systems through natural, whole, and integer systems. |
| II | Origins of Numbers | The Continuum | `book-continuum` | Embeddings, rationals, reals, complex numbers, and number-line constructions. |
| III | Classical Analysis | Bounds, Sequences, and Series | `book-analysis-i` | Foundational real-analysis toolkit, bounds, functions without limits, sequences, series, and function sequences. |
| III | Classical Analysis | Continuity | `book-analysis-ii` | Elementary functions, limits, and continuity. |
| III | Classical Analysis | Differentiation | `book-analysis-iii` | Differentiation. |
| III | Classical Analysis | Integration | `book-integration` | Riemann integration and related classical integration material. |
| IV | Mathematical Spaces | Mathematical Spaces | `book-spaces` | Metric spaces, topological spaces, measure spaces, set algebra, and algebras of sets. |
| V | Modern Analysis | Modern Analysis | `book-measure`, `book-probability`, `book-functional-analysis`, `book-complex-analysis` | Current roots are subject partitions under the Modern Analysis volume. |
| VI | Algebra | Algebra | `book-algebra`, `book-linear-algebra`, `book-lattice-order` | Current roots are algebraic subject partitions under the Algebra volume. |
| VII | Advanced Logic | Advanced Logic | `book-category-theory`, `book-model-theory`, `book-proof-theory`, `book-type-theory`, `book-lambda-calculus` | Current roots are advanced-logic subject partitions. |
| VIII | Applied and Computational Mathematics | Applied and Computational Mathematics | `book-applied-methods`, `book-numerical-foundations` | Applied methods and numerical foundations. |

## Book Root Naming

Every book must eventually build from a readable root named:

```text
volume-{roman}-{book-slug}-main.tex
```

The produced PDF uses the same stem:

```text
volume-{roman}-{book-slug}-main.pdf
```

Examples:

- `volume-i-mathematical-logic-and-proof-main.tex`;
- `volume-ii-the-continuum-main.tex`;
- `volume-iii-differentiation-main.tex`.

Legacy `main-book-*.tex` roots and transitional `main.tex` roots are accepted
only while repositories are being migrated to book-level frontmatter and build
roots.

Open naming decisions:

- whether Volume III `Continuity` later merges into `Differentiation` or
  remains a separate bridge book before differentiation;
- whether Modern Analysis, Algebra, Advanced Logic, and Applied and
  Computational Mathematics should keep subject-level roots as book titles or
  collapse under one book title per volume.

## Book Migration Checklist

1. Verify governance ground rules first: book registry, metadata fields,
   filename rules, validators, Docker build discovery, and output naming must
   all agree before content roots are renamed.
2. Rename or create book roots using
   `volume-{roman}-{book-slug}-main.tex`.
3. Duplicate and specialize book frontmatter so each book has its own title
   page, copyright/frontmatter policy, table of contents, and introduction
   hook.
4. Build each book independently and publish PDFs using the matching
   `volume-{roman}-{book-slug}-main.pdf` names.
5. Update Knowledge Explorer navigation from volume-only selection to
   volume/book/chapter selection.
6. Update knowledge extraction so records carry volume metadata and book
   metadata, including `book_slug`, `book_title`, and source root.
7. Add expected book-level TOC validation so misplaced or missing sections are
   caught mechanically.

## Canonical Volume Metadata Fields

Every volume must have one canonical metadata record. The record may live in a
volume-level YAML file or another approved registry, but it must expose these
fields:

- `volume_number`: Arabic number, such as `1`.
- `roman_numeral`: Roman numeral, such as `I`.
- `repository`: GitHub repository name, such as `wsollers/lra-volume-i`.
- `display_title`: canonical displayed volume title.
- `series_title`: frontmatter series title; normally `From Cantor to Ito`, or
  `From Turing to Carmack` for applied and computational books.
- `frontispiece_mathematician`: full mathematician name.
- `mathematician_lifespan`: birth-death years, formatted as `YYYY-YYYY`.
- `image_path`: volume-relative image path, formatted as
  `images/<filename>.png`.
- `frontispiece_file`: preferred frontispiece source file, normally
  `volume-*/frontispiece.tex`.
- `status`: one of `active`, `planned`, `stub`, `migrated`, or `archived`.

The metadata record is the authority for title and frontispiece consistency.
Generated title pages, frontispiece pages, volume indexes, and repository
documentation should agree with this record once the relevant migration phase
has run.

## Status Values

- `active`: the volume repository exists and is part of the current build or
  migration workflow.
- `planned`: the target volume is part of the architecture but is not yet a
  fully populated repository.
- `stub`: the repository or volume directory exists with placeholder content.
- `migrated`: content has been moved or split according to the target
  architecture.
- `archived`: historical content retained for reference and not part of the
  active volume route.

Archives must remain untouched unless a later task explicitly authorizes an
archive-only maintenance change.

## Title Consistency Rule

For each volume, these places must eventually use the same displayed volume
title:

- title page;
- frontispiece page;
- volume index;
- `\part` title;
- volume metadata.

Existing mismatches are migration targets, not permission to make opportunistic
edits. Title changes must occur in the title-standardization phase.

## Migration Rule

The migration must proceed by stubs first and small chapter-level moves later.
Do not perform bulk moves across multiple domains in a single commit. Do not
rename repositories, create new repositories, or move content until the
metadata conventions, frontmatter conventions, and workflow update plan are in
place.

When content eventually moves:

- preserve theorem labels;
- preserve proof labels;
- preserve citations;
- preserve cross-references;
- leave archives intact;
- prefer router files or compatibility stubs when they reduce breakage;
- test the source and destination volume builds before pushing.

## Current Integration Points

Each volume has an active `lra-volume-*` repository with a standalone build
root. Local Docker/build tooling recognizes the eight-volume identifier set.
The volume repos build independently; there is no monorepo and no
volume-to-monorepo sync. The knowledge refresh, orchestrated from
`lra-governance`, reads all eight `lra-volume-*` source trees.

## Deferred Phase 0 Findings

The deferred Phase 0 inventory (title, frontispiece, and image issues) is
recorded once in `docs/architecture/frontmatter-and-frontispiece-standard.md`.
Those items are intentionally deferred and must not be fixed as part of this
governance phase.

## Related Documents

- `docs/architecture/frontmatter-and-frontispiece-standard.md`
- `docs/plans/volume-renumbering-and-frontmatter-migration-plan.md`
