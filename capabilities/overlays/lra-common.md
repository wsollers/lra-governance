# Repo Overlay -- lra-common

Repo identity: Shared LaTeX macros, boxes, and templates.

Shared LaTeX macros, boxes, environments, and templates consumed by every volume. Changes here affect ALL volumes.

Capabilities (domain-specific to this repo; same author -> validate spine as the volumes):
- edit-shared-macro (PLANNED): change a macro/box; verifier = a consuming volume still builds.

Capabilities here are scoped to repo kind `library` in the manifest, so volume LaTeX
capabilities will NOT resolve in this repo (and vice versa). Capabilities marked PLANNED are
not yet implemented -- the shape and verifier are recorded so they can be built to spec.
