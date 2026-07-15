# Semantic Artifact Record

## Purpose

The semantic artifact record is the reviewed, renderer-independent description of one
atomic mathematical definition, axiom, theorem, lemma, proposition, or corollary.

It supports correction and deterministic regeneration of governed LaTeX, later HTML
and explorer renderers, validation, Lean/Mathlib crosswalks, and proof-vault links.
It describes mathematics and evidence. It never stores colors, columns, borders,
icons, spacing, page breaks, or CSS classes.

## Authority during calibration

During calibration:

1. reviewed volume LaTeX remains the canonical published statement;
2. `artifact.yaml` is a reviewed semantic sidecar;
3. the sidecar must round-trip to governed LaTeX without semantic drift;
4. schema or renderer gaps are fixed before authority moves to YAML.

A later governance decision may make approved artifact YAML authoritative.

## Atomicity

One concept corresponds to one formal environment, one label, one semantic record,
and one graph node. When one environment contains independent concepts, mark
`identity.atomicity.status: requires_split` and stop generation.

## Data classes

### Human-approved semantic data

Context, parameters, assumptions, statement, logical forms, useful normalized
negation, failure analysis, interpretation, examples, dependency meanings,
formalization correspondence, and proof-vault relationship.

### Mechanically derived data

Binder counts, free variables, mechanically pushed negation, block triggers,
rendered TeX/HTML, graph projections, semantic hashes, proof-vault attempt counts,
and resolved documentation URLs. Derived data belongs in validation or resolver
output, not as competing authority.

### Provenance data

Repository commits, source ranges, registry/schema versions, origin classification,
review state, and unresolved ambiguity.

## Required top-level shape

The machine authority is
`constitution/schema/semantic-artifact.schema.json`.

```yaml
schema_version: lra.semantic-artifact/1.0
identity: {}
location: {}
classification: {}
context: []
parameters: []
assumptions: []
statement: {}
logical_forms: {}
semantics: {}
failure_analysis: {}
relationships: {}
notation: {}
exposition: {}
verification: {}
provenance: {}
governance: {}
```

## Core distinctions

Keep these separate:

```text
ambient context
!= typed parameters
!= standing assumptions
!= statement content
!= statement negation
!= failure of applicability
!= actual predicate/theorem failure
```

For example, when nonemptiness is a standing assumption, `A = emptyset` is an
applicability failure, not automatically part of the negation.

## Formula representation

Formal formulas use a small typed AST. Every binder has a stable `binder_id`;
printed symbols alone do not identify binders. Restricted quantifiers retain their
restriction explicitly.

Initial node kinds:

- `variable`, `constant`, `application`;
- `predicate`, `relation`, `membership`, `equals`;
- `not`, `and`, `or`, `implies`, `iff`;
- `forall`, `exists`, `exists_unique`;
- `raw_latex` as a calibration escape hatch.

`raw_latex` emits a warning and should disappear as the schema stabilizes.

## Logical framework

Record both:

```yaml
logical_framework:
  mathematical_vernacular | first_order | many_sorted_first_order |
  second_order | set_theoretic | type_theoretic | axiom_schema

language_level:
  object_language | metalanguage | mixed
```

This is essential for logic chapters.

## Definitions and definedness

Definitions classify as predicate, object, recursive, inductive, quotient,
notation, or structure definitions. Object-producing definitions may record
obligations such as existence, uniqueness, closure, representative independence,
or recursion consistency/completeness.

## Logical forms

`standard_quantified` is reviewed.

`negation.mechanical` is derived from the AST.
`negation.approved_normal_form` is the reviewed useful form.
`normalization_requires` records every extra fact used to simplify it, such as
totality of an order, nonemptiness, classical logic, or decidability.

Definitions and axioms do not receive contrapositives.

## Relationship namespaces

Keep separate:

- `dependency_edges`: prerequisite, structural-existence, structural-pairing,
  proof-use;
- `ontology_edges`: specializes, derives_from, uses_ambient, legacy_alias_of;
- `provenance_edges`: source_variant_of, reduces_to;
- `proof_edges`: links among statements and proof evidence.

## Verification attachments

### Canonical proof

Record the owning volume proof label, path, commit, status, and layer completion.

### Lean formalizations

Record stable identifiers: `lra-lean` commit, Lean toolchain, pinned Mathlib
version/commit when applicable, module, declaration, source path, status, and the
artifact semantic hash at correspondence review.

A successful build does not prove exact correspondence. Classify correspondence as:

- exact;
- definitionally_equivalent;
- logically_equivalent;
- specialization;
- generalization;
- component;
- collective;
- partial;
- related_only.

### Mathlib crosswalks

Store the pinned version/commit, module, declaration, source path, and reviewed
relationship. Documentation and source URLs are derived from those identifiers.

### Proof vault

`lra-proof-vault/metadata.yaml` remains authoritative for attempt history. The
artifact stores a foreign key: theorem/proof labels, vault path, metadata path,
route version/confidence, optional featured attempt, and reviewed relationship.
Do not duplicate OCR details or attempt history.

## Provenance and ambiguity

Field-level mappings belong in `source-map.yaml`. An unresolved item has a code,
question, candidates, and `blocks_generation`. Meaning-changing ambiguity blocks
generation.

## Return-package manifest

Every returned directory includes `package.yaml`. It pins the artifact label,
source and governance commits, review status, and the SHA-256 digest of every
returned file. The manifest makes package completeness and accidental mutation
machine-checkable. It is governed by
`constitution/schema/semantic-artifact-package.schema.json`.

Support files carry their own schema version:

- `lra.semantic-artifact-validation/1.0`;
- `lra.semantic-artifact-source-map/1.0`;
- `lra.semantic-artifact-registry-needs/1.0`;
- `lra.semantic-artifact-formalization-links/1.0`;
- `lra.semantic-artifact-proof-vault-links/1.0`.

## Rendering contract

Renderers consume semantic data plus the governed block registry. The initial TeX
renderer preserves current environments and block order. Restyling shared macros
does not alter semantic data.

## Versioning

Pin semantic schema, governance, registry, source, and renderer-contract versions.
Schema changes require migration notes and regression against the golden corpus.
