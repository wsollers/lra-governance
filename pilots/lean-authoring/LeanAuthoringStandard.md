# Experimental Lean Topic Authoring Standard

Status: disposable pilot; proposed input to a later governance prompt.

## Purpose

This standard defines how a short mathematical authoring request becomes a
reviewable declaration-family package, checked Lean source, and a plain LaTeX
projection. It calibrates the workflow before any production backport replaces
an originating Volume I or Volume III declaration.

The authoritative unit is a **concept family** inside a **topic**. A concept
family contains one primary generic declaration and only those checked
specializations, relationships, examples, counterexamples, or failure
statements that have been deliberately selected. A topic is an ordered group
of concept families; it is not a single large Lean file.

## Ownership

The layers have distinct authority:

1. The chat response proposes mathematics in simple LaTeX and Lean.
2. The normalized request records placement and requested scope.
3. The reviewed concept package owns the pilot source payload and selections.
4. Python validates and materializes that package; it does not invent claims.
5. Lean checks declarations and records whether proofs use placeholders.
6. Extraction supplies compiled evidence and trust information.
7. Publication review chooses which checked projections appear in a volume.

The pilot package is authoritative only for generated pilot files. It does not
supersede production Lean, volume LaTeX, semantic artifacts, or registries.

## Repository and folder layout

Generic mathematics belongs at its earliest mathematical home. Carrier-specific
material imports the generic declaration rather than restating its body.

```text
LRA/Pilot/
  VolumeI/
    <Subject>/<Topic>/
      Topic.lean
      index.tex
      Concepts/
        <Concept>/
          All.lean
          Definition.lean
          Theorems.lean          # only when selected
          definition.tex
          concept-package.json
  VolumeIII/
    <Subject>/<Topic>/
      Topic.lean
      index.tex
      Concepts/
        <Concept>/...
```

Lean module and namespace segments use PascalCase. Topic and concept display
titles remain separately recorded. TeX labels and future volume paths use
lowercase kebab-case. The concept folder is the complete local family unit;
the topic router imports concept routers in reviewed dependency order.

## Declaration order inside a concept family

When present, declarations are ordered as follows:

1. primary generic vocabulary or structure;
2. primary definition, axiom, or theorem statement;
3. definitional aliases and adapters;
4. elementary consequences;
5. existence and uniqueness results;
6. equivalent formulations and named logical variants;
7. negations and failure predicates;
8. carrier or structure specializations;
9. relationships to sibling concepts;
10. checked examples, boundary cases, and counterexamples.

Absent categories are omitted. Empty placeholder modules are not generated.

## Minimum assumptions

A generic declaration uses only the structure needed to state its mathematics.
For example, an upper-bound predicate needs a binary relation and membership;
it does not need reflexivity, transitivity, antisymmetry, totality, a field, or
subset nonemptiness. Stronger assumptions belong on the theorem or
specialization that uses them.

Canonical project vocabulary is preferred when it is already governed. The
Upper Bound pilot therefore uses `LRA.VolumeI.Relations.Endorelation` rather
than introducing a second binary-relation alias.

## Naming and source style

Public Lean declarations and namespaces use descriptive PascalCase names.
Parameters, hypotheses, and witnesses use readable prose-style camelCase
names. Every public declaration has a mathematical doc comment and a fenced
`Logical form:` block. The logical form shows the unfolded proposition for a
proposition-valued definition.

One public declaration introduces one atomic mathematical object or claim.
Greatest Element, Bounded Above, and Upper Bound are sibling concepts even
when their definitions depend on one another.

## Definitions, theorems, and proof state

Definitions and data declarations contain complete bodies. A theorem requested
for statement authoring is emitted with `sorry` unless proof completion is
separately requested. The package must then record
`proof_status: "stub-sorry"`.

Lean accepting a theorem containing `sorry` verifies elaboration of the
statement, not the proof. Such a declaration is never reported as proof-checked
or used as independent evidence for a correspondence. A theorem proved without
placeholders records `proof_status: "checked"`. Definitions record
`proof_status: "not-applicable"`.

## Generic declarations and carrier specializations

A carrier specialization must reference the primary generic declaration. It
must not copy the generic predicate body as an independently maintained fact.
The package records whether the relationship is:

- definitionally equal;
- supplied by a named checked proof;
- accepted only as a statement stub; or
- selected by an author but not yet verified.

Volume I owns generic order-theoretic declarations. Volume III may own
real-number wrappers and analysis results. The wrapper is checked by Lean; a
publication decision remains separate.

A specialization is never inferred merely because a later volume is known to
use the concept. It is generated only when the request or a reviewed package
selection asks for it. Likewise, when a request names an ambient project
structure such as the Volume I `Poset`, normalization must use that structure;
it must not weaken the declaration to an arbitrary relation merely because the
resulting predicate body would be extensionally similar.

## Optional family-member decision rules

Each candidate is selected, deferred, rejected, or not applicable with a short
reason.

| Candidate | Include when |
|---|---|
| Literal negation | The negative condition is reused or published. |
| Pushed negation | It improves mathematical use and its logical principles are recorded. |
| Strict-order variant | A checked declaration carries the necessary total/linear-order assumptions. |
| Failure predicate | Failure has multiple reusable branches or is a recurring diagnostic concept. |
| Converse or inverse | It is mathematically meaningful and its truth status is known. |
| Contrapositive | It is pedagogically or technically used; do not add it mechanically as clutter. |
| Specialization | A later volume genuinely consumes the restricted carrier or structure. |
| Example | It demonstrates use, a boundary, or an important non-obvious instance. |
| Counterexample | It refutes a plausible false implication, converse, or omitted hypothesis. |

Failure modes are not generated merely because a proposition can be negated.
They are warranted when the decomposition identifies distinct mathematical
causes that downstream prose, proofs, or diagnostics will name. Pedagogical
labels for those causes remain authored even when Lean checks the predicates.

Counterexamples must identify the exact target claim or boundary they witness.
Preferred roles are `false-converse`, `missing-hypothesis`,
`structure-boundary`, `carrier-boundary`, and `degenerate-case`. A surprising
object without a named target is an example, not yet a governed counterexample.

## Chat response and normalization

The initial response is no broader than the request. For a definition-only
request it is deliberately small:

- one ordinary-language definition;
- one undecorated display formula;
- the smallest Lean declaration that expresses the requested concept; and
- no automatically invented theorem family, example set, failure taxonomy,
  carrier specialization, or publication prose.

When the request explicitly asks for negations, variants, examples, or
counterexamples, the response includes a selection report. A valid form is
emitted as a proposed declaration; a false converse or inverse is emitted only
as a counterexample target; and an uninteresting or inapplicable form is
recorded as omitted with a reason. The normalizer must not turn a false variant
into a declaration that asserts it.

Normalization then resolves canonical identity, volume, subject, topic,
namespace, existing vocabulary, and optional-family selections. Any addition
beyond the chat request records its provenance and requires review. Volume or
carrier placement not present in the request is not silently inferred.

## Package and materialization contract

The request and concept-package JSON documents validate against the pilot
schemas. Exact Lean and LaTeX source appears in the reviewed package so Python
performs deterministic file creation rather than mathematical synthesis.

The materializer must:

- reject absolute paths and path traversal;
- reject duplicate modules, files, or declarations;
- require proof status appropriate to the declaration kind;
- create deterministic concept and topic routers;
- preserve files outside its generated paths and marked wiring block;
- copy the normalized package into each generated concept folder;
- support a read-only `--check` mode; and
- be idempotent.

Generated LaTeX is a plain projection. In this pilot it uses only normal prose,
display math, `\section`, and `\input`; it does not emit LRA environments,
boxes, labels, logical blocks, dependencies, or publication decorations.

## Backport gate

Nothing in this pilot replaces an originator. Before a production backport:

1. compare the new family against every current originator and consumer;
2. choose the canonical production namespace and compatibility period;
3. prove or definitionally validate each replacement relation;
4. migrate imports and TeX correspondence without duplicating formulas;
5. complete or explicitly retain theorem stubs according to volume policy;
6. regenerate extraction evidence and verify placeholder/axiom closure; and
7. obtain review of publication selection and independently authored prose.
