# Reference standards and architecture

Shared, single-source rule and architecture documents referenced lazily by
capability routes. Open the smallest document that answers a concrete
question; nothing here is preloaded.

- `*.md` — content standards authored work must obey (authoring, proofs,
  notation, decoration, stubs, refactoring, vaults, editions, scope limits,
  agent-instruction policy).
- `architecture/*.md` — where things live and how repos, volumes, builds,
  pipelines, and sync paths are organized.

Rules of the layer:

- Repo overlays (`capabilities/overlays/`) are additive: they refine these
  global rules for one repository's owned work and must not fork or weaken
  them.
- Task procedures live in `capabilities/<route>/capability.md`; this
  directory holds only rules and architecture facts shared across routes.
- Add new policy to the smallest applicable document here, and register it in
  the owning route's `lazy_references` (or `capabilities/reference-index.md`)
  so it stays discoverable.
- Structured, machine-checked data lives in `constitution/schema/` — do not
  duplicate it here.
