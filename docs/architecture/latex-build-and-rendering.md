# LaTeX Build And Rendering Architecture

LaTeX build behavior follows repository ownership. Agents should use the build
path for the repository being edited and avoid importing specialist validation
workflows into unrelated repos.

## Independent Volume Builds

Each `lra-volume-*` repo builds its own digital and print PDFs independently in
a Docker container, checking out `lra-common` (for shared LaTeX infrastructure)
and `lra-governance` (for validators and canonical YAML) at build time, and
publishing to `lra-volumes-output`. There is no assembled monorepo or omnibus
build; `Learning-Real-Analysis` is retired.

Docker build details live in `lra-common/docker`. Governance docs record
ownership and safety boundaries rather than duplicating every build command.

## Volume Repos

Each `lra-volume-*` repo is Overleaf-ready. The full volume builds from
`volume-{roman}.tex`; each book builds from
`volume-{roman}-{book-slug}.tex`. Legacy `volume-{roman}-{book-slug}-main.tex`,
`main-book-*.tex`, and transitional `main.tex` roots are accepted only while old
branches finish migration. The root uses `common/` supplied by the build
environment (Docker image, explicit `lra-common` checkout, or Overleaf upload)
and inputs only that volume's content. `common/` is ignored by every volume repo
and is not stored as a synced copy in the volume repo.

Volume repos own volume content only. They do not own shared LaTeX
infrastructure, canonical YAML, Lean formalization, NURBS/Vulkan simulation,
numerical-analysis benchmark workflows, or PDF extraction tooling.

## Shared LaTeX Infrastructure

`lra-common` owns shared LaTeX infrastructure:

- `common/`,
- macros,
- environments,
- boxes,
- colors,
- preambles.

Changes to shared LaTeX infrastructure must be made in `lra-common`. Builds
consume it directly through the Docker image or an explicit checkout; it is not
fanned out into other repos.

## Cross-Book And Cross-Volume References

Book roots may reference labels defined in sibling book PDFs or in other volume
PDFs. Source references remain canonical unprefixed labels, for example
`\hyperref[def:real-ordered-field]{Real Ordered Field}`.

Build-time resolution is handled by `lra-common/common/volume-preamble.tex` with
`xr-hyper`. When an external `.aux` file exists, the preamble imports its labels;
when it does not exist, the import is skipped. This keeps local, Docker, and
Overleaf builds portable while allowing complete workspaces to resolve cross-book
and cross-volume links.

The shared preamble must skip the active root's own aux file. Volume-level roots
import other volume-level aux files; book-level roots import same-volume sibling
book aux files and other volume-level aux files. Do not rewrite source labels
with volume prefixes merely to satisfy a split-PDF build.

The Docker build helper mounts the parent repositories directory read-only at
`/lra-repos` so a complete local checkout can resolve sibling volume aux files
inside the container. Local non-Docker builds may resolve the same aux files
through sibling paths such as `../lra-volume-ii/build/volume-ii.aux`.

## Figures

Dependency figures live in dedicated `figure-<n>.tex` files and are input by
notes files. Every nontrivial TikZ figure shall live in a dedicated figure
source file. Figure source files shall contain TikZ code only: no document
preamble, no figure environment, no caption, no label, no surrounding prose,
and no inline color-system redefinition.

Figure colors, boxes, and legend macros come from shared infrastructure rather
than local ad hoc definitions.

## Specialist Validation

Lean validation belongs to `lra-lean`; C++/Vulkan/geometry validation belongs
to `lra-nurbs`; numerical benchmark and plotting validation belongs to
`lra-numerical-analysis`. These workflows must not be applied as volume-content
rules.
