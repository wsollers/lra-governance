# Dependency Standards

Dependency standards govern dependency information wherever it appears in the
notes, proof files, stubs, structural presentations, and extracted knowledge
artifacts.

Dependencies are not a standalone mathematical artifact type. They are a
shared information set consumed by definitions, axioms, theorem-like
environments, completed proofs, proof stubs, structural presentations, and
Knowledge Explorer records.

## Scope

Use this standard whenever an item records mathematical prerequisites,
references another formal statement, links a proof artifact back to its source,
or exposes graph edges for extraction.

Dependency information may appear with:

- definitions;
- axioms;
- theorems, lemmas, propositions, and corollaries;
- completed proofs;
- proof stubs;
- vocabulary definitions;
- structural definitions;
- model-theoretic presentations;
- algebraic or structural blueprints;
- classification cards.

## Dependency Layer

A dependency block records graph-relevant mathematical routing. It is not merely
an exposition list, bibliography list, proof-location list, or informal reading
order.

Dependency blocks answer:

```text
Which formal mathematical artifacts should this item be connected to in the
learning graph?
```

This includes more than strict proof-theoretic ancestry. Dependency links may
record any of the following route kinds:

1. Direct prerequisites: formal items needed to state, parse, define, or prove
   the owning artifact.
2. Structural-existence routes: axioms or theorem-like artifacts that make the
   owning concept operative in the intended theory.
3. Structural-pairing routes: companion artifacts that give the concept its
   main mathematical role.
4. Proof-use routes: definitions, axioms, and prior results actually invoked by
   a completed proof or proof stub.

They do not answer:

```text
Where is the proof file?
What source text inspired this item?
What should be read next as ordinary exposition?
What is the informal motivation?
```

Those belong to proof navigation, source crosswalk remarks, reading order,
toolkits, interpretation remarks, or exposition remarks.

## Parse And Type Dependencies

Predicate-reading and formal-reading blocks create parse dependencies. If a
statement or predicate-reading block uses a mathematical carrier, ambient
object, packaged structure, or construction, the owning artifact must depend on
the formal item that introduces that object or structure.

Examples of parse/type dependencies include:

- `\mathbb{N}`, `\mathbb{Z}`, `\mathbb{Q}`, `\mathbb{R}`, and `\mathbb{C}`;
- ordered structures such as `P=\mathsf{OrderedSet}(A,\leq)`;
- sequence structures such as
  `\mathbf{x}=\mathsf{Sequence}((x_n),\mathbb{N},\mathbb{R})`;
- metric, topological, function-space, interval-family, and set-family
  structures;
- named relations or operations that are part of a structure constructor.

Thus a predicate-reading line such as

```latex
\mathbf{x}=\mathsf{Sequence}((x_n),\mathbb{N},\mathbb{R})
```

creates dependency requirements for the formal artifacts for natural numbers,
real numbers, and sequences. A line such as

```latex
Q=\mathsf{OrderedSet}(\mathbb{R},\leq)
```

creates dependency requirements for the formal artifacts for real numbers, the
relevant order on the real line, and ordered sets.

These dependencies are not optional stylistic links. They are what allow the
Knowledge Explorer to recover the type/ambient route that makes a predicate
well-formed.

If the relevant formal item exists, link it explicitly in the dependency block.
If it does not yet exist, write a TODO dependency note rather than inventing a
label. New generated or hand-authored content must not omit these parse/type
dependencies merely because they are visible in the predicate-reading line.

## Definition Dependency Rule

A definition may list both direct vocabulary prerequisites and structural
artifacts that govern use of the concept.

For example, the definition of supremum has a direct prerequisite edge to upper
bound and a structural-existence edge to the Axiom of Completeness. Upper bound
is needed to define what a supremum is. Completeness is the axiom that ensures
important bounded-above subsets of `\mathbb{R}` actually have suprema. Without
that structural route, the Knowledge Explorer misses the mathematical hinge:

```text
Upper bound <-- Supremum --> Axiom of Completeness
```

Preferred dependency block for this case:

```latex
\begin{dependencies}
\begin{itemize}
  \item \hyperref[def:upper-bound]{Upper bound}
  \item \hyperref[ax:real-completeness]{Axiom of Completeness}
\end{itemize}
\end{dependencies}
```

Axioms remain formal roots as statements. Do not assign prerequisites to an
axiom merely because its wording uses prior vocabulary. Axioms may, however,
appear as dependency targets for definitions, theorems, and proofs when the
axiom structurally governs the concept or result.

## Standard LaTeX Form

Visible dependency blocks must use the shared `dependencies` environment.

Preferred form:

```latex
\begin{dependencies}
\begin{itemize}
  \item \hyperref[label]{Readable Name}
\end{itemize}
\end{dependencies}
```

The dependency target must be a mathematical statement label with an approved
prefix:

- `def:`;
- `ax:`;
- `thm:`;
- `lem:`;
- `prop:`;
- `cor:`.

Do not use `prf:` labels as dependency targets. A `prf:` label identifies a
proof location, not a mathematical prerequisite.

## Silent Foundational Marker

Use `\NoLocalDependencies` only for axiom statements with no local
mathematical prerequisites:

```latex
\NoLocalDependencies
```

Do not use `\NoLocalDependencies` on ordinary definitions, theorems, lemmas,
propositions, or corollaries. If a definition is a reviewed primitive, mark it
with `\DefinitionalRoot`; otherwise write an explicit dependency block.

Do not print a visible dependency block that says only "No local dependencies."
The silent marker is structural metadata, not prose, and should render nothing.

## TODO Dependencies

If a dependency is mathematically real but the target statement has not yet
been formalized, write a TODO dependency note and do not invent a label.

Example:

```latex
\begin{dependencies}
\begin{itemize}
  \item TODO: formalize the relevant compactness statement.
\end{itemize}
\end{dependencies}
```

Replace TODO dependency notes with formal links once the target exists.

## Proof Dependencies

Completed proofs and proof stubs must record dependencies according to their
own proof standards, but the dependency targets still follow this standard.

Proof-vault URLs are not dependency targets. They are proof artifact metadata
and must use the proof-vault macro specified by proof standards and extraction
standards.

## Structural Presentations

Structure blueprints, classification cards, and signature presentations may
carry dependency metadata, but they do not automatically require visible
dependency blocks unless they introduce a formal statement or a reusable
extraction record.

When a structural presentation points to formal prerequisites or structural
routes, use the same approved label prefixes and readable link text.

## Extraction Contract

Dependency information is extraction-visible. Tooling should treat each
approved `\hyperref[label]{Readable Name}` dependency item as a graph edge from
the owning artifact to the target label.

When tooling supports edge kinds, the standard dependency route kinds are:

- `prerequisite`;
- `structural-existence`;
- `structural-pairing`;
- `proof-use`.

If the LaTeX source does not encode an explicit kind, extraction tooling should
record the edge as an untyped dependency edge and may infer a route kind only
when a deterministic rule or canonical route registry supports that inference.

Extraction implementation details belong in `extraction-standards.md`; this
document is the author-facing dependency rule source.
