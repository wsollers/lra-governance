# Order Inventory and Placement Plan

This document is a working map of order-related material across the first five
LRA volumes. Its purpose is to make the scattered order layer visible before
we decide what to consolidate, duplicate deliberately, move, or cite.

The first pass searched Volumes I through V for order-related definitions,
theorems, lemmas, propositions, corollaries, and axioms. The inventory below is
curated: it records the main order-bearing artifacts and their homes, not every
downstream theorem whose statement happens to use a bound, positive number, or
monotone argument.

## Placement Principle

Use the earliest volume where the structure naturally belongs, and cite forward
instead of re-proving unless the later context needs a specialized version.

| Layer | Proper home | Role |
| --- | --- | --- |
| Relation properties | Volume I | Pure set-theoretic predicates on binary relations. |
| Abstract ordered sets | Volume I | Posets, total orders, well-orders, chains, bounds, sup/inf, lattices. |
| Ordered maps | Volume I | Order-preserving, order-reversing, order embeddings, monotone maps between ordered sets. |
| Arithmetic order compatibility | Volume II | How algebraic operations interact with order in constructed number systems. |
| Positive cones | Volume II | Algebraic mechanism that generates strict order from positivity. |
| Constructed number orders | Volume II | Specific order on Q and R, including trichotomy and ordered-field structure. |
| Real inequality calculus | Volume III | User-facing rules for manipulating inequalities in real analysis. |
| Absolute value and triangle inequalities | Volume III | Analysis toolkit built from ordered-field/order-calculus facts. |
| Generic ordered-field laws | Volume IV | Abstract spaces/structures viewpoint; reusable ordered-field theorem package. |
| Norm/metric inequalities | Volume IV | Cauchy-Schwarz, Minkowski, metric consequences, norm-induced metrics. |
| Advanced ordered algebra/analysis structures | Volume V and later | Add only when a later structure needs its own order theory. |

## Volume I: Sets, Relations, and Abstract Order

Volume I should own the pure language of order before numbers enter.

### Relation Properties

Source: `lra-volume-i/volume-i/book-sets/relations/notes/relations/notes-relation-properties.tex`

| Label | Kind | Title | Line |
| --- | --- | --- | --- |
| `def:reflexive` | definition | Reflexive Relation | 15 |
| `def:irreflexive` | definition | Irreflexive Relation | 63 |
| `def:symmetric` | definition | Symmetric Relation | 123 |
| `def:antisymmetric` | definition | Antisymmetric Relation | 170 |
| `def:asymmetric` | definition | Asymmetric Relation | 219 |
| `def:transitive` | definition | Transitive Relation | 275 |
| `def:total-rel` | definition | Total (Connex) Relation | 325 |
| `def:preorder` | definition | Preorder | 412 |
| `def:partial-order` | definition | Partial Order | 448 |
| `def:strict-partial-order-relations` | definition | Strict Partial Order | 488 |
| `def:total-order` | definition | Total Order | 542 |

Decision note: these are the primitive relation predicates. Later chapters
should cite these labels when proving that a concrete order is reflexive,
antisymmetric, transitive, total, strict, etc.

### Ordered Sets

Source: `lra-volume-i/volume-i/book-sets/orderings/notes/order/notes-order.tex`

| Label | Kind | Title | Line |
| --- | --- | --- | --- |
| `def:ordered-set` | definition | Ordered Set | 12 |
| `def:partially-ordered-set` | definition | Partially Ordered Set | 50 |
| `def:poset` | definition | Poset | 84 |
| `def:toset` | definition | Toset | 109 |
| `def:loset` | definition | Loset | 134 |
| `def:woset` | definition | Woset | 161 |
| `def:strict-order` | definition | Strict Order | 186 |
| `def:non-strict-order-induced-by-strict-order` | definition | Non-Strict Order Induced by a Strict Order | 223 |
| `thm:strict-order-induced-by-linear-order` | theorem | Strict Order Induced by a Linear Order | 252 |
| `thm:linear-order-induced-by-strict-linear-order` | theorem | Linear Order Induced by a Strict Linear Order | 287 |
| `thm:trichotomy-for-linear-orders` | theorem | Trichotomy for Linear Orders | 322 |
| `def:comparable` | definition | Comparable Elements | 362 |
| `def:incomparable` | definition | Incomparable Elements | 389 |
| `def:totally-ordered-set` | definition | Totally Ordered Set | 422 |
| `def:upper-bound` | definition | Upper Bound | 462 |
| `def:lower-bound` | definition | Lower Bound | 492 |
| `def:order-minimal-element` | definition | Minimal Element | 527 |
| `def:order-maximal-element` | definition | Maximal Element | 557 |
| `def:order-least-element` | definition | Least Element | 587 |
| `def:order-greatest-element` | definition | Greatest Element | 618 |
| `def:order-preserving-map-ordered-sets` | definition | Order-Preserving Map | 658 |
| `def:order-reversing-map` | definition | Order-Reversing Map | 698 |
| `def:order-isomorphism-ordered-sets` | definition | Order Isomorphism | 732 |
| `thm:order-isomorphisms-preserve-and-reflect-order` | theorem | Order Isomorphisms Preserve and Reflect Order | 775 |
| `def:well-ordered-set` | definition | Well-Ordered Set | 814 |
| `def:order-chain` | definition | Chain | 870 |
| `def:order-antichain` | definition | Antichain | 900 |
| `def:initial-segment` | definition | Initial Segment | 930 |
| `def:directed-set` | definition | Directed Set | 970 |
| `def:net` | definition | Net | 1025 |

Decision note: Volume I already has enough abstract order vocabulary to support
later ordered sets, directed sets, nets, and order isomorphism language. Later
volumes should not redefine these in a new vocabulary unless specializing to a
concrete structure.

### Suprema, Infima, and Lattices

Sources:

- `lra-volume-i/volume-i/book-sets/orderings/notes/order/notes-order-sup-inf.tex`
- `lra-volume-i/volume-i/book-sets/orderings/notes/order/notes-order-lattices.tex`

| Label | Kind | Title | Line |
| --- | --- | --- | --- |
| `def:sup-inf` | definition | Supremum and Infimum | 64 |
| `prop:sup-unique` | proposition | Uniqueness of Supremum and Infimum | 132 |
| `prop:sup-char` | proposition | Characterisation of Supremum | 253 |
| `prop:sup-inf-duality` | proposition | Duality of Supremum and Infimum | 307 |
| `def:lattice` | definition | Lattice | 48 |
| `def:complete-lattice` | definition | Complete Lattice | 130 |
| `def:distributive-lattice` | definition | Distributive Lattice | 205 |
| `def:boolean-lattice` | definition | Complement and Boolean Lattice | 254 |
| `thm:knaster-tarski` | theorem | Knaster-Tarski Fixed-Point Theorem | 338 |

Decision note: abstract sup/inf belongs here. Real suprema and completeness
belong later because they use the real line and least-upper-bound property.

### Extensions and Choice Principles

Sources:

- `lra-volume-i/volume-i/book-sets/orderings/notes/order/notes-order-extensions.tex`
- `lra-volume-i/volume-i/book-sets/orderings/notes/zorn/notes-zorn.tex`

Key labels include `def:preorder-extension`, `thm:szpilrajn`,
`cor:complete-preorder-extension`, `def:owc`, `prop:owc-characterization`,
`thm:zorn`, and `thm:hausdorff`.

Decision note: these are high-level abstract order/choice results. They should
stay in Volume I unless a later volume needs a short contextual reminder.

### Order and Functions

Source cluster:
`lra-volume-i/volume-i/book-sets/functions-and-order/notes/`

Important labels include:

- `def:strictly-monotone-map-functions-order`
- `prop:constant-maps-monotone`
- `thm:strict-monotone-injective-linear`
- `thm:monotone-composition-rules`
- `def:order-reflecting-map`
- `def:order-embedding-function-form`
- `prop:order-embedding-injective-revisited`
- `thm:order-embedding-isomorphism-onto-image`
- `thm:inverse-order-isomorphism`
- `def:upper-lower-set`
- `prop:boundedness-image-boundedness`
- `thm:preimage-upper-lower-sets`
- `prop:images-chains-monotone`

Decision note: these are structural facts about functions between ordered
sets. Analysis-specific monotone functions should cite this layer but may have
their own real-function theorem statements.

### Set Inclusion and Cardinality Order

Source cluster:

- `lra-volume-i/volume-i/book-sets/set-theory/notes/sets/notes-set-operations.tex`
- `lra-volume-i/volume-i/book-sets/cardinality/notes/cardinality/notes-cardinality.tex`

Important labels include `def:inclusion-monotone-set-operation`,
`def:inclusion-antitone-set-operation`, `thm:union-monotone-inclusion`,
`thm:intersection-monotone-inclusion`, `thm:power-set-monotone-inclusion`,
`thm:complement-antitone-inclusion`, `thm:set-difference-monotone-left`,
`thm:set-difference-antitone-right`, and `def:cardinality-order`.

Decision note: inclusion order and cardinality comparison are set-theoretic
orders/comparisons. They should remain separate from numeric inequality.

## Volume II: Number Construction and Arithmetic Order

Volume II should own concrete order on the constructed number systems and the
algebraic compatibility needed to prove they are ordered fields.

### Generic Arithmetic Order Compatibility

Source: `lra-volume-ii/volume-ii/book-discrete-algebraic/arithmetic-operations-relations/notes/order-compatibility/notes-order-compatibility.tex`

| Label | Kind | Title | Line |
| --- | --- | --- | --- |
| `def:right-monotony` | definition | Right Monotony | 2 |
| `def:left-monotony` | definition | Left Monotony | 35 |
| `def:two-sided-monotony` | definition | Two-Sided Monotony | 68 |
| `def:right-order-reflection` | definition | Right Order Reflection | 100 |
| `def:left-order-reflection` | definition | Left Order Reflection | 134 |
| `def:two-sided-order-reflection` | definition | Two-Sided Order Reflection | 168 |
| `def:positive-cone` | definition | Positive Cone | 201 |
| `def:monotone-map` | definition | Monotone Map | 255 |
| `def:strictly-monotone-map` | definition | Strictly Monotone Map | 287 |
| `prop:addition-order-compatibility-left` | proposition | Addition Preserves Order on the Left | 319 |
| `prop:addition-order-compatibility-right` | proposition | Addition Preserves Order on the Right | 352 |
| `prop:addition-order-compatibility` | proposition | Addition Preserves Order | 385 |
| `prop:multiplication-order-compatibility-left` | proposition | Multiplication Preserves Order on the Left | 419 |
| `prop:multiplication-order-compatibility-right` | proposition | Multiplication Preserves Order on the Right | 454 |
| `prop:multiplication-order-compatibility` | proposition | Multiplication Preserves Order | 489 |

Decision note: `def:positive-cone` is the natural abstract bridge for proving
sign and inequality facts. If real order calculus is rebuilt, cite or specialize
this definition instead of inventing another notion of positivity.

### Order on Q

Source: `lra-volume-ii/volume-ii/book-continuum/rationals/notes/order-on-q/notes-order-on-q.tex`

Key order definitions and structure:

- `def:positive-rational`
- `thm:positivity-on-q-well-defined`
- `def:strict-order-on-q`
- `def:order-on-q`
- `prop:product-of-positives-is-positive-q`
- `thm:sign-trichotomy-on-q`
- `thm:trichotomy-on-q`
- `thm:strict-order-on-q-irreflexive`
- `thm:strict-order-on-q-asymmetric`
- `thm:strict-order-on-q-transitive`
- `thm:order-on-q-reflexive`
- `thm:order-on-q-antisymmetric`
- `thm:order-on-q-transitive`
- `thm:order-on-q-total`
- `thm:q-totally-ordered-set`

Key arithmetic order laws:

- `thm:addition-preserves-strict-order-on-q`
- `thm:addition-preserves-order-on-q`
- `cor:addition-reflects-order-on-q`
- `thm:positive-multiplication-preserves-strict-order-on-q`
- `thm:positive-multiplication-preserves-order-on-q`
- `thm:negative-multiplication-reverses-strict-order-on-q`
- `cor:negative-multiplication-reverses-order-on-q`
- `thm:sign-of-reciprocal-q`
- `thm:reciprocal-reverses-order-on-positives-q`
- `thm:reciprocal-reverses-order-on-same-sign-q`
- `thm:reciprocal-reverses-nonstrict-order-on-positives-q`
- `thm:reciprocal-reverses-nonstrict-order-on-same-sign-q`

Absolute-value related:

- `def:absolute-value-on-q`
- `thm:absolute-value-nonnegative-on-q`
- `thm:absolute-value-zero-iff-on-q`
- `thm:absolute-value-multiplicative-on-q`
- `thm:triangle-inequality-on-q`
- `thm:absolute-value-of-reciprocal-q`

Decision note: these belong in construction because they prove the rational
system has the expected order. Later inequality sections should avoid proving
the rational analogues again unless they need comparison examples.

### Order on R

Source: `lra-volume-ii/volume-ii/book-continuum/reals/notes/order-on-r/notes-order-on-r.tex`

| Label | Kind | Title | Line |
| --- | --- | --- | --- |
| `def:order-on-r` | definition | Order on R | 4 |
| `def:strict-order-on-r` | definition | Strict Order on R | 32 |
| `thm:order-on-r-reflexive` | theorem | Order on R Is Reflexive | 61 |
| `thm:order-on-r-antisymmetric` | theorem | Order on R Is Antisymmetric | 86 |
| `thm:order-on-r-transitive` | theorem | Order on R Is Transitive | 116 |
| `thm:comparability-of-cuts` | theorem | Comparability of Cuts | 145 |
| `thm:order-on-r-total` | theorem | Order on R Is Total | 174 |
| `thm:trichotomy-on-r` | theorem | Trichotomy on R | 203 |
| `thm:r-totally-ordered-set` | theorem | R Is a Totally Ordered Set | 234 |

Decision note: this is the concrete real-order construction layer. It should
not become a general inequality chapter, but it should include enough order
facts to prove the real ordered-field theorem.

### Ordered Field Structure of R

Source: `lra-volume-ii/volume-ii/book-continuum/reals/notes/field-and-ordered-field-structure-of-r/notes-field-and-ordered-field-structure-of-r.tex`

Key labels:

- `thm:r-is-a-field`
- `cor:field-laws-on-r`
- `thm:addition-preserves-order-on-r`
- `thm:positive-multiplication-preserves-order-on-r`
- `thm:r-is-an-ordered-field`
- `cor:ordered-field-laws-on-r`
- `thm:r-is-complete-ordered-field`

Decision note: this is the canonical place to say that R is an ordered field.
It can cite Volume IV's abstract ordered-field package only if cross-volume
dependencies are intended in that direction; otherwise Volume IV should present
the abstract package and refer backward to this concrete instance.

### Multiplication, Reciprocal, and Absolute Value on R

Source: `lra-volume-ii/volume-ii/book-continuum/reals/notes/multiplication-on-r/notes-multiplication-on-r.tex`

Key order-relevant labels:

- `def:nonnegative-cut`
- `def:product-nonnegative-on-r`
- `lem:product-nonnegative-is-a-cut`
- `def:real-chapter-absolute-value-on-r`
- `thm:triangle-inequality`
- `def:reciprocal-positive-on-r`
- `thm:sign-of-reciprocal-r`
- `thm:reciprocal-reverses-order-on-positives-r`
- `thm:reciprocal-reverses-nonstrict-order-on-positives-r`
- `thm:reciprocal-reverses-order-on-same-sign-r`
- `thm:reciprocal-reverses-nonstrict-order-on-same-sign-r`
- `thm:absolute-value-of-reciprocal-r`

Decision note: this material straddles construction and toolkit. The
construction-specific definitions of cut multiplication and reciprocal belong
in Volume II. The user-facing inequality forms probably belong in Volume III,
with citations back to these labels.

## Volume III: Real Analysis Inequality Toolkit

Volume III already contains substantial real inequality and modulus material.
This should probably become the main "how to manipulate real inequalities"
section for analysis readers.

### Real Inequality Calculus

Source: `lra-volume-iii/volume-iii/book-analysis-i/real-analysis/notes/inequality/notes-inequality.tex`

Key labels:

- `thm:ineq-add-both-sides`
- `thm:ineq-nonstrict-add-both-sides`
- `thm:ineq-add-inequalities`
- `thm:ineq-nonstrict-add-inequalities`
- `thm:ineq-mixed-add`
- `thm:ineq-multiply-positive`
- `thm:ineq-multiply-negative`
- `thm:ineq-nonstrict-multiply-positive`
- `thm:ineq-nonstrict-multiply-nonneg`
- `lem:positive-product`
- `lem:negative-times-negative-is-positive`
- `lem:positive-times-negative-is-negative`
- `lem:negative-times-positive-is-negative`
- `lem:order-and-subtraction`
- `lem:non-strict-order-and-subtraction`
- `lem:division-by-positive-preserves-order`
- `lem:division-by-negative-reverses-order`
- `thm:ineq-squeeze`
- `thm:ineq-transitivity-strict`
- `thm:ineq-transitivity-mixed`
- `thm:ineq-reciprocal-positive`
- `thm:ineq-reciprocal-flip`
- `lem:positive-powers-are-positive`
- `lem:powers-preserve-order-for-positive-numbers`
- `thm:ineq-square-monotone`
- `thm:ineq-square-root-monotone`
- `thm:ineq-am-gm-two`
- `thm:ineq-bernoulli`

Decision note: this file is already close to the "order calculus" the reader
needs before deeper analysis. It should be audited against Volume II and Volume
IV so that dependencies are explicit and duplicate statements are deliberate.

### Modulus / Absolute Value

Source: `lra-volume-iii/volume-iii/book-analysis-i/real-analysis/notes/modulus/notes-modulus.tex`

Key labels:

- `def:absolute-value`
- `thm:absolute-value-nonneg`
- `thm:absolute-value-zero-iff-zero`
- `thm:absolute-value-self-or-neg`
- `thm:absolute-value-symmetric`
- `thm:absolute-value-product`
- `thm:absolute-value-quotient`
- `thm:absolute-value-bounds`
- `thm:absolute-value-le-iff`
- `thm:absolute-value-lt-iff`
- `thm:reverse-triangle-inequality`
- `thm:absolute-value-sum-bound`

Decision note: Volume II has construction-era absolute value on Q and R.
Volume III should own the analysis-facing absolute value toolkit.

### Bounds, Suprema, Infima, and Completeness

Source cluster:
`lra-volume-iii/volume-iii/book-analysis-i/bounding/notes/`

Important files and labels:

- `bounds-extremals/notes-upper-lower-bounds.tex`
  - `def:bound`
  - `def:real-upper-bound`
  - `def:real-lower-bound`
  - `def:bounded-above`
  - `def:bounded-below`
  - `def:bounded`
- `bounds-extremals/notes-maxima-minima.tex`
  - maxima/minima definitions and uniqueness/comparison facts.
- `bounds-extremals/notes-suprema-infima.tex`
  - supremum/infimum definitions specialized to real sets.
  - uniqueness, membership, comparison, and existence consequences.
- `completeness/notes-axiom-of-completess.tex`
  - `def:least-upper-bound-property`
  - `ax:completeness-of-reals`
- `completeness/notes-order-separation.tex`
  - `thm:order-separation-by-supremum`
  - `thm:dedekind-cut-property`
  - `cor:no-gaps-in-r`

Decision note: abstract sup/inf belongs in Volume I; real sup/inf and real
completeness belong here, where they support sequences and limits.

### Density and No-Adjacent-Point Results

Source: `lra-volume-iii/volume-iii/book-analysis-i/bounding/notes/completeness/notes-density.tex`

Important labels include `def:dense-subset`, `def:order-dense-subset`,
`thm:density-of-rationals-in-reals`, `thm:density-of-irrationals`,
`cor:no-adjacent-real-numbers`, `thm:no-immediate-successors-in-r`,
`thm:no-immediate-predecessors-in-r`, and
`cor:every-open-interval-contains-rational-and-irrational`.

Decision note: density is order-theoretic, but its natural home is real
analysis because it is about the real line and its important subsets.

## Volume IV: Spaces and Abstract Structures

Volume IV has two relevant kinds of order material: abstract ordered-field
facts and metric/norm inequality facts.

### Ordered Fields

Source: `lra-volume-iv/volume-iv/book-spaces/mathematical-spaces/notes/ordered-fields/notes-ordered-fields.tex`

| Label | Kind | Title | Line |
| --- | --- | --- | --- |
| `def:ordered-field` | definition | Ordered Field | 2 |
| `thm:ordered-field-translation-invariant` | theorem | Order Is Translation Invariant | 61 |
| `thm:ordered-field-positive-multiplication-preserves-order` | theorem | Order Is Preserved by Positive Multiplication | 104 |
| `thm:ordered-field-negative-multiplication-reverses-order` | theorem | Order Is Reversed by Negative Multiplication | 149 |
| `thm:ordered-field-positive-reciprocals` | theorem | Positive Elements Have Positive Reciprocals | 194 |
| `thm:ordered-field-negative-reciprocals` | theorem | Negative Elements Have Negative Reciprocals | 235 |
| `thm:ordered-field-squares-nonnegative` | theorem | Squares Are Nonnegative | 277 |
| `thm:ordered-field-one-positive` | theorem | One Is Positive | 315 |
| `thm:ordered-field-no-square-root-negative-one` | theorem | No Ordered Field Has Square Root of Negative One | 351 |
| `lem:ordered-field-product-sign-laws` | lemma | Product Sign Laws in an Ordered Field | 388 |
| `lem:ordered-field-division-order-laws` | lemma | Division Order Laws in an Ordered Field | 438 |

Decision note: this is the most reusable abstract ordered-field package found
so far. Decide whether Volume III should cite this abstract package, or whether
Volume III should be self-contained and Volume IV should cite Volume III/II as
motivating examples.

### Metric and Norm Inequalities

Source: `lra-volume-iv/volume-iv/book-spaces/metric-spaces/notes/metrics/notes-metrics.tex`

Key labels:

- `def:norm-on-real-vector-space`
- `thm:norm-induces-metric`
- `def:real-line-euclidean-distance`
- `def:euclidean-space`
- `def:euclidean-distance-rn`
- `thm:cauchy-schwarz-inequality`
- `cor:minkowski-inequality-rn`
- `def:lp-metric-rn`
- `thm:lp-metric-rn`
- `def:bounded-real-sequence-space`
- `prop:bounded-real-sequence-space-sup-metric`

Decision note: Cauchy-Schwarz and Minkowski currently live in metric spaces.
If Volume III grows a "Basic Inequalities" chapter, decide whether these
statements move earlier, remain here with forward citations, or are duplicated
as a finite-dimensional analysis toolkit with later metric-space reuse.

## Volume V: Modern Analysis

Initial search found no substantive order-specific theorem/definition layer in
the current Volume V source. Volume V currently has book/chapter stubs for
complex analysis, functional analysis, measure theory, and probability.

Decision note: future Volume V order material may include ordered vector
spaces, Banach lattices, measure/lattice operations, almost-everywhere order,
and stochastic order. Those should not be added until the relevant chapters
exist and need them.

## Known Scattering and Duplication

The current order material is not random, but the reader-facing path is not yet
clear.

1. Abstract order is in Volume I.
2. Constructed number order is in Volume II.
3. Real inequality manipulation is in Volume III.
4. Abstract ordered-field laws are in Volume IV.
5. Cauchy-Schwarz and Minkowski are in Volume IV metric spaces, while AM-GM and
   Bernoulli are in Volume III inequality notes.

The main tension is between Volume III and Volume IV:

- Volume III has concrete real inequality statements useful before sequences,
  limits, and continuity.
- Volume IV has an abstract ordered-field package that proves several of the
  same ideas once and for all.

Possible resolution: keep Volume III as the analysis-facing calculus and make
its dependencies explicit. Keep Volume IV as the abstract structure chapter and
let it state generic versions, with a note that Volume III specialized these
rules to the real line for analysis.

## Proposed Consolidation Work

1. Add a short "Order Dependency Map" paragraph to the Volume III inequality
   section:
   - relation/order vocabulary from Volume I;
   - real ordered-field structure from Volume II;
   - optional abstract ordered-field package in Volume IV.

2. Decide whether `def:positive-cone` should be specialized to R explicitly:
   - possible new Volume II result: `P_R = {x in R : 0 < x}` is the positive
     cone of R;
   - then Volume III sign and inequality proofs can cite that bridge.

3. Audit Volume III inequality proofs:
   - each theorem should cite the earliest appropriate source;
   - avoid vague dependencies such as "multiply positive";
   - distinguish concrete real facts from generic ordered-field facts.

4. Decide where the "Basic Inequalities" chapter/section should live:
   - AM-GM and Bernoulli are already in Volume III;
   - Cauchy-Schwarz and Minkowski are in Volume IV;
   - Chebyshev, rearrangement, Holder, and general Minkowski may form a new
     Volume III or Volume IV section depending on whether the goal is
     pre-analysis technique or normed-space structure.

5. Add cross-volume references only where the build system and reading order
   support them. If cross-volume links are fragile, use text references and
   repeated labels in local dependency notes rather than hard `\hyperref`s.

## Search Notes

Search was performed across `lra-volume-i` through `lra-volume-v` using labels,
statement titles, and paths containing order-related terms such as `order`,
`ordered`, `strict`, `linear`, `partial`, `total`, `preorder`, `poset`, `chain`,
`upper`, `lower`, `bound`, `supremum`, `infimum`, `lattice`, `monotone`,
`positive`, `negative`, `inequality`, `trichotomy`, `cone`, `reflexive`,
`antisymmetric`, and `transitive`.

This document should be updated after each consolidation pass.
