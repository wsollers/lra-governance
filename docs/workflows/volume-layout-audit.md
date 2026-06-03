# Volume Layout Audit Workflow

Use this workflow to mechanically audit volume, chapter, and topic folder
layout.

Machine-readable layout authority lives in
`constitution/schema/file-schema.yaml`.

Run from `lra-governance` against a leaf repo, volume root, or chapter root:

```powershell
python tools\governance\audit_volume_layout.py --root F:\repos\lra-volume-ii --refactor-mode
```

Use `--strict` when the target is expected to satisfy the current
volume/chapter/topic architecture:

```powershell
python tools\governance\audit_volume_layout.py --root F:\repos\lra-volume-ii --strict
```

Use JSON output for generated reports:

```powershell
python tools\governance\audit_volume_layout.py --root F:\repos\lra-volume-ii --format json
```

The audited rule set is the volume/chapter/topic layout portion of
`constitution/schema/file-schema.yaml`, with human-facing context in
`docs/architecture/volume-layout.md`.

The audit does not move files or modify source.
