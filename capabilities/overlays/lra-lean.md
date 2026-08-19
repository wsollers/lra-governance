# Repo Overlay -- lra-lean

Repo identity: Lean formalization.

Formalization takes place in `lra-lean`. When looking for Lean-formalized
proofs, checked Lean declarations, or Lean proof-completion work, inspect this
repository's `LRA/` modules first; volume repositories may carry source prose
and verification links, but they do not own Lean proof source. Lean rules
apply only here and must not be injected into volume content instructions.

## Implementation Standards

Lean code should be readable formal mathematics, not compressed tactic output.
Follow the existing module style: clear namespaces, descriptive theorem,
definition, hypothesis, and witness names, and proof structure legible enough
to match back to the source mathematics. Prefer small named lemmas and
explicit local structure over dense anonymous tactic blocks when the proof has
reusable mathematical content.

Public mathematical declarations must have a doc comment that makes the Lean
shape searchable in ordinary mathematical English. Theorem-like declarations
use a two-leg comment when the proof proceeds by extensionality,
iff-introduction, constructors, or similar decompositions: state the theorem
in its displayed Lean direction, then add an "equivalently"/"memberwise"
sentence describing the elementwise shape used by the proof. Definition-like
declarations first name the object, then state its
membership/evaluation/field condition. Keep comments mathematical, not
tactic-oriented ("for every element `x`, ..." rather than "after `intro x`").

Every LRA-authored public mathematical declaration must expose its formal
content in editor hover text: after the prose explanation, add a
`Logical form:` section containing a fenced `lean` block with the
declaration's proposition, defining equation, evaluation rule, membership
condition, or structure contract. Definitions returning `Prop` must show the
unfolded logical body, not just a signature. No proof tactics or proof-state
narration in the block; keep it synchronized with the declaration.

Naming: source-facing mathematical declarations use prose-style PascalCase
(`IsUpperBound`, `IsSupremum`, `MaximumIsSupremum`). LRA-authored public
declarations must not use snake_case; snake_case is permitted only for
genuinely local proof helpers, private implementation details, legacy
declarations quarantined under an explicit `Old` namespace, or names required
by an imported library convention. Never attach TeX metadata to snake_case
helpers; attach it to the canonical PascalCase declaration.

When adding source-aligned declarations, model definitions and theorem
statements first. Do not complete Lean proof bodies unless the user
explicitly requests proofs; use a compiling placeholder (`sorry`) for
accepted statements. Do not create new axiom artifacts unless the user
explicitly instructs it: attach Lean metadata to an existing source axiom
environment, never promote a definition/predicate/theorem to a Lean `axiom`
for metadata convenience, and stop and ask if the source kind is unclear.
For proof-photo memorialization, record or reference the corresponding Lean
statement but leave the proof body a placeholder unless a separate Lean
proof-completion task is started.

## Module Layout

- Lean source under `LRA/Volume*/...`; active volume roots at
  `LRA/Volume*.lean`; Lake library declarations in `lakefile.lean`;
  validation/extraction helpers under `scripts/`; Docker and wrapper build
  entrypoints at the repo root.
- Concept folders: `LRA/Volume*/<Topic>/<Concept>/` with semantically named
  files (`Definition.lean`, `Characterizations.lean`, `Theorems.lean`,
  `FailureModes.lean`, `Examples.lean`, `Relationships.lean`, `All.lean`).
  Create only the files the reviewed concept package requires; no competing
  catch-all files. No separate `Counterexamples.lean`: reviewed false
  variants, boundary failures, negations, and witness constructions go in
  `FailureModes.lean`, each followed immediately by a theorem proving it
  realizes the advertised failure. The `Logic` area is exempt from the
  concept-folder rule.
- Generic structural material belongs at its earliest mathematical home:
  equality/substitution under `LRA.VolumeI.Identity`, binary relation
  predicates under `LRA.VolumeI.Relations`, order laws under
  `LRA.VolumeI.Relations.Order`, operation and identity-element laws under
  `LRA.VolumeI.Operations`, bundled structures (magma ... field) under
  `LRA.VolumeI.Structures`. Later volumes import the Volume I module rather
  than re-introducing `LRA.VolumeII.Foundations.*` namespaces for generic
  material.
- Use a single dotted namespace declaration
  (`namespace LRA.VolumeI.Identity`), never stacked one-component
  `namespace` declarations.
- Keep examples and tests separate: readable mathematical example modules may
  live under `LRA/Volume*/...`; build-regression checks and unit-test-style
  assertions belong under a top-level `test/` tree built through a test Lake
  target. Prefer `example : ... := by ...` over `#check`/`#print`.
- Do not commit local build products, generated declaration inventories, or
  private source PDFs.

## Verification Metadata

Declarations that mirror a volume artifact record a stable, grep-friendly
mapping near the declaration: the volume label, Lean module, declaration
name, and verification status. Report `checked` only when the declaration is
accepted by the local Lean build without placeholders for that declaration;
distinguish accepted statements with unfinished proofs. Downstream explorer
extraction populates verification fields from this metadata.

When adding, deleting, moving, or revising source-facing declarations,
refresh the governed internal object index after the Lean build gate (route
`prepare-lean-tex-lookup`). Generated index and state files stay in ignored
or external locations unless a small curated crosswalk is deliberately
reviewed and committed.

## Success gates

CI builds through `Dockerfile`, then runs Lake inside the container. Docker is
the reproducible path; native `lake build` is acceptable only when the pinned
`lean-toolchain` is installed locally. When adding a Lean volume, add its
`lean_lib` to `lakefile.lean` before extending CI to build it.

- `docker build -t lra-lean .`
- `docker run --rm -v "$PWD:/workspace" -w /workspace lra-lean lake build LRAVolumeI LRAVolumeII`

Local Windows: `.\build.ps1 docker-build` then `.\build.ps1 build-all`.
Do not use LaTeX render checks as substitutes for Lean validation.
