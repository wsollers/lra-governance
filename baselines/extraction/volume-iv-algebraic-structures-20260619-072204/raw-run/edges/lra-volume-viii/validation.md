# Dependency Graph Validation

- Issues: 23
- Errors: 21
- Warnings: 2

## Issue Counts

- `ambiguous_dependency_target`: 4
- `closure_leaf_not_allowed_root`: 2
- `duplicate_global_label`: 17

## Issues

- **error** `duplicate_global_label`  label=`def:abelian-group`: Label def:abelian-group appears 2 times globally.
- **error** `duplicate_global_label`  label=`def:abstract-field`: Label def:abstract-field appears 2 times globally.
- **error** `duplicate_global_label`  label=`def:abstract-integral-domain`: Label def:abstract-integral-domain appears 2 times globally.
- **error** `duplicate_global_label`  label=`def:associativity`: Label def:associativity appears 2 times globally.
- **error** `duplicate_global_label`  label=`def:commutative-ring`: Label def:commutative-ring appears 2 times globally.
- **error** `duplicate_global_label`  label=`def:commutativity`: Label def:commutativity appears 2 times globally.
- **error** `duplicate_global_label`  label=`def:group`: Label def:group appears 2 times globally.
- **error** `duplicate_global_label`  label=`def:homomorphism`: Label def:homomorphism appears 2 times globally.
- **error** `duplicate_global_label`  label=`def:l-structure`: Label def:l-structure appears 2 times globally.
- **error** `duplicate_global_label`  label=`def:left-distributivity`: Label def:left-distributivity appears 2 times globally.
- **error** `duplicate_global_label`  label=`def:monoid`: Label def:monoid appears 2 times globally.
- **error** `duplicate_global_label`  label=`def:partial-order`: Label def:partial-order appears 2 times globally.
- **error** `duplicate_global_label`  label=`def:right-distributivity`: Label def:right-distributivity appears 2 times globally.
- **error** `duplicate_global_label`  label=`def:ring`: Label def:ring appears 2 times globally.
- **error** `duplicate_global_label`  label=`def:semigroup`: Label def:semigroup appears 2 times globally.
- **error** `duplicate_global_label`  label=`def:strict-partial-order`: Label def:strict-partial-order appears 2 times globally.
- **error** `duplicate_global_label`  label=`def:total-order`: Label def:total-order appears 2 times globally.
- **error** `ambiguous_dependency_target` lra-volume-viii/volume-viii/algebras-of-sets/notes/rings-of-sets/notes-boolean-rings.tex:116 label=`def:boolean-ring` target=`def:ring`: def:boolean-ring target def:ring has multiple global matches.
- **error** `ambiguous_dependency_target` lra-volume-viii/volume-viii/algebras-of-sets/notes/rings-of-sets/notes-boolean-rings.tex:218 label=`def:idempotent-element` target=`def:ring`: def:idempotent-element target def:ring has multiple global matches.
- **error** `ambiguous_dependency_target` lra-volume-viii/volume-viii/model-theory/notes/l-structures/notes-l-structures.tex:217 label=`def:variable-assignment` target=`def:l-structure`: def:variable-assignment target def:l-structure has multiple global matches.
- **error** `ambiguous_dependency_target` lra-volume-viii/volume-viii/model-theory/notes/l-structures/notes-l-structures.tex:260 label=`def:term-evaluation` target=`def:l-structure`: def:term-evaluation target def:l-structure has multiple global matches.
- **warning** `closure_leaf_not_allowed_root` lra-volume-viii/volume-viii/algebras-of-sets/notes/rings-of-sets/notes-boolean-rings.tex:166 label=`lem:self-additive-inverse` target=`def:idempotent-element`: lem:self-additive-inverse dependency closure reaches non-root leaf def:idempotent-element.
- **warning** `closure_leaf_not_allowed_root` lra-volume-viii/volume-viii/algebras-of-sets/notes/rings-of-sets/notes-boolean-rings.tex:166 label=`lem:self-negation` target=`def:idempotent-element`: lem:self-negation dependency closure reaches non-root leaf def:idempotent-element.
