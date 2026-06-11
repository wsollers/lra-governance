# Governance Rule Atoms

Rules in this tree are small, pure checks. Each file should answer one question,
for example "is the proof stub state square?" or "does this block have a
dependencies marker?"

Rules must:

- expose a `check(...)` function;
- return `core.finding.Finding` objects;
- avoid filesystem writes, CLI parsing, and orchestration;
- stay small enough to read in one sitting.

Validators compose rule atoms into task-sized gates. Generators live elsewhere
and use a dry-run/apply, idempotent plan.
