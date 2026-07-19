# lra-lean Overlay

Repo overlay for Lean formalization.

Owned concerns:

- Lean-specific proof architecture,
- Mathlib policy,
- Lean module and namespace rules,
- configurable number-system constructions,
- theorem-status metadata,
- Lean Blueprint generation,
- Lean CI and validation.

## Agent Scope

Lean guidance applies only to `lra-lean`.
It must not be injected into volume content instructions.

Use the Docker build path for reproducible validation. Do not use LaTeX render
checks as substitutes for Lean validation.

Canonical architecture and layout guidance lives in
`docs/architecture/lra-lean-architecture.md`.

## Governance Doc Set

Load these governance documents for Lean work:

- `docs/governance/repo-overlays/lra-lean.md`;
- `docs/architecture/lra-lean-architecture.md`;
- `docs/architecture/semantic-artifact-record.md` when mapping Lean
  declarations to semantic artifacts, Blueprint nodes, or explorer verification
  metadata.

Use `[external:lra-lean] README.md`, `DESIGN.md`, `lakefile.lean`,
`lean-toolchain`, and the nearest Lean module for implementation details. Do not
load volume-authoring, PDF-extractor, source-profile, or numerical overlays
unless the task explicitly crosses that boundary.

## Namespace Policy

All Volume II declarations belong under the exact root namespace
`LRA.VolumeII`.

Subject namespaces mirror the module tree:

- `LRA.VolumeII.PeanoSystems`;
- `LRA.VolumeII.NaturalNumbers`;
- `LRA.VolumeII.WholeNumbers`;
- `LRA.VolumeII.Integers`;
- `LRA.VolumeII.Rationals`;
- `LRA.VolumeII.Reals`;
- `LRA.VolumeII.NumberSystemTower`.

Construction namespaces are nested beneath their number system, for example:

- `LRA.VolumeII.Integers.Canonical`;
- `LRA.VolumeII.Integers.Tao`;
- `LRA.VolumeII.Integers.Mendelson`;
- `LRA.VolumeII.Rationals.Canonical`;
- `LRA.VolumeII.Reals.Dedekind`;
- `LRA.VolumeII.Reals.Cauchy`;
- `LRA.VolumeII.Reals.Cantor`;
- `LRA.VolumeII.Reals.IntervalQuotient`;
- `LRA.VolumeII.Reals.Dyadic`.

Do not create compatibility aliases, forwarding namespaces, deprecated module
paths, or duplicate declarations when renaming. Update imports and qualified
names in the same change. A failed stale import is preferred to silent
compatibility debt.

## Model and Construction Policy

Each configurable number system uses three explicit layers:

1. a signature containing carrier data, operations, and relations;
2. a proposition-valued law bundle;
3. a model bundling the signature and its law proof.

Use the semantic names:

- `IntegerSignature`, `IntegerLaws`, `IntegerModel`;
- `RationalSignature`, `RationalLaws`, `RationalModel`;
- `RealSignature`, `RealLaws`, `RealModel`.

Generic theorems consume explicit model arguments. Concrete construction modules
prove that their carriers satisfy the shared interface. Do not use global
instances to choose among alternate mathematical universes.

The default construction tower is:

- canonical integer quotient;
- canonical rational fraction quotient;
- Dedekind-cut real construction.

Alternate constructions remain separate carrier types and are related by
explicit isomorphism theorems. Do not make alternate constructions
definitionally equal through `abbrev`.

Selectors return bundled models or extensions because construction branches may
have different carrier types. Selection modules are terminal convenience
modules and must not be imported by individual construction modules.

## Quotient and Recursion Architecture

Quotient constructions must use the common representative-independence layer:

1. define a raw representative operation;
2. prove left and right compatibility, or invoke a proved commutative reduction;
3. combine them into full compatibility;
4. lift the operation, predicate, or relation to the quotient.

Peano-recursive operations must use the common iterator architecture. When an
operation depends on a fixed parameter, use the parameterized iterator wrapper
rather than separately rebuilding a family of unary iterators.

Keep the two meanings of well-definedness distinct:

- recursive existence and uniqueness;
- quotient representative independence.

## Implementation Standards

Lean code should be readable formal mathematics, not compressed tactic output.
Follow the existing module style: package declarations under clear namespaces,
use descriptive theorem, definition, hypothesis, and witness names, and keep
proof structure legible enough for a maintainer to match it back to the source
mathematics. Prefer small named lemmas and explicit local structure over dense
anonymous tactic blocks when the proof has reusable mathematical content.

File and module organization should mirror the formal subject matter. New
modules belong under the appropriate `LRA/Volume*/...` tree, imported through
the relevant volume root, and exposed through stable names that make downstream
verification, Blueprint declaration checking, and explorer extraction
straightforward.

Use PascalCase for structures, inductive types, and modules. Use semantic
snake_case for definitions, theorems, lemmas, propositions, and corollaries.
Lean declarations that are mathematically propositions or corollaries may use
the standard `theorem` command when Lean has no distinct command, but their
doc-comment display role must say `Proposition` or `Corollary`.

## Placeholder Proof Policy

Accepted theorem statements may use `sorry` while the user completes proofs.
A declaration containing `sorry` must compile and is recorded as
`statement-accepted-proof-pending`, not as checked.

Ordinary `lake build` must not treat `sorry` warnings as build failures. CI may
publish a separate proof-status report based on axiom footprints, but that
report is informational unless a workflow explicitly targets a no-placeholder
milestone.

Do not replace intended proof obligations with axioms merely to avoid `sorry`.
Use theorem-like declarations with the intended statement and a placeholder
proof.

## Layout Overlay

Follow the canonical architecture layout:

- Lean source belongs under `LRA/Volume*/...`.
- Active volume roots belong at `LRA/Volume*.lean`.
- Lake library declarations belong in `lakefile.lean`.
- Lean validation and extraction helpers belong under `scripts/`.
- Blueprint sources belong under `blueprint/`.
- GitHub Pages assembly helpers belong under `scripts/` or `website/`.
- Docker and wrapper build entrypoints stay at the repo root.

Do not commit local build products, generated declaration inventories, generated
Blueprint HTML/PDF, or private source PDFs as architecture.

## Build and Validation

CI builds the repo through `Dockerfile`, then runs Lake inside the container:

```bash
docker build --target lean-build -t lra-lean .
docker run --rm -v "$PWD:/workspace" -w /workspace lra-lean lake build \
  LRAVolumeI LRAVolumeII
```

The documentation target adds Lean Blueprint, Graphviz, and TeX tooling:

```bash
docker build --target documentation-build -t lra-lean-docs .
docker run --rm -v "$PWD:/workspace" -w /workspace lra-lean-docs \
  leanblueprint checkdecls
docker run --rm -v "$PWD:/workspace" -w /workspace lra-lean-docs \
  leanblueprint web
docker run --rm -v "$PWD:/workspace" -w /workspace lra-lean-docs \
  leanblueprint pdf
```

Pin Blueprint Python dependencies. Documentation tools are build-time tools and
do not alter the Volume II no-Mathlib dependency policy.

Local Windows validation should prefer `./build.ps1 docker-build` followed by
`./build.ps1 build-all`, which builds the active libraries declared in
`lakefile.lean`. Native `lake build` is acceptable only when the pinned
`lean-toolchain` is installed locally. When adding a Lean volume, add its
`lean_lib` to `lakefile.lean` before extending CI to build it.

## Lean Blueprint and GitHub Pages

The Blueprint is a published documentation view of the formalization, not an
imported Lean dependency.

Each Blueprint node and Lean declaration must share a stable mathematical
identifier. Blueprint declaration checking must verify that referenced Lean
names exist. GitHub Pages deployment runs only after the Lean build and
Blueprint build succeed.

Pull requests build and validate the Blueprint but do not deploy it. Pushes to
`main` build Blueprint HTML/PDF, assemble the site, and deploy through GitHub
Pages using GitHub Actions.

Generated proof status may distinguish:

- statement absent;
- statement accepted with `sorry`;
- proof checked without `sorryAx`;
- construction model assembled;
- comparison isomorphism checked.

## Volume II Verification Map

For Volume II formalization work, each declaration that mirrors a volume
artifact must record a stable mapping back to the LaTeX label. Use a
small, grep-friendly metadata comment near the declaration or module section
that includes:

- the Volume II label;
- the Lean module;
- the declaration name;
- the Blueprint label;
- the verification status.

The status must distinguish an accepted statement with unfinished proof work
from a checked declaration. Report `checked` only when the declaration is
accepted by the local Lean build without placeholders for that declaration.
This metadata is the source that downstream explorer and Blueprint extraction
may use to populate verification fields.
