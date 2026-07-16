# lra-knowledge-explorer Overlay

This overlay applies to `lra-knowledge-explorer`.

Owned concerns:

- extraction pipeline implementation,
- knowledge graph and edge generation,
- explorer UI,
- rebuild refresh expectations.

## Agent Scope

Extraction implementation and UI changes belong here. The rebuild is
orchestrated from `lra-governance` over the independent volume repos, but
extractor code ownership remains with `lra-knowledge-explorer`.

Do not duplicate canonical YAML ownership here.

## Governance Doc Set

Load these governance documents for explorer work:

- `docs/architecture/knowledge-pipeline.md`;
- `docs/architecture/theorem-explorer-pipeline.md`;
- `docs/workflows/knowledge-extraction.md`;
- `docs/governance/extraction-standards.md`;
- `docs/architecture/local-semantic-logic-verifier.md` only when semantic AST
  fields affect explorer extraction or display.

Use the local `[external:lra-knowledge-explorer] README.md` and `PIPELINE.md`
for operational details. Do not load Lean, PDF-extractor, source-profile, or
volume authoring overlays unless the task explicitly crosses that boundary.
Shared Python layout and code-style rules live in
`docs/governance/code-repo-standards.md` and are enforced by
`tools/governance/validate_code_repo_layout.py` through the shared
`build-repo` path.

## Formal Verification Surface

When explorer records include formal verification metadata, the UI should show
it as a first-class proof companion rather than as ordinary prose. The proof
modal should include a `Verification` tab that displays:

- the verification system,
- status,
- module and declaration when known,
- source path when known,
- well-formatted formal code when available.

The UI must surface the proof modal when formal verification is the only proof
companion for a node. In that case, opening proofs should land on the
`Verification` tab rather than an empty standard-proof tab.

The UI must not present pending or incomplete targets as checked. Missing code
or missing metadata should render as an explicit empty state, not as a broken
panel.
