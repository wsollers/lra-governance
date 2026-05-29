# LRA Governance

This directory is the canonical source for project-wide governance rules.

Agent-specific files such as `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`,
`.github/copilot-instructions.md`, and `.github/instructions/*.instructions.md`
are generated artifacts, not source-of-truth documents.

Future generators will combine:

1. global core governance rules,
2. the appropriate repo overlay,
3. provider-specific wrapper formatting.

Repo overlays are additive. They refine the global rules for a repository's
owned work, but they do not fork or weaken the global rules.

## Planned Modules

- `agent-instruction-policy.md`
- `task-scope-limits.md`
- `authoring-standards.md`
- `proof-standards.md`
- `extraction-standards.md`
- `notation-standards.md`
- `file-splitting-standards.md`
- `refactoring-standards.md`
- `model-view-standards.md`
- `build-render-standards.md`
- `repo-overlays/`
