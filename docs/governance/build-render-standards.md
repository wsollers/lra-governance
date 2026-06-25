# Build And Render Standards

## Global Expectation

Use the build or render path owned by the repository being edited. Do not
substitute a specialist repo's validation workflow for a volume or governance
task.

## Volume Repos

Volume repos are Overleaf-ready and build through book-level roots named
`volume-{roman}-{book-slug}-main.tex`, with `common/` supplied by the build
environment (Docker image or explicit `lra-common` checkout) rather than a
synced copy. Legacy `main-book-*.tex` roots and transitional `main.tex` roots
are accepted only during migration.

## Independent Builds

There is no monorepo; `Learning-Real-Analysis` is retired. Each volume builds
its own digital and print PDFs independently in Docker, checking out
`lra-common` and `lra-governance` at build time, and publishes to
`lra-volumes-output`. Canonical YAML lives in `lra-governance`.

## Specialist Repos

Lean validation belongs in the `lra-lean` overlay. C++/Vulkan validation
belongs in the `lra-nurbs` overlay. Numerical benchmark and plotting validation
belongs in the `lra-numerical-analysis` overlay.
