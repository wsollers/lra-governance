# Digital, Print, And Reference Edition Standards

This document governs edition behavior for LRA volume builds. It is the
canonical policy for what changes between digital, print, and reference output.

## Core Rule

Edition and paper size are separate decisions.

- `digital`, `print`, and `reference` describe behavior.
- `letter`, `a4`, `sixbynine`, or another trim describe geometry.

A PDF may be a digital target, a print target, or a compact reference target. A
press-bound PDF uses print behavior. A screen-read PDF uses digital behavior. A
reference PDF is a generated compact source containing only definitions and
theorem-like statements for fast digital lookup or lightweight printing.

## Edition Matrix

The visual hierarchy and mathematical content style are shared across editions.
Only navigation and supplemental rendering differ.

| Feature | Print | Digital | Reference |
| --- | --- | --- | --- |
| Definitions | render | render | render |
| Theorems, lemmas, propositions, corollaries | render | render | render |
| Other chapter notes and topic exposition | render | render | omit |
| Top breadcrumb / orientation chrome | render | render | omit except generated headings |
| Footer / running breadcrumb | render | render | omit |
| Proof vault routes | omit | render | omit |
| Exercise vault routes | omit | render | omit |
| Capstone exercise route | omit | render | omit |
| Dependency blocks | omit body when the shared environment is print-aware | render | omit unless inside an extracted statement |
| Worked examples governed as digital-only | omit | render | omit |
| Hyperlinked breadcrumb nodes | omit as interaction | render when implemented | omit as interaction |
| Previous / next controls | omit | render when implemented | omit |
| Sibling navigation panels | omit | render when implemented | omit |
| Hover, focus, or interactive affordances | omit | render when implemented | omit |
| PDF bookmarks | optional | render when implemented | optional |

## Routing Boundary

Chapter routers own the print-edition boundary. They use one
`\LRAExcludeFromPrintEditionBegin ... \LRAExcludeFromPrintEditionEnd` block
around the proof, exercise, and capstone routes.

Files below `proofs/` and `proofs/exercises/` use ordinary `\input{...}` lines.
They must not contain edition gates unless a specific future standard grants an
exception.

Retired print-aware input macros must not be reintroduced. Use ordinary
`\input{...}` inside the chapter router's print-exclusion block.

Reference builds do not use chapter-router exclusion blocks. The governance
build helper generates a temporary reference TeX root by following routed source
order and extracting only `definition`, `theorem`, `lemma`, `proposition`, and
`corollary` environments. The generated root belongs under `build/reference/`
and must not be edited by hand.

## Build Requirements

Volume build workflows must build all editions:

- digital build without the print-edition switch;
- print build with the print-edition switch enabled.
- reference build with `--edition reference`.

For volume repos, the canonical Docker helper builds every canonical root,
including the main volume root and individual book roots, unless a task
explicitly asks for one root.

```powershell
python ..\lra-governance\tools\governance\build_volume_docker.py --root . --common-root ..\lra-common --edition digital --paper letter --output-dir build\digital-letter
python ..\lra-governance\tools\governance\build_volume_docker.py --root . --common-root ..\lra-common --edition print --paper sixbynine --output-dir build\print-sixbynine
python ..\lra-governance\tools\governance\build_volume_docker.py --root . --common-root ..\lra-common --edition reference --paper letter --output-dir build\reference-letter
```

## Implementation Boundary

Edition policy belongs here. Shared LaTeX implementation belongs in
`lra-common`. Volume repos consume the common implementation; they do not carry
local copies of shared edition or breadcrumb packages.

If implementation and this standard disagree, treat the disagreement as drift:
either update `lra-common` or update this standard, then rerun validation.
