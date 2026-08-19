# Content Generation From Source

Use this workflow whenever a source snippet of text or image is converted into
LRA-ready candidate LaTeX. This applies whether the snippet comes from a GUI,
plain chat paste, OCR, image paste, or an automated tool.

## Core Rule

Comprehend first, rewrite second, emit LaTeX third.

Do not mechanically wrap OCR fragments in LaTeX environments. Read the whole
visible mathematical passage, understand the math, rewrite it internally as a
clean mathematical note, and then generate LaTeX from that rewritten note.

## Concept Authoring Gate

For a new or materially revised concept, source extraction and implementation
begin only after a human has authored and reviewed a baseline **concept
contract**. The definition and canonical vocabulary are decisions, not search
results. Discovery may test or motivate a later reviewed revision, but it must
not silently replace the contract.

The concept contract records:

- a stable concept ID;
- the normalized definition;
- carrier and ambient-structure assumptions;
- notation and variables;
- the intended Lean signature (an authored target, not a claim that a
  declaration exists);
- learner-facing terminology;
- accepted synonyms and explicitly excluded meanings;
- the owning repository, volume/topic, or governance registry; and
- contract status and review attribution.

The contract is atomic under
`capabilities/reference/atomic-artifact-standards.md`. If definition or ownership is
still ambiguous, keep the contract in a non-approved state and stop before
candidate discovery.

### Source-grounded candidate discovery

After the baseline contract is reviewed, discover candidate material in two
separately recorded lanes:

1. **Configured primary-source profiles.** Record the profile or curated source
   list, its version or commit, the configured minimum/source-count policy when
   one applies, sources searched, queries, locations, excerpts or summaries,
   and whether the minimum was satisfied. A minimum is a coverage gate, not a
   voting rule: recurrence and disagreement still require mathematical review.
2. **External Mathlib declaration/API discovery.** Record the pinned Mathlib
   version or commit, module, declaration, signature, documentation/source
   location, query, and match assessment. Mathlib is API and formalization
   evidence; it does not overwrite the authored LRA definition or terminology.

Existing internal LRA Lean and LaTeX may be searched only as **integration
evidence**: existing identifiers, dependencies, links, placement, and
compatibility constraints. Internal LRA content is not independent
mathematical-discovery evidence and must not be counted toward a primary-source
minimum or source recurrence.

Discovery should seek mathematically useful material:

- canonical recurring theorems;
- clarifications, restrictions, and extensions that sharpen the concept;
- relationships to other concepts;
- representative examples and boundary cases;
- counterexamples that expose a genuine failed implication or excluded
  meaning; and
- pedagogically useful exercises.

Do not manufacture converse, inverse, negation, quantifier permutations, or
other formal logical variants merely for syntactic coverage. A logical variant
is a candidate only when sources, a checked external API, or a clear
pedagogical need gives it independent mathematical value.

The reusable discovery protocol is governed by the receipt schema
`constitution/schema/concept-discovery-receipt.schema.json` and the deterministic
builder `tools/governance/concept_candidate_discovery.py`. The source-index
facade `tools/governance/lra_lookup.py --candidate-discovery-config <path>` may
run the same protocol and must keep internal LRA Lean/TeX out of the discovery
lane. A discovery receipt is evidence for review; it does not approve,
materialize, or publish candidates.

Primary-source discovery starts from the configured topic, chapter, volume, or
source-list profile before raw search. Search by stable `source_id` or source
list, not by fragile author strings. By default, collect at least five
independent close primary sources. A smaller source set requires an explicit
reviewed exception in the receipt; Mathlib, internal LRA Lean, and internal LRA
LaTeX never count toward the five-source minimum.

The strict concept phrase query is exact and case-insensitive, with ordinary
whitespace and OCR line breaks normalized. The phrase may cross one physical
index line, but the phrase itself must not be loosened when formal labels are
expanded. Formal-label proximity accepts hits on the same physical index line
as, or within two lines of, one of:

- `Definition`;
- `Theorem`;
- `Lemma`;
- `Proposition`;
- `Corollary`;
- `Exercise`;
- `Example`;
- `Counterexample`.

For every accepted primary-source hit, record the source ID, source-profile or
source-list identity and revision, extraction quality, indexed-text versus
direct-PDF inspection, physical page, section, index line, raw locator or
excerpt locator, normalization notes, supported candidate IDs, and unresolved
ambiguity. Reject and record false positives where the phrase belongs to a
proof, citation, running header, unrelated nearby statement, accidental
proximity, or an alternate meaning.

When indexed extraction is empty, damaged, or ambiguous, record a direct-PDF
fallback in the receipt and inspect the visual PDF or reviewed page evidence
before accepting or rejecting the hit. If the visual fallback still cannot
certify the formal statement, keep the ambiguity unresolved rather than
inventing evidence.

Mathlib discovery is independent. Search relevant external Mathlib modules and
record the pinned Mathlib version or commit, module, exact declaration name,
exact signature and assumptions, documentation or source locator, and the
relationship to the normalized candidate. Mathlib evidence is API/formalization
evidence; it does not overwrite LRA vocabulary and does not count as a primary
source.

### Candidate records and review

Normalize candidates to the contract's vocabulary and carrier assumptions,
then deduplicate them by mathematical meaning rather than title or surface
syntax. Merging duplicate candidates must retain every evidence record,
source/API location, query, match note, and original discovered wording.

Keep immutable discovery evidence separate from mutable review decisions. An
evidence record is append-only and identifies its lane and source snapshot. A
review event identifies the reviewer, action, timestamp, rationale, and, for
an edit or move, the before/after revision or destination concept. Corrections
to discovery evidence are new superseding records; review actions never rewrite
the original evidence.

The lifecycle must represent these states and actions:

- `discovered`, `normalized`, and `proposed` for intake and review preparation;
- `approved`, `deferred`, and `rejected` as review decisions;
- `approve_with_edit` as an action that creates a reviewed revision and then
  records approval of that exact revision;
- `reassigned` (or `moved_to_related_concept`) with a destination concept ID;
- `generated`, `lean_validated`, and `publication_approved` as downstream
  states after approval.

Only a candidate with an approval event for its current normalized revision may
be used to generate or wire Lean, LaTeX, manifests, or receipts. Any later
meaning-changing edit invalidates that approval and returns the revision to
`proposed`. `generated` does not imply Lean validity, and `lean_validated` does
not imply publication approval. Publication requires the explicit
`publication_approved` decision.

A small typed YAML- or JSON-backed table or form is sufficient for the initial
interface. It need only expose the concept contract, separate evidence lanes,
normalized candidate, review history, current state, and applicable gates. Do
not make a large UI a prerequisite for this workflow, and do not create a
second concept, vocabulary, or semantic-artifact authority.

Any Python that materializes approved records must be deterministic: validate
typed input, use stable IDs and ordering, make output independent of filesystem
enumeration order and wall-clock time, and produce byte-identical output for
identical inputs and tool versions. Generation is a projection of approved
records; it must not discover, invent, approve, or silently normalize
mathematics.

### Canonical package schema and storage

The canonical successor record format is
`lra.source-grounded-concept-package/0.2`, governed by
`constitution/schema/concept-authoring-package.schema.json` and validated by
`tools/governance/validate_concept_authoring_package.py`. The schema authority
lives in `lra-governance`; concept folders in downstream volume repositories
may hold reviewed package instances, but they do not own the schema or create a
second vocabulary registry.

Use one reviewed package as the typed interchange record for Phase 1:

- concept contracts live with the owning concept folder when the target concept
  is volume-owned, with governance retaining the schema and validation rules;
- vocabulary references point to the existing LRA vocabulary, predicate,
  notation, and semantic-artifact authorities rather than copying formulas or
  creating a parallel registry;
- immutable evidence records live in the governance-owned concept-authoring
  evidence lane or a reviewed package snapshot and are append-only;
- review events live separately from evidence in mutable package/review
  history and are append-only;
- approved generation packages and receipts live with governance-owned
  generation records until downstream integration is explicitly approved;
- concept-folder records may reference governance schemas and registries, but
  the concept folder owns only the concept-specific authored contract and
  reviewed package instance;
- JSON is the initial canonical machine format. YAML may be accepted only when
  the same schema and deterministic validator are used and serialization order
  remains stable.

Schema versions are explicit. A new semantic requirement changes the package
version or adds a reviewed migration rule. Validators reject unknown fields,
duplicate stable IDs, unresolved approved contracts, stale approval, invalid
state transitions, unsorted records, and generation packages that do not name
the current approved normalized revision.

The generation package is only typed input for later deterministic generation.
It records approved candidate revisions and tool versions, uses stable
lexicographic ordering, and contains no discovery, normalization, review, or
approval behavior. A generation receipt records emitted artifact paths, hashes,
tool versions, and the originating candidate revision for each artifact. Receipt
artifacts must be deterministically ordered.

### Legacy package migration

Packages with schema `lra.lean-concept-package/0.1` remain inspectable for
pilot calibration and migration planning, but they are non-materializable.
Neither `family_status`, `publication_status`, nor `selected` is approval of a
current normalized revision. Migration must create explicit successor records:
missing contract, evidence, review, or revision facts remain `unresolved`,
`absent`, or `not_applicable` as appropriate.

Migrated candidates return to `proposed` unless reviewed evidence can represent
approval of the exact current normalized revision. Existing Upper Bound pilot
fixtures must not be promoted silently. Corrections to migrated evidence create
superseding evidence records instead of rewriting historical records.

### Relationship to formalization-first study

The source-grounded concept-authoring workflow supersedes any reading of the
formalization-first adversarial study protocol that lets internal LRA Lean own
the initial concept meaning. The approved concept contract comes first. Primary
sources and external Mathlib are then searched in separate discovery lanes,
with source recurrence and pedagogical judgment reviewed explicitly. Internal
LRA Lean and LaTeX are integration evidence only: they may inform naming,
structure reuse, placement, collision checks, and backport review, but they are
not independent mathematical-discovery sources.

Lean remains essential after candidate approval. It validates approved
statements, tests boundaries, supports adversarial weakening/strengthening
studies, and records checked examples and counterexamples. Compilation alone
does not establish intended meaning, learner value, source grounding, or
publication approval.

## Extraction Pipeline

### 1. Convert input into editable text

- Determine whether the input is already text or an image.
- If the input is already text, use that text directly.
- If the input is an image, run OCR first.
- Expose OCR text for review before final extraction.
- Treat OCR text as provisional. Mathematical symbols, endpoints, quantifiers,
  subscripts, superscripts, and interval brackets require review.

Image input becomes text first, then follows the same extraction workflow as
pasted text.

### 2. Read the whole visible passage

Read the entire visible mathematical passage before deciding what to extract.

Do not anchor on:

- the first bolded label,
- the first explicit `Definition`, `Theorem`, or `Example`,
- the first displayed formula,
- the most visually prominent local block.

Default to extracting the full visible passage unless the user explicitly
chooses selected-item extraction.

### 3. Understand the mathematics

Before producing LaTeX, understand what the passage is doing mathematically.

Ask:

- What is the topic?
- What are the mathematical objects?
- What is being defined?
- What is being claimed?
- What is being illustrated?
- What fails?
- Is there a counterexample?
- Is there a replacement law or weaker statement?
- Is there a special case?
- Is notation being introduced?
- Are there computational formulas or rules?
- What formulas are central?

Common source content includes definitions, theorem-like claims, propositions,
laws, examples, counterexamples, notation, computational formulas, proof
sketches, warnings, pitfalls, special cases, and explanatory prose.

### 4. Write an internal bullet list

Before emitting LaTeX, write an internal bullet list of every mathematical
claim or displayed formula in the visible snippet.

The bullet list is the comprehension guardrail.

It should include:

- every displayed formula that states a definition, claim, law, example,
  counterexample, special case, or computation rule;
- every prose sentence that makes a mathematical claim;
- every warning, failure, exception, or special case;
- every example or counterexample;
- every introduced piece of notation.

If the bullet list omits an important visible formula or claim, redo the
summary before generating LaTeX.

Do not skip earlier claims because a later `Example`, `Definition`, or
`Theorem` label appears.

### 5. Rewrite into a clean mathematical note

Rewrite the passage internally into standard mathematical form before
generating LaTeX.

The rewritten note should be better organized than the raw source while
preserving its meaning.

Use the mathematical role of each item:

- definitions become `definition` environments;
- theorem-like claims, laws, and reusable facts become `proposition` or another
  theorem-like environment;
- examples and counterexamples become `example*` blocks or `remark*`
  examples/non-examples metadata unless the task explicitly asks for a
  numbered formal example artifact;
- warnings, exposition, interpretation, and informal comments become `remark*`
  environments.

If the source gives one definition with several operation cases, emit a short
exposition remark and then one definition per operation or case.

If the source states several laws, emit propositions or grouped propositions.

If the source gives a counterexample, title it by the law it refutes.

If the source says a law fails and then gives a weaker replacement law, extract
both the failure/counterexample and the weaker law.

If the source gives a warning or practical comment, use `remark*`.

### 6. Emit LaTeX from the rewritten note

Generate LaTeX from the cleaned mathematical note, not directly from OCR
fragments.

Choose environments by mathematical role, not by raw visual layout.

For a single definition snippet, emit one definition.

For a definition cluster, emit clustered definitions.

For a mixed mathematical passage, emit the clean note that best represents the
full visible mathematical argument.

### 7. Check the output

Before returning the candidate LaTeX, check:

- No important visible formula or claim was dropped.
- The extraction did not accidentally start too late in the passage.
- The output preserves the mathematical flow of the source.
- Examples are classified as examples.
- Counterexamples are identified by the law they refute.
- Warnings and informal comments are not over-promoted into theorems.
- Labels are semantic and stable.
- Titles are meaningful mathematical titles, not OCR phrases.
- Display math delimiters are balanced.
- Environments are balanced.
- Citations and labels follow project style.

## User-Guided Checkboxes

Optional UI checkboxes may guide extraction:

- Contains definitions
- Contains theorems/propositions/laws
- Contains examples
- Contains counterexamples
- Contains notation
- Contains computational formulas
- Contains proof/proof sketch
- Contains warnings/pitfalls
- Contains special cases
- Rewrite into standard note form
- Preserve source order closely
- Generate explanatory remarks
- Generate small examples when helpful
- Extract full visible passage
- Extract selected highlighted item only

Default behavior:

- Extract full visible passage.
- Rewrite into standard note form.
- Generate explanatory remarks when useful.
- Do not extract only a local example, theorem, or definition unless the user
  explicitly selected `Extract selected highlighted item only`.

Checkboxes guide extraction, but they do not replace mathematical
comprehension.

## Labels and Citations

Do not use raw OCR phrases as titles.

Bad:

```latex
\begin{example}[As a Counter Example Consider]
\label{ex:as-a-counter-example-consider}
```

Good:

```latex
\begin{example}[Failure of distributivity]
\label{ex:failure-of-distributivity}
```

Labels must come from normalized mathematical titles, not from OCR spans,
section prose, page numbers, running headers, or truncated fragments.

For extracted definitions, use the project's canonical order:

```latex
\begin{definition}[Title]
\cite{SourceKey}
\label{def:semantic-label}
...
\end{definition}
```

Generated exposition and generated examples are explanatory additions, not
source quotations. Do not cite generated examples unless the example itself is
copied or directly adapted from the source.

## LaTeX Validity

Before returning output, check:

- every `\[` has a matching `\]`;
- every `\begin{...}` has a matching `\end{...}`;
- no `\cite` or `\label` appears inside unfinished display math;
- citations and labels use the project's canonical order;
- labels are semantic and stable.

For newly generated note files or note directories, run the integrated volume
validator:

```sh
python tools/governance/validate_volume.py <target-repo> --fail-on-errors
```

Use the scoped audit tools only when a task needs a focused inventory or
refactor report.

## House Rules

Apply the current constitution and governance standards while generating:

- `constitution/master.md`
- `capabilities/reference/authoring-standards.md`
- `capabilities/reference/atomic-artifact-standards.md`
- `capabilities/reference/notation-standards.md`
- `capabilities/reference/extraction-standards.md`

Generated output is always staged candidate content for human review. It must
not be treated as final note insertion.
