# lra-lean Overlay

Stub overlay for Lean formalization.

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
verification and explorer extraction straightforward.

## Layout Overlay

Follow the canonical architecture layout:

- Lean source belongs under `LRA/Volume*/...`.
- Active volume roots belong at `LRA/Volume*.lean`.
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
