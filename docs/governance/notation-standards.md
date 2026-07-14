# Notation Standards

## Layer-Gated Notation

Before editing or generating a formal block, classify its role. Definition,
theorem, lemma, proposition, corollary, axiom bodies, and ordinary quantified
statements use standard mathematical notation. Predicate names are reserved for
approved predicate-reading layers and related analysis layers.

Predicate names, signatures, and ambient-structure conventions are governed by
`predicate-standards.md`. This notation standard governs mathematical symbols
and house normalization rules.

## No Predicate Leakage

Canonical predicate names must not appear in formal statement bodies. This
applies to boxed and unboxed `definition`, `axiom`, `theorem`, `lemma`,
`proposition`, and `corollary` environments. Formal statement bodies must use
ordinary mathematical notation and prose such as "is injective", "is bounded",
or an explicit displayed formula.

Predicate-style operator notation from the canonical notation registry is also
barred from formal statement bodies when it functions as predicate vocabulary,
for example UpperCamel names such as `\operatorname{AtPointOp}`. Predicate
language belongs in `Predicate reading`, `Negation predicate reading`,
`Contrapositive predicate reading`, and predicate-form failure displays.

The integrated volume validator enforces this as
`predicate_operator_in_formal_statement`. Do not work around the validator by
renaming a predicate locally or moving predicate language into a formal theorem
statement. Rewrite the formal statement in ordinary mathematical notation and
place the extraction-oriented predicate form in the appropriate support block.

## Canonical Sources

The source-of-truth files live in `lra-governance`:

- `predicates.yaml`
- `structures.yaml`
- `notation.yaml`
- `relations.yaml`

They are not duplicated into volume repos and should be treated as read-only by
automated authoring processes unless the task is specifically to update the
canonical YAML source.

## Notation Templates

Notation entries may include an optional `template` field when a symbol is a
family of expressions rather than a single fixed token. The `symbol` field gives
the representative house form; the `template` field gives the TeX pattern with
angle-bracket placeholders for substitutable parts.

For example:

```yaml
symbol: 'I_r(c)'
template: 'I_{<radius>}(<center>)'
```

The template records notation shape only. It does not assert the mathematical
object exists, expand the notation, or replace the corresponding structure and
predicate entries in `structures.yaml` and `predicates.yaml`.

## Standard Notation Normalizations

Preserve mathematical meaning; normalize mathematical notation.

When source text, OCR text, or image-derived mathematical content is converted
into LRA-ready candidate LaTeX, rewrite common source/OCR notation into house
LaTeX unless the task explicitly requests source-faithful transcription.

| Source or OCR form                                                 | House LaTeX form                                           |
| ------------------------------------------------------------------ | ---------------------------------------------------------- |
| `R`, `Real`, `reals` when meaning the real numbers                 | `\mathbb{R}`                                               |
| `N`, `Z`, `Q` when meaning standard number systems                 | `\mathbb{N}`, `\mathbb{Z}`, `\mathbb{Q}`                   |
| `I(R)`, `I\((R)\)`, interval family over `R`                       | `\mathcal{I}(\mathbb{R})`                                  |
| `in` when used as membership                                       | `\in`                                                      |
| `notin`, `not in`, `∉`                                             | `\notin`                                                   |
| `subset`, `subseteq`, `⊆`                                          | `\subseteq`                                                |
| `proper subset`, `⊂` when source clearly means proper subset       | `\subsetneq`                                               |
| `forall`, `for all`, `∀`                                           | `\forall`                                                  |
| `exists`, `there exists`, `∃`                                      | `\exists`                                                  |
| `=>`, `implies`, `⇒`                                               | `\Rightarrow`                                              |
| `<=>`, `iff`, `⇔`                                                  | `\Longleftrightarrow`                                      |
| `*` used as multiplication                                         | `\cdot`                                                    |
| juxtaposed interval products such as `AB` when clarity requires it | `A\cdot B`                                                 |
| `A(B+C)`                                                           | `A\cdot(B+C)` when multiplication clarity is needed        |
| `t in R`                                                           | `t\in\mathbb{R}`                                           |
| `0 in B`                                                           | `0\in B`                                                   |
| `0 notin B`, `0 ∉ B`                                               | `0\notin B`                                                |
| `inf`, `sup` as operators                                          | `\inf`, `\sup`                                             |
| `min`, `max` as operators                                          | `\min`, `\max`                                             |
| `epsilon`, `eps`, `ε`                                              | `\varepsilon` unless source convention requires `\epsilon` |
| `delta`, `δ`                                                       | `\delta`                                                   |
| `bar a`, `a_bar`, upper endpoint of interval                       | `\overline a`                                              |
| `underline a`, `a_under`, lower endpoint of interval               | `\underline a`                                             |
| `[a,b]` closed interval                                            | `[a,b]`                                                    |
| `(a,b)` open interval                                              | `(a,b)`                                                    |
| `[a,b)` half-open interval                                         | `[a,b)`                                                    |
| `(a,b]` half-open interval                                         | `(a,b]`                                                    |

For interval arithmetic, use `\mathcal{I}(\mathbb{R})` for the set of bounded
closed real intervals. Use endpoint notation such as
`A=[\underline a,\overline a]` and `B=[\underline b,\overline b]`. Use
`\cdot` for interval multiplication in formal notes, explicit membership such
as `A,B\in\mathcal{I}(\mathbb{R})`, explicit conditions such as `0\notin B`,
and `\subseteq` for sub-distributivity.

Do not normalize notation when the task explicitly asks for exact
transcription, the source is introducing special notation, changing notation
would obscure a source distinction, or the notation is part of a named
convention being quoted or compared. When source notation is preserved
intentionally, add a brief review note if the notation differs from house
style.

## Missing Predicate Protocol

Do not invent predicates or structure constructors inline. Apply
`predicate-standards.md`: first check whether an existing ambient-structure
predicate can express the reading by changing the ambient argument. If not,
report the missing predicate or structure need instead of creating an ad hoc
name.
