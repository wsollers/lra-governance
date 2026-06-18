# Repo Overlay -- lra-volume-iv

Repo identity: Volume IV.

Local conventions:
- Content lives under `volume-iv/<chapter>/notes/<section>/notes-<section>.tex`;
  proofs under `.../proofs/<section>/prf-<slug>.tex`.
- Definitions are ordinary `definition` environments unless a rare load-bearing definition warrants a semantic box.
- Decoration blocks are unboxed `remark*`; dependencies use `\begin{dependencies}` or `\NoLocalDependencies`.
- Chapters route into BOTH `volume-iv/index.tex` (monorepo) and `main.tex` (local build).
- Canonical YAML registries live at the monorepo root; cross-volume `\hyperref` targets resolve
  only in the assembled monorepo build.
- Volume success requires both governance validation and `latexmk -lualatex main.tex`.

Applicable capabilities: author-statement, author-stub-chapter, author-stub-section.

Overlay-specific verifier args:
- Plain-style volume: prefer unboxed formal environments except for rare structural emphasis.
Pass `--canonical-dir <monorepo-root>` to `validate_decoration.py` to enable formal-reading triggers.
