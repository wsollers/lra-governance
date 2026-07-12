# lra-lean Architecture

`lra-lean` is the standalone Lean 4 formalization workspace for LRA. It owns
checked Lean source, Lake configuration, Lean-specific scripts, and formal
verification metadata. Volume repositories may reference Lean statements, but
they do not build Lean source.

## Workspace Layout

```text
lakefile.lean          Lake library declarations
lake-manifest.json     pinned package manifest
lean-toolchain         pinned Lean toolchain
Dockerfile             reproducible Linux Lean environment
Makefile               Docker-first Unix build wrapper
build.ps1              Docker-first Windows build wrapper
scripts/               Lean validation and extraction helpers
LRA/                   Lean source modules
  VolumeI.lean         Volume I library root
  VolumeII.lean        Volume II library root
  VolumeI/             Volume I modules
  VolumeII/            Volume II modules
```

Generated local inventories, build products, and private source PDFs are not
architecture and should remain untracked.

## Module Architecture

Lean modules are organized by volume and mathematical subject. A volume root
imports the modules that belong to that active library. New volume libraries
must be declared in `lakefile.lean` before CI is extended to build them.

Volume II is built around abstract Peano systems before concrete models:

```text
LRA/VolumeII/
  Foundations/         foundational logic, relations, and functions
  PeanoSystems/        PeanoSystem, induction, recursion, basic theorems
  NaturalNumbers/      arithmetic built from the Peano recursion architecture
```

Lower layers may not import higher layers. Arithmetic modules may use the
recursion architecture but should not redefine foundational concepts.

## Formalization Policy

Agent-facing Lean implementation standards live in
`docs/governance/repo-overlays/lra-lean.md`. This architecture document records
ownership, layout, and import boundaries.

Volume II must remain Mathlib-free. Mathlib imports are not allowed in
`LRA/VolumeII/**`; future higher-volume work may opt into Mathlib only when the
volume library and overlay explicitly allow it.
