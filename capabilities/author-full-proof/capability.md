# Capability: author-full-proof

## Action

Author the mathematical content of one complete proof as a typed `proof`
artifact in `constitution/schemas/mathematical-content.schema.json`, then pass
it to the deterministic mathematical TeX renderer.

## Inputs And Boundaries

- Preserve the exact supplied theorem subtype, label, title, and restatement.
- Supply the professional proof, detailed proof steps, proof-structure account,
  approved dependencies or explicit no-local mode, and optional approved proof
  vault URL.
- The active model owns every proof argument and mathematical judgment.
- The renderer owns the canonical proof-file layers, labels, links, escaping,
  ordering, and file behavior. It never fills a missing step or calls a model.
- When a durable stub already exists, use `--populate-proof-stub <file>` so the
  renderer verifies its theorem target and restatement, then replaces only the
  proof bodies, proof structure, dependencies, and explicitly supplied metadata.
- Do not use the proof-stub renderer for a full proof. Do not place TODO or stub
  content in a full-proof payload.

Use the lazy proof and semantic references only for a concrete structural or
verification question. Difficult proofs may use an interactively selected
reasoning level; permanent governance must not name a transient model.

## Success Gates

- `python <governance-root>/tools/governance/generators/mathematical_tex.py --payload <payload.yaml> --check`
- For an existing stub: `python <governance-root>/tools/governance/generators/mathematical_tex.py --payload <payload.yaml> --populate-proof-stub <proof.tex>`
- `python <governance-root>/tools/governance/validate_volume.py <volume-root> --fail-on-errors`
- `python <governance-root>/tools/governance/audit_proof_layout.py --root <volume-root> --strict`

Stop when the source theorem is ambiguous, a dependency is unresolved, or a
required deterministic gate fails.
