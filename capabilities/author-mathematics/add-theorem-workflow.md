# Add Theorem With Proof Stub

Use this workflow in a leaf volume repository, which is the canonical source.
There is no monorepo.

## Required Steps

1. Author a typed theorem-family artifact under the `author-mathematics`
   capability. Preserve its theorem, lemma, proposition, or corollary subtype,
   give it a stable source label, and set `proof_stub: true`.
2. Validate the payload against
   `constitution/schemas/mathematical-content.schema.json` and render the
   statement plus optional proof-stub post-step with
   `tools/governance/generators/mathematical_tex.py`.
3. Write the rendered statement to the appropriate `notes/**/*.tex` file and
   the matching proof stub to the leaf repo `proofs/**/*.tex` tree.
4. The renderer delegates the stub shape to the canonical deterministic
   proof-stub renderer. Do not hand-expand or improvise it.
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
