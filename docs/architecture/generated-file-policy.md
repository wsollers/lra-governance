# Generated File Policy

Agent instruction files and downstream compatibility wrappers should be treated
as generated artifacts.

Generated files must include:

- source document list,
- source revision or hash,
- generation timestamp when useful,
- local-edit warning,
- pointer back to `lra-governance`.

Generators must support dry-run mode and report drift before writing.

Generated files must not contain secrets or machine-local credentials.
