# Capability: author-mathematics

## Convention

In this capability, **theorem** names the theorem family: theorem, lemma,
proposition, or corollary. Preserve the requested subtype in the payload.

## Action

Turn a named request, pasted source, or screenshot into one typed mathematical
payload. The active model owns the mathematics; Python validates and renders
the representation. A payload may contain one artifact or a coherent ordered
collection.

## Contract

1. Read the request or ephemeral source and choose only the needed artifact
   kinds: `axiom`, `definition`, `theorem`, `example`, `exposition`, or `proof`.
2. Emit `constitution/schemas/mathematical-content.schema.json`, not final TeX.
   Supply every mathematical assertion in the typed fields. Do not ask Python
   to choose hypotheses, conclusions, dependencies, facts, or proof steps.
3. Use `axiom.statement`; `definition.defined_term` and
   `definition.defining_condition`; theorem `subtype`, `hypotheses`, and
   `conclusion`; example `setup`, optional `calculation`, and optional
   `explanation`; exposition `subtype` and `body`; or the full proof fields.
4. Use typed paragraphs, display-math blocks, and text, math, reference,
   emphasis, code, or citation segments. Math fields contain formulas, not
   environments, labels, links, file commands, or document structure.
   Preserve additional canonical predicate, negation, contrapositive,
   failure-mode, example, or non-example remarks in `support_blocks`; the
   renderer obtains their order and allowed relationships from the shared
   formal-decoration contract.
5. Resolve labels and dependencies through the canonical lookup/index. Query
   `predicates.yaml`, `structures.yaml`, `notation.yaml`, and `relations.yaml`
   through the routed vocabulary tool and record selected ids in
   `registry_ids`. Never invent a governed name or copy a registry into the
   payload.
6. Record source context or genuine uncertainty only when it matters. Intake
   text and screenshots remain ephemeral; do not add them to governance.
7. Load the lazy model-theory/universal-algebra reference only when the subject
   or request requires that specialization.
8. Run the deterministic renderer. For a requested theorem proof stub, set
   `proof_stub: true` and use the renderer's optional proof-stub post-step. A
   full proof is authored content and follows the separate full-proof route.

## Deterministic Boundary

`tools/governance/generators/mathematical_tex.py` owns schema validation,
registry-id checks, Unicode normalization, TeX escaping, canonical environment
and macro construction, block order, subtype rendering, output paths, atomic
writes, overwrite refusal, and byte-identical repeated rendering. It does not
call a model, infer mathematics, repair mathematical substance, or assert truth.

## Success Gates

- `python <governance-root>/tools/governance/generators/mathematical_tex.py --payload <payload.yaml> --check`
- Render to an explicit output target and run the route-provided volume,
  semantic, and proof gates that apply to the resulting artifact kinds.

Stop if a needed canonical label, dependency, notation, predicate, relation,
or structure is missing, or if the renderer rejects the payload.
