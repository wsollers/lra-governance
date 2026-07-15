# Semantic Artifact Calibration

## Goal

Calibrate reviewed semantic records and governed LaTeX one formal environment at a
time before processing the corpus in batches. Source repositories are
`lra-volume-i` through `lra-volume-viii`; vocabulary and policy come from
`lra-governance`.

## One-at-a-time phase

Continue one at a time until ten consecutive varied artifacts require no schema
change and no structural renderer correction.

Choose samples that expose new shapes: nested quantifiers, disjunctions,
existence/uniqueness, recursive and quotient definitions, object/meta-language
claims, partial/total orders, theorem contrapositives, well-definedness obligations,
Lean links, and proof-vault links.

## Codex input packet

```yaml
task:
  mode: calibrate_semantic_artifact
  requested_action: review_and_return
source:
  repository: wsollers/lra-volume-iii
  commit: "<sha>"
  file: "<path>"
  label: def:supremum
  environment_kind: definition
  current_tex: |
    ...
  nearby_context: |
    ...
governance:
  repository: wsollers/lra-governance
  commit: "<sha>"
  schema: constitution/schema/semantic-artifact.schema.json
  registries:
    - predicates.yaml
    - structures.yaml
    - notation.yaml
    - relations.yaml
verification_context:
  lra_lean_commit: null
  proof_vault_commit: null
```

Send only the owning environment, attached support blocks, minimal convention
context, and exact commits.

## Required return package

```text
<label-root>/
├── package.yaml
├── artifact.yaml
├── corrected.tex
├── source.patch
├── validation.yaml
├── source-map.yaml
├── registry-needs.yaml
├── formalization-links.yaml
└── proof-vault-links.yaml
```

`artifact.yaml` is reviewed semantic content.
`corrected.tex` preserves governed environments, labels, titles, block order,
proof links, and dependencies.
`source.patch` is the exact unified diff.
`validation.yaml` contains all checks.
`source-map.yaml` maps fields to source lines and origin classes.
`registry-needs.yaml` reports missing/ambiguous canonical vocabulary.
The two resolver files contain refreshable Lean/Mathlib and proof-vault lookup data.

## Codex integration rules

1. Validate `artifact.yaml`.
2. Stop on errors or blocking ambiguity.
3. Compare returned TeX and patch with the exact target.
4. Apply only the reviewed environment patch.
5. Preserve unrelated source.
6. Run volume governance validation and the target build.
7. Store the approved item as a golden fixture.
8. Report every applied file and check.

Do not hand-correct renderer-owned TeX. Patch the record or renderer and regenerate.

## Validation

```powershell
python tools\governance\validate_semantic_artifact.py `
  --artifact <artifact.yaml> `
  --package-dir <returned-package-directory> `
  --governance-root <lra-governance> `
  --repos-root F:\repos `
  --strict
```

The validator covers schema, atomic labels, registry IDs/arities, binder scope,
logical policy, relationship namespaces, verification-link shape, unresolved
ambiguity, and presentation-key exclusion.

Owning-repo checks additionally validate exact label targets, compilation, Lean
builds, Mathlib declaration resolution, and proof-vault routes.

## Golden fixtures

```text
fixtures/semantic-artifacts/<label-root>/
├── input.tex
├── artifact.yaml
├── expected.tex
├── expected-validation.yaml
└── source-map.yaml
```

Classify regression differences as semantic, presentation-only, diagnostic-only,
or expected migration.

## Stabilization gate

Move to dependency-related groups of five only when:

- ten consecutive varied artifacts require no schema change;
- generated TeX needs no structural hand correction;
- all variables are declared or bound;
- approved negations match the mechanical form under listed assumptions;
- registry signatures and ambient arguments resolve;
- source maps preserve origin distinctions;
- Lean and proof-vault data remain foreign keys, not copied state;
- every golden fixture still passes.

Route unusual items back to individual calibration.
