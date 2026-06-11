# Repo Overlay -- lra-volume-iv

Repo identity: TODO: Volume IV title.

Local conventions:
- Content lives under `volume-iv/<chapter>/notes/<section>/notes-<section>.tex`;
  proofs under `.../proofs/<section>/prf-<slug>.tex`.
- Definitions are PLAIN (\begin{definition} ... no box); verifiers run with `--no-require-box`.
- Decoration blocks are unboxed `remark*`; dependencies use `\begin{dependencies}` or `\NoLocalDependencies`.
- Chapters route into BOTH `volume-iv/index.tex` (monorepo) and `main.tex` (local build).
- Canonical YAML registries live at the monorepo root; cross-volume `\hyperref` targets resolve
  only in the assembled monorepo build.

Applicable capabilities: author-statement, author-stub-chapter, author-stub-section.

Overlay-specific verifier args:
- Plain-style volume: pass `--no-require-box` to `validate_decoration.py`.
Pass `--canonical-dir <monorepo-root>` to `validate_decoration.py` to enable formal-reading triggers.
