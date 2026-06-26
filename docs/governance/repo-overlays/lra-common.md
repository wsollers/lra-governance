# lra-common Overlay

Stub overlay for shared LaTeX infrastructure.

Owned concerns:

- `common/`,
- bibliography helper scripts,
- shared LaTeX macros, environments, boxes, colors, and preambles,
- canonical shared LaTeX infrastructure consumed directly by builds.

## Agent Scope

Edit shared LaTeX infrastructure here, not in volume repo staging directories.
Do not expect `common/` to be copied or committed into volume repos. Build
workflows should obtain `lra-common` directly through an explicit checkout and
mount `common/` into the Docker build container.

Add bibliography entries in the owning `lra-volume-*` repository shard.
`lra-common/bibliography/` is a retired mirror, not a sync source. Mobile photo,
screenshot, OCR, and extractor
candidates must be searched and deduplicated before promotion to a canonical
`.bib` file.

Do not edit canonical YAML here; that is owned by `lra-governance`.
