# Capability Reference Index

Use this file only after loading one capability and one repo overlay (the
resolver eager-loads `capabilities/overlays/<repo>.md` for every task). Open
the smallest referenced document that answers the concrete question.

## Indexed LRA Lookup

For `lookup-lra`:

- Source authority and index ownership: `docs/governance/source-indexing-policy.md`
- Canonical vocabulary authority: `docs/architecture/canonical-yaml.md`
- Internal index refresh: `docs/workflows/internal-object-index-delta.md`

Run the lookup tool before opening these references. Open only the reference
needed to interpret, refresh, or validate the returned lane.

## Typed Mathematical Authoring

For `author-mathematics`:

- Decoration shape: `docs/governance/decoration-box-standards.md`
- Dependency links and `\NoLocalDependencies`: `docs/governance/dependency-standards.md`
- Proof stubs and proof file layers: `docs/governance/proof-standards.md`
- Statement atomicity: `docs/governance/atomic-artifact-standards.md`
- Notation and canonical symbols: `docs/governance/notation-standards.md`
- Add theorem workflow: `docs/workflows/add-theorem-with-proof-stub.md`
- Proof layout validator usage: `docs/workflows/proof-layout-audit.md`
- Definition atomicity: `docs/governance/atomic-artifact-standards.md`
- Predicate and notation discipline: `docs/governance/notation-standards.md`
- Extraction-facing labels and identity: `docs/governance/extraction-standards.md`

## Chapter And Section Scaffolding

For `author-stub-chapter`:

- Volume architecture: `docs/architecture/volume-architecture.md`
- Volume structure: `docs/governance/volume-structure.md`
- Repository layout: `docs/architecture/repository-layout.md`
- Chapter stub standard: `docs/governance/stub-chapter-standards.md`
- Layout audit workflow: `docs/workflows/volume-layout-audit.md`

For `author-stub-section`:

- Volume structure: `docs/governance/volume-structure.md`
- Section stub standard: `docs/governance/stub-section-standards.md`
- File splitting and routing: `docs/governance/file-splitting-standards.md`
- Layout audit workflow: `docs/workflows/volume-layout-audit.md`

## Lean Work

For `author-lean-theorem`:

- General task scope: `docs/governance/task-scope-limits.md`

Prefer nearby Lean files and project commands before opening broader docs.

## C++ Numerical Work

For `cpp-build-task`:

- Shared code layout and style: `docs/governance/code-repo-standards.md`
- Build/render standards: `docs/governance/build-render-standards.md`
- Repository layout: `docs/architecture/repository-layout.md`

Prefer local source, tests, and repo build scripts before opening broader docs.

## Build And Validate Repos

For `build-repo`:

- Build and rendering standards: `docs/governance/build-render-standards.md`
- LaTeX build architecture: `docs/architecture/latex-build-and-rendering.md`
- Volume layout validation: `docs/workflows/volume-layout-audit.md`
- Proof layout validation: `docs/workflows/proof-layout-audit.md`
- Shared code layout and style: `docs/governance/code-repo-standards.md`
- Governance audit workflow: `docs/workflows/governance-audit.md`

The repository overlay's `Success gates` section names the gates that apply;
open a reference here only to interpret a failing gate.

## Cross-Repo Or Generated Files

Open these only when the task crosses repository boundaries or generated-file
ownership is unclear:

- Multi-repo sync: `docs/architecture/multi-repo-sync.md`
- Generated-file policy: `docs/architecture/generated-file-policy.md`
- Generated wrapper sync: `docs/workflows/generated-wrapper-sync.md`
- Agent task index: `docs/agent-task-index.md`
