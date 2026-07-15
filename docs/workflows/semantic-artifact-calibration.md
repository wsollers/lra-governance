# Semantic Artifact Calibration

## Goal

Calibrate reviewed semantic records and governed LaTeX one formal environment at a
time before processing the corpus in batches. Source repositories are
`lra-volume-i` through `lra-volume-viii`; vocabulary and policy come from
`lra-governance`.

## External reviewer requirement

Review must be performed by the governed external transport in
`docs/workflows/external-gpt-reviewer.md`. Codex prepares the input packet but may
not generate or self-certify the semantic package.

Required call properties:

```yaml
provider: openai_responses_api
requested_model: gpt-5.6
resolved_model: gpt-5.6-sol...
reasoning_effort: high
self_review: false
```

A Codex subagent, second Codex pass, or unverified manually written package is not
an external review. Stop when the external transport is unavailable.

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
  source_hash: "sha256:<digest>"
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

## Reviewer invocation

```powershell
python <governance-root>\tools\governance\invoke_external_gpt_reviewer.py semantic `
  --input <semantic-input.json> `
  --output <label-root> `
  --prompt <governance-root>\constitution\prompts\calibrate-semantic-artifact.md
```

The executor writes the package and `external-review-receipt.yaml`. Codex must not
repair a partial result.

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
├── proof-vault-links.yaml
└── external-review-receipt.yaml
```

`artifact.yaml` is reviewed semantic content. `corrected.tex` preserves governed
environments, labels, titles, block order, proof links, and dependencies.
`source.patch` is the exact unified diff. The other YAML files record validation,
source provenance, registry needs, and refreshable verification links. The receipt
records the external GPT-5.6 response evidence.

## Codex integration rules

1. Validate `artifact.yaml` and `package.yaml`.
2. Live-verify the external response evidence.
3. Stop on errors, blocking ambiguity, wrong model, or unverifiable response ID.
4. Compare returned TeX and patch with the exact target.
5. Apply only the reviewed environment patch.
6. Preserve unrelated source.
7. Run volume governance validation and the actual target build.
8. Store the approved item as a golden fixture.
9. Report every applied file and check.

Do not hand-correct reviewer or renderer output. Route defects back through a new
external review call or fix the schema/renderer under separate approval.

## Validation

```powershell
python <governance-root>\tools\governance\validate_semantic_artifact.py `
  --artifact <artifact.yaml> `
  --package-dir <returned-package-directory> `
  --governance-root <governance-root> `
  --repos-root <repos-root> `
  --strict

python <governance-root>\tools\governance\validate_external_reviewer_evidence.py `
  --package <returned-package-directory>\package.yaml `
  --verify-live
```

The first validator covers schema, atomic labels, registry IDs/arities, binder
scope, logical policy, relationships, verification links, unresolved ambiguity,
and presentation-key exclusion. The second retrieves the stored external result
and verifies its ID, GPT-5.6 model, completion status, and output hash.

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
- every external response live-verifies;
- every golden fixture passes.

Route unusual items back to individual calibration.

## Reversible topic audit mode

For topic-by-topic review that stores packages and evidence but leaves canonical
TeX unchanged, use `docs/workflows/topic-semantic-audit-loop.md`.
