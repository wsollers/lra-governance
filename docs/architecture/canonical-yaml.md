# Canonical YAML

Source: `DESIGN.md` and `REPOSITORY_STRUCTURE.md`.

The source-of-truth YAML files live in `lra-governance`:

- `predicates.yaml`
- `structures.yaml`
- `notation.yaml`
- `relations.yaml`

They live at the repository root, not under a volume repo and not under a
chapter-local `docs/` directory.

They moved here when the assembled monorepo (`Learning-Real-Analysis`) was
retired. They are not duplicated into volume repos. Automated authoring,
auditing, and extraction tools read them from `lra-governance`, resolved the same
way as the rest of governance.

## Tool Access

Tools that run outside `lra-governance` resolve the canonical YAML through the
governance root: `LRA_GOVERNANCE_ROOT`, a sibling `../lra-governance` checkout,
or the build Docker image. Older auditor entry points that accept an explicit
root (for example a `REPO_ROOT` environment variable or a `--repoDir` / `--root`
option) should be pointed at the `lra-governance` checkout rather than a
monorepo.

No agent may invent predicate, structure, relation, or notation names locally in
content files. Missing canonical vocabulary must be reported as a governance or
YAML update need. Predicate names, structure constructors, signatures, and
ambient-structure polymorphism are governed by
`docs/governance/predicate-standards.md`.
