# lra-volume-ii Overlay

Volume II uses the generic `lra-volume.md` overlay plus the additional
verification-link boundary below.

Owned concerns:

- Volume II content and Overleaf-ready source layout,
- stable theorem, definition, axiom, lemma, proposition, and corollary labels,
- cross-repository verification metadata that points to `lra-lean`,
- independent volume PDF builds published to `lra-volumes-output`.

## Agent Scope

Follow the generic volume overlay. Do not place formal proof implementation
work in `lra-volume-ii`; formal proof implementation is owned by `lra-lean`.

## Verification Links

Every theorem-like or definition-like artifact in Volume II should have a
stable LaTeX label that can be mapped to a formal verification target. When the
target is not available yet, record the status as pending rather than omitting
the relationship.

Volume II may carry lightweight verification metadata: LaTeX label,
verification status, target formalization repository, and target module or
declaration name when known.

Use `\LeanFormalizes{<book-label>}{lra-lean}{<module>}{<declaration>}{<status>}`
for extraction-visible Lean mappings. The `<book-label>` must match the
immediately preceding formal artifact. Use `checked` only for declarations that
build in `lra-lean` without placeholders for that declaration.

Do not inline formal proof code as ordinary volume prose. The volume may point
to the formalization, but `lra-lean` owns checked formal source and any
implementation workflow. `lra-knowledge-explorer` owns the UI surface that
displays mapped verification code.

Use status wording that does not overclaim:

- `pending` when no target has been written,
- `statement` when a formal statement exists but the proof is incomplete,
- `checked` only when the target declaration is accepted by the formal build
  without placeholders for that declaration.
