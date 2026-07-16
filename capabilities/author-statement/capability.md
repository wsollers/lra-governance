# Capability: author-statement

## Action

Write one decorated statement: axiom, theorem, lemma, proposition, corollary,
or general statement. Definitions may use `author-definition` when the request
is specifically to define a term.

## Inputs

- Statement kind, title, target location, and either verbatim LaTeX or a precise
  description.
- Repo overlay, `proof_stub.py`, registries if the statement uses canonical
  predicates or notation, and one nearby example.

## Do

1. If the user supplied verbatim LaTeX, preserve the mathematical statement exactly.
2. Resolve `kind` and label prefix:
   definition->`def:`, axiom->`ax:`, theorem->`thm:`, lemma->`lem:`,
   proposition->`prop:`, corollary->`cor:`.
   Use semantic box wrappers only for load-bearing statements. When a statement
   is boxed, use the matching house wrapper:
   definition->`definitionbox`, axiom->`axiombox`, theorem->`theorembox`,
   lemma->`lemmabox`, proposition->`propositionbox`, corollary->`corollarybox`.
3. Emit the statement in the repo house style with required decoration remarks:
   standard quantified statement, interpretation, and dependencies or `\NoLocalDependencies`.
4. For theorem, lemma, proposition, and corollary, create the proof stub in the
   matching `proofs/<section>/prf-<slug>.tex` file using `proof_stub.render_proof_stub(...)`
   and route it from the section proof index. Do this in the same change as the statement.
5. Axioms and definitions do not get proof stubs.
6. For every new formal statement, create or update the semantic artifact
   package and run the local semantic AST gate before treating the statement as
   ready. The gate is `validate_semantic_artifact.py`,
   `validate_semantic_logic.py`, and `compare_semantic_ast_extractors.py`
   against the exact source snippet.

## Success Gates

- `python tools/governance/validate_decoration.py --root <volume-root> --chapter <chapter> --canonical-dir <canonical-root>`
- `python <governance-root>/tools/governance/validate_semantic_artifact.py --artifact <artifact.yaml> --package-dir <package-dir> --governance-root <governance-root> --repos-root <repos-root>`
- `python <governance-root>/tools/governance/validate_semantic_logic.py --artifact <artifact.yaml> --corrected-tex <corrected.tex> --output <logic-validation.yaml>`
- `python <governance-root>/tools/governance/validate_semantic_logic.py --llm-data <reviewer-output.json> --output <logic-validation.yaml>` when validating reviewer-returned artifact data before it has been split into files.
- `python <governance-root>/tools/governance/validate_semantic_logic.py --artifact <artifact.yaml> --repos-root <repos-root> --volume <i-viii> --target <volume-relative-chapter-or-topic> --label <thm-or-lem-label> --output <logic-validation.yaml>` when the source/corrected TeX must be resolved from indexed volume documents; the volume is mandatory.
- `python <governance-root>/tools/governance/semantic_artifact_inventory.py --repos-root <repos-root> --volume <i-viii> --book <book> --chapter <chapter> --section <section> --label <statement-label>` before generation when the package is missing; only routed book source counts.
- `python <governance-root>/tools/governance/compare_semantic_ast_extractors.py --source-tex <artifact-source-snippet.tex> --artifact <artifact.yaml> --output <ast-extractor-comparison.yaml>`
- For provable statements: `python tools/governance/audit_proof_layout.py --root <volume-root> --chapter <chapter> --strict`
- `cd <volume-root> && python ../lra-governance/scripts/build_volume.py --root .`

## Reference Escalation

If the overlay and nearby examples do not answer a structural question, open
`capabilities/reference-index.md` and use only the `Volume Statement Authoring`
row needed for the issue.

Stop if the target section is ambiguous, a canonical registry entry is required
but missing, or either success gate fails.
