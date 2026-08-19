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
test/                  Lean smoke and regression test modules
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
Build-regression and smoke-test modules live under `test/` and are built through
test-specific Lake targets, not production volume roots.

Concept-facing Lean source is organized by topic and concept folder:

```text
LRA/VolumeI/
  <Topic>/
    <Topic>.lean       optional topic aggregate when the topic has submodules
    <Concept>/
      Definition.lean
      Characterizations.lean
      Theorems.lean
      FailureModes.lean
      Examples.lean
      Relationships.lean
      All.lean
```

Use only the files that the reviewed concept package needs, but keep these
semantic roles stable:

- `Definition.lean` owns the public definition or predicate declaration and
  immediate notation/evaluation lemmas.
- `Characterizations.lean` owns equivalent formulations and source-approved
  restatements of the same concept.
- `Theorems.lean` owns canonical theorem-like consequences selected for the
  concept package.
- `FailureModes.lean` owns reviewed negations, boundary failures, and false
  readings made precise. A named failure-mode definition, predicate, or
  witness construction should be followed immediately by a theorem proving that
  it actually realizes the advertised failure. For an implication failure, the
  theorem should normally prove an existential counterexample such as
  `∃ x, P x ∧ ¬ Q x`, not merely leave an unprovable goal or failed tactic.
- `Examples.lean` owns readable positive examples that belong with the source
  concept interface.
- `Relationships.lean` owns links to related concepts, duals, restrictions,
  extensions, and placement/backport helpers.
- `All.lean` imports the concept-folder modules in deterministic order and is
  the only concept-folder aggregate imported by the topic or volume root.

Do not introduce ad hoc filenames such as `Basic.lean`, `Lemmas.lean`, or
`Misc.lean` for source-grounded concept packages unless the package review adds
a narrower canonical role. Local proof helpers should remain inside the
smallest semantic file that needs them or be private/internal implementation
details.

The concept-folder layout does not apply to foundational `Logic` modules.
Logic owns cross-cutting logical infrastructure and may use a structure suited
to inference rules, connectives, quantifiers, equivalence principles, and proof
tools rather than topic/concept package folders. Do not move `Logic` material
into concept folders merely to satisfy the concept-package layout.

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
`capabilities/overlays/lra-lean.md`. This architecture document records
ownership, layout, and import boundaries.

Volume II construction modules must remain Mathlib-free. Mathlib imports are
allowed only in explicit switch or interoperability modules under
`LRA/VolumeII/Switches/**`; Peano systems, number-system constructions, and
their proofs must import switch interfaces rather than Mathlib directly. Future
higher-volume work may opt into Mathlib only when the volume library and
overlay explicitly allow it.
