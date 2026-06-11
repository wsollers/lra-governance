# Repo Overlay -- lra-lean

Repo identity: Lean formalization.

Lean formalization of the mathematics.

Success gates:
- `lake build`

Capabilities (domain-specific to this repo; same author -> validate spine as the volumes):
- author-lean-theorem: given "formalize X", add a descriptively-named theorem in the locally inferred file/namespace and run the success gates below.

Capabilities here are scoped to repo kind `lean` in the manifest, so volume LaTeX
capabilities will NOT resolve in this repo (and vice versa).
