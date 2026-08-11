# Validate Volume

Run the integrated validator against the full target volume:

```text
python <governance-root>/tools/governance/validate_volume.py <repo-root> --fail-on-errors
```

Use `--chapter` only to narrow the report while working; the full-volume gate
remains authoritative before completion. Open a referenced standard or schema
only when a reported violation needs interpretation. Do not preload validator
source, house-rule documents, or schema bodies.
