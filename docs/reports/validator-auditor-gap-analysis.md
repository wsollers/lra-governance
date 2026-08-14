# Validator/Auditor Gap Analysis

Updated: 2026-08-12

## Scope

This report compares the legacy auditor prompt contracts in
`constitution/prompts/audit-*.md` with the current validation surface in:

- `constitution/auditor/audits/*.py`
- `constitution/auditor/validators/*.py`
- `tools/governance/*.py`
- `tools/governance/rules/**`
- `capabilities/*/verify.py`

The purpose is to decide what still blocks capability installation and legacy
auditor retirement.

## Executive Summary

The deterministic validators now cover much of the structural surface that the
legacy auditors described, especially chapter routing, proof layout, decoration
presence/order, label discipline, dependency links, box discipline, figure
placement, generated-block hygiene, canonical volume shape, print-edition
routing, router-only topic indexes, and canonical capstone/exercises routing.

Since the first draft of this report, `tools/governance/validate_volume.py` has
become the primary volume-level runner. It runs `volume_shape` first and fails
fast when the canonical tree is not present; only then does it run the small
composable validators. The parity fixture harness now includes
`validate_volume.py` coverage in addition to legacy layout/proof/decoration
checks.

Parity is not complete. The remaining gaps are concentrated in semantic or
judgment-heavy checks:

- mathematical correctness of negations, contrapositives, and quantified forms;
- atomicity of definitions and theorem-like statements;
- canonical notation consistency beyond simple predicate/name scans;
- semantic notation equivalence beyond exact registry spellings;
- audit-report output parity for statement audits;
- proof body quality checks beyond layer/layout enforcement.

Recommendation: install the capability path as the primary workflow, but keep
legacy auditors archived as fallback until the gaps below are resolved or
explicitly retired.

## Current Surfaces

### Legacy Auditors

| Legacy auditor | Contract type | Output |
|---|---:|---|
| `audit-statement.md` | LLM structural and semantic statement audit | JSON audit report |
| `audit-proof.md` | LLM proof-file layer and proof quality audit | JSON audit report |

### Current Validators And Auditors

| Surface | Nature | Notes |
|---|---:|---|
| `constitution/auditor/audits/statement.py` | LLM-backed | Still calls `audit_statement` prompt. Not a deterministic replacement. |
| `constitution/auditor/audits/proof.py` | Hybrid | TODO stubs are deterministic; full proof audit still calls prompt. |
| `constitution/auditor/audits/stub.py` | Deterministic | Adapts canonical planned-chapter validator findings to the shared JSON audit-report contract. |
| `constitution/auditor/audits/symbols.py` | Deterministic | Adapts the canonical chapter-symbol scanner to the existing Markdown report path. |
| `constitution/auditor/validators/generated_block.py` | Deterministic | Good generated statement block preflight. Narrower than statement audit. |
| `constitution/auditor/validators/ontology.py` | Deterministic | Validates canonical ontology files, not chapter usage parity. |
| `tools/governance/validate_decoration.py` | Deterministic | Thin harness over decoration rules. Strong structural replacement for many statement checks. |
| `tools/governance/audit_proof_layout.py` | Deterministic | Strong proof layout validator. |
| `tools/governance/validate_volume.py` | Deterministic | Primary composable volume validator with shape fail-fast. |
| `tools/governance/validators/*.py` | Deterministic | Small validator modules for routing, proof contracts, capstones, dependencies, labels, formal decoration, and structure. |
| Retired chapter house-rule validator | Deterministic legacy | Removed after useful structural checks were folded into `validate_volume.py` modules or explicitly retired as stale/mutating behavior. |
| `tools/governance/audit_volume_layout.py` | Deterministic legacy | Volume/chapter routing and layout validation. Useful as comparison/fallback until parity retirement. |
| `tools/governance/test_parity_fixtures.py` | Deterministic test | Now includes `validate_volume.py` expected code coverage for the broken parity fixture. |
| `tools/governance/generators/mathematical_tex.py` | Deterministic validator/renderer | Validates typed mathematical payloads and renders canonical TeX without model calls. |
| `tools/governance/generators/proof_stub.py` | Deterministic generator | Generates proof stubs as a separate optional post-step; not itself an auditor. |

## Gap Matrix

### Statement Auditor Versus Validators

| Legacy check | Current deterministic coverage | Gap |
|---|---|---|
| Environment label present, prefix, lowercase slug | Covered by `validate_volume.py` modules and generated-block validation. | Low. |
| Box presence and house colors | Covered by generated-block validation and `validate_volume.py` modules. | Low for generated/current forms. Legacy wrapper variants should remain tested. |
| Proof link from theorem-like statement | Covered by decoration rules and proof/coverage validators. | Low. |
| Required decoration blocks present | Covered for rendered typed payloads and by `validate_volume.py` modules. | Medium. Coverage is not full artifact-matrix parity for every optional/conditional/dependent block. |
| Decoration block order | Covered by `formal_decoration.py`; needs parity fixtures for all block-order cases. | Low/medium. |
| Forbidden decoration blocks by artifact type | Covered by `formal_decoration.py`. | Low. |
| Dependent block parent/child rules | Covered by `formal_decoration.py`; needs broader tests for each dependent pair. | Low/medium. |
| Dependencies block or `\NoLocalDependencies` | Covered by generated-block validation and dependency validators. | Low. |
| Dependency targets are formal labels, not proof labels | Covered by generated-block validation and dependency validators. | Low. |
| Source crosswalk citation presence | Covered structurally by decoration validation where applicable. | Medium. Validator checks citation presence, not provenance semantics. |
| Examples/non-examples do not introduce labels/formal statements | Covered by block discipline and formal decoration validators. | Low/medium. |
| Predicate names not in formal bodies | Covered for `\operatorname` leakage and some known predicate forms. | Medium. It does not fully prove all predicate-language leakage. |
| Predicate names registered in canonical source | Covered for explicit `\operatorname{...}` uses by the deterministic chapter scanner. | Low. Prose-only predicate concepts are not inferred. |
| Notation matches `notation.yaml` | Exact registered spellings are inventoried; broader style validators remain active. | Medium. Semantic equivalence is deliberately not inferred. |
| Relation names match `relations.yaml` | Not applicable: this registry contains ontology edges, not TeX relation spellings. | The legacy check had no valid data contract. |
| Correct negated quantified statement | Not deterministically covered. | High. Requires semantic logic or explicit structured source fields. |
| Correct contrapositive | Not deterministically covered. | High. Requires semantic logic or structured hypothesis/conclusion representation. |
| Quantifier variables all fixed/explicit | Not deterministically covered except some style triggers. | High. |
| Atomicity of formal item | Not deterministically covered. | High. This is repository-identity critical and still judgment-heavy. |
| Figure atomicity / embedded TikZ | Partly covered by current structural validators; nontrivial figure judgment remains heuristic. | Low/medium. |
| JSON audit-report schema output | Covered only for prompt-backed auditor path. | Medium. Deterministic validators emit their own records, not the legacy audit JSON shape. |

### Proof Auditor Versus Validators

| Legacy check | Current deterministic coverage | Gap |
|---|---|---|
| Layer order | Covered by `audit_proof_layout.py` and `validate_volume.py` proof modules. | Low. |
| `\newpage`, `\phantomsection`, proof label, `\LRAProofFor` | Covered. | Low. |
| Label root and filename match | Covered. | Low. |
| Return navigation | Covered. | Low. |
| Proof-vault URL placement and raw image rejection | Covered by `audit_proof_layout.py`. | Low. |
| Restatement has no label and uses starred theorem-like env | Covered. | Low. |
| Professional and detailed proof layers present | Covered. | Low. |
| Proof structure remark present | Covered. | Low. |
| Dependencies block present and formal targets only | Covered. | Low. |
| Proof topic/index reachability | Covered by `audit_proof_layout.py`, `audit_volume_layout.py`, and `validate_volume.py` proof modules. | Low. |
| Stub squareness | Covered by `audit_proof_layout.py`, decoration rules, and proof-stub generator. | Low. |
| No proof-structuring/flash macros | Partly covered by proof and block-discipline validators. | Medium. Custom macro universe is not exhaustively classified. |
| No topicbox/exposition in proof files | Mostly covered by top-level environment discipline. | Medium. Needs explicit parity fixture. |
| Professional proof is compact and rigorous | Not covered. | High. This is semantic/quality judgment. |
| Detailed proof steps are genuine logical milestones | Not covered. | High. |
| House notation in proof bodies | Not fully covered. | High. |
| Full JSON audit-report schema output | Prompt-backed proof auditor still provides this; deterministic layout validator uses its own JSON shape. | Medium. |

### Stub Auditor Versus Validators

| Legacy check | Current deterministic coverage | Gap |
|---|---|---|
| Chapter required paths | Covered by `chapter_stub.py` and the integrated `validate_volume.py` registry. | Closed. |
| Chapter router heading/label/breadcrumb/input order | Covered by the shared `chapter_router.py` single-chapter contract. | Closed. |
| Notes/proofs topic routing | Covered. | Low. |
| Capstone standard location/routing | Covered, including the optional paired-path rule and router-only input. | Closed. |
| Folder/file naming discipline | Canonical chapter slug and generated capstone filename are covered. | Closed for planned stubs. |
| Chapter registry membership and neighbors | Covered when a registry is supplied to the focused audit. | Closed. |
| Planned-volume `index.tex` scope and registry | Covered by `planned_volume_stub.py`. | Closed for deterministic generator output. |
| Planned-volume manifest ordering | Covered by `planned_volume_stub.py` against the explicit ordered registry. | Closed. |
| JSON audit-report schema output | Deterministic adapter preserves the shared report shape. | Closed. |

### Chapter Symbol Auditor Versus Validators

| Legacy check | Current deterministic coverage | Gap |
|---|---|---|
| Registry YAML parses and required list shapes are valid | Covered by registry validators and scanner input validation. | Closed. |
| Predicate `\operatorname{...}` leakage into formal bodies | Covered by `formal_predicate_leakage.py`. | Closed for registered predicate names. |
| Unknown `\operatorname{...}` names | Covered by `operator_metadata.py`. | Closed. |
| Predicate and structure command spelling | Covered by exact `\operatorname` / `\mathsf` classification. | Closed. |
| Predicate-reading arity and ambient arguments | Covered by signature and construction validators. | Closed for machine-readable registry roles. |
| Registered notation use | Exact literal registry spellings are inventoried. | Closed for exact spellings; semantic equivalence is explicitly out of scope. |
| Arbitrary missing or inconsistent notation | Not inferred from mathematical prose or formulas. | Deliberately out of scope pending a structured notation grammar. |
| Relation names in chapter formulas | `relations.yaml` stores ontology edges, not TeX relation spellings. | Invalid legacy contract; no relation-symbol claim is made. |
| Unused registry entries by chapter | Deterministically reported as informational. | Closed. |
| Markdown symbol-audit output | Deterministic report preserves the existing saved-report workflow. | Closed. |

## Cross-Cutting Gaps

### 1. Prompt-Backed Auditors Still Exist

The `constitution/auditor/audits` modules still call legacy prompt contracts for
statement and full-proof audits. Stub and chapter-symbol audits now use tested
deterministic validators and compatibility report adapters.

### 2. Output Shape Is Not Unified

Legacy auditors return `constitution/schemas/audit-report.json` shaped reports.
The deterministic validators return validator-specific JSON or terminal output.
Before retiring auditors, decide whether parity requires:

- preserving the old audit-report schema;
- accepting validator-native reports;
- adding a small adapter that converts validator records into audit-report
  records for compatibility.

### 3. Semantic Checks Need A Data Model

The hardest statement checks cannot be made robust with regex alone:

- correct negation;
- correct contrapositive;
- all variables fixed or quantified;
- atomicity;
- notation equivalence;
- predicate arity equivalence.

To retire the prompt auditor for these, the source needs structured fields or a
small intermediate representation. Otherwise these should be explicitly marked
"human/LLM review retained" rather than claimed as validator parity.

### 4. Parity Fixtures Are Too Small

`tools/governance/fixtures/parity/manifest.json` now locks a small but more
representative set of issue codes, including unified `validate_volume.py`
coverage:

- unified volume validation: chapter router shape, router-only topic indexes,
  missing dependency declarations, interpretation warnings, wrong label prefix,
  unknown/forbidden decoration blocks, missing dependent decoration parents,
  source crosswalk citation hygiene, formal claims inside expository blocks,
  decoration order, label-inside-restatement, topicbox/exposition in proof
  files, inline TikZ placement, duplicate labels, boxed nonformal content, proof
  routing/reachability, stub discipline, proof dependency targets, and proof
  exercises routing;
- decoration: wrong label prefix, missing interpretation, missing dependencies,
  missing standard quantified statement, missing proof navigation, proof stub
  structure not blank;
- proof layout: partial stub, proof dependency target, proof reachability;
- volume layout: unrouted proofs topic.

This is a useful start, but still not enough to justify deletion of the legacy
semantic auditors.

## Retirement Readiness

### Safe To Treat As Validator-Owned Now

These rule families can be treated as validator-owned, with legacy auditors only
as optional fallback:

- proof file layer presence/order;
- proof label/root/filename association;
- proof routing/index reachability;
- chapter notes/proofs topic layout;
- chapter router order;
- formal label prefix and slug hygiene;
- required basic decoration presence;
- dependency block presence and target-prefix discipline;
- box color/style discipline;
- generated-block basic hygiene;
- inline/nontrivial TikZ placement checks.

### Not Safe To Remove Yet

Retain structured semantic or explicit human review for:

- statement semantic correctness;
- atomicity detection;
- negation and contrapositive correctness;
- semantic notation equivalence beyond exact registry spellings;
- proof body quality and logical milestone review;
- old audit-report JSON compatibility, if any downstream tooling consumes it.

## Recommended Closeout Plan

1. Continue adding parity manifest rows for every legacy auditor requirement
   that is validator-owned.
2. Continue adding negative fixtures for lower-priority deterministic checks as
   they are declared validator-owned.
3. Extend the deterministic chapter-symbol scanner only when registries expose
   additional machine-readable notation or relation-symbol contracts.
4. Preserve the audit-report adapter where downstream auditor workflows consume it.
5. Mark remaining semantic checks as either structured-data future work or retained
   human/LLM review.
6. Remove each remaining audit prompt only after its live caller has a tested
   deterministic or deliberately scoped judgment boundary.

## Bottom Line

Validator coverage is strong enough to install capabilities and route normal
work through the deterministic path. It is not strong enough to delete the
legacy auditors without either losing semantic review coverage or formally
declaring those semantic checks out of scope.
