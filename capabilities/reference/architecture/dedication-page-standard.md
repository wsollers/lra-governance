# Dedication Page Standard

This document governs the shared dedication page used by every active
Learning Real Analysis PDF entry root.

## Source File

The dedication page source is owned by `lra-common`:

```text
lra-common/common/dedication.tex
```

Volume repositories must not keep local dedication-page copies. PDF roots
include the shared page through:

```latex
\input{common/dedication}
```

## Placement

Every standalone PDF entry root must include the dedication page exactly once.
It must appear after the standardized frontmatter page and before the table of
contents:

```latex
\input{volume-iii/frontmatter}
\LRAFrontMatterPage{From Cantor to Ito}{Classical Analysis}{Integration}
  {Bernhard Riemann}{1826-1866}{images/riemann.png}
\input{common/dedication}

\tableofcontents
```

This rule applies to both full-volume roots and standalone book roots.

## Duplication Rule

A PDF entry root must not inline dedication text and must not input
`common/dedication` more than once. The shared page is the only active
dedication source.

## Validation

`tools/governance/validate_volume.py` includes the `dedication_page` validator.
It checks every registry-backed PDF entry root and enforces:

- exactly one `\input{common/dedication}`;
- the dedication input appears after `\LRAFrontMatterPage`;
- the dedication input appears before `\tableofcontents`;
- when a sibling `lra-common` checkout exists, `common/dedication.tex` is not
  empty.

Archive material is out of scope unless an archive-specific task explicitly
authorizes changes.
