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

## Success Gates

- `python tools/governance/validate_decoration.py --root <volume-root> --chapter <chapter> --canonical-dir <canonical-root>`
- For provable statements: `python tools/governance/audit_proof_layout.py --root <volume-root> --chapter <chapter> --strict`
- `cd <volume-root> && python ../lra-governance/scripts/build_volume.py --root .`

## Reference Escalation

If the overlay and nearby examples do not answer a structural question, open
`capabilities/reference-index.md` and use only the `Volume Statement Authoring`
row needed for the issue.

Stop if the target section is ambiguous, a canonical registry entry is required
but missing, or either success gate fails.
