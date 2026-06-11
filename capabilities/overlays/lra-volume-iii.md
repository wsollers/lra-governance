# Repo Overlay -- lra-volume-iii

Repo identity: Volume III.

Local conventions:
- Content lives under `volume-iii/<chapter>/notes/<section>/notes-<section>.tex`;
  proofs under `.../proofs/<section>/prf-<slug>.tex`.
- Definitions are wrapped in the semantic `definitionbox` family (common/boxes.tex).
- Decoration blocks are unboxed `remark*`; dependencies use `\begin{dependencies}` or `\NoLocalDependencies`.
- Chapters route into BOTH `volume-iii/index.tex` (monorepo) and `main.tex` (local build).
- Canonical YAML registries live at the monorepo root; cross-volume `\hyperref` targets resolve
  only in the assembled monorepo build.

Applicable capabilities: author-statement, author-stub-chapter, author-stub-section.

Overlay-specific verifier args: none beyond the capability default.
Pass `--canonical-dir <monorepo-root>` to `validate_decoration.py` to enable formal-reading triggers.
