# Continuation Prompt: Formalization-First Ordering and Bounds

Use this handoff to continue the Ordering, Sets, and Bounds work in a new
Codex conversation. The motivating conversation from 2026-08-13 may be pinned
for historical context, but this document is intended to be self-contained.

## Objective

Restart the learning process with a formalization-first pilot centered on
order bounds:

```text
review the mathematical concept
  -> model it with LRA-owned Lean structures
  -> prove the definition and selected theorems
  -> challenge every condition
  -> formalize examples and counterexamples
  -> verify readable failure modes
  -> harvest typed dependencies and logical shape
  -> connect Lean to the TeX artifacts
  -> write or improve exposition from the verified packet
```

The work spans:

```text
F:\repos\lra-lean
F:\repos\lra-volume-i
F:\repos\lra-volume-iii
F:\repos\lra-governance
F:\repos\lra-knowledge-explorer       # later consumer, not the first edit target
```

Primary subject areas:

- Volume I: predicate sets, membership, relations, preorders, partial orders,
  posets, linear orders, bounds, extremal elements, suprema, infima,
  completeness, and lattices;
- Volume III: real-analysis Bounds and Extremal Values;
- governance: predicate vocabulary, TeX/Lean crosswalks, semantic artifacts,
  dependency extraction, explorer export, and deterministic TikZ inputs.

## GitHub Issues

These issues memorialize the decisions and process:

- [lra-governance#16](https://github.com/wsollers/lra-governance/issues/16):
  formalization-first adversarial study protocol for definitions and theorems;
- [lra-governance#17](https://github.com/wsollers/lra-governance/issues/17):
  extraction of elaborated Lean semantics, explorer chunks, and TikZ diagrams;
- [lra-lean#11](https://github.com/wsollers/lra-lean/issues/11):
  concrete Bounds pilot.

Read all three before changing the mathematical code or notes.

## Repository State at Handoff

Handoff date: 2026-08-13.

```text
lra-governance          main  d80f087  dirty with substantial intentional work
lra-lean                main  ed92e44  clean
lra-volume-i            main  ef00bd4  clean
lra-volume-iii          main  39052ee  clean
lra-knowledge-explorer  main  68b4f47  clean
```

The governance changes predate this handoff and belong to the user. Preserve
them. Do not reset, revert, clean, discard, overwrite, stage, or commit them.
This handoff file is an additional uncommitted governance file.

Do not commit or push any repository unless explicitly requested.

## First Actions in the New Conversation

1. Run and report `git status --short --branch` in all five repositories.
2. Read the applicable `AGENTS.md` files.
3. Resolve the task through the canonical governance resolver for each
   repository before doing repository-specific work.
4. Read the three GitHub issues above.
5. Inspect the live files listed below. Treat every implementation detail in
   this handoff as provisional until verified.
6. Build an exact declaration/TeX/predicate inventory for the first pilot
   slice before moving or renaming files.
7. Do not begin with a broad reorganization. First choose the canonical
   declaration family and prove that the proposed import direction is acyclic.

Suggested status commands:

```powershell
git -C F:\repos\lra-governance status --short --branch
git -C F:\repos\lra-lean status --short --branch
git -C F:\repos\lra-volume-i status --short --branch
git -C F:\repos\lra-volume-iii status --short --branch
git -C F:\repos\lra-knowledge-explorer status --short --branch
```

Suggested initial resolution for the Lean implementation work:

```powershell
python F:\repos\lra-governance\capabilities\resolve.py `
  --repo lra-lean `
  --task "Implement the first formalization-first Ordering and Bounds pilot slice, with named examples, counterexamples, and verified failure modes" `
  --root F:\repos\lra-lean
```

Re-resolve separately before editing Volume I or Volume III TeX.

## Authority and Ownership

For the reviewed pilot slice:

- The LRA Lean declaration owns the checked mathematical definition or
  theorem statement.
- A completed named Lean proof owns a verified theorem, example,
  counterexample, or equivalence witness.
- The predicate registry owns canonical readable vocabulary, roles,
  signatures, and notation. It does not own copied definition bodies.
- `\LeanFormalizes` records the reviewed TeX-to-Lean correspondence.
- The existing semantic-artifact AST is the portable projection format. Do
  not create another AST or independently authored formula corpus.
- Python owns deterministic extraction, validation, serialization, graph
  slicing, rendering, and files.
- Authored TeX owns the learning narrative and pedagogical presentation.
- The knowledge explorer consumes harvested formal facts plus authored
  pedagogical relationships; it is not a mathematical authority.

The ordinary mathematical declarations should use Lean's native dependent
type system. Do not route them through Volume I's memorialized first-order
logic library merely to obtain a formula representation.

For the initial Volume I core, prefer the LRA-owned set/relation/order layers
and keep Mathlib out of the semantic dependency chain. Optional Mathlib
crosswalks may be added later as verified projections; they are not the
authority for this pilot.

## Live Lean Foundations

Inspect these before relying on the summary:

```text
F:\repos\lra-lean\LRA\VolumeI\Set\LRASet\LRASet.lean
F:\repos\lra-lean\LRA\VolumeI\Set\Interface\Membership.lean
F:\repos\lra-lean\LRA\VolumeI\Set\Interface\Subset.lean
F:\repos\lra-lean\LRA\VolumeI\Relations\Basic\Relations.lean
F:\repos\lra-lean\LRA\VolumeI\Relations\Order\Relations.lean
F:\repos\lra-lean\LRA\VolumeI\Relations\Order\OrderStructures\Preorder.lean
F:\repos\lra-lean\LRA\VolumeI\Relations\Order\OrderStructures\PartialOrder.lean
F:\repos\lra-lean\LRA\VolumeI\Relations\Order\OrderStructures\Poset.lean
F:\repos\lra-lean\LRA\VolumeI\Relations\Order\OrderStructures\LinearOrder.lean
F:\repos\lra-lean\LRA\VolumeI\Relations\Order\Bounds.lean
F:\repos\lra-lean\LRA\VolumeI\Relations\Order\Completeness.lean
F:\repos\lra-lean\LRA\VolumeI\Relations\Order\Lattices.lean
F:\repos\lra-lean\LRA\VolumeI\Relations\Order\Examples.lean
F:\repos\lra-lean\LRA\VolumeI\Relations\Order.lean
```

Important verified shapes at handoff:

```lean
def LRASet (Alpha : Type u) := Alpha -> Prop

structure Poset where
  Carrier : Type u
  Relation : Endorelation Carrier
  RelationIsPartialOrder : PartialOrder Relation
```

Volume I already defines relation- and membership-backend-parametric versions
of:

```text
UpperBound
LowerBound
LeastElement
GreatestElement
MinimalElement
MaximalElement
Supremum
Infimum
LeastUpperBoundProperty
GreatestLowerBoundProperty
Join
Meet
Lattice
CompleteLattice
```

This is a strong foundation. The dependent public reading is conceptually:

```text
P : Poset
A : Set(P.Carrier)
u : P.Carrier

UpperBound(P.Relation, A, u)
```

which maps to the predicate presentation:

```text
UpperBound(u,A,P)
```

The low-level relation-parametric definitions may remain more general. If a
Poset-shaped public declaration is useful for harvesting, it should be a thin
definitional projection, not a second independently maintained meaning.

## Live Volume III Lean Surface

Inspect:

```text
F:\repos\lra-lean\LRA\VolumeIII\Analysis\Bounding.lean
F:\repos\lra-lean\LRA\VolumeIII\Analysis\Bounding\Bounds.lean
F:\repos\lra-lean\LRA\VolumeIII\Analysis\Bounding\ExtremalBounds.lean
F:\repos\lra-lean\LRA\VolumeIII\Analysis\Bounding\ExtremalBounds\UpperLowerBounds.lean
F:\repos\lra-lean\LRA\VolumeIII\Analysis\Bounding\ExtremalBounds\SupremaInfima.lean
F:\repos\lra-lean\LRA\VolumeIII\Analysis\Bounding\ExtremalBounds\MaximaMinima.lean
F:\repos\lra-lean\LRA\VolumeIII\Analysis\Bounding\ExtremalBounds\EpsilonCharacterization.lean
F:\repos\lra-lean\LRA\VolumeIII\Analysis\Bounding\RelativeBounds.lean
F:\repos\lra-lean\LRA\VolumeIII\Analysis\Bounding\Examples.lean
```

At handoff, the aggregate imports both `Bounding.Bounds` and
`Bounding.ExtremalBounds`. They contain parallel definitions such as
`IsUpperBound`, `IsLowerBound`, `IsBoundedAbove`, `IsBoundedBelow`,
`IsBounded`, `IsSupremum`, and `IsInfimum` in different namespaces. Select a
canonical family before harvesting or migrating callers.

Many Volume III theorem bodies still contain `sorry`. A declaration with
`sorry` verifies only that the statement elaborates; it does not verify the
proof or justify a `checked` TeX link.

## Live TeX Surface

Volume I set and order foundations:

```text
F:\repos\lra-volume-i\volume-i\book-sets\set-theory\notes\sets\notes-foundations.tex
F:\repos\lra-volume-i\volume-i\book-sets\set-theory\notes\sets\notes-set-operations.tex
F:\repos\lra-volume-i\volume-i\book-sets\orderings\notes\order\notes-order.tex
F:\repos\lra-volume-i\volume-i\book-sets\orderings\notes\order\notes-order-sup-inf.tex
F:\repos\lra-volume-i\volume-i\book-sets\orderings\notes\order\notes-order-hasse-sup-duality.tex
F:\repos\lra-volume-i\volume-i\book-sets\orderings\notes\order\notes-order-extensions.tex
F:\repos\lra-volume-i\volume-i\book-sets\orderings\notes\order\notes-order-induced.tex
F:\repos\lra-volume-i\volume-i\book-sets\orderings\proofs\order
```

Volume III Bounds:

```text
F:\repos\lra-volume-iii\volume-iii\book-analysis-i\bounding\notes\bounds-extremals\notes-upper-lower-bounds.tex
F:\repos\lra-volume-iii\volume-iii\book-analysis-i\bounding\notes\bounds-extremals\notes-suprema-infima.tex
F:\repos\lra-volume-iii\volume-iii\book-analysis-i\bounding\notes\bounds-extremals\notes-maxima-minima.tex
F:\repos\lra-volume-iii\volume-iii\book-analysis-i\bounding\notes\bounds-extremals\notes-relative-bounds-suprema.tex
F:\repos\lra-volume-iii\volume-iii\book-analysis-i\bounding\notes\bounds-extremals\notes-epsilon-characterization-supremum.tex
F:\repos\lra-volume-iii\volume-iii\book-analysis-i\bounding\proofs\bounds-extremals
```

Volume I already introduces ordered sets, partial orders, posets,
comparability, total orders, upper/lower bounds, minimal/maximal and
least/greatest elements, suprema/infima, uniqueness, duality, and examples.
Volume III specializes and extends this material for real analysis. The pilot
must decide which concepts are foundational Volume I authorities and which
Volume III declarations are specializations or analysis theorems.

## Known Audit Findings and Proof Obligations

Verify each finding before changing anything.

1. **Stale Lean namespaces in Volume I TeX.** Some tags refer to names such as
   `LRA.VolumeI.Order.Bounds`, while the live namespace is
   `LRA.VolumeI.Relations.Order`. Audit every touched `\LeanFormalizes` target;
   do not repair them by name guessing.

2. **Parallel Volume III APIs.** `Bounding.Bounds` and
   `Bounding.ExtremalBounds` both define a Bounds vocabulary and are both
   imported. A one-to-one harvested mapping is impossible until a canonical
   family is selected.

3. **Explicit ambient versus dependent Lean context.** TeX/predicates often
   write `UpperBound(u,S,P)`. Lean may represent `P` by its carrier, relation,
   or typeclass arguments. Record the projection explicitly; do not claim that
   the ambient disappeared.

4. **Partial order is not total order.** In a poset, `Not (a <= b)` does not
   imply `b < a`; the elements may be incomparable. Therefore the raw failure
   of upper bound is:

   ```text
   exists a in A, Not (a <= u)
   ```

   A strict witness `u < a` requires stronger order assumptions.

5. **Volume I supremum characterization needs scrutiny.** The current
   `prop:sup-char` and nearby exposition use the claim that every element
   strictly below a candidate supremum fails to be an upper bound, while the
   stated ambient is an arbitrary poset. This local strict test may not rule
   out incomparable upper bounds. Ask Lean to prove the equivalence or produce
   a countermodel; do not assume the published statement is correct.

6. **Volume III generic failure readings have the same risk.** Strict
   rewrites are valid over the real/linear-order specialization but not
   automatically over a generic partial order.

7. **Maximal is not greatest.** A maximal element has no strictly larger
   competitor; a greatest element is above every member. An equality/discrete
   finite poset supplies simple counterexamples and should be formalized.

8. **Supremum need not be a maximum.** Keep membership in the set distinct
   from being an ambient least upper bound.

9. **Boundedness and completeness are distinct.** A bounded nonempty subset
   need not possess a supremum without an ambient completeness property.

10. **Examples must be named when they are published artifacts.** Anonymous
    Lean `example` commands are useful smoke tests but cannot be stable
    `\LeanFormalizes` or explorer targets.

11. **Current extraction is not yet elaborated-expression harvesting.** The
    existing inventories largely discover declarations from source text. The
    compiled-environment exporter requested by governance issue #17 remains
    future work. Do not represent regex discovery as semantic verification.

12. **The registry is vocabulary, not a definition store.** The canonical
    Bounds entries include `UpperBound`, `LowerBound`, `BoundedAbove`,
    `BoundedBelow`, `Bounded`, `LeastElement`, `GreatestElement`,
    `LeastUpperBound`, and `GreatestLowerBound`. Query the live registry before
    using them and do not copy Lean bodies into it.

## Formalization-First Study Protocol

For every selected definition, explicitly investigate:

- Why does each condition exist?
- Which pathology does it prevent?
- Is the condition needed to state the concept, to prove uniqueness, or only
  for a later theorem?
- What happens if it is removed?
- What happens if it is weakened?
- What becomes easier or equivalent if it is strengthened?
- What is the exact raw negation?
- Which readable failure forms are actually equivalent, and under which order
  assumptions?
- What positive, boundary, vacuous, and negative examples isolate the role of
  each condition?

For every selected theorem:

- complete the proof without local `sorry`;
- locate the use of each hypothesis;
- remove or weaken hypotheses individually;
- test the converse and common near-converses;
- weaken and strengthen the conclusion;
- formalize explicit counterexamples to false variants;
- identify the dual theorem and any specialization/generalization;
- distinguish symbols in the statement from lemmas used only in the proof;
- write the pedagogical proof idea after the boundary of the theorem is known.

Not every exploratory theorem or counterexample must enter the published
notes. Valuable investigations may remain named Lean declarations and later
appear in the explorer. Promote only material that improves the learning
narrative.

## Recommended First Pilot Slice

Keep the first implementation deliberately small:

1. `Poset` and the selected set/membership backend;
2. `UpperBound` and `LowerBound`;
3. `LeastElement`/`GreatestElement` and
   `MinimalElement`/`MaximalElement`;
4. `Supremum` and `Infimum`;
5. uniqueness under antisymmetry;
6. greatest element implies supremum and the dual theorem;
7. supremum plus membership gives greatest element and the dual theorem;
8. general raw failure of `UpperBound`;
9. counterexample to the strict failure form in a non-total poset;
10. repaired strict failure theorem under the correct linear-order
    assumptions.

Named examples should include a reviewed subset of:

- a finite chain with an upper bound, greatest element, and supremum;
- an upper bound that is not least;
- a supremum outside the subset;
- empty-set/vacuous-bound behavior;
- a set bounded above but not below;
- two incomparable elements in a finite poset;
- a maximal element that is not greatest;
- failure of uniqueness when antisymmetry is removed, if the preorder layer is
  included.

For a particularly small incomparability countermodel, consider an equality
order on a two-element carrier and a singleton predicate set. Verify the
construction in Lean rather than relying on this suggestion.

## Concept-Centered Lean Organization

The desired long-term unit is a concept package, not a monolithic chapter
file. A possible shape is:

```text
Relations/Order/Bounds/
  Core.lean
  Characterizations.lean
  FailureModes.lean
  Examples.lean
  Counterexamples.lean
  Theorems.lean
  Bounds.lean
```

or finer directories per concept if necessary.

This is a design target, not permission to move everything immediately.
Confirm the canonical declarations, callers, aggregate imports, namespace
strategy, and migration plan first. Definitions must not import examples or
counterexamples.

## Lean-to-TeX Workflow

For each completed concept:

1. Record the exact fully qualified Lean declaration.
2. Record explicit, implicit, dependent, and instance argument projections.
3. Classify its relation to the TeX artifact as exact, specialization,
   generalization, or proved equivalence.
4. Prove any expanded reading or failure reading that will be published.
5. Add or repair `\LeanFormalizes` only after the target exists and is
   reviewed.
6. Use `checked` only when the active build checks the declaration and the
   selected proof has no local `sorry`.
7. Make targeted TeX corrections from proved Lean findings; do not rewrite all
   exposition mechanically.
8. Preserve authored pedagogical dependencies separately from harvested Lean
   occurrence and proof dependencies.

Each exposition packet should contain:

```text
exact declaration
canonical predicate reading
verified expanded definition
verified failure characterization
minimal structure assumptions
why each condition is present
weakened/strengthened variants
positive examples
counterexamples and repaired claims
statement dependencies
proof-only dependencies
formalization status
```

Use that packet to write about why bounds arise from an order relation, how
ambient structure matters, how incomparability changes reasoning, and why
least/greatest, minimal/maximal, and supremum/maximum are distinct.

## Dependency Harvesting and Diagrams

After the first Lean slice is stable, governance issue #17 should provide an
extractor over Lean's compiled environment. It must keep these relationships
distinct:

```text
uses_symbol       occurrence in a statement
defined_using     occurrence in a selected definition body
proved_using      proof-term dependency
satisfies         verified positive example fact
fails             verified negative example fact
counterexample_to reviewed refutation link
formalized_by     TeX/artifact to Lean declaration
depends_on        authored learner prerequisite
crosswalks_to     proved equivalent/specialized declaration
```

The knowledge explorer and deterministic TikZ renderer should consume the
same graph projection. Proof-term edges must not automatically become learner
dependencies, and formula-symbol occurrence must not replace mathematical
dependency.

A first diagram should be a small concept slice, not a rendering of the whole
graph:

```text
order relation
  -> upper/lower bound
  -> boundedness
  -> least/greatest and minimal/maximal
  -> supremum/infimum
  -> existence and uniqueness
  -> partial-order counterexamples
  -> linear-order specializations
```

## Non-Goals and Guardrails

- Do not formalize all predicate entries before delivering value.
- Do not create a second AST, registry, or authored Lean/YAML formula mirror.
- Do not make governance import a volume repository.
- Do not use Mathlib as the semantic authority for the Volume I core.
- Do not treat a compiling declaration with `sorry` as a completed proof.
- Do not treat an unsuccessful tactic as a counterexample; prove a witness or
  a negation theorem.
- Do not infer pedagogical intent solely from Lean dependencies.
- Do not force every useful experiment into the notes.
- Do not broadly reorganize Lean until canonical declarations and caller
  migration are understood.
- Do not commit, push, reset, clean, or discard work unless explicitly asked.

## Validation Expectations

Follow every validation command returned by the resolver. At minimum, after
relevant implementation changes:

1. Build the affected Lean libraries, including `LRAVolumeI` and the selected
   Volume III target when touched.
2. Confirm the selected pilot declarations and proofs contain no local
   `sorry`.
3. Run the LRA Mathlib import-policy check for Volume I.
4. Run focused tests for named examples, counterexamples, and generated
   witnesses.
5. Validate touched Volume I and Volume III TeX through their resolved
   governance routes.
6. Audit every touched `\LeanFormalizes` target against the live compiled
   declaration.
7. Rebuild affected book/volume PDFs if the resolved workflow requires it.
8. Re-export and inspect the relevant explorer slice only after the semantic
   records are stable.
9. Report exact commands and distinguish passing, failing, and skipped gates.

## Requested First-Turn Output

Begin with a live audit and a narrowly scoped implementation proposal. Report:

- the current worktree states;
- the exact canonical declaration candidates;
- duplicate or stale declarations and tags;
- the first caller migration boundary;
- the first definitions, proofs, examples, and counterexamples to complete;
- the proposed file/namespace shape for only that slice;
- the Lean and TeX validation plan;
- any mathematical statement that must be corrected before implementation.

If the canonical ownership decision remains genuinely ambiguous, stop before
moving declarations and present the alternatives. Otherwise implement only
the smallest approved slice and verify it before expanding.
