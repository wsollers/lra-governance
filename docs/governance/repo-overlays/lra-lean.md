# lra-lean Overlay

Repo overlay for Lean formalization.

Formalization takes place in `lra-lean`. When looking for Lean-formalized
proofs, checked Lean declarations, or Lean proof-completion work, inspect the
`lra-lean` repository and its `LRA/` modules first; volume repositories may
carry source prose and verification links, but they do not own Lean proof
source.

Owned concerns:

- Lean-specific proof architecture,
- Mathlib policy,
- Lean module and namespace rules,
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
- `docs/architecture/semantic-artifact-record.md` when mapping checked Lean
  declarations to semantic artifacts or explorer verification metadata.

Use `[external:lra-lean] README.md`, `lakefile.lean`, `lean-toolchain`, and the
nearest Lean module for implementation details. Do not load volume authoring,
PDF-extractor, source-profile, or numerical overlays unless the task explicitly
crosses that boundary.

## Implementation Standards

Lean code should be readable formal mathematics, not compressed tactic output.
Follow the existing module style: package declarations under clear namespaces,
use descriptive theorem, definition, hypothesis, and witness names, and keep
proof structure legible enough for a maintainer to match it back to the source
mathematics. Prefer small named lemmas and explicit local structure over dense
anonymous tactic blocks when the proof has reusable mathematical content.

In `lra-lean`, source-facing mathematical declarations should preserve the
project's prose-style names. Prefer PascalCase theorem and predicate names such
as `IsUpperBound`, `IsSupremum`, and `MaximumIsSupremum` when those declarations
mirror named concepts from the volumes. Use snake_case only for local helpers,
implementation details, or declarations that intentionally follow an imported
library's naming convention.

LRA-authored public declarations must not use snake_case. Any declaration that
can be referenced by `\LeanFormalizes`, imported by another LRA module as part
of a mathematical interface, or read as a volume-facing definition/theorem must
use prose-style PascalCase. Snake_case is permitted only for genuinely local
proof helpers, private/internal implementation details, legacy declarations
quarantined under an explicit `Old` namespace, or compatibility names required
by an imported library convention. Do not attach TeX metadata to snake_case
helpers; attach it to the canonical PascalCase declaration in the proper module.

When adding source-aligned declarations, model definitions and theorem
statements first. Do not complete Lean proof bodies unless the user explicitly
requests proofs. Use a compiling placeholder proof such as `sorry` for accepted
statements whose proof work has not been requested.

Do not create new axiom artifacts unless the user explicitly instructs you to add
a new axiom. When a source already contains an axiom environment, attach
Lean metadata to that existing artifact; do not create a duplicate TeX
axiom box, and do not promote a definition, predicate, or theorem to a
Lean `axiom` merely to make metadata placement convenient. If the source
kind is unclear, stop and ask before adding or reclassifying axioms.

For proof-photo memorialization, do not turn a photographed handwritten proof
into a completed Lean proof as part of the memorialization task. Record or
reference the corresponding Lean statement, and leave the proof body as an
accepted placeholder unless the user starts a separate Lean proof-completion
task.

File and module organization should mirror the formal subject matter. New
modules belong under the appropriate `LRA/Volume*/...` tree, imported through
the relevant volume root, and exposed through stable names that make downstream
verification and explorer extraction straightforward.

Generic structural material belongs at its earliest mathematical home, not
under the first later volume that happens to use it. Volume II must not
introduce namespaces such as `LRA.VolumeII.Foundations.IdentityElements`,
`LRA.VolumeII.Foundations.IdentityEquality`, or
`LRA.VolumeII.Foundations.OrderRelations` for generic equality, substitution,
relation predicates, order predicates, identity elements, absorbing elements,
operation laws, or algebra laws. Put equality and substitution declarations
under `LRA.VolumeI.Identity`; put binary relation predicates under
`LRA.VolumeI.Relations`; put order laws under `LRA.VolumeI.Relations.Order`;
put operation laws and identity-element laws under `LRA.VolumeI.Operations`;
reserve `LRA.VolumeI.Structures` for bundled structures such as magma,
semigroup, monoid, group, ring, and field; and let later volumes import the
Volume I module.

Do not introduce stacked namespace declarations that spell a module path one
component at a time, such as `namespace LRA`, then `namespace VolumeII`, then
`namespace Foundations`, then `namespace IdentityElements`. Use a single dotted
namespace declaration such as `namespace LRA.VolumeI.Identity` or
`namespace LRA.VolumeI.Relations.Order`.

Keep examples and tests separate. Source-facing example modules may live under
`LRA/Volume*/...` when they are readable mathematical examples that a maintainer
might browse alongside the formal interface. Build-regression checks, API smoke
tests, and unit-test-style assertions belong under a top-level `test/` source
tree and should be built through a test Lake target rather than imported by
production volume roots. Prefer `example : ... := by ...` checks over
interactive/debug commands such as `#check` or `#print`.

## Layout Overlay

Follow the canonical architecture layout:

- Lean source belongs under `LRA/Volume*/...`.
- Active volume roots belong at `LRA/Volume*.lean`.
- Lean test source belongs under `test/`, with Lake test targets separated from
  the production volume libraries.
- Lake library declarations belong in `lakefile.lean`.
- Lean validation and extraction helpers belong under `scripts/`.
- Docker and wrapper build entrypoints stay at the repo root.

Do not commit local build products, generated declaration inventories, or
private source PDFs as architecture.

## Build And Validation

CI builds the repo through `Dockerfile`, then runs Lake inside the container:

```bash
docker build -t lra-lean .
docker run --rm -v "$PWD:/workspace" -w /workspace lra-lean lake build \
  LRAVolumeI LRAVolumeII
```

Local Windows validation should prefer `.\build.ps1 docker-build` followed by
`.\build.ps1 build-all`, which builds the active libraries declared in
`lakefile.lean`. Native `lake build` is acceptable only when the pinned
`lean-toolchain` is installed locally. When adding a Lean volume, add its
`lean_lib` to `lakefile.lean` before extending CI to build it.

## Lean/TeX Lookup Index

When adding, deleting, moving, or revising source-facing Lean declarations,
refresh the governed internal object index after the Lean build gate that is
appropriate for the task. The index refresh is not a substitute for Lake; it is
the lookup surface that lets volume TeX artifacts and Lean declarations stay
discoverable together.

```powershell
python ..\lra-governance\tools\governance\update_internal_object_index.py `
  --tex-root ..\lra-volume-iii `
  --lean-root . `
  --output D:\Readings\indexes\lra\internal\volume-iii-lean-tex-index.yaml `
  --include-match-report
```

Repeat `--tex-root` for every volume whose TeX objects should be compared
against the Lean root, or use a volume-scoped output for focused work. Use
`--full` when the index state is missing, stale, or suspicious. Generated index
and state files belong in ignored build or external index locations unless a
small curated crosswalk is intentionally reviewed and committed elsewhere.

## Volume II Verification Map

For Volume II formalization work, each declaration that mirrors a volume
artifact should record a stable mapping back to the LaTeX label. Prefer a
small, grep-friendly metadata comment near the declaration or module section
that includes:

- the Volume II label,
- the Lean module,
- the declaration name,
- the verification status.

The status must distinguish an accepted statement with unfinished proof work
from a checked declaration. Report `checked` only when the declaration is
accepted by the local Lean build without placeholders for that declaration.
This metadata is the source that downstream explorer extraction may use to
populate verification fields.
