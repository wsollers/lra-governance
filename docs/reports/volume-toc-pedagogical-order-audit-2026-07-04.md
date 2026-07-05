# Volume TOC Pedagogical Order Audit

Date: 2026-07-04

Scope: all active `lra-volume-*` repositories, Volumes I-VIII.

Inputs inspected:

- `docs/architecture/volume-architecture.md`
- `docs/architecture/book-registry.json`
- rendered route order reached from each `volume-{roman}.tex` and
  `volume-{roman}-{book}.tex` root by following `\input{...}` recursively

This audit is qualitative. The rendered chapter and section routes largely
match `book-registry.json`; the findings below identify places where the
registered order itself appears pedagogically weak or where routed subsections
appear before their prerequisites.

## Executive Summary

High-confidence order problems:

1. Volume II / Discrete Number Systems / Peano Systems routes
   `Presburger Arithmetic` before `Defining Peano Systems`.
2. Volume II / The Continuum places `Number Lines and Intervals` after
   rationals, reals, extended reals, and complex numbers.
3. Volume III / Functions, Continuity, and Differentiation starts
   `Elementary Functions` with `Hyperbolic Functions`.
4. Volume III / Integration routes `The Cauchy Integral` before the Riemann
   and Darboux developments, and places `Measure Zero and the Lebesgue
   Criterion` after generalized integration topics.
5. Volume VIII / Applied Methods places computational geometry and geometric
   modeling before computational linear algebra.

Medium-confidence order problems:

1. Volume III / Bounds, Sequences, and Series places a broad
   `Structure of the Real Line` chapter before the dedicated `Bounds` chapter.
2. Volume III / Sequences places `Examples and Counterexamples` before
   `Convergence`.
3. Volume III / Structure of the Real Line delays `Unions and Intersections`
   until after open/closed sets, limit points, and interior/boundary language.
4. Volume IV / Metric Spaces begins the chapter spine with both
   `Metric Spaces` and `Definitions`, creating an apparent duplicate/generic
   opener before the actual metric machinery.
5. Volume VIII routes `Applied Methods` before `Numerical Foundations`, even
   though the latter supplies floating-point and interval-arithmetic ground
   rules used by later computational material.

Advisory order questions:

1. Volume I / Mathematical Logic and Proof places `Proof Techniques` after
   propositional, predicate, many-sorted, second-order, and axiom-system
   chapters. This is defensible as a synthesis chapter, but weak if the goal is
   to teach proof-writing before logic.
2. Volume VII / Advanced Logic starts with `Category Theory` before model,
   proof, type theory, and lambda calculus. This is defensible for categorical
   foundations, but less natural for a logic-first path.
3. Volume VI / Algebra places the general algebra book before linear algebra.
   This is defensible for abstract structure, but a learner-oriented path often
   benefits from linear algebra earlier.

## Volume-Level Order

Current volume order is coherent as a broad curriculum:

1. Logic, Sets, and Proof
2. Origins of Numbers
3. Classical Analysis
4. Mathematical Spaces
5. Modern Analysis
6. Algebra
7. Advanced Logic
8. Applied and Computational Mathematics

No required volume renumbering is indicated by this audit. The only
volume-level concern is that Algebra appears after Modern Analysis, while parts
of functional analysis, complex analysis, numerical methods, and applied
mathematics naturally use linear algebra. That concern is better handled by
cross-volume prerequisite notes or by moving selected linear-algebra material
earlier, not by renumbering all volumes.

## Detailed Findings

### Volume I: Logic, Sets, and Proof

Books:

1. Mathematical Logic and Proof
2. Set Theory
3. Foundational Geometry

Assessment: coherent.

Finding V1-A, advisory: `Proof Techniques` is last in Mathematical Logic and
Proof.

Current chapter order:

1. Propositional Logic
2. Predicate Logic
3. Many-Sorted Logic
4. Standard Second-Order Logic
5. Languages, Axioms, and Models
6. Proof Techniques

Pedagogical concern: proof-writing mechanics may be needed before students
enter predicate logic and axiom systems. If this chapter is intended as a
general student toolkit, consider moving it before `Propositional Logic` or
between `Predicate Logic` and `Many-Sorted Logic`. If it is intended as a
synthesis chapter, the current order is acceptable.

No chapter-order issues were found in Set Theory. The sequence
`Set Theory -> Relations -> Functions -> Orderings -> Cardinality` is coherent.

No major issue was found in Foundational Geometry. `Euclidean Geometry ->
Trigonometry -> Analytical Geometry` is defensible, though analytic geometry
could also precede trigonometry in a coordinate-first treatment.

### Volume II: Origins of Numbers

Books:

1. Discrete Number Systems
2. The Continuum

Assessment: mostly coherent, with two high-confidence local order problems.

Finding V2-A, high: `Presburger Arithmetic` precedes `Defining Peano Systems`.

Current Peano Systems section order:

1. Presburger Arithmetic
2. Defining Peano Systems
3. Examples of Peano Systems
4. Recursion on Peano Systems

Recommended order:

1. Defining Peano Systems
2. Examples of Peano Systems
3. Recursion on Peano Systems
4. Presburger Arithmetic

Rationale: Presburger arithmetic assumes a formal arithmetic language over
natural-number structure. It should follow the definition and examples of
Peano systems, and probably follow recursion once arithmetic operations are
being formalized.

Finding V2-B, high: `Number Lines and Intervals` appears too late in The
Continuum.

Current Continuum chapter order:

1. Rational Numbers
2. Real Numbers
3. The Extended Real Numbers
4. Complex Numbers
5. Number Lines and Intervals
6. Embedding the Number Systems
7. Summary: The Number Systems

Recommended order:

1. Rational Numbers
2. Number Lines and Intervals
3. Real Numbers
4. The Extended Real Numbers
5. Complex Numbers
6. Embedding the Number Systems
7. Summary: The Number Systems

Alternative: put `Number Lines and Intervals` immediately after `Real Numbers`
if the chapter needs the completed real line.

Rationale: number lines and interval language support the real-number and
extended-real narrative. Placing them after complex numbers delays a
foundational visualization and ordering tool until after a non-ordered field.

Other Volume II sequences are coherent:

- `Natural Numbers -> Whole Numbers -> Integers` is correct.
- `Integers -> Rational Numbers -> Real Numbers -> Extended Real Numbers /
  Complex Numbers` is coherent.
- `Embedding the Number Systems` works as a synthesis chapter near the end.

### Volume III: Classical Analysis

Books:

1. Bounds, Sequences, and Series
2. Functions, Continuity, and Differentiation
3. Integration

Assessment: the book-level order is correct, but several chapter and section
orders need attention.

Finding V3-A, medium: `Structure of the Real Line` precedes `Bounds`.

Current order in Bounds, Sequences, and Series:

1. Real Analysis
2. Structure of the Real Line
3. Bounds
4. Functions
5. Discrete Calculus
6. Sequences
7. Series
8. Function Sequences

Recommended order:

1. Real Analysis
2. Bounds
3. Structure of the Real Line
4. Functions
5. Discrete Calculus
6. Sequences
7. Series
8. Function Sequences

Rationale: the current real-line structure chapter includes compactness,
covers, open/closed sets, intervals, neighborhoods, and limit points. Those
topics rely heavily on bounds, extrema, supremum/infimum, and completeness.
The dedicated `Bounds` chapter should supply that toolkit first.

Finding V3-B, medium: `Unions and Intersections` is delayed inside Structure
of the Real Line.

Current local order:

1. Real Line One Dimensional
2. Order Distance Length
3. Absolute Value as Distance
4. Intervals as Subsets
5. Neighborhoods and Balls
6. Open Sets
7. Closed Sets
8. Interior Exterior Boundary
9. Limit and Isolated Points
10. Unions and Intersections
11. Covers and Subcovers
12. Compactness on R
13. Heine Borel

Recommended local order:

1. Real Line One Dimensional
2. Order Distance Length
3. Absolute Value as Distance
4. Intervals as Subsets
5. Unions and Intersections
6. Neighborhoods and Balls
7. Open Sets
8. Closed Sets
9. Interior Exterior Boundary
10. Limit and Isolated Points
11. Covers and Subcovers
12. Compactness on R
13. Heine Borel

Rationale: union/intersection behavior is used naturally in open/closed set
algebra, covers, and compactness. It should appear before those topics.

Finding V3-C, medium: `Examples and Counterexamples` precedes `Convergence`
in Sequences.

Current sequence:

1. Sequence Definitions
2. Examples and Counterexamples
3. Convergence
4. Tails
5. Monotonicity
6. Subsequences
7. Divergence
8. Liminf and Limsup
9. Order-Theoretic Limit Constructions
10. Cluster Values of Sequences
11. Cauchy
12. Applications of Sequences

Recommended sequence:

1. Sequence Definitions
2. Convergence
3. Tails
4. Examples and Counterexamples
5. Monotonicity
6. Subsequences
7. Divergence
8. Liminf and Limsup
9. Cluster Values of Sequences
10. Cauchy
11. Order-Theoretic Limit Constructions
12. Applications of Sequences

Rationale: examples and counterexamples are more useful once convergence,
tails, and basic limit language are available. Cauchy sequences should likely
precede or accompany cluster/limsup material depending on theorem dependencies.

Finding V3-D, high: Elementary Functions starts with Hyperbolic Functions.

Current order:

1. Hyperbolic Functions
2. The Logarithm
3. Power Functions and the Exponential
4. Trigonometric Functions

Recommended order:

1. Power Functions and the Exponential
2. The Logarithm
3. Trigonometric Functions
4. Hyperbolic Functions

Rationale: hyperbolic functions are normally defined through exponentials or
developed after the exponential/logarithm toolkit. Starting with them reverses
the natural prerequisite chain.

Finding V3-E, high: Integration introduces the Cauchy integral before Riemann
and Darboux, and delays measure-zero criteria.

Current order:

1. Partitions and Tags
2. The Cauchy Integral
3. The Riemann Integral
4. The Darboux Integral
5. The Riemann--Stieltjes Integral
6. The Henstock--Kurzweil Integral
7. The McShane Integral
8. Measure Zero and the Lebesgue Criterion

Recommended order:

1. Partitions and Tags
2. The Riemann Integral
3. The Darboux Integral
4. The Cauchy Integral
5. Measure Zero and the Lebesgue Criterion
6. The Riemann--Stieltjes Integral
7. The Henstock--Kurzweil Integral
8. The McShane Integral

Rationale: partitions/tags naturally feed Riemann and Darboux definitions.
Measure-zero/Lebesgue criterion belongs with the Riemann integrability theory
before broader generalized integrals.

Follow-up note: the integration chapter should also preserve the computational
quadrature thread explicitly. Add a dedicated section, sidebar, or subsection
for rectangle rules, midpoint rule, trapezoidal rule, Simpson's rule, and
parabolic/quadratic approximation so these historically important approximation
methods do not disappear while the chapter focuses on integrability theory.
This material should be presented as numerical approximation of integral
values, not as a replacement for the existence/applicability criteria of the
integral theories.

### Volume IV: Mathematical Spaces

Book:

1. Mathematical Spaces

Assessment: coherent at the chapter level, with one medium-confidence local
ordering concern.

Current chapter order:

1. Mathematical Spaces
2. Metric Spaces
3. Topology
4. Set Algebra
5. Algebras of Sets
6. Measure Spaces

This order is coherent: concrete metric spaces precede topology, and set
algebras precede measure spaces.

Finding V4-A, medium: Metric Spaces has a duplicated/generic opening spine.

Current section order:

1. Metric Spaces
2. Definitions
3. Metrics
4. Examples of Metric Spaces
5. Distances, Boundedness, and Balls
6. Open and Closed Sets
7. Limit Points and Isolated Points
8. Sequential Convergence

Recommended order:

1. Definitions
2. Metrics
3. Examples of Metric Spaces
4. Distances, Boundedness, and Balls
5. Open and Closed Sets
6. Limit Points and Isolated Points
7. Sequential Convergence

Rationale: a section named `Metric Spaces` immediately followed by
`Definitions` looks like a duplicate introduction. If `Metric Spaces` is an
orientation section, it should be renamed accordingly or folded into
`Definitions`.

### Volume V: Modern Analysis

Books:

1. Measure Theory
2. Probability
3. Functional Analysis
4. Complex Analysis

Assessment: coherent as currently stubbed.

No chapter or section order problem is visible because each book currently has
a single chapter-level spine. The book order `Measure Theory -> Probability ->
Functional Analysis -> Complex Analysis` is defensible, especially if
probability is treated measure-theoretically.

### Volume VI: Algebra

Books:

1. Algebra
2. Linear Algebra
3. Lattice and Order Theory

Assessment: mostly coherent, with one advisory book-order question.

Finding V6-A, advisory: Linear Algebra may deserve to precede the broader
Algebra book in a learner-oriented route.

Current book order:

1. Algebra
2. Linear Algebra
3. Lattice and Order Theory

Alternative order:

1. Linear Algebra
2. Algebra
3. Lattice and Order Theory

Rationale: linear algebra is often the most useful algebraic prerequisite for
analysis, computation, and geometry. The current order is still defensible if
the Algebra book is intended to introduce general structures first.

The internal Algebra chapter order is coherent:

1. Introduction to Algebraic Structures
2. Abstract Algebra
3. Algebraic Geometry

The Lattice and Order Theory section order is coherent, though `Breadcrumb` is
probably a placeholder rather than a pedagogical section title.

### Volume VII: Advanced Logic

Books:

1. Category Theory
2. Model Theory
3. Proof Theory
4. Type Theory
5. Lambda Calculus

Assessment: coherent for a category-first advanced-foundations path, but
advisory concern for a logic-first route.

Finding V7-A, advisory: Category Theory comes before model/proof/type/lambda
topics.

Alternative logic-first order:

1. Model Theory
2. Proof Theory
3. Lambda Calculus
4. Type Theory
5. Category Theory

Alternative type-theory route:

1. Lambda Calculus
2. Type Theory
3. Proof Theory
4. Model Theory
5. Category Theory

Rationale: category theory can serve as a unifying language, but it is not the
most direct continuation from Volume I logic. The best order depends on whether
Volume VII is meant to be category-first foundations or advanced logic in the
traditional model/proof/type progression.

### Volume VIII: Applied and Computational Mathematics

Books:

1. Applied Methods
2. Numerical Foundations

Assessment: several applied/computational prerequisites are currently delayed.

Finding V8-A, medium: Numerical Foundations comes after Applied Methods.

Current book order:

1. Applied Methods
2. Numerical Foundations

Recommended order:

1. Numerical Foundations
2. Applied Methods

Rationale: floating-point formats, interval arithmetic, and numerical geometry
are prerequisites or at least safety rails for computational calculus,
computational geometry, numerical linear algebra, ODE/PDE computation, and
computational probability.

Finding V8-B, high: Computational Linear Algebra appears after geometry
topics.

Current Applied Methods chapter order:

1. Calculus
2. Geometric Modeling
3. Computational Geometry
4. Computational Linear Algebra
5. Fourier Analysis
6. Ordinary Differential Equations
7. Partial Differential Equations
8. Computational Probability

Recommended Applied Methods order:

1. Calculus
2. Computational Linear Algebra
3. Geometric Modeling
4. Computational Geometry
5. Fourier Analysis
6. Ordinary Differential Equations
7. Partial Differential Equations
8. Computational Probability

Rationale: geometric modeling and computational geometry rely on vectors,
matrices, transformations, determinants, projections, and orthogonality.
Computational linear algebra should precede them.

Finding V8-C, medium: Computational Geometry has duplicate `Convex Hulls`
headings.

Current route:

1. Convex Hulls
2. Convex Hulls

Rationale: this is probably a section/subsection duplication rather than a
semantic order issue, but it will look incoherent in a detailed TOC.

## Mechanical Registry Notes

The rendered route order mostly matches `docs/architecture/book-registry.json`.
This means the issues above should be fixed by changing the canonical expected
TOC in governance and the corresponding volume routers together, not by
one-off downstream edits.

Observed mechanical discrepancies worth separate cleanup:

- Volume I / Mathematical Logic and Proof / `proof-techniques` has routed
  notes sections, while `book-registry.json` records an empty notes list.
- Volume VIII / Numerical Foundations / `numerical-analysis` routes nested
  `numerical-geometry` subtopics beyond the registry's top-level notes list.
- Several chapter display titles differ from registry slugs by design, but the
  route order is otherwise aligned.

## Recommended Fix Order

1. Fix high-confidence local section orders first:
   V2-A, V3-D, V3-E, V8-B.
2. Fix high-confidence chapter placement:
   V2-B.
3. Decide medium-confidence analysis order changes:
   V3-A, V3-B, V3-C.
4. Clean up duplicate or placeholder TOC entries:
   V4-A, V8-C, `Breadcrumb` in Volume VI.
5. Make explicit curriculum decisions for advisory cases:
   V1-A, V6-A, V7-A, V8-A.

## Validation Recommendation

After any TOC reorder, update `docs/architecture/book-registry.json` first,
then update the matching volume routers. For each affected volume, run:

```powershell
python ..\lra-governance\scripts\build_volume.py --root . --validate-only
```

For rendered assurance, run the relevant Docker build helper from the affected
volume repository after the route changes are complete.
