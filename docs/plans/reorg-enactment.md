# Volume/Book Re-org — Enactment Plan (Two-Spine Final)

> **Status: working plan — NON-NORMATIVE.** The one-time re-org to the final
> two-spine shelf. Execute deliberately, on branches, **compile + validate after
> every step** (ref-warnings are acceptable mid-flight; broken builds are not).
> Companion to `cantor-to-ito-spine.md`.

## Governing principles

1. **Lego moves first.** Create `book-*` folders and `git mv` chapters until each
   volume compiles + validates under the new grammar. Bad `\ref` warnings are OK
   here; a non-compiling build is not.
2. **Move -> re-point -> renumber, never all at once.** Relocate content; then
   re-point cross-references as *verified* search-and-replace, one at a time,
   compiling between; then renumber the shells last.
3. **Every cross-reference re-point is tested.** Search, replace, compile, confirm
   the warning count dropped, commit. No blind sweeps.
4. **`git mv` always** (preserve history). Validators run on the machine, not here.

## Path grammar (lock first, step 0)

```
volume-<roman>/ book-<slug>/ <chapter-slug>/ {notes,proofs}/ ...
```

Uniform everywhere, including single-book volumes (`volume-v/book-modern-analysis/...`).
The volume token lives in routers (`\input{volume-x/...}`), `chapter.yaml`
(`volume:`, `path:`), any volume-encoding labels, and CI/output targets — so the
later renumber is a bounded sweep of *those four places*, not a rewrite.

## Final shelf (target)

| New Vol | Title | Built from |
|---|---|---|
| **I** | Foundations: Logic, Sets & Geometry | old I + geometry harvested from old V |
| **II** | Numbers | old II (− structure-of-real-line, − lean) |
| **III** | Classical Analysis | old III analysis cluster + structure-of-real-line |
| **IV** | Spaces | **new**: old-V topology + old-VIII algebras-of-sets + old-IV set-algebra + new metric-spaces |
| **V** | Modern Analysis | re-tasked old-V shell; seeded from old-III modern stubs |
| **VI** | Algebraic Structures | old IV (algebra, linear-algebra, lattice-order), renumbered |
| **VII** | Advanced Logic | old VIII (category/lambda/model/proof/type), renumbered |
| **VIII** | Applied & Computational *(Turing->Carmack)* | old VI + old VII consolidated, renumbered |

## Harvest / content-move map (the cross-volume moves)

| Content | From | To |
|---|---|---|
| euclidean-geometry, trigonometry, analytical-geometry | old V | **I** `book-geometry` |
| `topology` (abstract) | old V | **IV** `book-spaces` |
| differential-, riemannian-, non-euclidean-geometry | old V | **`lra-hold`** (manifolds/future) |
| `set-algebra` (power-set, sigma-intersection) | old IV | **IV** `book-spaces` (measure foundation) |
| `algebras-of-sets` (rings/sigma/borel) | old VIII | **IV** `book-spaces` (measure foundation) |
| `structure-of-real-line` | old II | **III** `book-analysis-i` (after toolkit) |
| measure-theory, probability-theory, functional-analysis, complex-analysis (stubs) | old III | **V** (Modern Analysis seeds) |
| number-theory, quantum-calculus, discrete-calculus | old III | **`lra-hold`** |
| elementary-functions: *construction* | old III | **I** `book-geometry` (trig + hyperbolic, parallel) |
| elementary-functions: *behavior* | old III | **III** `book-analysis-ii` |
| `lean` chapter | old II | dissolved -> generated `appendix-lean/` in I and II |

## Per-volume target layout

**Vol I — Foundations: Logic, Sets & Geometry**
- `book-logic`: propositional-logic, predicate-logic, axiom-systems, proof-techniques
- `book-sets`: set-theory, relations, functions, orderings, cardinality
- `book-geometry`: euclidean-geometry (Euclid I.1-3 real), trigonometry (+ hyperbolic, from first principles), analytical-geometry
- `appendix-lean/` (generated from `lra-lean`; empty stub seeded now)

**Vol II — Numbers**
- `book-discrete-algebraic`: formalizing-number-systems, identity-equality-equivalence, arithmetic-operations-relations, constructing-number-systems, peano-systems, natural-numbers, whole-numbers, integers
- `book-continuum`: embedding-number-systems, rationals, reals, complex-numbers, number-lines, numbers-summary
- `appendix-lean/` (generated; stub seeded now)
- *out:* structure-of-real-line -> III; lean -> appendix

**Vol III — Classical Analysis**
- `book-analysis-i`: real-analysis, bounding, functions*, sequences, series, function-sequences, (incoming) structure-of-real-line
- `book-analysis-ii`: functions/limits (moved), behavior-of-elementary-functions (new), continuity
- `book-analysis-iii`: differentiation
- `book-integration`: riemann-integration (+ future cauchy/darboux/stieltjes/FTC/approximation; rigorous ODE existence-uniqueness + classical PDE later)
- *evict:* modern stubs -> V; number-theory/quantum/discrete-calculus -> `lra-hold`

\* `functions` keeps algebra-of-functions, subsets-real-line, real-valued-functions; its `limits` topic moves to `book-analysis-ii`.

**Vol IV — Spaces** (new container)
- `book-spaces`: point-set-topology (from old-V topology), metric-spaces (new), measure-spaces + sigma-algebras (from old-VIII algebras-of-sets + old-IV set-algebra)

**Vol V — Modern Analysis** (re-tasked old-V shell, reserved)
- `book-measure`, `book-probability`, `book-functional-analysis`, `book-complex-analysis` — seeded from old-III stubs; mostly empty.

**Vol VI — Algebraic Structures** (old IV, renumbered)
- `book-algebra`: algebraic-structures (groups/rings/fields), abstract-algebra, algebraic-geometry
- `book-linear-algebra`: vector-spaces (Halmos)
- `book-lattice-order`: ordered-sets/lattices
- *out:* set-algebra -> IV

**Vol VII — Advanced Logic** (old VIII, renumbered)
- `book-category-theory`, `book-lambda-calculus`, `book-model-theory`, `book-proof-theory`, `book-type-theory`
- *out:* algebras-of-sets -> IV

**Vol VIII — Applied & Computational** (old VI + old VII, renumbered + consolidated)
- `book-numerical-foundations`: ieee-floating-point, interval-arithmetic, error/convergence, numerical-analysis, numerical-pde (the *theory of the methods* — Lipschitz/error bounds for GPU live here)
- `book-applied-methods`: computational-calculus (limits/continuity/derivatives/integrals/multivariable/sequences-series), ODE, PDE, computational-geometry (convex-hulls real), geometric-modeling (Bezier), computational-linear-algebra, fourier-analysis, computational-probability

## Renumber sweep checklist (the late pass)

When a volume's number changes, sweep these four (grep the old number first):
1. **Router `\input{volume-x/...}`** lines (the bulk; cheap).
2. **`chapter.yaml`** `volume:` and `path:` fields.
3. **Cross-volume references** (`\hyperref[...]`, `\ref`, `\Cref`) and any
   `sec:`/`ch:` labels that embed a volume number. Concept-named `prf:/thm:/def:`
   labels are stable and need no change — that is what makes this affordable.
4. **CI + output**: per-volume `main.tex`/workflow, and the published
   `digital/lra-volume-<roman>.pdf` / `print/...` targets in `lra-volumes-output`
   (renumber shifts published filenames + explorer/Pages links).

## Enactment order (gated)

0. **Governance/schema (no files moved).** Teach `file-schema.yaml` /
   `volume-structure.schema.json` / `validate_volume.py` the `book-*` tier; add a
   `book:` field to `chapter.yaml`; update the volume/book glossary in the layout
   docs. Gate: validator parses; nothing built yet.
1. **Pilot: partition Vol III internally** into `book-*` (lego moves only), add the
   book-index router layer, update `index.tex`. Gate: digital + print build;
   diff page counts vs. 667/351; validator clean on structure.
2. **Partition Vols I and II** the same way (book folders, routers). Gate: build + validate each.
3. **Cross-volume content moves** (harvest map), one source at a time: V-geometry->I,
   V-topology->IV(new), set-algebra->IV, algebras-of-sets->IV, structure-of-real-line->III,
   III-modern-stubs->V, asides->`lra-hold`. After each: build the *source* and
   *destination* volumes; expect ref-warnings (re-pointed next).
4. **Re-point cross-references** as verified search-and-replace, one at a time,
   compiling between, watching the warning count fall to zero.
5. **Renumber the shells** (old IV->VI, old VIII->VII, old VI+VII->VIII; re-task old V):
   run the four-point sweep per volume; rebuild; confirm `lra-volumes-output`
   targets and explorer links.
6. **Seed Vol IV/V/VIII new books + `appendix-lean/` stubs.** Gate: full build of
   every touched volume; validators clean; commit; tag the re-org.

## Resolved decisions

Holding repo = `lra-hold`. structure-of-real-line -> Analysis I (whole). elementary-
functions dissolved (construction->Geometry, behavior->Analysis II). Lean ->
generated appendix in I & II only. Spaces -> Vol IV (linear algebra stays in VI,
neighbor by cross-reference). Vol V reserved for Modern Analysis. Old IV->VI
(Algebraic Structures), old VIII->VII (Advanced Logic), old VI+VII->VIII (Applied).
Uniform `book-*` grammar everywhere.

## Caveats

- Validator/build gates run on the machine; the planning side can't run them.
- The renumber is bounded (four places) but is its own late pass *after* I-III are
  squared, specifically so cross-references never dangle.
- This is the last *structural* re-org of the core; future fan branches leave
  `lra-hold` for their own volumes by folder move under the same grammar.
