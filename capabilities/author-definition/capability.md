# Capability: author-definition

## Action

Write one mathematical definition in a volume chapter.

## Inputs

- Target file.
- Definition title and statement, or a precise natural-language request.
- Repo overlay and one nearby existing definition.
- Predicate registry only when the definition needs a formal predicate reading.

## Do

1. Use the repo's definition style from the overlay.
2. Add `\label{def:<slug>}`.
3. Include the required decoration remarks: standard quantified statement,
   interpretation, and dependencies or `\NoLocalDependencies`.
4. Use a canonical `\operatorname{<Name>}` only when that name exists in the
   predicate registry. Otherwise omit the predicate reading and report the gap.
5. Append to the target file unless the user asked for returned LaTeX only.
6. Create or update the semantic artifact package and run the local semantic
   AST gate before treating the definition as ready. The gate is
   `validate_semantic_artifact.py`, `validate_semantic_logic.py`, and
   `compare_semantic_ast_extractors.py` against the exact source snippet.

## Success Gates

- `python tools/governance/validate_decoration.py --root <volume-root> --chapter <chapter> --canonical-dir <canonical-root>`
- `python capabilities/author-definition/verify.py --target <file> --kind definition --predicates <canonical-root>/predicates.yaml`
- `python <governance-root>/tools/governance/validate_semantic_artifact.py --artifact <artifact.yaml> --package-dir <package-dir> --governance-root <governance-root> --repos-root <repos-root>`
- `python <governance-root>/tools/governance/validate_semantic_logic.py --artifact <artifact.yaml> --corrected-tex <corrected.tex> --output <logic-validation.yaml>`
- `python <governance-root>/tools/governance/validate_semantic_logic.py --llm-data <reviewer-output.json> --output <logic-validation.yaml>` when validating reviewer-returned artifact data before it has been split into files.
- `python <governance-root>/tools/governance/get_semantic_validation_targets.py --repos-root <repos-root> --volume <i-viii> --book <book> --chapter <chapter> --section <section> --label <def:label> --include-source-text` before generation when the package is missing; only routed book source counts.
- `python <governance-root>/tools/governance/create_semantic_validation_artifacts.py --repos-root <repos-root> --volume <i-viii> --book <book> --chapter <chapter> --section <section> --label <def:label>` to create generation request artifacts for missing packages.
- `python <governance-root>/tools/governance/validate_semantic_logic.py --artifact <artifact.yaml> --repos-root <repos-root> --volume <i-viii> --target <volume-relative-chapter-or-topic> --label <def:label> --output <logic-validation.yaml>` when the source/corrected TeX must be resolved from indexed volume documents; the volume is mandatory.
- `python <governance-root>/tools/governance/validate_semantic_scope.py --mode python --repos-root <repos-root> --volume <i-viii> --book <book> --chapter <chapter> --section <section> --label <def:label> --output <scope-validation.yaml>` for scoped create-then-validate; use `--no-create-missing` only for fast inspection.
- `python <governance-root>/tools/governance/validate_semantic_scope.py --mode python-llm --repos-root <repos-root> --volume <i-viii> --book <book> --chapter <chapter> --section <section> --label <def:label> --llm-data-dir <llm-payload-dir> --output <scope-validation.yaml>` when supplied LLM/reviewer payloads should be validated and materialized.
- `python <governance-root>/tools/governance/validate_semantic_label.py <def:label> --repos-root <repos-root> --with-llm --output <label-validation.yaml>` for label-first LLM validation; add `--volume <i-viii>` if the label is ambiguous.
- `python <governance-root>/tools/governance/compare_semantic_ast_extractors.py --source-tex <artifact-source-snippet.tex> --artifact <artifact.yaml> --output <ast-extractor-comparison.yaml>`
- `cd <volume-root> && python ../lra-governance/scripts/build_volume.py --root .`

## Reference Escalation

If the overlay and nearby examples do not answer a structural question, open
`capabilities/reference-index.md` and use only the `Volume Definition Authoring`
row needed for the issue.

Stop if a success gate fails, the target file is ambiguous, or the needed
canonical predicate is missing.
