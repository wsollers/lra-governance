# Governance Tools

This directory will hold governance generation, sync, validation, drift-check,
and task-scope audit tools.

No generator or sync tool is implemented yet.

Planned tools:

- `generate_agent_wrappers.py`
- `merge_repo_overlays.py`
- `validate_repo_rules.py`
- `audit_task_scope.py`
- `dry_run_sync.py`
- `sync_governance.py`

## Requirements

Future tools must support dry-run operation before writing downstream files.
They must refuse to touch `Learning-Real-Analysis/scripts/` and must not print
secret values.
