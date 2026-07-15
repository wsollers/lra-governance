# Capability: calibrate-semantic-artifact

## Action

Prepare, validate, and integrate one atomic mathematical artifact as reviewed
semantic YAML plus governed LaTeX.

## Inputs

- Target volume repository, file, and formal label.
- Exact target and governance commits.
- Target environment with support blocks.
- Minimal nearby context and one governed example.
- Canonical registries.
- Existing Lean, Mathlib, canonical-proof, and proof-vault links when present.

## Do

1. Follow `docs/workflows/semantic-artifact-calibration.md`.
2. Use `constitution/prompts/calibrate-semantic-artifact.md`.
3. Process one atomic environment during calibration.
4. Validate returned YAML before source changes.
5. Preserve semantic environments and canonical block order.
6. Treat appearance as renderer policy.
7. Add the approved golden fixture.
8. Run volume validation and the target build.

## Do not

- invent vocabulary, labels, or routes;
- merge independent concepts;
- mix standing assumptions into predicate negation;
- infer exact Lean correspondence from a successful build;
- duplicate proof-vault attempt history;
- hand-edit renderer-owned TeX;
- process batches before stabilization.

## Success gates

```powershell
python tools\governance\validate_semantic_artifact.py `
  --artifact <artifact.yaml> `
  --package-dir <returned-package-directory> `
  --governance-root <governance-root> `
  --repos-root <repos-root> `
  --strict
```

Then run integrated volume validation and the target book build.
