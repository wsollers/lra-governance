# Governance Tools

This directory contains the canonical implementations of governance generation,
wrapper preview, validation, drift-check, and task-scope audit tools.

Leaf repositories may carry wrapper scripts with matching paths, but those
wrappers must delegate back here. They must not copy or fork the implementation.
If a wrapper cannot locate `lra-governance`, it should fail with a clear error
message such as "lra-governance is not present" and should not silently skip the
required check.

Available and planned tools:

- `audit_latex_decoration.py` - inventory-only scanner for volume theorem and
  definition decoration compliance.
- `audit_proof_layout.py` - deterministic scanner for proof file layout,
  proof-stub status, topic-mirrored proof folders, and proof index reachability.
- `audit_volume_layout.py` - deterministic scanner for volume, chapter, topic,
  and router layout.
- `generate_stub.py` - deterministic scaffold for canonical stub chapters and
  topic-paired stub sections.
- `generate_agent_wrappers.py`
- `merge_repo_overlays.py`
- `report_wrapper_drift.py` - read-only comparison tool for generated wrapper
  previews versus downstream files.
- `sync_agent_wrappers.py` - guarded wrapper sync tool; dry-run by default,
  requires explicit repo selection, and write mode is not used until a pilot is
  approved.
- `validate_volume.py` - integrated volume validator for current LRA house
  rules and volume acceptance.
- `validate_repo_rules.py`
- `audit_task_scope.py`
- `dry_run_sync.py`
- `sync_governance.py`

## Requirements

Future tools must support dry-run operation before writing downstream files.
They must refuse to touch the retired `Learning-Real-Analysis` monorepo and
must not print secret values.

## Proof Layout Audit

Run from `lra-governance` against a leaf repo, volume, chapter, or section.
If the target name is not obvious, discover the available targets first:

```powershell
python tools\governance\audit_proof_layout.py --root F:\repos\lra-volume-ii --list-targets
python tools\governance\audit_proof_layout.py --root F:\repos\lra-volume-ii --chapter whole-numbers --section extending-addition --strict
```

Use `--strict` when the target is expected to satisfy the current
topic-mirrored proof architecture. Use `--format json` for machine-readable
reports.

## Volume Layout Audit

Run from `lra-governance` against a leaf repo, volume, chapter, or section.
Section scope audits the containing chapter, because topic routing and
notes/proofs pairing are chapter-level invariants:

```powershell
python tools\governance\audit_volume_layout.py --root F:\repos\lra-volume-ii --chapter whole-numbers --strict
```

Use `--strict` when the target is expected to satisfy the current
volume/chapter/topic architecture. Use `--format json` for machine-readable
reports.

## Volume Validation

Run from `lra-governance` against the target leaf volume repository:

```powershell
python tools\governance\validate_volume.py F:\repos\lra-volume-ii --fail-on-errors
```

To reduce noise during chapter work, filter the report while still validating
the full volume:

```powershell
python tools\governance\validate_volume.py F:\repos\lra-volume-ii --chapter peano-systems
```

The filtered mode changes only the printed/JSON report. The validator still
runs every volume validator across the full volume, and `--fail-on-errors`
continues to use full-volume errors as the failure gate.

Use scoped audit tools such as `audit_proof_layout.py` and
`audit_volume_layout.py` only when a task needs a focused report.

## Stub Generation

Run from `lra-governance` against the target leaf volume repository. Generate
stubs with the deterministic scaffold first, then validate the target volume.

```powershell
python tools\governance\generate_stub.py chapter --volume-root F:\repos\lra-volume-ii\volume-ii --subject ordered-fields --title "Ordered Fields" --section "Order"
python tools\governance\generate_stub.py section --chapter-root F:\repos\lra-volume-ii\volume-ii\ordered-fields --section "Completion Fields"
```

Use `--section` repeatedly or pass a semicolon-separated `--sections` list when
creating multiple section stubs in one command.

## Schema Coverage Rule

The integrated volume validator is the deterministic acceptance gate for
machine-checkable requirements from:

- `constitution/schema/file-schema.yaml`;
- `constitution/schema/block-registry.yaml`;
- `constitution/schema/artifact-matrix.yaml`.

When those schema files change, the same change must update the relevant
`validate_volume.py` module or document why a requirement is handled by another
deterministic tool. Semantic requirements such as whether a capstone truly
avoids later chapter material require source or knowledge-graph audits in
addition to structural validation.
