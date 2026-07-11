# Predicate Standards

Predicate standards govern canonical predicate names, predicate-reading blocks,
and the way predicates carry ambient mathematical structure.

## Canonical Source

The canonical predicate registry is `predicates.yaml` at the root of
`lra-governance`. Ambient mathematical structure constructors live in
`structures.yaml` beside it. Volume repositories do not own predicate names or
structure constructors and must not define local substitutes for missing
canonical vocabulary.

If a predicate is needed but absent from `predicates.yaml`, record a missing
predicate need instead of inventing an ad hoc name in a notes file, proof file,
prompt output, or extraction artifact. If an ambient object such as an ordered
set, function space, topological space, or set family is needed but absent from
`structures.yaml`, record a missing structure need instead of passing loose
pieces indefinitely.

## Layer Gate

Predicate names are reserved for predicate-reading layers and related
analysis/extraction layers. They do not appear inside formal definition bodies,
theorem bodies, standard quantified statements, negated quantified statements,
or ordinary exposition unless the text is explicitly discussing predicate
notation.

## Ambient-Structure Arguments

Predicates that depend on a mathematical setting carry that setting as an
explicit ambient argument. The ambient argument is normally the whole
structure, not only its carrier set or its raw relation symbols.

For example, in a metric space `M=(X,d)`, write

```latex
\operatorname{Sequence}(x_n,M)
\operatorname{ConvergentSequence}(x_n,x_0,M)
\operatorname{CauchySequence}(x_n,M)
\operatorname{Neighborhood}(U,x,M)
```

The carrier set and structural data are recovered from the ambient object:
`\operatorname{Carrier}(M)=X` and `d` is the metric of `M`. Do not replace the
ambient argument by a loose set parameter when the predicate uses more than the
set.

For ordered objects, introduce the structure object before using predicates
that depend on it:

```latex
\[
\begin{aligned}
&P=\mathsf{OrderedSet}(A,\leq),\\
&\operatorname{UpperBound}(u,S,P)
  \coloneqq
  S\subseteq A \wedge u\in A \wedge \forall s\in S\;(s\leq u).
\end{aligned}
\]
```

The structure assignment is part of the predicate reading. It must appear
before the first predicate that uses the structure unless the structure object
has already been fixed unambiguously in the same predicate-reading block.

## Polymorphism And Substitution

Prefer polymorphic predicates over families of specialized names. A predicate
such as `\operatorname{Sequence}(x_n,A)` means that `x_n` is a sequence valued
in the carrier of the ambient object `A`, whenever `A` has a carrier. The same
predicate can be used with `\mathbb{R}`, a metric space, a topological space,
or another suitable structure.

Do not create combinatorial variants such as `MetricSequence`,
`TopologicalSequence`, or `RealSequence` when a canonical predicate with an
ambient argument already expresses the distinction. Use specialized predicate
names only when the mathematical property itself is genuinely different and
cannot be represented by changing the ambient argument.

## Explicit Unpacking

Predicate readings must unpack newly introduced ambient structures before the
predicate line. Keep the predicate itself ambient-parametric:

```latex
\[
\begin{aligned}
&\text{Let } M=(X,d) \text{ be a metric space.}\\
&\operatorname{CauchySequence}(x_n,M)
  \coloneqq
  \forall \varepsilon>0\;\exists N\in\mathbb{N}\;
  \forall n,m\ge N\;(d(x_n,x_m)<\varepsilon).
\end{aligned}
\]
```

The unpacking line explains how the predicate reads in that structure. It does
not change the canonical predicate signature.

## Structure Constructors

Structure constructors are written with `\mathsf{...}` and are registered in
`structures.yaml`. They build ambient mathematical objects for predicate
arguments; they are not truth-valued predicates.

Use:

```latex
P=\mathsf{OrderedSet}(A,\leq)
\qquad
T=\mathsf{TopologicalSpace}(X,\tau)
\qquad
\mathcal{F}_U=\mathsf{SetFamily}(\mathcal{F},U)
```

Do not write a structure constructor as if it were a predicate:

```latex
\operatorname{UpperBound}(u,S,\operatorname{OrderedSet}(A,\leq))
```

Instead, assign the structure object first:

```latex
\[
\begin{aligned}
&P=\mathsf{OrderedSet}(A,\leq),\\
&\operatorname{UpperBound}(u,S,P).
\end{aligned}
\]
```

If the validity of the structure itself is at issue, use the appropriate
predicate separately, for example a predicate asserting that the relation is a
partial order on the carrier.

## Argument Role Conventions

Use stable argument names in predicate signatures and predicate-reading blocks
unless local notation has already fixed a different convention:

| Symbol | Role |
| --- | --- |
| `A`, `B`, `C` | sets, domains, codomains, carriers |
| `S`, `T` | subsets of an ambient set |
| `U` | ambient universe or ambient set |
| `\mathcal{F}` | family of sets |
| `\mathcal{C}` | cover |
| `I` | index set |
| `i`, `j` | indices |
| `a`, `b`, `c` | generic elements of sets |
| `x`, `y`, `z` | generic variables, especially ordered-set elements |
| `u` | upper-bound candidate |
| `\ell` | lower-bound candidate |
| `u^*` | supremum candidate |
| `\ell^*` | infimum candidate |
| `f`, `g`, `h` | functions |
| `R` | relation |
| `P` | ordered/preordered/poset ambient structure |
| `T` | topological ambient structure |
| `M` | model or metric ambient structure, according to chapter context |
| `s` | assignment in logic/model theory, or local element variable when no assignment is present |

Sequences are written as `(x_n)_{n\in\mathbb{N}}` or as a bold sequence object
`\mathbf{x}` when the whole sequence is an argument. Reserve uppercase `S` for
sets and subsets rather than sequence objects.

## Legacy Readings

Older notes may use implicit ambient predicates such as
`\operatorname{CauchySequence}(x_n)` in a real-analysis context. New content
should use the ambient-explicit form, for example
`\operatorname{CauchySequence}(x_n,\mathbb{R})`. Migration should be mechanical
and scoped; do not mix implicit and explicit signatures in new blocks.

## Registry Fields

Each predicate entry should state:

- `id`, with the `pred:` prefix;
- `name`, the `\operatorname{...}` name;
- `kind: predicate`;
- `category`;
- `arguments`, including which argument is ambient when applicable;
- `returns`;
- `surface_forms`, for trigger/audit discovery;
- a short `description`.

Additional metadata may record polymorphism, ambient support, legacy aliases,
or source notes, but the canonical name and argument convention remain the
source of truth.

Each structure entry in `structures.yaml` should state:

- `id`, with the `struct:` prefix;
- `name`, the canonical constructor name;
- `kind: structure`;
- `category`;
- `constructor`, normally `\mathsf{<Name>}`;
- `arguments`, including carrier and structural roles;
- `carrier_argument`, when the structure has a carrier;
- `structural_arguments`;
- `surface_forms`, for trigger/audit discovery;
- a short `description`.
