# Continuation Prompt: Complete the Source-Grounded Concept-Authoring Process

Continue the LRA Lean-authoring pilot by completing and canonically adopting
the source-grounded concept-authoring workflow.

The governing tracking issue is:

- `wsollers/lra-governance#22` — Complete and adopt the source-grounded
  concept-authoring process

Related implementation issues:

- `#18` — Define concept-authoring package v0.2 schemas, storage, and migration
- `#19` — Specify the source and Mathlib candidate-discovery protocol
- `#20` — Build a minimal human-in-the-loop candidate review interface
- `#21` — Restore deterministic materialization for approved concept packages
- `#16` — Existing formalization-first adversarial study protocol that must be
  reconciled with the new source-grounded workflow

Read these issues before making architectural decisions.

## Current state

Inspect the live repositories before relying on this summary.

In `F:\repos\lra-governance`:

- `docs/workflows/content-generation-from-source.md` has an uncommitted
  proposed `Concept Authoring Gate`.
- `pilots/lean-authoring/` is an existing untracked disposable pilot tree.
- The legacy package schema is `lra.lean-concept-package/0.1`.
- The legacy schema cannot represent concept contracts, immutable evidence,
  candidate revisions, review events, reassignment, or exact-revision
  approval.
- `materialize.py` therefore fails closed before writing anything, including
  under `--check`.
- The pilot README still documents a materialization command that is now
  intentionally blocked.
- `transcript.txt` and `transcript2.txt` are existing untracked user files.

Treat all tracked and untracked content as user work. Do not delete, reset,
clean, overwrite, stage, commit, or push unless explicitly authorized.

## Architectural decision

The intended process is:

```text
manual definition and vocabulary contract
        ↓
human approval of that contract
        ↓
primary-source and Mathlib candidate discovery
        ↓
mathematical normalization and deduplication
        ↓
human candidate review
        ↓
deterministic generation
        ↓
Lean validation
        ↓
publication approval
        ↓
integration and backport review
```

The definition and canonical vocabulary are authored decisions. They are not
inferred from search results.

Lean is the checked implementation and adversarial validation surface after
candidate approval. It must not silently replace the source-grounded discovery
and pedagogical-selection stages.

Existing internal LRA Lean and LaTeX are integration evidence only during
discovery. They may later be inspected for structure reuse, names, collisions,
placement, and backport targets.

## Immediate objective

Complete Phase 1: issue `#18`.

Define and implement the canonical successor data model, storage ownership,
validation rules, and migration policy needed by the remaining issues.

Do not re-enable materialization yet. Stop for human review after Phase 1 is
complete.

## Repository procedure

For every repository used:

1. Run `git status --short --branch`.
2. Read every applicable `AGENTS.md`.
3. Resolve the exact task through:

   ```text
   F:\repos\lra-governance\capabilities\resolve.py
   ```

4. Preserve all existing work.
5. Use the smallest canonical authority.
6. Do not create competing schema, vocabulary, or semantic authorities.
7. Use `apply_patch` for edits.
8. Run every resolver-required validation and focused test.
9. Do not stage, commit, push, or close GitHub issues.

Work principally in `lra-governance`. Inspect another repository only when
necessary to determine ownership or compatibility, and resolve the task
separately for it.

## Phase 1: successor schema and ownership

Design a versioned successor to package schema `0.1`. Use `0.2` unless
repository conventions require a different reviewed identifier.

Provide typed records for the following.

### Concept contract

Record:

- stable concept ID;
- display name;
- normalized mathematical definition;
- carrier and ambient structures;
- notation and variable roles;
- intended Lean signature;
- learner-facing terminology;
- accepted synonyms;
- explicitly excluded meanings;
- primary concept owner;
- related concepts;
- target volume, topic, and concept folder;
- contract revision;
- contract status;
- reviewer attribution.

The contract must distinguish absent, not applicable, unresolved, proposed,
and approved values.

### Evidence records

Represent these lanes separately:

- configured primary-source evidence;
- external Mathlib declaration/API evidence;
- internal LRA integration evidence;
- independently authored pedagogy;
- mechanical logical or structural derivation.

Evidence must be append-only. Corrections create superseding records rather
than rewriting historical evidence.

Primary-source evidence should support:

- stable source IDs;
- source-profile or source-list identity;
- source snapshot or revision;
- extraction quality;
- indexed-text versus direct-PDF inspection;
- physical page, section, and index-line locators;
- raw excerpt or evidence locator;
- normalization notes;
- supported candidate IDs;
- unresolved ambiguity.

Mathlib evidence should support:

- pinned Mathlib version or commit;
- module;
- exact declaration name;
- exact signature and assumptions;
- documentation or source locator;
- relationship to the normalized candidate.

### Candidate records

Each candidate must support:

- stable candidate ID;
- concept-contract ID and revision;
- normalized-revision ID;
- normalized mathematical statement;
- artifact kind;
- proposed Lean name;
- primary concept owner;
- related concepts;
- carrier structure;
- hypotheses;
- evidence references;
- provenance categories;
- normalization performed;
- mathematical-interest assessment;
- learner value;
- proposed placement;
- proof expectation;
- recommendation;
- unresolved fields.

Candidate identity must survive wording changes while normalized revisions
remain individually identifiable.

### Review events

Review history must be separate from discovery evidence and append-only.

Support these actions and states:

- `discovered`;
- `normalized`;
- `proposed`;
- `approved`;
- `approve_with_edit`;
- `deferred`;
- `rejected`;
- `reassigned` or `moved_to_related_concept`;
- `generated`;
- `lean_validated`;
- `publication_approved`.

Every review event must identify:

- reviewer;
- timestamp;
- action;
- rationale;
- candidate ID;
- affected normalized revision;
- previous and resulting states;
- edited revision or destination concept when applicable.

Approval applies only to the exact normalized revision named by the event. A
meaning-changing edit invalidates prior approval and returns the candidate to
`proposed`.

### Generation package and receipt

Define the typed input and receipt needed for deterministic generation.

Generation must:

- consume approved records only;
- reject unresolved concept contracts;
- reject unapproved or stale candidate revisions;
- use stable ordering;
- avoid wall-clock and filesystem-enumeration nondeterminism;
- produce byte-identical output for identical inputs and tool versions;
- record every emitted artifact and originating candidate revision;
- perform no discovery, normalization, or approval.

## Storage and authority

Determine and document:

- which repository owns each record type;
- where concept contracts live;
- where vocabulary references live;
- where immutable evidence lives;
- where mutable review events live;
- where approved generation packages and receipts live;
- whether records use YAML, JSON, or a reviewed split;
- how concept-folder records relate to governance-owned schemas;
- how schema versions and migrations are handled.

Do not create a second vocabulary registry or copied formula corpus.

## Migration policy

Specify what happens to schema `0.1`.

At minimum:

- legacy packages remain inspectable;
- legacy packages remain non-materializable;
- migration must not infer approval from `family_status`,
  `publication_status`, or `selected`;
- missing evidence or review data remains explicitly unresolved;
- migrated candidates return to `proposed` unless exact approval can be
  represented from reviewed evidence;
- no existing Upper Bound fixture is silently promoted.

## Reconcile issue #16

Document the relationship between this workflow and issue `#16`.

The resolution should preserve adversarial Lean study after approval while
clarifying that:

- the concept contract is approved first;
- mathematical candidates are discovered from primary sources and external
  Mathlib;
- source recurrence and pedagogical judgment are reviewed explicitly;
- Lean validates approved statements and explores their boundaries;
- internal LRA formalizations do not serve as independent discovery sources;
- compilation does not itself establish intended meaning or publication
  approval.

Do not silently leave contradictory authority models in force.

## Validation requirements

Add focused tests for:

- valid concept contracts;
- unresolved contracts;
- immutable evidence references;
- valid and invalid normalized revisions;
- approval of the current revision;
- stale approval after editing;
- deferred, rejected, and reassigned candidates;
- invalid state transitions;
- unknown fields;
- duplicate stable IDs;
- nondeterministic ordering;
- attempted generation from schema `0.1`.

Run all required governance tests and report exact results.

## Downstream path after Phase 1

Do not implement these phases during this continuation unless separately
approved.

### Phase 2 — Issue #19

Document and automate candidate discovery:

- configured source profiles first;
- at least five independent close primary sources by default;
- explicit reviewed exceptions;
- stable source-ID filtering;
- exact case-insensitive concept phrases;
- whitespace and OCR-line-break tolerance;
- no small result cap;
- proximity to formal declaration labels;
- substantive false-positive rejection;
- direct-PDF fallback;
- separate Mathlib search;
- auditable discovery receipts.

### Phase 3 — Issue #20

Build a small typed CLI/table or local form for candidate review and enforce
the lifecycle mechanically.

### Phase 4 — Issue #21

Update the README and restore materialization only for approved successor
packages. Add fail-before-write, exact-revision, byte-reproducibility, and
end-to-end tests.

### Phase 5 — separate mathematical review

Only after the workflow is approved:

- regenerate the Poset and Bounds candidate packages;
- review them against close source books;
- inspect internal LRA artifacts for integration;
- generate Lean and LaTeX;
- review collisions and backport targets;
- merge only after explicit approval.

Do not regenerate, migrate, merge, or modify Poset, Bounds, Lean, LaTeX,
manifests, topic wiring, or volume content during this continuation.

## Deliverables

Provide:

1. Authority and storage map.
2. Successor schema design.
3. Implemented schemas and deterministic validators.
4. State-transition model.
5. Migration policy from `0.1`.
6. Reconciliation proposal for issue `#16`.
7. Valid and invalid fixtures.
8. Test and validation results.
9. Compatibility impact.
10. Decisions requiring human review.
11. Recommended next action for issues `#19`, `#20`, and `#21`.

Stop for review after Phase 1.
