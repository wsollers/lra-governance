# Repo Overlay -- lra-lean

Repo identity: Lean formalization.

Lean formalization of the mathematics.

Capabilities (domain-specific to this repo; same author -> validate spine as the volumes):
- author-lean-theorem: given "formalize X", add a descriptively-named theorem (e.g. RationalEquivalenceClassAdditionIsCommutative) in the right place, formalize it to the project's standards, then VERIFY with `lake build`, then sync the formalized statement into its owning LaTeX volume. Standards doc + volume-sync mapping: TODO (owner-defined).

Capabilities here are scoped to repo kind `lean` in the manifest, so volume LaTeX
capabilities will NOT resolve in this repo (and vice versa). Capabilities marked PLANNED are
not yet implemented -- the shape and verifier are recorded so they can be built to spec.
