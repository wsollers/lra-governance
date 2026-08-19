<!-- GENERATED FILE. Source: capabilities/overlays-config.yaml via
generate_overlays.py (volume overlays only). Edit the config or template,
not this file. -->
# Repo Overlay -- lra-volume-ii

Repo identity: Volume II.

Scope:
- Volume content only. Edit only this volume's `volume-ii/` content unless the
  task explicitly says otherwise.
- Shared LaTeX infrastructure is owned by `lra-common`, canonical YAML
  registries by `lra-governance`, and Lean proof source by `lra-lean`; do not
  edit or duplicate them here.
- Specialist rules (Lean, C++/Vulkan, numerical analysis, PDF extraction) do
  not apply in volume repos.
- Preserve Overleaf readiness and the independent volume build; there is no
  assembled monorepo to sync into.

Local conventions:
- Content lives under `volume-ii/<chapter>/notes/<section>/notes-<section>.tex`;
  proofs under `.../proofs/<section>/prf-<slug>.tex`.
- Definitions use ordinary `definition` environments by default; wrap only load-bearing definitions in the semantic `definitionbox` family.
- Decoration blocks are unboxed `remark*`; dependencies use
  `\begin{dependencies}` or `\NoLocalDependencies`.
- Chapters route through `volume-ii/index.tex` and the owning book root. Chapter
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

Repo-specific rules:
- Every theorem-like or definition-like artifact should carry a stable label mappable to a formal verification target; when no target exists yet, record the status as pending rather than omitting the relationship.
- `\LeanFormalizes{<book-label>}{lra-lean}{<module>}{<declaration>}{<status>}` records extraction-visible verification mappings; `<book-label>` must match the immediately preceding formal artifact. Status wording must not overclaim: `pending` (no target), `statement` (formal statement, incomplete proof), `checked` (declaration builds in `lra-lean` with no placeholders for that declaration).
- Do not inline formal proof code as volume prose and do not place formal proof implementation work here; `lra-lean` owns checked formal source, and `lra-knowledge-explorer` owns the verification UI.

Overlay-specific verifier args: none beyond the capability default.
Pass `--canonical-dir <path-to-lra-governance>` to `validate_decoration.py` to enable formal-reading triggers.
