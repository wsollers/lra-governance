# Governance Tools

This directory will hold governance generation, sync, validation, drift-check,
and task-scope audit tools.

No generator or sync tool is implemented yet.

Planned tools:

- `audit_latex_decoration.py` - inventory-only scanner for volume theorem and
  definition decoration compliance.
- `audit_proof_layout.py` - deterministic scanner for proof file layout,
  proof-stub status, topic-mirrored proof folders, and proof index reachability.
- `audit_volume_layout.py` - deterministic scanner for volume, chapter, topic,
  and router layout.
- `generate_agent_wrappers.py`
- `merge_repo_overlays.py`
- `report_wrapper_drift.py` - read-only comparison tool for generated wrapper
  previews versus downstream files.
- `sync_agent_wrappers.py` - guarded wrapper sync tool; dry-run by default,
  requires explicit repo selection, and write mode is not used until a pilot is
  approved.
- `validate_repo_rules.py`
- `audit_task_scope.py`
- `dry_run_sync.py`
- `sync_governance.py`

## Requirements

Future tools must support dry-run operation before writing downstream files.
They must refuse to touch `Learning-Real-Analysis/scripts/` and must not print
secret values.

## Proof Layout Audit

Run from `lra-governance` against a leaf repo, volume root, or chapter root:

```powershell
python tools\governance\audit_proof_layout.py --root F:\repos\lra-volume-ii --refactor-mode
```

Use `--strict` when the target is expected to satisfy the current
topic-mirrored proof architecture. Use `--format json` for machine-readable
reports.

## Volume Layout Audit

Run from `lra-governance` against a leaf repo, volume root, or chapter root:

```powershell
python tools\governance\audit_volume_layout.py --root F:\repos\lra-volume-ii --refactor-mode
```

Use `--strict` when the target is expected to satisfy the current
volume/chapter/topic architecture. Use `--format json` for machine-readable
reports.
