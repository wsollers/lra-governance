# The Cantor-to-Ito Spine — and the Turing-to-Carmack Spine (Architecture Memo)

> **Status: exploratory — NON-NORMATIVE.**
> Records the organizing principle for the corpus. **Not** part of the agent
> instruction set, **not** referenced by `constitution/` or `AGENTS.md`, **not**
> enforced by any validator. It preserves reasoning so decisions are made against
> a record. Do not act on it; do not cite it as authority. The concrete moves it
> implies live in `reorg-enactment.md`.

## Two spines

The corpus has two parallel narratives, not one:

- **Cantor -> Ito** (the **theory** spine): *why it is true.* Rigorous control of
  limiting processes, taming the infinite from the countable to the continuous to
  the measurable to the stochastic. Volumes I-V (plus the structure companions
  VI-VII).
- **Turing -> Carmack** (the **practice** spine): *how to compute and render it.*
  From what is computable in principle to what renders in a frame budget.
  Volume VIII (Applied & Computational), trending toward the Vulkan / Brownian-
  motion-on-the-torus endgame.

The practice spine is the *goal*; the theory spine is *the learning that earns the
right to do it.* They mirror the project's founding two-sentence self-description:
deep structural mathematics **and** high-performance simulation.

## The theory spine

```
prop logic -> pred logic -> sets -> numbers -> [classical analysis]
                                            -> spaces -> [modern analysis]
```

Read it as a verb repeated: **each stage builds the arena the next runs in.** It is
not the same step every time; two kinds alternate:

- **Arena-builders** construct the ground a later subject stands on (sets build
  numbers; numbers build R; spaces build the abstract structural ground).
- **Eras** are where building stops and *inhabiting* begins (classical analysis in
  R; modern analysis in spaces).

Rhythm: language sharpens itself (logic) -> language precipitates structure (sets)
-> structure builds the inhabitant (numbers) -> live in it (classical analysis) ->
abstract its deep property into a new arena (spaces) -> live in that (modern
analysis).

## The era analogy

```
Numbers : classical analysis  ::  Spaces : modern analysis
```

Genuine and load-bearing because **completeness is the through-line.** R's
completeness is what makes differentiation and the elementary integral work; the
Spaces volume installs the generalizations — metric completeness, compactness,
sigma-algebras, completeness of function spaces. The second foundation is the
first's central property abstracted into its own subject. On the shelf this shows
up as **adjacent arena->era pairs: II->III and IV->V.**

## Shape: line, then fan

- First half (logic -> sets -> numbers -> classical analysis): a near-linear
  **spine**; "nothing used before it is proven" holds cleanly.
- Second half (spaces -> modern analysis, and onward to probability, stochastics,
  manifolds): a **fan / DAG**, not a line. The arena precedes a *branching
  structure*. Declare a dependency DAG with an open join; the torus/stochastics
  endgame is where the braid closes.

## Stability tiers (a refinement of "committed")

- **Foundational-frozen** — logic, sets (, geometry). Proven once, near-zero churn,
  enormous downstream out-degree; a change is near-constitutional.
- **Arena-committed** — numbers, spaces. Theorem-rich, occasionally re-sequenced.
- **Active** — whatever is currently being written.

## Glossary (this project inverts Bourbaki's word)

- **Volume** = the repo / shipping container (`lra-volume-iii`).
- **Book** = a subject-partition *inside* a volume (`volume-iii/book-analysis-i/`).
  One volume holds one or more books; uniform path grammar
  `volume-*/book-*/chapter-*/...` **everywhere**, including single-book volumes.
- **Physical bound object** = whatever a binding takes (~450-600 trophy pages); a
  book may print as several bound objects.

## The final shelf (working blueprint, June 2026 — still non-normative)

| Vol | Title | Role |
|---|---|---|
| **I** | Foundations: Logic, Sets & Geometry | foundational-frozen |
| **II** | Numbers | arena #1 (R) |
| **III** | Classical Analysis | era #1 |
| **IV** | Spaces | arena #2 (topology, metric, measure-spaces, sigma-algebras) |
| **V** | Modern Analysis | era #2 (measure/Lebesgue, probability, functional -> stochastics) — reserved, mostly empty |
| **VI** | Algebraic Structures | algebra + linear algebra (Halmos) + lattice-order |
| **VII** | Advanced Logic | category, lambda, model, proof, type theory |
| **VIII** | Applied & Computational *(Turing -> Carmack)* | numerical-foundations + applied-methods |

Properties: arena->era pairs are physically adjacent (II->III, IV->V); all theory
precedes the applied volume; Advanced Logic sits right after Algebraic Structures
(both "abstract structure" subjects). The shelf reads left-to-right as the spine.

### Placement calls (recorded)

- **Geometry is foundational** -> Vol I `book-geometry` (Euclid's *Elements*, the six
  trig functions from first principles + unit circle, analytic geometry). Upstream
  of analysis (trig precedes limits/Taylor/Fourier). Hyperbolic trig built in
  parallel to circular (x^2-y^2=1 vs x^2+y^2=1, area parameter). No forced
  "parabolic trig" pillar — at most an aside.
- **Elementary functions dissolve**: *construction* -> Geometry; *behavior*
  (fundamental limits, continuity, derivatives, growth) -> Classical Analysis, in
  the chain limits -> function-limits -> behavior-of-elementary-functions ->
  continuity (so it lands in the Functions, Continuity, and Differentiation
  book, after limits). exp/log behavior carries a forward-dependency on
  series/integration.
- **R-topology, two altitudes**: concrete (open/closed/compact, Heine-Borel on R)
  stays in Classical Analysis (`book-analysis-i`, after the toolkit); the general
  topological/metric framework is in Spaces.
- **ODE = classical**; its rigorous existence/uniqueness (Picard-Lindelof as a
  contraction mapping) belongs in Classical Analysis when written. **Applied
  ODE/PDE solving** belongs in the Applied volume. PDE is a braid: classical
  (Fourier, separation of variables) vs modern (weak solutions, Sobolev).
- **Linear algebra** (Halmos, *Finite-Dimensional Vector Spaces*) lives in
  Algebraic Structures (VI); it is the concrete neighbor of Spaces by
  cross-reference (finite-dim inner-product spaces -> Hilbert spaces), not by
  shared volume.
- **Lean**: formalization lives only in `lra-lean`. Volumes I and II carry a
  *generated* `appendix-lean/` (the Lean statements + exposition, emitted from
  `lra-lean` as plain `.tex` the volume `\input`s). One-directional: the volume
  build never runs a Lean toolchain. No other volume has Lean.

### Two honest caveats

- **prop -> pred is *refines*, not *grounds*** — the same logic with quantifiers, not
  a new arena. If the dependency front matter is formalized, mark that one link
  "refines."
- **This corpus's analysis is fat by design** — proofs-included, geometry-first.
  Books split on pedagogical arc, not Bourbaki's logical minimality. Keep the
  interpretation/figure layer Bourbaki refused.

## Through-line

One idea maturing — **rigorous control of limiting processes** — climbing countable
-> continuous -> measurable -> stochastic (Cantor to Ito), then made to *run on a
computer* (Turing to Carmack). The torus/stochastics endgame is where both spines
meet.

## Provenance

Derived from a design conversation (June 2026) reorganizing the `lra-volume-*`
repos into Bourbaki-style books, fixing the print/digital policy, and inventorying
what was actually on disk in Volumes IV-VIII. Page-count measurement recorded
separately. Nothing here is binding until explicitly adopted.
