# Repo Overlay -- lra-volume-iv

Repo identity: Volume IV.

Local conventions:
- Content lives under `volume-iv/<chapter>/notes/<section>/notes-<section>.tex`;
  proofs under `.../proofs/<section>/prf-<slug>.tex`.
- Definitions are ordinary `definition` environments unless a rare load-bearing definition warrants a semantic box.
- Decoration blocks are unboxed `remark*`; dependencies use `\begin{dependencies}` or `\NoLocalDependencies`.
- Chapters route through `volume-iv/index.tex` and the owning book root.
- Canonical YAML registries live in sibling `lra-governance`; do not duplicate
  them into volume repos.
- Cross-volume references must not rely on an assembled monorepo build.
- Volume success requires governance validation and a successful independent
  volume/book build.

Applicable capabilities: author-statement, author-stub-chapter, author-stub-section.

Overlay-specific verifier args:
- Plain-style volume: prefer unboxed formal environments except for rare structural emphasis.
Pass `--canonical-dir <path-to-lra-governance>` to `validate_decoration.py` to enable formal-reading triggers.
