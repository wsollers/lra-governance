<!-- GENERATED FILE. Source: capabilities/overlays-config.yaml via
generate_overlays.py (volume overlays only). Edit the config or template,
not this file. -->
# Repo Overlay -- lra-volume-v

Repo identity: Volume V.

Scope:
- Volume content only. Edit only this volume's `volume-v/` content unless the
  task explicitly says otherwise.
- Shared LaTeX infrastructure is owned by `lra-common`, canonical YAML
  registries by `lra-governance`, and Lean proof source by `lra-lean`; do not
  edit or duplicate them here.
- Specialist rules (Lean, C++/Vulkan, numerical analysis, PDF extraction) do
  not apply in volume repos.
- Preserve Overleaf readiness and the independent volume build; there is no
  assembled monorepo to sync into.

Local conventions:
- Content lives under `volume-v/<chapter>/notes/<section>/notes-<section>.tex`;
  proofs under `.../proofs/<section>/prf-<slug>.tex`.
- Definitions use ordinary `definition` environments by default; wrap only load-bearing definitions in the semantic `definitionbox` family.
- Decoration blocks are unboxed `remark*`; dependencies use
  `\begin{dependencies}` or `\NoLocalDependencies`.
- Chapters route through `volume-v/index.tex` and the owning book root. Chapter
  routers own the print-edition exclusion block around proof, exercise, and
  capstone routes.
- Digital, print, and reference editions are behavior modes, not paper sizes;
  breadcrumb/footer chrome is generated from one metadata source, and its
  shared implementation stays in `lra-common`.
- Cross-volume references must not rely on an assembled monorepo build.

Validate and build (from the volume root, with a sibling `lra-governance`;
forward-slash commands run unchanged in PowerShell and POSIX shells):
- `python ../lra-governance/scripts/build_volume.py --root . --validate-only`
- `python ../lra-governance/tools/governance/build_volume_docker.py --root . --common-root ../lra-common --edition <digital|print|reference> --paper <letter|sixbynine> --output-dir build/<edition>-<paper>`
  (discovers every canonical book root; add `--tex-root <book>.tex` for one book).
- "edit latex" means the governance devcontainer launcher (route
  `local-tex-devcontainer`); never build volumes with raw `latexmk`.
- After moving or adding active `.tex` files, refresh LaTeX Workshop root
  comments with `set_latex_root_comments.py --root . --write` then `--check`.
- After changing formal TeX artifacts, refresh the internal object index
  (route `prepare-lean-tex-lookup`); generated indexes stay uncommitted.
- Volume success requires governance validation and a successful independent
  volume/book build.

Overlay-specific verifier args: none beyond the capability default.
Pass `--canonical-dir <path-to-lra-governance>` to `validate_decoration.py` to enable formal-reading triggers.
