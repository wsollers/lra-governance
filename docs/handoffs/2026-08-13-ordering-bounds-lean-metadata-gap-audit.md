# Continuation Prompt: Ordering and Bounds Lean-to-Metadata Gap Audit

Continue the formalization-first Ordering and Bounds work by auditing what the
current compiled-Lean extractor can supply versus what LRA semantic metadata
currently records or requires.

This continuation is **diagnosis only**. Do not change Lean declarations,
attributes, schemas, registries, semantic-artifact files, TeX, or the explorer
until the gap inventory and ownership recommendations have been reviewed with
the user. Do not commit, reset, clean, revert, stage, or discard any existing
worktree change.

## Objective

Use the Ordering and Bounds pilot as a representative slice to determine:

1. which existing metadata fields Lean already supplies reliably;
2. which fields can be derived mechanically from Lean with extractor work;
3. which fields require explicit, minimal Lean annotations or named checked
   declarations;
4. which fields must remain authored mathematical or pedagogical metadata;
5. which existing metadata claims Lean can validate but should not generate;
6. which concepts, theorem variants, examples, counterexamples, or relations
   are missing from the pilot before it can exercise the full metadata model.

Bounds are the calibration slice because they exercise most expected blocks:
ambient structure, parameters, assumptions, definitions, expanded logical
forms, negations, contrapositives, duals, equivalences, existence, uniqueness,
failure modes, examples, counterexamples, proof dependencies, completeness,
formalization links, and learner prerequisites.

The immediate product is a gap report and recommendation matrix—not an
implementation.

## Repositories and preservation

Inspect these repositories read-only:

```text
F:\repos\lra-lean
F:\repos\lra-governance
F:\repos\lra-volume-i
F:\repos\lra-volume-iii
F:\repos\lra-knowledge-explorer
```

At the start:

1. Run `git status --short --branch` in all five repositories and report it.
2. Read each applicable `AGENTS.md`.
3. Resolve each repository-specific inspection through
   `F:\repos\lra-governance\capabilities\resolve.py` before working there.
4. Preserve every existing tracked and untracked change.
5. Do not run generators that overwrite semantic packages or TeX.
6. Do not invoke external semantic review; this pass compares existing
   evidence only.

## Current Lean pilot evidence

Inspect the live files; do not rely only on this summary:

```text
F:\repos\lra-lean\LRA\Pilot\Metadata.lean
F:\repos\lra-lean\LRA\Pilot\OrderBounds.lean
F:\repos\lra-lean\LRA\Pilot\OrderBoundsTheorems.lean
F:\repos\lra-lean\LRA\Pilot\OrderBoundsExamples.lean
F:\repos\lra-lean\LRA\Pilot\OrderBoundsCounterexamples.lean
F:\repos\lra-lean\LRA\Pilot\OrderBoundsMetadata.lean
F:\repos\lra-lean\LRA\Pilot\ExtractMetadata.lean
F:\repos\lra-lean\LRA\Pilot\Explorer\README.md
F:\repos\lra-lean\build\pilot\order-bounds-metadata.json
F:\repos\lra-lean\build\pilot\order-bounds-explorer.html
```

The last verified generated slice contained 46 declarations, 136 dependency
edges, 11 canonical concept IDs, and no `sorryAx` dependency. Recheck those
numbers without regenerating unless the existing output is missing or stale.

Inventory the exact current Lean-export fields. They presently include at
least:

```text
id
title
declaration
moduleName
kind
category
canonicalConceptId
statement
documentation
statementDependencies
definitionDependencies
proofDependencies
axioms
usesSorry
typed dependency edges
```

Do not assume the field named `axioms` means mathematical assumptions. Verify
its implementation. `Lean.collectAxioms` reports kernel-level proof
dependencies such as `Classical.choice`, `propext`, `Quot.sound`, and
`sorryAx`. It does not automatically label a completeness property, partial
order law, ZFC foundation, or learner prerequisite.

## Existing metadata evidence

Compare the Lean projection against these live authorities and examples:

```text
F:\repos\lra-governance\predicates.yaml
F:\repos\lra-governance\relations.yaml
F:\repos\lra-governance\structures.yaml
F:\repos\lra-governance\notation.yaml
F:\repos\lra-governance\constitution\schema\semantic-artifact.schema.json
F:\repos\lra-governance\docs\architecture\semantic-artifact-record.md
F:\repos\lra-governance\docs\workflows\semantic-artifact-calibration.md
```

Inspect the Bounds predicate entries, including at least:

```text
UpperBound
LowerBound
BoundedAbove
BoundedBelow
Bounded
MinimalElement
MaximalElement
LeastElement
GreatestElement
LeastUpperBound
GreatestLowerBound
EpsilonCharacterizationOfSupremum
EpsilonCharacterizationOfInfimum
LeastUpperBoundProperty / HasLeastUpperBoundProperty
```

Inspect existing semantic records in the routed Volume III Bounds topic,
especially:

```text
F:\repos\lra-volume-iii\volume-iii\book-analysis-i\bounding\notes\bounds-extremals\semantic-topic-audit.yaml
F:\repos\lra-volume-iii\volume-iii\book-analysis-i\bounding\notes\bounds-extremals\def-supremum\artifact.yaml
```

Sample other `artifact.yaml` records only when they expose a different field
shape. Do not treat local drafts, queued packages, failed audits, or pending
formalization links as approved truth.

Also inspect the routed Volume I order material and Volume III Bounds TeX for
the existing environments, support blocks, dependency blocks, proof links,
and `\LeanFormalizes` records. Use routed inventories where available rather
than raw filesystem globs as the authoritative artifact list.

## Required comparison model

For every metadata field or relationship, classify it as exactly one primary
acquisition class:

| Class | Meaning |
|---|---|
| `L0` | Already extracted reliably from the compiled Lean environment |
| `L1` | Mechanically derivable from Lean expressions, binders, bodies, or checked declarations with extractor work |
| `L2` | Available only after a minimal explicit Lean annotation or a named checked Lean declaration is added |
| `M` | Authored/reviewed semantic or pedagogical metadata; Lean must not infer it |
| `X` | Cross-repository foreign key or reconciliation result |
| `V` | Metadata supplied elsewhere that Lean can validate but should not originate |
| `U` | Unresolved or unsafe to infer |

For each classification record:

- the exact source field and destination field;
- one concrete Bounds example;
- whether the value is authoritative, evidence, a projection, or a draft;
- the derivation or validation rule;
- required assumptions;
- false-positive or semantic-loss risk;
- whether a stable identifier already exists;
- the smallest future change that would close the gap;
- the repository that should own that future change.

## Axiom and assumption analysis

Keep these axes separate in the report:

1. **Kernel axioms**: output of Lean proof-term axiom collection.
2. **Structural assumptions**: binders, typeclasses, and structure fields such
   as `PartialOrder`, linear order, nonemptiness, boundedness, or completeness.
3. **Mathematical prerequisites**: named facts needed for a theorem, including
   least-upper-bound or greatest-lower-bound properties.
4. **Conceptual prerequisites**: reviewed ontology or learner dependencies.
5. **Foundational lineage**: Lean type theory, an LRA ZFC realization, or
   another foundation.

Determine what can be extracted, what can only be recognized through a
canonical crosswalk, and what requires authored metadata. In particular:

- `LeastUpperBound` defines what a supremum candidate is; it does not assert
  existence and therefore should not automatically acquire completeness.
- A theorem asserting that every relevant set has a supremum is where a
  completeness assumption or least-upper-bound property belongs.
- An abstract `Poset` packages a carrier, a non-strict order, and the partial
  order laws. It does not by itself depend on a ZFC axiom. A specific
  set-theoretic construction may have separate ZFC lineage.

Identify any labels in the existing UI or schemas that currently blur these
distinctions.

## Logical-form analysis

Audit the feasibility and semantics of generating or validating:

```text
expanded definition
raw negation
approved negation normal form
contrapositive
converse
inverse
dual statement
equivalent forms
failure characterization
specialization/generalization
```

Distinguish expressions from proved declarations:

- Lean can mechanically form `Not P`, but that is the unproved logical
  opposite of `P`, not a theorem derived from a proof of `P`.
- For an implication `P → Q`, the contrapositive `¬Q → ¬P` is constructively
  provable.
- Converse and inverse are not generally derivable.
- Pushing negation through quantifiers or connectives may require classical
  assumptions and a selected normal form.
- Theorem statements often contain multiple dependent `∀` binders,
  typeclasses, and hypotheses; document when “the contrapositive” is ambiguous.
- In a partial order, `¬(a ≤ b)` does not imply `b < a`. Record the structure
  required by readable strict failure forms.

For each form, decide whether the best future representation is:

1. a virtual explorer node;
2. an extracted expression attached to the source node;
3. a named kernel-checked Lean declaration;
4. authored reviewed metadata with Lean validation;
5. deliberately unsupported.

## Bounds coverage matrix

Build a concept-by-block matrix covering at least:

- `Poset`, partial-order laws, and the Mathlib/LRA adapters;
- upper and lower bound;
- bounded above, bounded below, and bounded;
- least/greatest versus minimal/maximal elements;
- least upper bound/supremum and greatest lower bound/infimum;
- least-upper-bound and greatest-lower-bound existence properties;
- uniqueness under antisymmetry;
- maximum implies upper bound and supremum;
- supremum plus membership implies greatest element;
- dual theorems;
- empty-set/vacuous cases;
- boundedness without a supremum over `ℚ` at `√2`;
- supremum outside the subset;
- incomparability and maximal-not-greatest counterexamples;
- real and LRA-real-wrapper examples;
- epsilon characterizations over `ℝ`.

For each row show whether the current pilot has:

```text
canonical ID
checked definition/statement
completed proof
expanded logical form
raw negation
approved failure form
contrapositive when applicable
dual
positive example
boundary/vacuous example
counterexample
kernel axioms
structural assumptions
mathematical prerequisites
statement dependencies
definition dependencies
proof dependencies
pedagogical dependencies
TeX formalization link
semantic-artifact record
provenance/status
```

Use `present`, `partial`, `missing`, `not applicable`, or `unsafe to infer`, and
cite the exact evidence path/declaration for every `present` result.

## Questions the report must answer

1. What percentage of the semantic-artifact model can the current Lean
   extractor populate without new annotations?
2. What additional percentage is mechanically derivable from compiled Lean?
3. Which high-value gaps require named Lean declarations rather than
   annotations?
4. What is the minimal annotation vocabulary, if any? Do not design or add it
   yet.
5. Which existing metadata fields should be validated against Lean rather than
   generated from Lean?
6. Which fields are inherently pedagogical or provenance-oriented and must
   remain authored?
7. Where do existing metadata files overstate certainty, use stale Lean names,
   conflate kernel axioms with mathematical assumptions, or contain logical
   forms that the current parser could not represent?
8. Which missing Bounds declarations would exercise the largest number of
   currently untested metadata blocks?
9. What should the next smallest implementation slice be after the audit?
10. Which proposed extraction features could introduce false authority or
    silently change mathematical meaning?

## Required first-turn output

Return a self-contained diagnostic report in the conversation containing:

1. all five worktree states;
2. the exact evidence files inspected;
3. the live Lean output inventory and counts;
4. a field-level Lean-to-semantic-metadata crosswalk;
5. the Bounds concept-by-block coverage matrix;
6. the separate kernel/structural/mathematical/conceptual/foundational axiom
   analysis;
7. the logical-form feasibility matrix;
8. stale, contradictory, ambiguous, or unverified metadata findings;
9. a prioritized gap backlog grouped into:
   - extractor-only work,
   - Lean declaration work,
   - minimal annotation candidates,
   - semantic-artifact/schema reconciliation,
   - authored pedagogical review;
10. one recommended next implementation slice, with explicit ownership and
    validation boundaries.

Do not implement the recommendation in that first turn. Stop after presenting
the evidence-backed gap report so the user can choose what Lean should own and
what must remain metadata.

## Guardrails

- Do not create a second semantic AST, registry, or formula corpus.
- Do not copy elaborated Lean expressions into canonical registries.
- Do not infer learner prerequisites from proof-term dependencies.
- Do not treat kernel axioms as mathematical-topic axioms.
- Do not treat generated negations as proved counterexamples.
- Do not treat a theorem converse or inverse as derivable without proof.
- Do not promote a parser draft or local semantic package to reviewed status.
- Do not repair stale `\LeanFormalizes` names by guessing.
- Do not broaden the pilot beyond Ordering and Bounds merely to increase
  coverage counts.
- Do not modify or regenerate source artifacts during this audit.
