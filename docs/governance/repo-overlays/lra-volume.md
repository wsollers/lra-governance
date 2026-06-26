# lra-volume Overlay

Stub overlay for `lra-volume-i` through `lra-volume-viii`.
Named volume overlays, such as `lra-volume-ii.md`, may add narrow
cross-repository metadata contracts while keeping implementation ownership in
the specialist repo.

Owned concerns:

- volume content only,
- Overleaf-ready volume roots,
- external `lra-common` consumed by the build environment,
- independent volume PDF builds published to `lra-volumes-output`.

This overlay may contain negative guard rails that say specialist rules do not
apply to volume repos. It must not contain positive Lean-specific, C++ /
Vulkan / simulation, numerical-analysis / benchmark / plotting, or PDF
extraction workflow rules.

## Agent Scope

Volume agents may edit only the owning `volume-N/` content unless a task
explicitly says otherwise. They should not edit copied `common/`, generated
governance wrappers, or canonical YAML. Shared LaTeX infrastructure belongs in
`lra-common` and is supplied to builds by the Docker image or an explicit
checkout.

Volume tasks should preserve Overleaf readiness and the independent volume build
shape. There is no monorepo to sync into.

## Build Commands

From a volume repository, validation is:

```powershell
python ..\lra-governance\scripts\build_volume.py --root . --validate-only
```

The Docker build helper discovers and builds every canonical root:
`volume-{roman}.tex` plus each `volume-{roman}-{book-slug}.tex`. Use it for
full volume and individual book PDF checks:

```powershell
python ..\lra-governance\tools\governance\build_volume_docker.py --root . --common-root ..\lra-common --output-dir build\digital
python ..\lra-governance\tools\governance\build_volume_docker.py --root . --common-root ..\lra-common --print-edition --output-dir build\print
```

To build one book root, pass it explicitly:

```powershell
python ..\lra-governance\tools\governance\build_volume_docker.py --root . --common-root ..\lra-common --tex-root volume-i-set-theory.tex --output-dir build\digital
```

## Stub Chapters

Volume chapter stubs follow the global `stub-chapter-standards.md` standard.
After stub generation, run the local volume build command when available; for
standard LRA volume roots, use the Docker build helper above unless local
instructions say otherwise.

## Stub Sections

Volume section stubs follow the global `stub-section-standards.md` standard.
Section-stub tasks must update the owning chapter's notes and proofs routers
using the local routing convention, then run the local volume build command
when available.

## Artifact Payload Generation

For large chapter artifact generation, use the deterministic payload workflow
in `docs/workflows/artifact-payload-generation.md`. Machine-ingested JSON or
JSONL payloads are the source of truth; Codex should rehydrate payloads through
the importer and generator, preserve pedagogical order, keep notation before
first use, and run deterministic local audits by default. AI-backed audits
using `-ai codex` are opt-in only.
