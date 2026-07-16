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

## Signature Enforcement

Predicate-reading blocks must use the argument signatures registered in
`predicates.yaml` and `structures.yaml`. A predicate call must have the
registered number of arguments, and a structure constructor must be introduced
with its registered constructor form.

Surface forms that describe equivalent presentations of a concept are not
automatically new canonical predicates. For example, a source may discuss
epsilon--delta, neighbourhood, and sequential formulations of the derivative.
If the registry has one canonical derivative predicate plus the lower-level
limit and convergence predicates needed to express the other forms, record the
extra names as equivalent-language aliases or registry needs. Do not silently
promote `Derivative_top` or `Derivative_seq` to canonical predicate IDs.

For example, if `predicates.yaml` registers
`ConvergesTo(x,L,X)` and `IsCauchy(x,X)`, do not write the legacy implicit
forms:

```latex
\operatorname{ConvergesTo}(x_n,L)
\qquad
\operatorname{IsCauchy}(x_n)
```

Instead, introduce or name the sequence object and pass the ambient object:

```latex
\[
\begin{aligned}
&\mathbf{x}=\mathsf{Sequence}((x_n),\mathbb{N},\mathbb{R}),\\
&\operatorname{ConvergesTo}(\mathbf{x},L,\mathbb{R})
  \Longleftrightarrow
  \operatorname{IsCauchy}(\mathbf{x},\mathbb{R}).
\end{aligned}
\]
```

Validators may surface mismatched arities, missing ambient arguments, and
structure constructors written as `\operatorname{...}`. During broad migrations
these findings may be review-level, but new content should satisfy them.

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

## Construction Lines

A predicate-reading block may introduce local construction lines that name the
objects used by later predicates. These lines are part of the formal reading of
the block, not ordinary exposition.

Use construction lines for sequences, ordered ambients, topological ambients,
metric ambients, function spaces, set families, and similar packaged context:

```latex
\[
\begin{aligned}
&P=\mathsf{OrderedSet}(\mathbb{N},\leq),\\
&Q=\mathsf{OrderedSet}(\mathbb{R},\leq),\\
&\mathbf{x}=\mathsf{Sequence}((x_n),\mathbb{N},\mathbb{R}),\\
&\operatorname{OrderPreserving}(\mathbf{x},P,Q).
\end{aligned}
\]
```

Construction lines should use stable local names (`P`, `Q`, `M`, `T`,
`\mathbf{x}`, and similar) and should appear before all predicate calls that
use them. They should not hide mathematical data: if the construction mentions
`\mathbb{N}`, `\mathbb{Z}`, `\mathbb{Q}`, `\mathbb{R}`, `\mathbb{C}`, an order
relation, a topology, a metric, or a function space, those objects are part of
the parse context and must be visible to dependency extraction.

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

## Domain-Carrying Function Predicates

Some function predicates intentionally do not include a separate domain
argument because the domain is carried by the typed function datum. For example,
the canonical limit predicate is
`TendsTo(f,a,L,X,Y)`, not `TendsTo(f,A,a,L,X,Y)`. In such a predicate, if
`f:A\to Y`, then `A` is intrinsic to `f`, while `X` records the source ambient
space in which the approach to `a` is interpreted.

Registry entries that use this convention must declare
`domain_convention.kind: typed_function_domain`. Semantic artifacts using such
predicates must keep the restricted-domain quantification visible in the
quantified form, for example `\forall x\in A`, and must not pass the domain set
as a shifted predicate argument. If this convention is not mathematically
adequate for a topic, add a governed predicate or structure representation
rather than inventing a local argument order.

## Legacy Readings

Older notes may use implicit ambient predicates such as
`\operatorname{CauchySequence}(x_n)` in a real-analysis context. New content
should use the ambient-explicit form, for example
`\operatorname{CauchySequence}(x_n,\mathbb{R})`. Migration should be mechanical
and scoped; do not mix implicit and explicit signatures in new blocks.

## Registry Fields

Predicate and structure registries are machine-readable contracts, not glossaries.
They must preserve:

- arity, by the length of the ordered `arguments` list;
- argument position, by YAML list order, optionally mirrored by a matching
  `position` field;
- argument role/type intent, by each argument's `role`;
- predicate return type, by `returns`;
- structure assembly data, by `carrier_argument`, `structural_arguments`, and
  `carried_context` where applicable.

No semantic data may disappear merely because it is packaged inside a predicate
or structure argument. If an argument carries a domain, codomain, carrier,
relation, topology, metric, operation, index set, ambient space, or similar
context, the registry must expose that packaging through existing structure
fields or through `carried_context`.

Each predicate entry should state:

- `id`, with the `pred:` prefix;
- `name`, the `\operatorname{...}` name;
- `kind: predicate`;
- `category`;
- `arguments`, including which argument is ambient when applicable;
- `returns`;
- `surface_forms`, for trigger/audit discovery;
- a short `description`.

Predicate entries may include `carried_context` items of the form:

```yaml
carried_context:
  - kind: domain
    source: type_of_argument
    argument: f
    exposes_as: admissible_input_domain
```

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

Structure entries may include `carried_context` items of the form:

```yaml
carried_context:
  - kind: carrier
    source: argument
    argument: X
    exposes_as: carrier
  - kind: topology
    source: argument
    argument: tau
    exposes_as: topology
```

The registry contract validator rejects missing names/roles, duplicate argument
names, mismatched explicit positions, predicate return types other than
`truth_value`, structure carrier/structural references that do not point to real
arguments, and carried-context references to non-existent arguments.
