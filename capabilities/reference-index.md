# Capability Reference Index

Use this file only after loading one capability and one repo overlay (the
resolver eager-loads `capabilities/overlays/<repo>.md` for every task). Open
the smallest referenced document that answers the concrete question.

## Indexed LRA Lookup

For `lookup-lra`:

- Source authority and index ownership: `capabilities/reference/source-indexing-policy.md`
- Canonical vocabulary authority: `capabilities/reference/architecture/canonical-yaml.md`
- Internal index refresh: `capabilities/prepare-lean-tex-lookup/capability.md`

Run the lookup tool before opening these references. Open only the reference
needed to interpret, refresh, or validate the returned lane.

## Typed Mathematical Authoring

For `author-mathematics`:

- Decoration shape: `capabilities/reference/decoration-box-standards.md`
- Dependency links and `\NoLocalDependencies`: `capabilities/reference/dependency-standards.md`
- Proof stubs and proof file layers: `capabilities/reference/proof-standards.md`
- Statement atomicity: `capabilities/reference/atomic-artifact-standards.md`
- Notation and canonical symbols: `capabilities/reference/notation-standards.md`
- Add theorem workflow: `capabilities/author-mathematics/add-theorem-workflow.md`
- Proof layout validator usage: `capabilities/audit-proof-layout/capability.md`
- Definition atomicity: `capabilities/reference/atomic-artifact-standards.md`
- Predicate and notation discipline: `capabilities/reference/notation-standards.md`
- Extraction-facing labels and identity: `capabilities/reference/extraction-standards.md`
- Structural presentations (signatures, languages, models, classification
  cards, blueprints): `capabilities/reference/model-standards.md`

## Chapter And Section Scaffolding

For `author-stub-chapter`:

- Volume architecture: `capabilities/reference/architecture/volume-architecture.md`
- Volume structure: `capabilities/reference/volume-structure.md`
- Repository layout: `capabilities/reference/architecture/repository-layout.md`
- Chapter stub standard: `capabilities/reference/stub-chapter-standards.md`
- Layout audit workflow: `capabilities/refactor-volume-layout/capability.md`

For `author-stub-section`:

- Volume structure: `capabilities/reference/volume-structure.md`
- Section stub standard: `capabilities/reference/stub-section-standards.md`
- File splitting and routing: `capabilities/reference/file-splitting-standards.md`
- Layout audit workflow: `capabilities/refactor-volume-layout/capability.md`

## Lean Work

For `author-lean-theorem`:

- General task scope: `capabilities/reference/task-scope-limits.md`

Prefer nearby Lean files and project commands before opening broader docs.

## C++ Numerical Work

For `cpp-build-task`:

- Shared code layout and style: `capabilities/reference/code-repo-standards.md`
- Build/render standards: `capabilities/reference/build-render-standards.md`
- NURBS workspace architecture: `capabilities/reference/architecture/lra-nurbs-architecture.md`
- Repository layout: `capabilities/reference/architecture/repository-layout.md`

Prefer local source, tests, and repo build scripts before opening broader docs.

## Build And Validate Repos

For `build-repo`:

- Build and rendering standards: `capabilities/reference/build-render-standards.md`
- LaTeX build architecture: `capabilities/reference/architecture/latex-build-and-rendering.md`
- Volume layout validation: `capabilities/refactor-volume-layout/capability.md`
- Proof layout validation: `capabilities/audit-proof-layout/capability.md`
- Shared code layout and style: `capabilities/reference/code-repo-standards.md`
- Governance audit workflow: `capabilities/audit-governance/capability.md`

The repository overlay's `Success gates` section names the gates that apply;
open a reference here only to interpret a failing gate.

## Cross-Repo Or Generated Files

Open these only when the task crosses repository boundaries or generated-file
ownership is unclear:

- Multi-repo sync: `capabilities/reference/architecture/multi-repo-sync.md`
- Workflow and data-flow map: `capabilities/reference/architecture/workflow-data-flow.md`
- Generated-file policy: `capabilities/reference/architecture/generated-file-policy.md`
- Generated wrapper sync: `capabilities/generate-governance-wrappers/capability.md`
- Agent task index: `capabilities/task-index.md`

## Volume Structure, Editions, And Front Matter

For volume layout, build, and print/digital work:

- Edition behavior (digital/print/reference): `capabilities/reference/digital-print-edition-standards.md`
- Breadcrumb/footer chrome and placement: `capabilities/reference/breadcrumb-footer-standards.md`
- Dedication pages: `capabilities/reference/architecture/dedication-page-standard.md`
- Front matter and frontispieces: `capabilities/reference/architecture/frontmatter-and-frontispiece-standard.md`
- Adding a book to a volume: `capabilities/reference/book-addition-standards.md`
- Chapter capstone selection and layout: `capabilities/reference/capstone-exercise-standards.md`
