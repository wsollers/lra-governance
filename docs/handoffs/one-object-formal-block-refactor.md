# Handoff: One-Object Formal Block Refactor Across LRA Volumes

Continue the current governance and volume-cleanup process exactly. The working
workspace is `F:\repos`, with sibling repos:

- `lra-governance`
- `lra-common`
- `lra-volume-i` through `lra-volume-viii`

Always start from the target repository, read its local `AGENTS.md` and
`README.md`, and run commands from that repository. Do not build volume repos
with raw `latexmk`; use the repo-local governance validation/build commands.

This handoff reflects the process captured in
`F:\repos\lra-volume-ii\summary.md`. The work should continue in small,
reviewable chunks, preferably using plan mode or a fresh context per chunk
when possible. Do not try to mechanically clear a whole volume by inserting
generic validator scaffolding.

## Current Intent

We are standardizing formal mathematical content so each formal environment
contains exactly one primary predicate-level mathematical sentence.

The rule applies to:

- `definition`
- `axiom`
- `theorem`
- `lemma`
- `proposition`
- `corollary`

Each such environment should have:

- one formal label,
- one governing `remark* [Standard quantified statement]`,
- one real `remark* [Predicate reading]` when required by the current
  predicate-reading rules,
- one atomic concept or assertion,
- support blocks that describe that same object only.

Do not bundle independently nameable concepts in one formal box. Examples that
must be split:

- bounded above, bounded below, bounded,
- comparable and incomparable,
- chain and antichain,
- minimum and maximum,
- upper bound and lower bound,
- monotone and antitone,
- injective and surjective.

Compound predicates are allowed only as their own separate formal statement
after the atomic predicates have been defined.

Support blocks must contain real mathematical content for the formal object.
Never insert placeholder text such as:

- "The displayed statement is the standard quantified statement for this formal
  item."
- "This is the predicate-level reading of the displayed quantified statement."
- "This formal item records the assertion stated in the displayed block."

If the correct quantified statement or predicate reading is not clear, stop and
classify the item for discussion instead of adding a generic box.

## Required Workflow Shape

Prefer this chunked process, especially when a volume has many errors:

1. Start a clean chunk in the target repo.
2. Read local `AGENTS.md` and `README.md`.
3. Check `git status`.
4. Run the validator and save JSON output.
5. Summarize the error counts by code.
6. Before editing mathematical content in a volume, first run or inspect the
   operator metadata validator output and triage every
   `unregistered_operatorname` error. Classify each name as existing canonical
   vocabulary, ordinary mathematical notation/function to register in
   `notation.yaml`, stale/legacy vocabulary to rewrite, or genuinely new
   vocabulary to propose. Do this before the volume-wide vocabulary discovery
   so discovery is not polluted by ordinary functions, capitalization drift, or
   legacy aliases. The July 2026 retroactive check found this debt in earlier
   volumes: Volume I had 624 unregistered operator-name errors across 159
   unique names, and Volume II had 464 across 172 unique names.
7. Before editing mathematical content in a volume, run the vocabulary
   discovery phase across the entire target volume. The volume-wide sweep must
   happen before selecting the first repair scope so repeated predicates,
   structures, relations, operations, notation, and variable conventions are
   visible up front.
8. Present proposed new or standardized vocabulary for approval.
9. Wait for approval before adding or relying on new predicates, structures,
   relations, or notation.
10. After the volume-wide vocabulary inventory is approved, select a small
   coherent repair batch, such as one topic file, one section, or one
   repeated error pattern.
11. Inspect each affected formal block and classify the needed action before
   editing.
12. If new canonical predicates, structures, notation, or relations appear
   necessary during the batch, pause and return to the vocabulary approval step.
13. Make the smallest content-preserving edits for that batch.
14. Run `git diff --check`.
15. Rerun the volume validator.
16. Summarize the batch:
    - files changed,
    - formal objects split,
    - labels removed or preserved,
    - references updated,
    - new vocabulary proposed or added,
    - validation result.

After each major step or batch, provide a short summary and the validation
result before proceeding. Do not hide broad mechanical changes inside a single
large pass.

## Vocabulary Discovery And Approval

Do this before fixing a new volume. For each volume, sweep the entire volume
first, before choosing the first repair batch. Additional book-, section-, or
error-family discovery may still be done later when a local pattern is unclear,
but it does not replace the initial volume-wide sweep. The goal is to get the
vocabulary down first, then refactor formal blocks against approved
vocabulary.

1. Inventory the relevant formal objects from the selected scope:
   definitions, axioms, theorems, lemmas, propositions, and corollaries.
2. Extract the mathematical predicates, structures, relations, operations,
   notation symbols, and recurring variables implied by those objects.
3. Compare the extracted vocabulary against:
   - `predicates.yaml`
   - `structures.yaml`
   - `relations.yaml`
   - `notation.yaml`
4. Produce an approval list with these categories:
   - existing vocabulary to reuse,
   - proposed new predicates,
   - proposed new structures,
   - proposed new relations,
   - proposed new notation,
   - proposed standard variable conventions,
   - ambiguous cases requiring user direction.
5. For every proposed item, include:
   - intended name,
   - arity and argument order,
   - structure-style argument form,
   - one example predicate reading,
   - source formal objects that need it.
6. Ask for approval before editing canonical YAML or using the new vocabulary
   throughout the volume.

An explicit user response such as "Proceed" after proposed vocabulary entries
counts as approval for that proposed batch, unless the user objects, changes
direction, or asks for clarification.

Do not proceed by inventing local one-off predicate readings. If the vocabulary
is not already canonical and is needed repeatedly, propose it first. If a
predicate reading can be expressed using existing vocabulary, prefer reuse.

Use this compact approval format:

```text
Existing vocabulary to reuse:
- P = OrderedSet(A, \leq); UpperBound(u, S, P)

Proposed predicates:
- BoundedAbove(S, P)
  Arity: 2
  Reading: S is bounded above in the ordered set (A, \leq).
  Needed by: def:bounded-above, thm:...

Proposed structures:
- OrderedSet(A, \leq)
  Fields: carrier A, order relation \leq
  Needed by: order and bound predicate readings.

Questions:
- Should "bounded" be a compound predicate after BoundedAbove and
  BoundedBelow, or should it remain only exposition?
```

### Algebraic Vocabulary Proposal Guidelines

Use these rules when proposing algebraic predicates and structures during a
volume-wide vocabulary sweep:

- Structure constructors package the carrier, operations, constants, and any
  inherited structure data. Predicates assert that the packaged data satisfies
  the relevant laws.
- Do not suffix algebraic structure constructors with `Structure`. Use the
  mathematical name directly, such as `Magma`, `Monoid`, `Ring`, `Field`,
  `OrderedField`, and `CompleteOrderedField`.
- Stronger algebraic structures should be constructed compositionally, in the
  Lean style, from weaker structures plus additional law predicates. For
  example, propose
  `CommutativeMonoid(Monoid(Semigroup(Magma(A,\star)),e))`, not a flat
  unrelated constructor.
- Pair each algebraic constructor with an `Is...` predicate when the text needs
  to assert that the structure satisfies its laws. For example,
  `Monoid(...)` packages data and `IsMonoid(Monoid(...))` is the truth-valued
  assertion.
- Quotient is a structure constructor. Use `Quotient(A,\sim)` to package a
  carrier and equivalence relation before asserting quotient-set,
  quotient-operation, or representative-independence properties.
- Identity and inverse predicates must include the governing operation and
  carrier. Prefer `LeftIdentity(e,A,\star)`,
  `RightIdentity(e,A,\star)`, `Identity(e,A,\star)`,
  `LeftInverse(y,x,e,A,\star)`, `RightInverse(y,x,e,A,\star)`,
  and `Inverse(y,x,e,A,\star)` over operation-free forms.
- Prefer additive and multiplicative readings as specializations of the
  operation-explicit predicates, such as `Identity(0,A,+)` and
  `Inverse(y,x,1,A,\cdot)`, unless the volume needs a separately named
  additive or multiplicative concept.
- Well-definedness proposals must distinguish existence, uniqueness, closure,
  and representative independence when those are mathematically separate. Do
  not hide uniqueness inside a vague `WellDefined` predicate when a relation,
  quotient operation, recursive definition, or case split must produce a unique
  value.

## Error-Fixing Policy

Treat these as real errors to fix with real content or structure changes:

- `formal_reading_missing`
- `missing_interpretation`
- `missing_dependencies`
- `unknown_decoration_block`
- `plain_remark_or_example`
- `top_level_prose`
- `unexpected_top_level_environment`
- `invalid_formal_label_count`

`topicbox_or_exposition_in_proof` may remain warning-level in governance, but
proof files still must not be used for exposition or newly written proofs.

Do not fix missing support blocks by adding empty, generic, or tautological
boxes. A missing block means the mathematical object needs a real standard
quantified statement, predicate reading, interpretation, or dependency
declaration.

## Predicate And Structure Readings

Use the canonical vocabulary in `lra-governance`:

- `predicates.yaml`
- `structures.yaml`
- `relations.yaml`
- `notation.yaml`

Do not invent predicate, structure, relation, notation, label, or dependency
names silently. If the current formal object needs vocabulary that does not
exist, propose it first.

Predicate readings should use structure-style arguments where this makes the
reading clearer. Assign the structure object first, then pass that ambient
object to the predicate. For example, prefer:

```tex
\begin{aligned}
&P=\mathsf{OrderedSet}(A,\leq),\\
&\operatorname{UpperBound}(u,S,P).
\end{aligned}
```

over either inline structure constructors or flat, unexplained argument lists
such as:

```tex
\operatorname{UpperBound}(u,S,\mathsf{OrderedSet}(A,\leq))
\operatorname{UpperBound}(u,S,A,\leq)
```

Make structure assignments explicit enough that a later reader or the knowledge
explorer can recover the intended domains and relations.

When standardizing variable conventions, prefer readable mathematical names
already used in the local text. Examples:

- sets: `A`, `B`, `S`, `T`
- elements or bounds: `a`, `b`, `x`, `y`, `u`, `\ell`
- functions: `f`, `g`, with domain/codomain structures explicit when needed
- sequences: use the local sequence notation, such as `(s_n)` or `S`, and
  record the convention in the vocabulary proposal when it matters.

## Governance Changes Already Made Locally

In `lra-governance`, the current local changes include:

- `tools/governance/validators/dependency_graphs.py`
  - `invalid_formal_label_count` is promoted to error.
  - Other dependency graph issues remain warnings.
- `tools/governance/dependency_graph.py`
  - Euclid Book I legacy aliases are normalized:
    `thm:euclid-i-N` plus `prop:I.N` is treated as the canonical
    `thm:euclid-i-N` node.
- `tools/governance/validators/labels.py`
  - `prop:I.N` weak-label warnings are suppressed only for the Euclid Book I
    construction propositions file.
- `docs/governance/authoring-standards.md`
  - Documents the one-object rule.
  - Documents the narrow Euclid legacy exception.
- `docs/governance/decoration-box-standards.md`
  - Clarifies that standard quantified statements belong to one formal object.

The Euclid exception is intentionally narrow. Do not remove or rewrite Euclid
historical labels such as `prop:I.1`.

## Volume I Current Status

Volume I has already been refactored for the first set of one-object failures.
Do not re-remove the Euclid aliases.

Files changed in `lra-volume-i`:

- `volume-i/book-sets/orderings/notes/order/notes-order.tex`
  - split `Order-Structure Synonyms` into separate `Poset`, `Toset`,
    `Loset`, and `Woset` definitions;
  - split `Comparable and Incomparable Elements`;
  - split `Upper and Lower Bounds`;
  - removed unused duplicate alias labels such as `def:min-max`,
    `def:least-greatest`, `def:order-pres`, `def:order-iso`,
    `def:well-order`;
  - split `Chain and Antichain`;
  - updated local dependencies to target the separated objects.
- `volume-i/book-sets/orderings/notes/order/index.tex`
  - updated upper/lower bound links to `def:upper-bound` and
    `def:lower-bound`.
- `volume-i/book-sets/orderings/notes/order/notes-order-sup-inf.tex`
  - updated old `def:bounds` links/dependencies.
- `volume-i/book-sets/orderings/notes/order/notes-order-extensions.tex`
  - updated old `def:bounds` dependency.

Validation after the Euclid skip:

```powershell
python ..\lra-governance\tools\governance\validate_volume.py . --json build\volume-i-one-object-rule-euclid-skip-labels.json --preprocess-dir build\preprocess-volume-i-one-object-rule-euclid-skip-labels
```

Result:

```text
310 issue(s) [0 error, 310 warning, 0 review]
```

Repo-local validation also passes:

```powershell
$env:TEMP='F:\repos\lra-volume-i\build\tmp'
$env:TMP='F:\repos\lra-volume-i\build\tmp'
python ..\lra-governance\scripts\build_volume.py --root . --validate-only
```

Result:

```text
310 issue(s) [0 error, 310 warning, 0 review]
```

If `TEMP`/`TMP` are not redirected, the sandbox may deny access to
`C:\Users\wsoll\AppData\Local\Temp`.

## Proof Rule

Proofs are never written by AI.

If any proof file is touched or generated, proof bodies must remain stubs only,
using the existing local stub shape. Acceptable proof body content is TODO-style
stub text after `\LRAProofBodyStart`. Do not fill in mathematical proof
arguments.

Before finishing a volume, inspect any proof files touched during that volume.

## Process For Each Volume

Process volumes in order:

1. `lra-volume-i`
2. `lra-volume-ii`
3. `lra-volume-iii`
4. `lra-volume-iv`
5. `lra-volume-v`
6. `lra-volume-vi`
7. `lra-volume-vii`
8. `lra-volume-viii`

For each volume:

1. Change to the volume repo.
2. Read `AGENTS.md` and `README.md`.
3. Check git status.
4. Run the updated validator and collect errors:

   ```powershell
   python ..\lra-governance\tools\governance\validate_volume.py . --json build\one-object-rule.json --preprocess-dir build\preprocess-one-object-rule
   ```

5. Summarize all current error counts by error code.
6. Before the full-volume vocabulary discovery, triage all
   `unregistered_operatorname` validator errors. Map each operator name to
   existing metadata, ordinary notation/function metadata, stale legacy
   vocabulary to rewrite, or unknown/new vocabulary requiring approval. This
   pre-discovery cleanup is required because the retroactive operator metadata
   validator found substantial debt in Volume I and Volume II after they had
   previously reached 0 hard errors.
7. Run a full-volume vocabulary discovery and approval phase before choosing
   the first repair scope:
   - inventory every formal object in the volume;
   - extract candidate predicates, structures, relations, operations,
     notation, and recurring variable conventions;
   - compare them with the canonical governance YAML;
   - present existing vocabulary to reuse, proposed additions, and questions.
8. Do not edit mathematical content until the volume-wide vocabulary is
   approved or the user explicitly says to proceed using only existing
   vocabulary.
9. Choose the first small repair scope.
10. Identify `invalid_formal_label_count` errors and any related support-block
   errors in the same files.
11. For each error, decide whether it is:
   - a true multi-object formal statement to split,
   - a duplicate/alias label to remove,
   - a legitimate historical alias requiring a narrow governance skip,
   - a missing real support block for an otherwise valid one-object formal,
   - malformed prose or decoration that needs to be moved into a canonical
     block with real content.
12. Prefer splitting true multi-object boxes into separate formal boxes.
13. Preserve existing labels when they are referenced; update references only
    when a combined label is removed.
14. Do not invent predicates if an existing canonical predicate or structure
    exists. Check `predicates.yaml`, `structures.yaml`, `relations.yaml`, and
    `notation.yaml` in `lra-governance` when needed.
15. Use structure-style readings where appropriate, for example:

    ```tex
    \operatorname{UpperBound}(u,S,\mathsf{OrderedSet}(A,\leq))
    ```

16. Ensure each new or repaired formal object has proper support blocks with
    real mathematical content:
    - `remark* [Standard quantified statement]`
    - `remark* [Predicate reading]` when required by the current rules
    - `remark* [Interpretation]`
    - local `dependencies` or `\NoLocalDependencies`
17. Keep exposition in allowed blocks only.
18. Run `git diff --check`.
19. Run volume validation again.
20. Run the repo-local validation command from that volume's `README.md`.
21. Summarize:
    - files changed,
    - formal objects split,
    - labels removed or preserved,
    - references updated,
    - validation result.

Do not commit unless explicitly asked.

## Expected Validation Goal

The immediate goal is:

```text
0 error
```

Warnings may remain unless they are directly caused by this refactor. Do not
expand scope into unrelated warning cleanup without user approval.

Repo-local PDF builds are a separate checkpoint. Use the build commands from
the target volume's `README.md`, normally the governance Docker builder for
digital and print editions. A successful build may still report LaTeX warnings
such as overfull boxes, tcolorbox page-break warnings, multiply defined
citations, or print-edition unresolved proof-reference warnings. Treat those as
warnings unless the command exits nonzero or the user explicitly asks for layout
or reference cleanup.

## Decoration And Failure-Mode Details

When adding or repairing support blocks, preserve the canonical decoration
order exactly:

1. formal environment and label;
2. proof navigation link, inside theorem-like environments when required;
3. `remark* [Standard quantified statement]`;
4. `remark* [Predicate reading]`;
5. `remark* [Negated quantified statement]`;
6. `remark* [Negation predicate reading]`;
7. `remark* [Failure modes]`;
8. `remark* [Contrapositive quantified statement]`;
9. `remark* [Contrapositive predicate reading]`;
10. `remark* [Interpretation]`;
11. `remark* [Notation]`;
12. source/provenance blocks such as `Historical note`;
13. `remark* [Exposition]`;
14. `remark* [Examples]`;
15. `remark* [Non-Examples]`;
16. `dependencies` or `\NoLocalDependencies`.

Dependencies come last. Do not place an interpretation, notation, exposition,
example, or non-example block after a dependency block.

Failure-mode blocks must use the validator shape:

```tex
\begin{remark*}[Failure modes]
\begin{description}
  \item[Exposition.]
  <general failure picture>

  \item[<Mode name>.]
  <mode-specific explanation>
  \[
  <quantified failure statement>
  \]
  \[
  <predicate-style failure statement, when predicate language exists>
  \]
\end{description}
\end{remark*}
```

If the owning object has a predicate reading, each non-exposition failure mode
needs both a quantified display and a predicate-style display. Do not use a
failure-mode block as a renamed interpretation block.

## Important Cautions

- Do not adjust Euclid content to satisfy the one-object rule. Use the existing
  narrow skip.
- Do not write proofs.
- Do not collapse multiple predicates into one standard quantified statement.
- Do not add placeholder quantified statements, predicate readings, or
  interpretations.
- Do not mechanically rename noncanonical decoration titles if the underlying
  content should instead be split, rewritten, or classified.
- Do not place top-level prose outside allowed environments.
- Do not use plain `remark` or `example`; use starred forms according to
  governance.
- Do not add broad validator exemptions. Any skip must be file- and
  pattern-specific, with a documented reason.
- Do not modify generated downstream `AGENTS.md` files.
- Do not touch unrelated dirty work in any repo.

## Volume II Current Status

Volume II has been brought to the immediate governance target:

```text
validate volume: F:\repos\lra-volume-ii\volume-ii: 625 issue(s) [0 error, 625 warning, 0 review]
```

Both digital and print PDF builds completed successfully through the governance
Docker builder:

```powershell
python ..\lra-governance\tools\governance\build_volume_docker.py --root . --common-root ..\lra-common --output-dir build\digital
python ..\lra-governance\tools\governance\build_volume_docker.py --root . --common-root ..\lra-common --print-edition --output-dir build\print
```

Generated PDFs:

- `build\digital\volume-ii.pdf`
- `build\digital\volume-ii-discrete-number-systems.pdf`
- `build\digital\volume-ii-the-continuum.pdf`
- `build\print\volume-ii.pdf`
- `build\print\volume-ii-discrete-number-systems.pdf`
- `build\print\volume-ii-the-continuum.pdf`

Do not redo Volume II hard-error cleanup unless new errors appear after later
governance changes. The remaining Volume II items are warning-level cleanup.

## Current Useful Commands

From `lra-governance`:

```powershell
python -m py_compile tools\governance\dependency_graph.py tools\governance\validators\dependency_graphs.py tools\governance\validators\labels.py
git diff --check -- docs\governance\authoring-standards.md docs\governance\decoration-box-standards.md tools\governance\dependency_graph.py tools\governance\validators\dependency_graphs.py tools\governance\validators\labels.py
```

From a volume repo:

```powershell
python ..\lra-governance\tools\governance\validate_volume.py . --json build\one-object-rule.json --preprocess-dir build\preprocess-one-object-rule
$env:TEMP='<volume-repo>\build\tmp'
$env:TMP='<volume-repo>\build\tmp'
python ..\lra-governance\scripts\build_volume.py --root . --validate-only
git diff --check
```

Use PowerShell paths appropriate to the current volume, for example
`F:\repos\lra-volume-ii\build\tmp`.
