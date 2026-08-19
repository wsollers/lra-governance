# Build And Render Standards

## Global Expectation

Use the build or render path owned by the repository being edited. Do not
substitute a specialist repo's validation workflow for a volume or governance
task.

## Volume Repos

Volume repos are Overleaf-ready. The full volume builds through
`volume-{roman}.tex`, and each book builds through
`volume-{roman}-{book-slug}.tex`, with `common/` supplied by the build
environment (Docker image, explicit `lra-common` checkout, or Overleaf upload)
rather than a synced copy. Every volume repo ignores `common/`. Legacy
`volume-{roman}-{book-slug}-main.tex`, `main-book-*.tex`, and transitional
`main.tex` roots are accepted only during migration.

## Independent Builds

There is no monorepo; `Learning-Real-Analysis` is retired. Each volume builds
its own digital and print PDFs independently in Docker, checking out
`lra-common` and `lra-governance` at build time, and publishes to
`lra-volumes-output`. Canonical YAML lives in `lra-governance`.

## Specialist Repos

Lean validation belongs in the `lra-lean` overlay. C++/Vulkan validation
belongs in the `lra-nurbs` overlay. Numerical benchmark and plotting validation
belongs in the `lra-numerical-analysis` overlay.
