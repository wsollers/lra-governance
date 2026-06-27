# Frontmatter and Frontispiece Standard

This document governs volume frontmatter and mathematician frontispieces. It
is documentation/governance only. It does not authorize changing current TeX
frontmatter, generating images, moving content, or modifying archives.

## Required Frontmatter Consistency

Every standalone PDF entry root must render a standardized frontmatter page
before the shared dedication page and table of contents.

The full-volume root `volume-{roman}.tex` renders volume frontmatter with:

- series title;
- volume display title;
- volume frontmatter mathematician;
- volume mathematician lifespan;
- volume frontmatter image.

Each standalone book root `volume-{roman}-{book-slug}.tex` renders book
frontmatter with the same fields plus the book title:

- series title;
- volume display title;
- book display title;
- book frontmatter mathematician;
- book mathematician lifespan;
- book frontmatter image.

When a book record has not yet been assigned book-specific frontmatter
metadata, the book root may temporarily inherit the volume frontmatter
mathematician, lifespan, and image. Once book-specific metadata is present in
`book-registry.json`, the book root must use it.

The displayed volume title must be identical in the frontmatter page, volume
index, `\part` title, and volume metadata. The book title must be identical in
the book frontmatter page and canonical book metadata.

## Series Title Rule

Every book title page and book frontmatter sequence must display a series title
at the bottom of the page. The default series title is:

```text
From Cantor to Ito
```

Applied and computational books use the applied series title instead:

```text
From Turing to Carmack
```

The series title is metadata, not part of the volume title or book title. It
must be visually subordinate to the book title and volume title, and must not
replace the frontispiece plaque text.

## Standard Frontmatter File Name

Each active volume repository must define the reusable frontmatter renderer at:

```text
volume-*/frontmatter.tex
```

Active PDF roots must input this file and call `\LRAFrontMatterPage` with six
arguments:

```latex
\input{volume-iii/frontmatter}
\LRAFrontMatterPage{From Cantor to Ito}{Classical Analysis}{Integration}
  {Bernhard Riemann}{1826-1866}{images/riemann.png}
```

For full-volume roots, the third argument is empty:

```latex
\LRAFrontMatterPage{From Cantor to Ito}{Classical Analysis}{}
  {Augustin-Louis Cauchy}{1789-1857}{images/cauchy.png}
```

Existing files such as `frontispiece.tex`, `cantor-quote.tex`,
`peano-quote.tex`, `hilbert-quote.tex`, `euler-quote.tex`, and
`gauss-quote.tex` may remain temporarily as inactive transition files until a
later cleanup phase removes them. Active roots must not route them.

## Image Path Rule

All LaTeX image paths for volume frontispieces must be volume-root-relative.

Allowed:

```latex
\includegraphics[width=0.6\textwidth]{images/<filename>.png}
```

Forbidden:

```text
volume-i/images/...
volume-ii/images/...
volume-*/images/...
```

The path rule applies in each volume repository: the LaTeX source must reference
`images/<filename>.png` from the volume root, not a volume-prefixed path.

## House Image Style

Each frontmatter page should use the standard mathematician portrait style:

- monochrome black-and-white engraved line art;
- centered circular medallion portrait;
- bold dark circular border;
- relevant formulas or diagrams lightly arranged inside the circle;
- rectangular engraved nameplate below the medallion;
- short stem connecting the medallion to the nameplate;
- plaque text containing exactly the mathematician's full name and lifespan.

The plaque must not include titles, volume numbers, quotes, nicknames, or
extra commentary.

## Target Volume Frontmatter

| Volume | Display title | Mathematician | Lifespan | Image path |
|---|---|---|---|---|
| Volume I | `Logic, Sets, and Proof` | Georg Cantor | 1845-1918 | `images/cantor.png` |
| Volume II | `Origins of Numbers` | Richard Dedekind | 1831-1916 | `images/dedekind.png` |
| Volume III | `Classical Analysis` | Augustin-Louis Cauchy | 1789-1857 | `images/cauchy.png` |
| Volume IV | `Mathematical Spaces` | Constantin Caratheodory | 1873-1950 | `images/caratheodory.png` |
| Volume V | `Modern Analysis` | Stefan Banach | 1892-1945 | `images/banach.png` |
| Volume VI | `Algebra` | Emmy Noether | 1882-1935 | `images/noether.png` |
| Volume VII | `Advanced Logic` | David Hilbert | 1862-1943 | `images/hilbert.png` |
| Volume VIII | `Applied and Computational Mathematics` | Isaac Newton | 1643-1727 | `images/newton.png` |

Book-level frontmatter mathematicians are recorded in
`docs/architecture/volume-architecture.md` and machine-readable form in
`docs/architecture/book-registry.json`.

## Generation Boundary

If a required image does not exist, an image-generation phase may create it.
That phase must:

- use the house image style above;
- save the file as `images/<lastname>.png`;
- reference the image as `images/<lastname>.png`;
- avoid volume-local image directories.

Governance-only phases must not generate, replace, delete, resize, or
re-encode images unless the task explicitly requests frontmatter production
standardization using generated images.

## Migration Discipline

Frontmatter changes must be small and auditable:

- first standardize metadata conventions;
- then standardize displayed titles;
- then introduce `frontmatter.tex` renderers and route all PDF roots through
  them;
- then attach or update image assets;
- then remove obsolete title, quote, or frontispiece transition files only when
  no inputs reference them.

Archive material must remain untouched. Existing historical frontmatter inside
archives should not be normalized unless a later archive-specific task
explicitly requires it.

## Validation

`tools/governance/validate_volume.py` includes a focused
`frontmatter_standard` validator. It compares every active PDF entry root
against `docs/architecture/book-registry.json` and enforces:

- `volume-*/frontmatter.tex` exists and defines `\LRAFrontMatterPage`;
- each `volume-{roman}.tex` root inputs `volume-*/frontmatter` and calls
  `\LRAFrontMatterPage` with volume metadata;
- each `volume-{roman}-{book-slug}.tex` root inputs `volume-*/frontmatter` and
  calls `\LRAFrontMatterPage` with book metadata;
- all frontmatter image paths use `images/<filename>.png`;
- each referenced frontmatter image file exists in the volume repository;
- the shared dedication page follows the frontmatter page exactly once;
- `\part` titles match the canonical volume display title;
- `\lrameta` series values match the registry series title.

The validator treats frontmatter drift as an error because every active PDF
entry root is expected to be independently renderable and self-identifying.

## Deferred Phase 0 Findings

The following known issues were part of the original Phase 0 inventory and are
retained for historical traceability. Items that have since been migrated are
now mechanically checked by the validator above; remaining warning/review
findings should be resolved in the title-page/frontispiece migration phase, not
by opportunistic rewrites:

- Volume I title rename from the current working title to
  `Logic, Sets, and Proof`;
- Volume II duplicate `peano-quote` input;
- Volume II misspelling `Guiseppe`;
- Volume III mismatch between `Advanced Mathematics` and
  `Abstract Mathematics`;
- Volume III Hilbert frontispiece eventually moving to Volume VIII;
- Volume IV Euler frontispiece eventually moving to Volume VI;
- Volume V numerical content eventually moving to Volume VII;
- untracked frontispiece images for Hausdorff, Kolmogorov, Newton, Noether,
  Poincare, and misspelled `reimann`.
