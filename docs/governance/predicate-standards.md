# Predicate Standards

Predicate standards govern canonical predicate names, predicate-reading blocks,
and the way predicates carry ambient mathematical structure.

## Canonical Source

The canonical predicate registry is `predicates.yaml` at the root of
`lra-governance`. Volume repositories do not own predicate names and must not
define local substitutes for missing canonical predicates.

If a predicate is needed but absent from `predicates.yaml`, record a missing
predicate need instead of inventing an ad hoc name in a notes file, proof file,
prompt output, or extraction artifact.

## Layer Gate

Predicate names are reserved for predicate-reading layers and related
analysis/extraction layers. They do not appear inside formal definition bodies,
theorem bodies, standard quantified statements, negated quantified statements,
or ordinary exposition unless the text is explicitly discussing predicate
notation.

## Ambient-Structure Arguments

Predicates that depend on a mathematical setting carry that setting as an
explicit ambient argument. The ambient argument is normally the whole
structure, not only its carrier set.

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

Predicate readings may unpack the ambient structure before the predicate line
when this improves readability. Keep the predicate itself ambient-parametric:

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
