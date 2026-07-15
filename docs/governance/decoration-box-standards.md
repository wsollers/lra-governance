# Decoration Box Standards

Decoration box standards govern the non-statement information blocks that
surround definitions, theorem-like environments, and related formal artifacts.

These blocks are part of the standard information set for an artifact. They are
not decorative flourish. They provide quantified restatements, predicate
readings, failure-mode analysis, interpretation, exposition, examples,
non-examples, source crosswalks, dependencies, and proof navigation where the
artifact type requires them.

## Rendering Rule

Decoration blocks are structural metadata blocks. Unless an artifact-specific
standard explicitly states otherwise, decoration blocks render as unboxed
`remark*` environments rather than standalone theorem-style boxes.

This applies to standard quantified statements, predicate readings, negated
quantified statements, negation predicate readings, failure-mode blocks,
interpretation blocks, exposition blocks, examples, non-examples, source
crosswalks, and dependency blocks.

The owning definition, theorem, lemma, proposition, corollary, or axiom remains
the primary formal artifact. Decoration blocks are attached metadata and do not
create an independent theorem-like visual hierarchy.

## Formal And Pedagogical Containers

Formal statement boxes contain the matching formal environment. For example, a
`theorembox` contains a `theorem`, a `propositionbox` contains a `proposition`,
and a `definitionbox` contains a `definition`. The inner formal environment owns
the statement label, proof-navigation link when required, and extraction
identity.

Unnumbered starred environments such as `theorem*` are reserved for proof-file
restatements and local presentation. They do not satisfy the formal-box
contract inside `theorembox`, `lemmabox`, `propositionbox`, `corollarybox`,
`definitionbox`, or `axiombox`.

Use `restatementbox` in note files for theorem-shaped reminders or teaching
restatements that help the reader recognize an already governed result. A
`restatementbox` is not a theorem-like artifact: it does not carry a formal
label, does not create a proof obligation, does not satisfy dependencies, and
does not replace the governed statement.

Use `derivationbox` in note files for pedagogical calculations, heuristic
derivations, worked transformations, and proof-like teaching passages that do
not assert a new formal result. A `derivationbox` is not a proof file and not a
formal statement container. It must not contain `proof`, formal theorem-like
environments, formal statement boxes, formal labels, or proof-vault navigation.

Canonical proofs remain in the owning `proofs/**/prf-*.tex` files. Note-side
derivations may prepare or explain a proof idea, but they do not replace the
professional and detailed learning proof layers required by the proof-file
standard.

## Scope

Use this standard for standardized surrounding blocks attached to:

- definitions;
- axioms;
- theorems;
- lemmas;
- propositions;
- corollaries;
- vocabulary definitions when applicable;
- structural definitions when applicable.

This standard does not decide whether an artifact requires each block. The
artifact-specific standard decides that. This document standardizes the shape,
meaning, and order of blocks once they are required or intentionally included.

## Decoration Blocks

The standardized decoration blocks are:

- Standard quantified statement;
- Predicate reading;
- Negated quantified statement;
- Negation predicate reading;
- Failure modes;
- Contrapositive quantified statement;
- Contrapositive predicate reading;
- Interpretation;
- Notation;
- Historical note;
- Source comparison;
- Source variant metadata;
- Exposition;
- Examples;
- Non-Examples;
- Dependencies;
- Proof navigation link.

Artifact-specific standards may omit blocks that are not meaningful for that
artifact type.

## Ordering Rule

When a block is present, use this order:

1. Formal environment and label
2. Proof navigation link, when required inside the formal environment
3. Standard quantified statement
4. Predicate reading
5. Negated quantified statement
6. Negation predicate reading
7. Failure modes
8. Contrapositive quantified statement
9. Contrapositive predicate reading
10. Interpretation
11. Notation
12. Historical note or Source comparison
13. `\SourceVariantOf`, when the artifact is a source variant
14. Exposition
15. Examples
16. Non-Examples
17. Dependencies or `\NoLocalDependencies`

Do not reorder blocks for aesthetics. Omit only blocks that the governing
artifact standard does not require.

## Cardinality Rule

For each formal artifact, use at most one block of each canonical support type.
For example, do not attach two `Interpretation` blocks to the same definition,
theorem, lemma, proposition, corollary, or axiom. Merge duplicate content into
the single canonical block.

`Failure modes`, `Exposition`, `Examples`, and `Non-Examples` may repeat when
the surrounding artifact genuinely needs multiple source-supported failure,
explanatory, or boundary blocks. They still follow the ordering rule above.

## Canonical Statement Skeleton

Three sources govern a statement artifact, and the decoration audit in
`tools/governance/validate_volume.py` enforces them:

- **Order** of blocks: the Ordering Rule above (this document).
- **Which blocks are required vs conditional per artifact type**:
  `constitution/schema/artifact-matrix.yaml` (R / C / D / N for
  def / thm / lem / prop / cor / ax).
- **Block identity, exact titles, and trigger conditions**:
  `constitution/schema/block-registry.yaml`.

Copy the matching skeleton below and keep the block order exactly. Each block is
annotated with its requirement level so you include only what the artifact type
and its triggers call for. Do not reorder, rename block titles, or invent
blocks. `R` = always present; `C` = only if its trigger holds; `D` = only if its
parent block is present; omit anything not triggered.

### Definition (and axiom)

A definition is wrapped in `definitionbox`; an axiom in `axiombox`. The unboxed
variant drops only the box wrapper, never the label or the required blocks.

```latex
\begin{definitionbox}{Definition (<Display Title>)}   % box: C (load-bearing def); axioms: always boxed
\begin{definition}[<Display Title>]                    % R: environment + label
\label{def:<root>}                                     % R: prefix def: (ax: for axioms)
<statement text>
\end{definition}
\end{definitionbox}

\begin{remark*}[Standard quantified statement]         % R: standard notation only, no predicate names
<formal statement>
\end{remark*}

\begin{remark*}[Predicate reading]                     % C: binder count >= 2 or useful canonical predicate
\[ \operatorname{<Name>}(<args>) \coloneqq <formula>. \]
\end{remark*}

\begin{remark*}[Negated quantified statement]          % C: the negation is a standard proof tool
<formal negation>
\end{remark*}

\begin{remark*}[Negation predicate reading]            % D: only if the negated block is present
<predicate-form negation>
\end{remark*}

\begin{remark*}[Failure modes]                         % C: named branches or witness behavior
\begin{description}
\item[Exposition.]
<general failure picture>

\item[<Mode name>.]
<mode-specific exposition>
\[
<quantified failure statement>
\]
\[
<predicate reading of failure, when predicate language exists>
\]
\end{description}
\end{remark*}

\begin{remark*}[Interpretation]                        % C, but treat as R unless nearby exposition already covers it
<prose meaning, why it matters, geometric picture>
\end{remark*}

\begin{remark*}[Notation]                              % C: notation, reading convention, or ambient convention
<notation convention introduced or fixed by the statement>
\end{remark*}

\begin{remark*}[Historical note]                       % C: known source correspondence (or "Source comparison")
<short provenance prose with \citet{...}>
\end{remark*}

\SourceVariantOf{<target-label>}{<author>}{<book-or-source>}{source_variant_of} % C: extraction-visible source variant

\begin{remark*}[Exposition]                            % C: broader conceptual framing, not a restatement
<narrative>
\end{remark*}

\begin{remark*}[Examples]                              % C: definitions only
<examples>
\end{remark*}

\begin{remark*}[Non-Examples]                          % C: definitions only; name the failed condition
<non-examples>
\end{remark*}

\begin{dependencies}                                   % R  (or \NoLocalDependencies if foundational)
\begin{itemize}
  \item \hyperref[<dep-label>]{<Readable Name>}
\end{itemize}
\end{dependencies}
```

### Theorem / lemma / proposition / corollary

Same order, with three differences: a proof-navigation link goes **inside** the
environment; there are **no** Examples / Non-Examples; and the **contrapositive**
blocks become available. Use the matching box (`theorembox`, `lemmabox`,
`propositionbox`, `corollarybox`).

```latex
\begin{theorembox}{Theorem (<Display Title>)}          % box: C (named / primary result)
\begin{theorem}[<Display Title>]                       % R: environment + label
\label{thm:<root>}                                     % R: prefix thm:/lem:/prop:/cor:
<statement text>

\smallskip
\noindent
\hyperref[prf:<root>]{\textit{Go to proof.}}           % R for thm/lem/prop/cor (N for def/ax); inside the env
\end{theorem}
\end{theorembox}

\begin{remark*}[Standard quantified statement]         % R
<formal statement>
\end{remark*}

\begin{remark*}[Predicate reading]                     % C: binder count >= 2 or useful canonical predicate
<predicate form>
\end{remark*}

\begin{remark*}[Negated quantified statement]          % C
<formal negation>
\end{remark*}

\begin{remark*}[Negation predicate reading]            % D: only if the negated block is present
<predicate-form negation>
\end{remark*}

\begin{remark*}[Failure modes]                         % C
\begin{description}
\item[Exposition.]
<general failure picture>

\item[<Mode name>.]
<mode-specific exposition>
\[
<quantified failure statement>
\]
\[
<predicate reading of failure, when predicate language exists>
\]
\end{description}
\end{remark*}

\begin{remark*}[Contrapositive quantified statement]   % C: contrapositive is a standard proof tool (thm-like only)
<formal contrapositive>
\end{remark*}

\begin{remark*}[Contrapositive predicate reading]      % D: only if the contrapositive block is present
<predicate-form contrapositive>
\end{remark*}

\begin{remark*}[Interpretation]                        % C, treat as R unless nearby exposition covers it
<prose meaning>
\end{remark*}

\begin{remark*}[Notation]                              % C: notation, reading convention, or ambient convention
<notation convention introduced or fixed by the statement>
\end{remark*}

\begin{remark*}[Historical note]                       % C: known source correspondence
<provenance prose>
\end{remark*}

\SourceVariantOf{<target-label>}{<author>}{<book-or-source>}{source_variant_of} % C: extraction-visible source variant

\begin{remark*}[Exposition]                            % C
<narrative>
\end{remark*}

\begin{dependencies}                                   % R
\begin{itemize}
  \item \hyperref[<dep-label>]{<Readable Name>}
\end{itemize}
\end{dependencies}
```

Real, validator-passing references: the definition skeleton matches
`def:upper-bound` / `def:supremum`, and the theorem skeleton matches
`thm:lub-property-implies-existence-of-suprema`, in
`volume-iii/analysis/bounding/notes/bounds-extremals/notes-supremum.tex`.

Easy-to-get-wrong points:

- The predicate-reading title is always `Predicate reading`.
- The proof link is `\hyperref[prf:<root>]{\textit{Go to proof.}}`, placed inside
  the environment body before `\end{...}`, and only for thm/lem/prop/cor — never
  definitions or axioms.
- Contrapositive blocks are theorem-like only; definitions and axioms never get
  them (no hypothesis–conclusion structure).
- Predicate names use `\operatorname{...}`. Do not invent a predicate to fill the
  block; if none is canonical, omit the predicate reading and (if one clearly
  deserves to exist) flag a missing-predicate audit entry.
- `dependencies` is the shared environment; use `\NoLocalDependencies` (a silent
  marker that renders nothing) for foundational items with nothing local to
  list.

### Print / digital handling

The `dependencies` environment is already print-aware: it renders in the digital
edition and silently swallows its body in the print edition, so it is never
wrapped by hand. `workedexample` is likewise digital-only by construction.

In the current corpus (verified in Volume II and the decorated Volume III), the
decoration `remark*` blocks above are **not** wrapped in
`\LRAExcludeFromPrintEditionBegin … \LRAExcludeFromPrintEditionEnd`; they render
in both editions. Whether these supplemental blocks should become digital-only
is an open policy decision, not yet reflected in the corpus or this skeleton.

## Standard Quantified Statement

Use a `remark*` block titled `Standard quantified statement`.

The block contains standard mathematical notation only. Do not use canonical
predicate names or extraction predicate forms here.

Preserve all hypotheses and ambient variables. For structured objects, state
the ambient setting explicitly rather than using malformed quantified syntax.

The standard quantified statement belongs to one formal object. If a proposed
definition or theorem needs separate quantified statements for separate
predicates, split the formal statement before writing support blocks. The
support blocks are not a place to choose one item from a multi-definition box;
the formal box itself must already be atomic.

## Predicate Readings

Use `Predicate reading` for definitions and theorem-like environments.

Predicate reading is required when the Standard quantified statement contains
at least two quantified variable binders. Count comma-separated binders
separately: `\forall x,y` counts as two; `\forall x,y,z` counts as three;
`\forall x,y,z\in A` counts as three; and
`\forall y\in B\,\exists x\in A` counts as two.

Predicate readings must use canonical predicate names when they exist. If no
canonical predicate exists, do not invent one merely to fill the block.

Use `\operatorname{...}` predicate notation unless a shared macro is explicitly
defined.

`Predicate reading`, `Negation predicate reading`, and `Contrapositive
predicate reading` blocks must contain at least one displayed formula. A prose
sentence may explain the display, but prose alone is not a predicate reading.

Predicate signatures and ambient-structure arguments are governed by
`predicate-standards.md`. When a concept depends on a surrounding structure,
pass the whole ambient object as a predicate argument, for example
`\operatorname{CauchySequence}(x_n,M)` for a metric space `M=(X,d)`, and unpack
the carrier or metric only inside the reading formula.

Vocabulary definitions and structural definitions normally omit predicate
readings unless the predicate is canonical and useful.

## Negation Blocks

Negated quantified statements and negation predicate readings are proof-use
blocks. Include them when the negated form is a standard proof tool or when the
artifact-specific standard requires them.

Negation support is attached to the positive support packet. A negated
quantified statement requires the corresponding `Negation predicate reading`,
and the pair requires a preceding `Standard quantified statement`.

Push negations inward and preserve the same ambient hypotheses and free
variables as the positive statement.

Do not include negation blocks merely because a formal negation can be written.

## Failure Modes

Use failure-mode blocks when a definition or result has meaningful ways to
fail and the distinction helps later reasoning.

Failure modes use one structured block with a `description` environment. The
first item is `\item[Exposition.]` and gives the general failure picture. Each
following item names one failure mode and contains mode-specific exposition, a
quantified failure display, and a predicate reading of the failure when
predicate language exists.

Failure-mode item labels name the failing predicate, structure constructor, or
canonical formal condition. Use labels such as
`\item[\(\operatorname{UpperBound}(u,A,P)\).]`,
`\item[\(\operatorname{IsCompact}(K,\mathbb{R})\).]`, or
`\item[\(\mathsf{OrderedSet}(S,\leq)\).]`. Do not use generic labels such as
`Displayed failure`, `Mechanism`, `Case`, `Negation`, `Contrapositive`,
`Condition fails`, or `Conclusion fails` as final failure-mode labels.

When negation or contrapositive predicate readings are present, each
non-exposition failure mode records both levels: the quantified failure display
and the matching predicate-reading display. The exposition item gives the
overall failure landscape; the subsequent items itemize the concrete predicate
or structure failures.

Do not use failure-mode blocks as informal interpretation. If the goal is to
explain meaning, use `Interpretation`.

## Contrapositive Blocks

Contrapositive blocks apply only to theorem-like environments with a genuine
hypothesis-conclusion structure.

Do not generate contrapositive blocks for definitions or axioms.

Include contrapositives only when they are standard proof tools for the result,
not merely because they can be formed mechanically.

A contrapositive quantified statement requires the corresponding
`Contrapositive predicate reading`, and the pair requires the positive
`Standard quantified statement`.

## Interpretation

Use a `remark*` block titled `Interpretation`.

Interpretation is prose only. It explains mathematical meaning, structural
role, standard failure picture, and local significance.

Interpretation blocks remain encouraged across artifact types, including
vocabulary and structural definitions.

## Notation

Use a `remark*` block titled `Notation`.

Notation blocks record symbols, reading conventions, and ambient conventions
introduced or fixed by the owning artifact. Use `Notation` for information such
as ``\(E^\circ\) is read as the interior of \(E\)'' or ``\(E^c\) denotes the
complement in the fixed ambient space \(X\).''

Notation is explanatory metadata, not a second formal definition. It appears
after `Interpretation` and before source crosswalk blocks. If a symbol is the
formal object being defined, keep the formal definition in the statement and
use `Notation` only for reading or ambient-use conventions.

## Exposition

Use a `remark*` block titled `Exposition`.

Exposition is broader mathematical narrative: motivation, intuition,
conceptual framing, structural commentary, historical or methodological
context, and relationships to nearby topics. It is not a formal definition,
theorem, predicate reading, or dependency list.

Use `Interpretation` when translating one specific formal item into ordinary
mathematical language. Use predicate-reading blocks when unpacking logical
form. Use `Exposition` for topic-level explanation or broader conceptual
framing.

Exposition blocks use the normal unboxed `remark*` style. They are
extractable explanatory metadata attached to the nearest relevant formal item
or section; they do not create separate knowledge-graph nodes by default.

Do not confuse `remark*` titled `Exposition` with the topic-level
`exposition` environment used inside topic boxes.

## Source Crosswalks

Use `Historical note` for direct provenance and `Source comparison` for
structural comparison with a cited source presentation.

Source crosswalks appear after Interpretation and before Exposition,
Examples, Non-Examples, and Dependencies. They
must not appear inside formal environments, quantified statements, predicate
readings, negation blocks, or failure-mode decompositions.

`Source comparison` blocks use a generic title so the comparison target can be
Peano, Dedekind, Landau, Tao, Feferman, or any other cited source without
creating one-off block titles. Name the source in the prose body and end the
block with a natbib-compatible citation command such as
`\citet{DedekindContinuityIrrationalNumbers}` or
`\citep{TaoAnalysisI}`.

Use `\SourceVariantOf{<target-label>}{<author>}{<book-or-source>}{<kind>}` when
the source crosswalk must be extraction-visible. The macro renders nothing in
the PDF and must appear after Historical note / Source comparison and before
Exposition, Examples, Non-Examples, and Dependencies. Allowed `<kind>` values
are `source_variant_of` and `reduces_to`.

## Examples And Non-Examples

Definitions may include optional concept-boundary blocks titled `Examples` and
`Non-Examples`.

Include them when they materially improve recognition of what the definition
does and does not cover. They are especially useful for major algebraic
structures, subtle predicates, and frequently confused pairs of concepts.

Non-examples should identify the failed axiom, condition, or hypothesis
whenever practical. These blocks are explanatory metadata attached to the
owning definition; they do not create separate knowledge-graph nodes.

## Dependencies

Dependency blocks are governed by `dependency-standards.md`. This standard
only fixes their position in the decoration order.

Use the shared `dependencies` environment for visible dependency blocks and
`\NoLocalDependencies` for foundational local note-body statements with no
local dependencies to display.

## Audit Boundary

Decoration audits check whether required blocks are present, ordered, and
well-formed. They do not decide mathematical correctness.

Auditors must apply the artifact-specific standard first. For example,
Vocabulary Definitions and Structural Definitions should not be flagged merely
because predicate-oriented blocks were omitted under their governing standard.
