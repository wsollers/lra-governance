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
5. The proof restatement must be copied from the theorem-like statement. If a
   later validator finds a mismatch while the proof remains a TODO stub,
   overwrite the proof restatement from the theorem source and preserve the
   rest of the stub.
6. Inspect nearby statements, proof stubs, and topic indexes before editing.
7. Ensure the proof file is routed through the chapter's proof indexes.
8. Create or update the semantic artifact package for the new theorem-like
   statement, including `statement.semantic_ast`,
   `logical_forms.standard_quantified.ast`, any predicate reading AST, and the
   source snippet for the exact new environment.
9. Run the semantic AST gate:

```bash
python ../lra-governance/tools/governance/validate_semantic_artifact.py --artifact <artifact.yaml> --package-dir <package-dir> --governance-root ../lra-governance --repos-root ..
python ../lra-governance/tools/governance/validate_semantic_logic.py --artifact <artifact.yaml> --corrected-tex <corrected.tex> --output <logic-validation.yaml>
python ../lra-governance/tools/governance/compare_semantic_ast_extractors.py --source-tex <artifact-source-snippet.tex> --artifact <artifact.yaml> --output <ast-extractor-comparison.yaml>
```

10. Run:

```bash
python scripts/build_volume.py --validate-only
```

The theorem, proof stub, and semantic artifact evidence should be committed
together. If validation or the AST gate fails, the change is not ready; fix it
before committing.

## Ownership

The leaf repo is the source of truth and builds independently. There is no
monorepo to sync into.
