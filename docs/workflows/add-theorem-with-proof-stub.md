# Add Theorem With Proof Stub

Use this workflow in a leaf volume repository, which is the canonical source.
There is no monorepo.

## Required Steps

1. Add the theorem-like statement in the appropriate `notes/**/*.tex` file.
2. Give every top-level `theorem`, `proposition`, `lemma`, and `corollary` a
   stable source label.
3. Create the matching proof stub in the leaf repo `proofs/**/*.tex` tree.
4. Build the stub by copying the canonical proof-stub template in
   `docs/governance/proof-standards.md` verbatim and substituting only the
   theorem root, restatement, and dependency links. The shape is enforced by
   `constitution/schema/file-schema.yaml`; do not improvise it.
5. Inspect nearby statements, proof stubs, and topic indexes before editing.
6. Ensure the proof file is routed through the chapter's proof indexes.
7. Run:

```bash
python scripts/build_volume.py --validate-only
```

The theorem and proof stub should be committed together. If validation fails,
the change is not ready; fix it before committing.

## Ownership

The leaf repo is the source of truth and builds independently. There is no
monorepo to sync into.
