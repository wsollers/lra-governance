# Digital And Print Edition Standards

This document governs edition behavior for LRA volume builds. It is the
canonical policy for what changes between digital and print output.

## Core Rule

Edition and paper size are separate decisions.

- `digital` and `print` describe behavior.
- `letter`, `a4`, `sixbynine`, or another trim describe geometry.

A PDF may be either a digital target or a print target. A press-bound PDF uses
print behavior. A screen-read PDF uses digital behavior.

## Edition Matrix

The visual hierarchy and mathematical content style are shared across editions.
Only navigation and supplemental rendering differ.

| Feature | Print | Digital |
| --- | --- | --- |
| Main mathematical statements | render | render |
| Chapter notes and topic content | render | render |
| Top breadcrumb / orientation chrome | render | render |
| Footer / running breadcrumb | render | render |
| Proof vault routes | omit | render |
| Exercise vault routes | omit | render |
| Capstone exercise route | omit | render |
| Dependency blocks | omit body when the shared environment is print-aware | render |
| Worked examples governed as digital-only | omit | render |
| Hyperlinked breadcrumb nodes | omit as interaction | render when implemented |
| Previous / next controls | omit | render when implemented |
| Sibling navigation panels | omit | render when implemented |
| Hover, focus, or interactive affordances | omit | render when implemented |
| PDF bookmarks | optional | render when implemented |

## Routing Boundary

Chapter routers own the print-edition boundary. They use one
`\LRAExcludeFromPrintEditionBegin ... \LRAExcludeFromPrintEditionEnd` block
around the proof, exercise, and capstone routes.

Files below `proofs/` and `proofs/exercises/` use ordinary `\input{...}` lines.
They must not contain edition gates unless a specific future standard grants an
exception.

Retired print-aware input macros must not be reintroduced. Use ordinary
`\input{...}` inside the chapter router's print-exclusion block.

## Build Requirements

Volume build workflows must build both editions:

- digital build without the print-edition switch;
- print build with the print-edition switch enabled.

For volume repos, the canonical Docker helper builds every canonical root,
including the main volume root and individual book roots, unless a task
explicitly asks for one root.

```powershell
python ..\lra-governance\tools\governance\build_volume_docker.py --root . --common-root ..\lra-common --edition digital --paper letter --output-dir build\digital-letter
python ..\lra-governance\tools\governance\build_volume_docker.py --root . --common-root ..\lra-common --edition print --paper sixbynine --output-dir build\print-sixbynine
```

## Implementation Boundary

Edition policy belongs here. Shared LaTeX implementation belongs in
`lra-common`. Volume repos consume the common implementation; they do not carry
local copies of shared edition or breadcrumb packages.

If implementation and this standard disagree, treat the disagreement as drift:
either update `lra-common` or update this standard, then rerun validation.
