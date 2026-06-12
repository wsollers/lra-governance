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

## Success Gates

- `python tools/governance/validate_decoration.py --root <volume-root> --chapter <chapter> --canonical-dir <canonical-root>`
- `python capabilities/author-definition/verify.py --target <file> --kind definition --predicates <canonical-root>/predicates.yaml`
- `cd <volume-root> && latexmk -lualatex main.tex`

## Reference Escalation

If the overlay and nearby examples do not answer a structural question, open
`capabilities/reference-index.md` and use only the `Volume Definition Authoring`
row needed for the issue.

Stop if a success gate fails, the target file is ambiguous, or the needed
canonical predicate is missing.
