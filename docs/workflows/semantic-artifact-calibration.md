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
2. Run the local semantic logic validator on `artifact.yaml` and `corrected.tex`.
3. Run independent AST extractor comparison on the exact source/corrected
   environment snippet and `artifact.yaml`.
4. Live-verify the external response evidence.
5. Stop on errors, blocking ambiguity, wrong model, unverifiable response ID, or
   any AST-gate disagreement.
6. Compare returned TeX and patch with the exact target.
7. Apply only the reviewed environment patch.
8. Preserve unrelated source.
9. Run volume governance validation and the actual target build.
10. Store the approved item as a golden fixture.
11. Report every applied file and check.

Do not hand-correct reviewer or renderer output. Route defects back through a new
external review call or fix the schema/renderer under separate approval.

Local reference packages are useful calibration artifacts, but they must not
masquerade as external review evidence. A package with synthetic response IDs,
placeholder hashes, or a local-reference note is not live evidence, even if its
YAML is schema-shaped. Such packages are for validator development only and must
not be applied to source.

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

python <governance-root>\tools\governance\validate_semantic_logic.py `
  --artifact <returned-package-directory>\artifact.yaml `
  --corrected-tex <returned-package-directory>\corrected.tex `
  --output <run-dir>\logic-validation.yaml

python <governance-root>\tools\governance\compare_semantic_ast_extractors.py `
  --source-tex <run-dir>\artifact-source-snippet.tex `
  --artifact <returned-package-directory>\artifact.yaml `
  --output <run-dir>\ast-extractor-comparison.yaml
```

The first validator covers schema, atomic labels, registry IDs/arities, binder
scope, logical policy, relationships, verification links, unresolved ambiguity,
and presentation-key exclusion. The second retrieves the stored external result
and verifies its ID, GPT-5.6 model, completion status, and output hash. The
logic validator and extractor comparison are the local AST gate; they control
whether the package is trusted for source integration.

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

## Closeout status policy

Artifact review must distinguish four outcomes:

- `mathematically_valid`: the core statement and mechanical negation are correct;
- `schema_valid`: the artifact and support files validate structurally;
- `governance_ready`: all labels, source provenance, proof provenance, registry
  signatures, and carried-context metadata resolve without warnings;
- `requires_migration`: the artifact is meaningful but should not remain in its
  current formal kind or concept ownership slot.

A package may be useful for calibration while still reporting
`governance_ready: pass_with_warnings`. Do not apply such a package to canonical
source unattended. Warnings that require closeout include:

- unresolved dependency or ontology labels;
- unverified proof edges or canonical proof routes;
- source hash mismatches or local-only source commits;
- equivalent-characterization edges from one `def:*` artifact to another
  `def:*`;
- quantified LaTeX whose quantifier binders are absent from the AST;
- theorem-level approved negations or contrapositives recorded in YAML but
  missing from corrected TeX;
- claimed ontology IDs or registry structures that do not resolve or do not
  appear structurally in the AST;
- raw-LaTeX binder domains where structured binder metadata is needed for full
  validation.

Theorem/proof policy:

- proof incompleteness is allowed during proof-reset workflows and should warn
  as `PROOF_INCOMPLETE`, `PROOF_STRUCTURE_EMPTY`, or
  `PROOF_DEPENDENCIES_TODO`;
- theorem dependencies used only inside a proof route should be recorded as
  `dependency_edges[].kind: proof-tool`, not as definitional prerequisites;
- do not add proof dependencies that assume the conclusion's missing regularity.
  For example, Darboux's theorem for derivatives must not depend on the
  continuous-function Darboux property for `f'`, because no continuity of `f'`
  is assumed;
- the attached owned proof should be recorded as
  `relationships.proof_edges[].kind: canonical-proof`, with proof incompleteness
  represented by proof-completion warnings rather than a missing edge;
- proof-statement divergence is blocking. The theorem statement, proof
  restatement, cited definitions, hypotheses, domains, quantifier order, and
  conclusion must describe the same mathematical claim;
- if the proof file is still a stub, meaning both proof bodies are TODO/reset
  placeholders, a proof-restatement mismatch is repairable by overwriting the
  proof's unnumbered restatement with the canonical theorem statement. This is
  a restatement synchronization, not proof generation. It must preserve the
  proof label, `\LRAProofFor{...}`, return link, proof-body TODOs, proof
  structure, dependencies block, and routing. Do not use this shortcut for an
  authored/non-stub proof; authored proof divergence remains blocking and
  requires review;
- theorem-level failure modes must be failures of the theorem, not merely
  failures of one predicate appearing inside the theorem. For an equivalence
  theorem, failure means disagreement among formulations.

Generation output must be compared against the Python validators before it is
trusted. At minimum, run the semantic artifact validator, the local semantic
logic validator, and the independent AST extractor comparison. The generated
artifact may be mathematically plausible, but if the Python validators disagree
with it, the validator output controls the closeout status until the artifact or
the validator rule is repaired under governance.

This requirement applies to every future permanent addition or revision of a
formal mathematical environment. External review supplies semantic content and
evidence; the local AST gate decides whether that content may be integrated.

Only `governance_ready: pass` packages are candidates for unattended
section-wide processing. `pass_with_warnings` packages are supervised
calibration artifacts.

## Reversible topic audit mode

For topic-by-topic review that stores packages and evidence but leaves canonical
TeX unchanged, use `docs/workflows/topic-semantic-audit-loop.md`.
