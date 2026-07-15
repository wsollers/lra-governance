# Calibrate One Semantic Artifact

Operate in one LRA split volume repository with `lra-governance` available through
`LRA_GOVERNANCE_ROOT` or a sibling checkout.

## Load only

1. target repo `AGENTS.md`;
2. `lra-governance/AGENTS.md`;
3. `docs/agent-task-index.md`;
4. `docs/workflows/semantic-artifact-calibration.md`;
5. `docs/architecture/semantic-artifact-record.md`;
6. `constitution/schema/semantic-artifact.schema.json`;
7. the target repo overlay;
8. the four canonical root registries;
9. the target environment and one nearby governed example.

## Select one atomic unit

Use one `definition`, `axiom`, `theorem`, `lemma`, `proposition`, or `corollary`
plus attached support blocks. If independent concepts are bundled, report
`requires_split` and stop.

## Prepare the handoff

Record exact repository/commit, path, label, environment kind, current source,
minimal nearby context, governance/registry commit, and known Lean/proof-vault links.
Do not rewrite mathematics before review.

## Require the external return

- `package.yaml`
- `artifact.yaml`
- `corrected.tex`
- `source.patch`
- `validation.yaml`
- `source-map.yaml`
- `registry-needs.yaml`
- `formalization-links.yaml`
- `proof-vault-links.yaml`

Reject invented canonical vocabulary or proof routes.

## Validate before applying

```powershell
python <governance-root>\tools\governance\validate_semantic_artifact.py `
  --artifact <returned>\artifact.yaml `
  --package-dir <returned> `
  --governance-root <governance-root> `
  --repos-root <repos-root> `
  --strict
```

Stop on errors or unresolved items with `blocks_generation: true`.

## Apply

Apply only the selected environment patch. Preserve unrelated source. Do not alter
registries without separate approval. Add an approved golden fixture. Run volume
validation and the target build. Remove temporary handoff files or keep them only
under ignored run output.

## Mathematical rules

Keep context, parameters, assumptions, statement, negation, applicability failure,
and actual failure distinct.

Standard quantified blocks use ordinary mathematics, not canonical predicate names.
Predicate readings use only registry entries and explicit ambient structures.

List every assumption used to normalize a negation. Do not replace `x \nleq y` by
`y < x` without the required order law.

Definitions and axioms do not receive contrapositives.

## Verification rules

Lean links record pinned versions, declaration identity, build status, and reviewed
correspondence; type-checking alone does not establish exact equivalence.

Proof-vault links are foreign keys to `lra-proof-vault/metadata.yaml`; do not copy
attempt history or OCR data into the artifact.

## Completion

Complete only when semantic validation, governed source validation, target build,
fixture creation, and cleanup all pass.
