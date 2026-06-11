# Repo Overlay -- lra-volume-vii

Repo identity: Volume VII.

Local conventions:
- Content lives under `volume-vii/<chapter>/notes/<section>/notes-<section>.tex`;
  proofs under `.../proofs/<section>/prf-<slug>.tex`.
- Definitions are wrapped in the semantic `definitionbox` family (common/boxes.tex).
- Decoration blocks are unboxed `remark*`; dependencies use `\begin{dependencies}` or `\NoLocalDependencies`.
- Chapters route into BOTH `volume-vii/index.tex` (monorepo) and `main.tex` (local build).
- Canonical YAML registries live at the monorepo root; cross-volume `\hyperref` targets resolve
  only in the assembled monorepo build.
- Volume success requires both governance validation and `latexmk -lualatex main.tex`.

Applicable capabilities: author-statement, author-stub-chapter, author-stub-section.

Overlay-specific verifier args: none beyond the capability default.
Pass `--canonical-dir <monorepo-root>` to `validate_decoration.py` to enable formal-reading triggers.
