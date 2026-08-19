# Repo Overlay -- lra-knowledge-explorer

Repo identity: Knowledge Explorer web app.

Knowledge Explorer web app consuming extracted knowledge-graph data.

Owned concerns:

- extraction pipeline implementation,
- knowledge graph and edge generation,
- explorer UI,
- rebuild refresh expectations.

Agent scope: extraction implementation and UI changes belong here. The
rebuild is orchestrated from `lra-governance` over the independent volume
repos, but extractor code ownership remains with `lra-knowledge-explorer`.
Do not duplicate canonical YAML ownership here. Use the local `README.md`
and `PIPELINE.md` for operational details.

## Formal Verification Surface

When explorer records include formal verification metadata, the UI shows it
as a first-class proof companion, not ordinary prose. The proof modal
includes a `Verification` tab displaying the verification system, status,
module and declaration when known, source path when known, and
well-formatted formal code when available.

The UI must surface the proof modal when formal verification is the only
proof companion for a node, landing on the `Verification` tab rather than an
empty standard-proof tab. Never present pending or incomplete targets as
checked; missing code or metadata renders as an explicit empty state, not a
broken panel.

Layout gate:

- `python tools/governance/validate_code_repo_layout.py --root <repo-root> --repo lra-knowledge-explorer --governance-root <lra-governance>`

## Success gates

- `python -m pytest tests`
- extraction smoke commands only when graph output changes.
