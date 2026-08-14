# Specialized Mathematical Authoring: Model Theory And Universal Algebra

Load this reference only for explicit model-theory or universal-algebra work.
Use the ordinary typed mathematical payload and deterministic renderer; this
reference does not define a second payload or rendering path.

- Make the language or signature, arities, carriers, operations, relations,
  assignments, satisfaction relation, homomorphism class, and ambient theory
  explicit exactly when the authored mathematics depends on them.
- Keep object-language syntax, metalanguage statements, semantic satisfaction,
  and syntactic derivability distinct in typed prose, inline math, and display
  math.
- For universal algebra, state the signature and the preservation obligations
  actually used by the artifact. Do not infer omitted operations or equations.
- For model theory, state the structure, assignment, theory, and satisfaction
  scope actually used by the artifact. Do not silently change free variables,
  parameters, or the ambient language.
- Select canonical ids from `predicates.yaml`, `structures.yaml`,
  `notation.yaml`, and `relations.yaml`; the renderer consumes those canonical
  owners. Do not reproduce their entries here or invent specialized aliases.
- If a required canonical entry is absent, stop with the missing id or concept
  instead of encoding an unregistered governed name in TeX.

Mathematical equivalence, correctness, proof choice, and source reconstruction
remain model-owned. Python checks only structure and renderability.
