# Local Semantic Logic Verifier

The local semantic logic verifier is the default post-generation logic gate for
semantic artifact packages. It is a deterministic Python validator, not an
external reviewer and not a theorem prover. Its job is to make the semantic
artifact record carry enough structured metadata that common logic regressions
can be checked without an OpenAI call.

## Default transport policy

`tools/governance/invoke_external_gpt_reviewer.py logic` defaults to the local
Python verifier.

Use an external OpenAI review only when explicitly requested:

```powershell
python <governance-root>\tools\governance\invoke_external_gpt_reviewer.py logic `
  --logic-reviewer external `
  --input <run-dir>\logic-input.json `
  --output <run-dir>\logic-validation.yaml `
  --prompt <governance-root>\constitution\prompts\validate-semantic-artifact-logic.md `
  --governance-root <governance-root>
```

The local mode requires the generated artifact and corrected TeX:

```powershell
python <governance-root>\tools\governance\invoke_external_gpt_reviewer.py logic `
  --input <run-dir>\logic-input.json `
  --output <run-dir>\logic-validation.yaml `
  --artifact <artifact-folder>\artifact.yaml `
  --corrected-tex <artifact-folder>\corrected.tex `
  --governance-root <governance-root>
```

The direct validator entrypoint is:

```powershell
python <governance-root>\tools\governance\validate_semantic_logic.py `
  --artifact <artifact-folder>\artifact.yaml `
  --corrected-tex <artifact-folder>\corrected.tex `
  --output <run-dir>\logic-validation.yaml
```

## Metadata needed for deterministic validation

For definitions, the semantic artifact must make definitional equivalence
explicit in the AST whenever the prose or LaTeX asserts an equivalence.

Correct shape:

```yaml
statement:
  canonical_latex: \operatorname{UpperBound}(u,A,P_{\mathbb{R}})\iff(\forall x\in A)(x\leq u).
  semantic_ast:
    kind: iff
    left:
      kind: predicate
      predicate_id: pred:upper-bound
      arguments: [...]
    right:
      kind: forall
      binder: ...
      body: ...
logical_forms:
  standard_quantified:
    latex: \operatorname{UpperBound}(u,A,P_{\mathbb{R}})\iff(\forall x\in A)(x\leq u).
    ast:
      kind: iff
      left: ...
      right: ...
```

Incorrect shape:

```yaml
statement:
  canonical_latex: \operatorname{UpperBound}(u,A,P_{\mathbb{R}})\iff(\forall x\in A)(x\leq u).
  semantic_ast:
    kind: forall
    ...
```

The incorrect shape loses the fact that the artifact defines a predicate rather
than merely asserting the right-hand condition.

For theorem-like artifacts, an \(n\)-way equivalence must be represented as a
conjunction of adjacent biconditionals, not as a nested biconditional.

Correct three-way shape:

```yaml
statement:
  canonical_latex: (E\Longleftrightarrow N)\land(N\Longleftrightarrow S).
  semantic_ast:
    kind: and
    left:
      kind: iff
      left: ...
      right: ...
    right:
      kind: iff
      left: ...
      right: ...
```

Incorrect shapes:

```yaml
semantic_ast:
  kind: iff
  left: E
  right:
    kind: iff
    left: N
    right: S
```

and:

```yaml
semantic_ast:
  kind: iff
  left: E
  right:
    kind: and
    left: N
    right: S
```

The first incorrect shape can be true when two formulations disagree; the
second says one formulation is equivalent to both others being true, not that
the three formulations have the same truth value.

## Applicability and failure

Standing assumptions belong in `assumptions`. Failure of those assumptions is an
applicability failure, not a negated predicate result.

For `def:real-upper-bound`, the metadata should separate:

- `A\subseteq\mathbb{R}`, `A\neq\varnothing`, and `u\in\mathbb{R}` as
  assumptions;
- empty or ill-typed input as `failure_analysis.applicability_failures`;
- actual predicate failure as `failure_analysis.statement_failures`.

## Mechanical versus normalized negation

The mechanical negation should preserve the logical negation first:

```yaml
logical_forms:
  negation:
    mechanical:
      latex: (\exists x\in A)\neg(x\leq u).
```

If the package normalizes this to a strict comparison, it must record the
normalization dependency:

```yaml
logical_forms:
  negation:
    approved_normal_form:
      latex: (\exists x\in A)(u<x).
    normalization_requires:
      - id: real_total_order
        reason: In the standard total order on the real line, not (x <= u) is equivalent to u < x.
        dependency_label: def:reals
```

Without this dependency, the verifier treats the strict-order rewrite as an
unjustified order-strength change.

## Current verifier scope

The local verifier checks:

- binder references in structured ASTs;
- definition biconditional shape in YAML and corrected TeX;
- theorem-level \(n\)-way equivalence shape;
- quantified LaTeX/AST parity: explicit `\forall` and `\exists` binders in
  `logical_forms.standard_quantified.latex` must have corresponding structural
  quantifier nodes in `logical_forms.standard_quantified.ast`; comma-bound
  variables such as `\forall x,y\in I` count as two bound variables and should
  be represented by two AST binder nodes;
- predicate arities for known semantic predicates;
- separation of assumptions, statement, applicability failures, and statement
  failures;
- mechanical negation shape;
- declared assumptions for strict-order normalization;
- core YAML/TeX symbol agreement;
- theorem-level logical-form coverage: if YAML records an approved negation or
  a contrapositive, corrected TeX must contain a named failure/negation block or
  contrapositive block rather than silently omitting that logical form.

It also checks registry-driven predicate and structure assembly. Each
registered predicate or structure constructor supplies an ordered argument
signature. The local verifier checks arity, broad role compatibility, and
obvious ambient/type mismatches. For example, an element typed over
`\mathbb{N}` must not be passed to a real-line predicate position unless the
AST records an explicit coercion or conversion. For order predicates whose
ambient argument is a structure such as `OrderedSet(S,\leq)`, the verifier
looks through the structure to its registered carrier `S`.

## Lean/mathlib crosswalk

The verifier and explorer should not replace LRA's pedagogical TeX language
with Lean vocabulary. Instead, `lean-crosswalk.yaml` maps LRA predicate IDs and
surface forms to Lean/mathlib declarations. That registry lets downstream
tools offer an LRA lens and a Lean lens over the same semantic record.

For supremum, the preferred proposition anchor is `IsLUB`, while `sSup` is the
operator/value lens. This keeps applicability assumptions such as
`Set.Nonempty` and `BddAbove` separate from the predicate failure analysis.

The same registry can also record local LRA Lean declarations, such as
`Bounds.IsSupremum` in `LRA/VolumeIII/Bounds.lean`. The intended comparison is:

- LRA TeX surface: "s is the supremum of A";
- LRA semantic AST: `LeastUpperBound(s,A,P)`;
- LRA Lean: `Bounds.IsSupremum s A`;
- mathlib Lean: `IsLUB A s`;
- bridge theorem: `Bounds.SupremumIffIsLUB`.

That gives the knowledge explorer enough structure to compare the book's
wording, the project's own Lean formalization, and mathlib's canonical name
without forcing the TeX to use Lean-facing vocabulary.

The verifier does not prove arbitrary theorem correctness. When a package uses
only raw LaTeX or needs mathematical insight beyond these structural rules, it
should return warnings or failures that identify the missing metadata.

## Independent AST extraction gate

Before trusting the generated artifact AST, run independent source extractors and
compare their facts against the semantic artifact:

```powershell
python <governance-root>\tools\governance\compare_semantic_ast_extractors.py `
  --source-tex <artifact-source-snippet.tex> `
  --artifact <artifact-folder>\artifact.yaml `
  --output <run-dir>\ast-extractor-comparison.yaml
```

The comparison tool currently emits a compact fact AST from multiple readers:

- `surface_regex`: source-level environment, label, prose cues, predicate macro
  names, and dependency labels;
- `displayed_math_regex`: displayed-equation cues such as `\iff`, `\forall`,
  `\exists`, negation, and predicate macro names;
- `pylatexenc`: optional LaTeX node parser backend, used when installed;
- `tree_sitter_latex`: optional source parser backend slot, used when installed
  and configured.

The purpose is not to make any one extractor authoritative. The gate is useful
because disagreement is actionable:

- if source extractors see `\iff` or "Equivalently" and the artifact AST lacks an
  `iff` node, the artifact lost definition shape;
- if source extractors see `\forall` or `\exists` and the artifact has no matching
  quantified node, the binder structure is probably underspecified;
- if source extractors see a predicate macro such as `\operatorname{UpperBound}`
  and the AST omits the corresponding registry predicate, the predicate reading
  is incomplete.

The extractor treats UpperCamel `\operatorname{...}` names as predicate-shaped
surface forms. Lowercase operator names such as `\operatorname{sgn}`,
`\operatorname{sin}`, or `\operatorname{exp}` are term-level function symbols,
not governed predicates, unless they are explicitly promoted through the
predicate registry. This prevents illustrative examples from forcing ordinary
scalar functions into the semantic predicate AST while still catching names such
as `IsContinuous`, `Derivative`, or `UpperBound`.

This gives the audit loop a cheap "two readers saw the same thing" gate before
running deeper logical checks. As stronger parser backends are installed, the
same comparison output can include their facts without changing the artifact
schema.

## Governance-readiness gate

Semantic validation must not collapse all successful checks into a single
"clean pass." The validators distinguish:

- mathematical logic: the statement, negation, and predicate assembly are
  internally coherent;
- schema validity: the artifact and support files satisfy their schemas;
- registry alignment: predicate and structure calls preserve canonical name,
  arity, argument order, return type, and carried-context metadata;
- source provenance: the source file, source hash, and recorded commit are
  independently checkable;
- proof provenance: proof edges and canonical proof records resolve to real
  proof labels or proof-vault records;
- origin classification: author-derived composite theorems identify their
  source components and derivation rule instead of masquerading as a theorem
  copied from one primary source;
- migration state: the artifact may be mathematically valid but require a
  formal-kind or concept-ownership migration before permanent normalization.

`validate_semantic_artifact.py` emits `governance_ready`:

- `pass` when there are no errors or warnings;
- `pass_with_warnings` when the artifact is schema/math valid but has unresolved
  governance work;
- `fail` when schema, registry, or blocking governance checks fail.

With `--repos-root`, the artifact validator builds a local label index from
chapter registries, TeX labels, proof labels, and canonical predicate/structure
registries. Relationship targets must resolve against that index. Dependency
labels such as `def:*` should point to visible statement labels; ontology edges
to `pred:*` or `struct:*` must resolve in canonical registries; proof edges must
resolve to `prf:*` labels or be moved to unresolved provenance.

The artifact validator also rejects overclaimed registry metadata:

- `context[].ontology_id` values beginning with `pred:` or `struct:` must exist
  in the canonical registries;
- `logical_forms.predicate_reading.registry_structures` may name only
  structures that actually appear as structured AST applications;
- raw notation such as `(x,y)` does not justify claiming `struct:interval`
  until it is represented by a governed interval constructor.

Some dependency mistakes are semantic rather than syntactic. For example,
`thm:darboux` must not use `thm:darboux-property` as a proof dependency for the
derivative theorem: that property is about continuous functions and would
smuggle in continuity of `f'`, which Darboux's theorem explicitly does not
assume.

The same gate checks source provenance. A source hash mismatch, missing source
file, local-only commit, or commit absent from visible remote branches prevents
an artifact from being treated as governance-ready even if the mathematical AST
is valid.

For LRA-authored theorems assembled from source components, use
`provenance.origin.kind: author_derived_from_source_components` with
`source_status: composite_source_route`. The artifact validator requires
component evidence and a derivation rule. A derivative-equivalence theorem, for
example, can cite source-backed limit-equivalence and derivative-as-limit
components, then record the difference-quotient instantiation as the derivation
rule.

Equivalent characterizations must not silently become duplicate definitions. If
a `def:*` artifact has an `equivalent-characterization` edge to another
`def:*`, the validator reports `FORMAL_KIND_MIGRATION_REQUIRED`; the source may
remain unchanged during audit, but permanent normalization should migrate the
characterization to a theorem-like artifact with a verified proof.

## Stable sequence AST conventions

Use typed binders in the standard quantified form when the mathematical object
is naturally typed:

```yaml
binder:
  binder_id: x_seq
  symbol: x
  domain:
    kind: raw_latex
    latex: \mathbb{N}\to A
```

Use canonical structure constructors in predicate readings when arity and
carried context matter:

```yaml
kind: application
function: struct:sequence
arguments:
  - {kind: variable, binder_id: x_seq}
  - {kind: variable, binder_id: N}
  - {kind: variable, binder_id: A}
```

A sequence is a function or indexed object, not a subset. Avoid canonical forms
like `(x_n)\subseteq A`; use `x:\mathbb{N}\to A` or
`Sequence(x,\mathbb{N},A)`.

For image sequences, pass the whole termwise image sequence to convergence
predicates:

```yaml
kind: application
function: image_sequence
arguments:
  - {kind: variable, binder_id: f}
  - {kind: variable, binder_id: x_seq}
```

Do not pass the ambiguous pointwise expression `f(x_n)` as the first argument
to `ConvergesTo`; that predicate expects a sequence object.
