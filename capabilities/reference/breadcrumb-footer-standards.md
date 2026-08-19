# Breadcrumb And Footer Standards

This document governs LRA orientation chrome: top breadcrumbs, footer
breadcrumbs, and future navigation controls.

## Hierarchy

The LRA reader hierarchy is:

```text
Series -> Volume -> Book -> Chapter -> Section -> Topic
```

Each level narrows scope. The hierarchy is invariant across all volumes and
editions.

## Current-Level Rule

A breadcrumb answers "where am I?" The emphasized entry is the current level,
not always the deepest possible level.

Required invariant:

- render only ancestors through the current level;
- emphasize exactly one entry;
- the emphasized entry is the current level;
- never show a deeper level than the current level.

Examples:

- chapter-opening chrome ends at `Chapter`;
- section chrome ends at `Section`;
- topic chrome ends at `Topic`;
- book-opening chrome ends at `Book`.

## Metadata Rule

Breadcrumb and footer text must come from one metadata source. Do not hand-type
one trail for the top of the page and a second trail for the footer.

Canonical metadata fields are:

- `series`;
- `volume`;
- `book`;
- `chapter`;
- `section`;
- `topic`;
- `current`.

Display strings use the form `Label: Title` when a level has a label:

```text
Volume III: Classical Analysis
Book I: Foundations of Analysis
Chapter 4: Sequences
Section: Sequences
```

Series, section, and topic may be unnumbered.

## Visual Model

Each hierarchy level may have a stable identity treatment, but state controls
emphasis.

- current level: full emphasis, strongest fill or type treatment;
- ancestor level: muted treatment;
- no information may be conveyed by color alone.

Icons, if used, must be render-stable and must not depend on platform emoji.

Breadcrumb chrome must not compete with mathematical content. It is orientation
and navigation furniture, not a theorem-like block.

## Footer Rule

The footer breadcrumb is the compact running form of the same metadata used by
the top breadcrumb.

Footers must not introduce a second naming convention, an alternate chapter
order, or hand-maintained previous/next text.

## Edition Behavior

Print and digital edition behavior is governed by
`digital-print-edition-standards.md`.

In short:

- print may render static orientation chrome;
- digital may add hyperlinks and navigation controls;
- print must not render button-like previous/next controls, sibling panels,
  hover affordances, or other interactive furniture.

## Current Implementation Note

The active common implementation exposes the metadata-driven API:

```latex
\lrasetup{...}
\lrameta{...}
\LraBreadcrumb
\LraFooterBreadcrumb
\LraEnableFooterBreadcrumb
```

The legacy chapter-level
`\breadcrumb{<chapter-slug>}{<prior>}{<current>}{<next>}` macro remains valid
only as a migration compatibility path.

Do not introduce a second competing breadcrumb package in volume repos.
