# Populate Proof Stub

Use this workflow when a proof stub already exists and the task is to replace
TODO proof bodies with canonical proof content.

## Required Steps

1. Work in the leaf volume repository that owns the proof file.
2. Locate the existing proof file by theorem label and `\LRAProofFor{...}`.
3. Preserve the durable proof container (see "Proof Stub Durability" in
   `docs/governance/proof-standards.md`, enforced by
   `constitution/schema/file-schema.yaml`).
4. Before writing proof content, verify that the unnumbered proof restatement
   matches the current theorem-like source. If it does not, synchronize the
   restatement from the theorem source while the file is still a stub.
5. Replace only the professional proof TODO body and detailed learning proof
   TODO body unless the task explicitly authorizes broader edits.
6. Add or refine dependency/proof-structure remarks as needed.
7. Run:

```bash
python scripts/build_volume.py --validate-only
```

## Invariant

Proof population happens in place. Do not delete, replace, or relocate the
proof file as part of ordinary proof generation.
