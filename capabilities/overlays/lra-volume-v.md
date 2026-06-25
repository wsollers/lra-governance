# Repo Overlay -- lra-volume-v

Repo identity: Volume V.

Local conventions:
- Content lives under `volume-v/<chapter>/notes/<section>/notes-<section>.tex`;
  proofs under `.../proofs/<section>/prf-<slug>.tex`.
- Definitions use ordinary `definition` environments by default; wrap only load-bearing definitions in the semantic `definitionbox` family.
- Decoration blocks are unboxed `remark*`; dependencies use `\begin{dependencies}` or `\NoLocalDependencies`.
- Chapters route through `volume-v/index.tex` and the owning book root.
- Canonical YAML registries live at the monorepo root; cross-volume `\hyperref` targets resolve
  only in the assembled monorepo build.
- Volume success requires governance validation and a successful governance book build.

Applicable capabilities: author-statement, author-stub-chapter, author-stub-section.

Overlay-specific verifier args: none beyond the capability default.
Pass `--canonical-dir <monorepo-root>` to `validate_decoration.py` to enable formal-reading triggers.
