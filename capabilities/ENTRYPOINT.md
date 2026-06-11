# LRA Agent Entrypoint  (CANONICAL SOURCE — edit only this file)

You are an automated agent working inside a governed LRA repository. This file
is the single entrypoint. Everything else is reached by pointer from here; do
not read the whole governance tree.

## How to work

1. Identify the repo you are in (e.g. `lra-volume-i`) and the task you were given.
2. Open `capabilities/index.md`. Find the ONE capability row whose trigger matches the task.
3. Load ONLY what that capability names: its `capability.md`, the schema/data files it lists,
   the matching overlay in `capabilities/overlays/<repo>.md`, and one nearby example.
   Do not load other capabilities, standards, or prompts.
4. Perform the capability's procedure.
5. Run the capability's BOUND VERIFIER on what you wrote. The task is NOT complete until the
   verifier exits 0. If it fails, fix and re-run. Never report success on a failing verifier.

## Composition rule

Every task = global core (this file) + exactly ONE repo overlay + exactly ONE capability + its bound verifier.
Never load more than one overlay or more than one capability for a single task.

## Always-on invariants (apply to every capability)

- Canonical names only. Use the canonical predicate/notation from the YAML registries; never invent a
  name. If none exists and one is clearly warranted, flag it — do not coin it inline.
- Shape here, semantics in their homes. Generated artifacts and views never restate axioms, formulas, or
  signatures that live in a canonical file or labeled artifact; they reference them.
- Do not formalize ahead of the mathematics. No structure/predicate entries for concepts a written volume
  has not yet earned.
- Single source of truth. Do not hand-edit synced downstream copies or generated files; edit the canonical
  source and let sync/generation propagate.
- Structural change is moves, not rewrites. Consolidation relocates existing content; it does not rewrite
  rules or invent new ones.
- Do not modify mathematical content during a mechanics task unless the task is itself to author it.

## Pointers

- Capability manifest: `capabilities/index.md`
- Repo overlays: `capabilities/overlays/`
- Canonical schema/data: `constitution/schema/` and the canonical `*.yaml` registries at the monorepo root.
