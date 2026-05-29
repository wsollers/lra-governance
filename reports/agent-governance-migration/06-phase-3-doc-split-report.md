# Phase 3 Document Split Report

Generated: 2026-05-29

## Scope

Phase 3 populated the modular governance and architecture skeleton with
first-pass rule summaries derived from existing `DESIGN.md`,
`REPOSITORY_STRUCTURE.md`, repo READMEs, and workflow ownership boundaries.

`DESIGN.md` and `REPOSITORY_STRUCTURE.md` were preserved as compatibility
sources. No downstream repositories were edited or synced.

## Updated Areas

- `docs/governance/`
- `docs/governance/repo-overlays/`
- `docs/architecture/`
- `docs/schemas/README.md`
- `tools/governance/README.md`
- `prompts/README.md`

## Source Mapping

- Authoring, boxes, exposition, chapter entry, and stability rules moved into
  `docs/governance/authoring-standards.md`.
- Proof architecture, proof labels, navigation, and dependency remarks moved
  into `docs/governance/proof-standards.md`.
- Logical blocks, dependency blocks, labels, and theorem-explorer extraction
  contracts moved into `docs/governance/extraction-standards.md`.
- Predicate, notation, relation, and missing-predicate rules moved into
  `docs/governance/notation-standards.md`.
- Repository ownership, sync, volume layout, theorem-explorer dispatch, and
  canonical YAML ownership moved into `docs/architecture/`.
- Repo-specific guidance was placed into additive overlays.

## Explicitly Not Done

- Did not delete or rewrite `DESIGN.md`.
- Did not generate `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, Copilot files, or
  `.github/instructions/*.instructions.md`.
- Did not sync downstream repos.
- Did not edit mathematical content.
- Did not touch `F:\repos\Learning-Real-Analysis\scripts\`.

## Review Focus

- Whether the modular split preserves the meaning of current rules.
- Whether repo overlays remain additive and correctly scoped.
- Whether specialist guidance is isolated to the right overlays.
- Whether `DESIGN.md` can remain as a compatibility source until generator
  wrappers exist.
