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

## Providers, Defaults, and Substitutable Models

**Decision.** Provider substitution occurs at an explicit interface or
certified-model boundary. Defaults are convenience selections, not that
boundary, and richer construction-specific models interoperate through named
reducts rather than by sharing one forced representation.

LRA distinguishes four roles that are easy to conflate in Lean source:

1. an **interface** states the carrier, operations, relations, and certified
   laws required by reusable mathematics;
2. a **construction** builds a concrete object and proves that it realizes an
   interface;
3. a **provider** exposes construction-specific aliases or scoped instances
   at an interoperability boundary; and
4. a **default** selects one convenient provider for code that intentionally
   accepts the project-wide choice.

Reusable theorems depend on the weakest interface or certified model that
contains their assumptions. They do not depend on a default carrier alias or
on a construction namespace. Construction modules return that common model
through a named realization or reduct such as `satisfiesGeneric`,
`genericModel`, `to...Model`, or `<Construction>Realizes<Concept>Model`.
Different constructions are interchangeable after this projection even when
their internal model structures are not definitionally equal.

For bundled mathematical subjects, prefer an explicit ambient model value:

```lean
section

variable (LRA_Model : ConceptModel)
variable {x y : LRA_Model.Carrier}

-- The model determines its carrier, operations, relations, and law fields.

end
```

Theorems should normally take the model explicitly, possibly as an implicit
section variable, and recover subordinate data through projections. A richer
first-order, Henkin, full second-order, axiomatic, or Mathlib construction may
provide a `toConceptModel` or other named reduct. The shared theorem is proved
once on the reduct; thin construction- or logic-specific wrappers may remain
when they preserve useful provenance or discharge different boundary
obligations.

Use typeclass inference for operations and laws that are canonical *relative
to an already selected model*. Model structures may expose instance-valued
fields, and a construction may install them with `letI` inside a proof. Do not
make the model selection itself a global instance when multiple models on the
same carrier could coexist. Prefer an explicit model parameter and local
instances; use a scoped provider only when the API is intentionally
typeclass-shaped and provider isolation is tested.

Provider modules live under
`LRA/<Subject>/Interop/Providers/<Provider>`. Opening a provider scope is a
local choice:

```lean
open scoped LRA.Subject.Interop.Providers.Mathlib
```

Importing an aggregate provider module must not silently activate competing
instances. Provider isolation tests should demonstrate that each provider can
be imported and opened independently.

Default aliases such as `LRA.Set.LRA_Set` or a subject-local
`LRA_DefaultCarrier` are compile-time abbreviations, not dynamically
rebindable providers. They are appropriate for examples, executable defaults,
and deliberately default-backed APIs. A theorem intended to survive provider
substitution must quantify over the common interface/model instead. Within a
section, a concrete realization can be given a local notation such as
`LRA_Model`, but substitution occurs by changing the supplied model value or
provider scope, not by mutating the project-wide abbreviation.

The existing families illustrate complementary parts of this rule:

- Set interop exposes named LRA and Mathlib provider aliases, while `LRA_Set`
  is the fixed predicate-set default.
- Identity interop exposes isolated Default, LRA, and Mathlib scoped instances,
  while substantial identity laws quantify over `LRA.Identity.IdentityModel`.
- Number-system constructions realize shared `NaturalNumberModel`,
  `IntegerModel`, `RationalModel`, and `RealModel` interfaces; their
  construction-specific carriers and the `LRA_DefaultCarrier` aliases are not
  the reusable theorem boundary.

When a logical level contributes additional semantics, package the facts
needed by downstream mathematics in a common certified reduct rather than
forcing first- and second-order model structures to have the same shape. For
identity, `LRA.Identity.IdentityModel` is this ordinary theorem boundary. It
exposes its carrier, identity relation, admissible predicates, identity theory,
and the admissibility of the identity fibers. First-order formula definability,
Henkin-domain membership, and full second-order admissibility are separate
adapter proofs feeding that same model and remain outside ordinary law files.
The identity-owned adapters live beside their source models in
`Interface/FirstOrder/Adapter.lean` and `Interface/SecondOrder/Adapter.lean`;
cross-provider conversions and scoped provider exports remain under `Interop`.

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
