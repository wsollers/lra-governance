# Capability Reference Index

Use this file only after loading one capability and one repo overlay. Open the
smallest referenced document that answers the concrete question.

## Volume Statement Authoring

For `author-statement`:

- Decoration shape: `docs/governance/decoration-box-standards.md`
- Dependency links and `\NoLocalDependencies`: `docs/governance/dependency-standards.md`
- Proof stubs and proof file layers: `docs/governance/proof-standards.md`
- Statement atomicity: `docs/governance/atomic-artifact-standards.md`
- Notation and canonical symbols: `docs/governance/notation-standards.md`
- Add theorem workflow: `docs/workflows/add-theorem-with-proof-stub.md`
- Proof layout validator usage: `docs/workflows/proof-layout-audit.md`

## Volume Definition Authoring

For `author-definition`:

- Decoration shape: `docs/governance/decoration-box-standards.md`
- Dependency links and `\NoLocalDependencies`: `docs/governance/dependency-standards.md`
- Definition atomicity: `docs/governance/atomic-artifact-standards.md`
- Predicate and notation discipline: `docs/governance/notation-standards.md`
- Extraction-facing labels and identity: `docs/governance/extraction-standards.md`

## Chapter And Section Scaffolding

For `author-stub-chapter`:

- Volume architecture: `docs/architecture/volume-architecture.md`
- Volume layout: `docs/architecture/volume-layout.md`
- Repository layout: `docs/architecture/repository-layout.md`
- Chapter stub standard: `docs/governance/stub-chapter-standards.md`
- Layout audit workflow: `docs/workflows/volume-layout-audit.md`

For `author-stub-section`:

- Volume layout: `docs/architecture/volume-layout.md`
- Section stub standard: `docs/governance/stub-section-standards.md`
- File splitting and routing: `docs/governance/file-splitting-standards.md`
- Layout audit workflow: `docs/workflows/volume-layout-audit.md`

## Lean Work

For `author-lean-theorem`:

- Lean repo overlay: `docs/governance/repo-overlays/lra-lean.md`
- General task scope: `docs/governance/task-scope-limits.md`

Prefer nearby Lean files and project commands before opening broader docs.

## C++ Numerical Work

For `cpp-build-task`:

- Numerical-analysis overlay: `docs/governance/repo-overlays/lra-numerical-analysis.md`
- NURBS overlay, when working in `lra-nurbs`: `docs/governance/repo-overlays/lra-nurbs.md`
- Build/render standards: `docs/governance/build-render-standards.md`
- Repository layout: `docs/architecture/repository-layout.md`

Prefer local source, tests, and repo build scripts before opening broader docs.

## Build And Validate Repos

For `build-repo`:

- Build and rendering standards: `docs/governance/build-render-standards.md`
- LaTeX build architecture: `docs/architecture/latex-build-and-rendering.md`
- Volume layout validation: `docs/workflows/volume-layout-audit.md`
- Proof layout validation: `docs/workflows/proof-layout-audit.md`
- Lean overlay: `docs/governance/repo-overlays/lra-lean.md`
- C++ numerical overlay: `docs/governance/repo-overlays/lra-numerical-analysis.md`
- NURBS overlay: `docs/governance/repo-overlays/lra-nurbs.md`
- Governance audit workflow: `docs/workflows/governance-audit.md`

Prefer `capabilities/build-repo/build_repo.py --dry-run` before opening broader
docs; the generated plan usually shows which local or remote gate applies.

## Cross-Repo Or Generated Files

Open these only when the task crosses repository boundaries or generated-file
ownership is unclear:

- Multi-repo sync: `docs/architecture/multi-repo-sync.md`
- Generated-file policy: `docs/architecture/generated-file-policy.md`
- Generated wrapper sync: `docs/workflows/generated-wrapper-sync.md`
- Agent task index: `docs/agent-task-index.md`
