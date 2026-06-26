# Repo Overlay -- lra-volume-iii

Repo identity: Volume III.

Local conventions:
- Content lives under `volume-iii/<chapter>/notes/<section>/notes-<section>.tex`;
  proofs under `.../proofs/<section>/prf-<slug>.tex`.
- Definitions use ordinary `definition` environments by default; wrap only load-bearing definitions in the semantic `definitionbox` family.
- Decoration blocks are unboxed `remark*`; dependencies use `\begin{dependencies}` or `\NoLocalDependencies`.
- Chapters route through `volume-iii/index.tex` and the owning book root.
- Canonical YAML registries live in sibling `lra-governance`; do not duplicate
  them into volume repos.
- Cross-volume references must not rely on an assembled monorepo build.
- Volume success requires governance validation and a successful independent
  volume/book build.

Applicable capabilities: author-statement, author-stub-chapter, author-stub-section.

Overlay-specific verifier args: none beyond the capability default.
Pass `--canonical-dir <path-to-lra-governance>` to `validate_decoration.py` to enable formal-reading triggers.
