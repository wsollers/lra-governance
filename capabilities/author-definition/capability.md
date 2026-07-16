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
- `python <governance-root>/tools/governance/compare_semantic_ast_extractors.py --source-tex <artifact-source-snippet.tex> --artifact <artifact.yaml> --output <ast-extractor-comparison.yaml>`
- `cd <volume-root> && python ../lra-governance/scripts/build_volume.py --root .`

## Reference Escalation

If the overlay and nearby examples do not answer a structural question, open
`capabilities/reference-index.md` and use only the `Volume Definition Authoring`
row needed for the issue.

Stop if a success gate fails, the target file is ambiguous, or the needed
canonical predicate is missing.
