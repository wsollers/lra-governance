# Repo Overlay -- lra-common

Repo identity: Shared LaTeX macros, boxes, and templates.

Shared LaTeX macros, boxes, environments, colors, preambles, and templates
consumed by every volume. Changes here affect ALL volumes.

Agent scope:

- Edit shared LaTeX infrastructure here, not in volume repo staging
  directories. `common/` is never copied or committed into volume repos:
  build workflows obtain `lra-common` through an explicit checkout and mount
  `common/` into the Docker build container.
- Add bibliography entries in the owning `lra-volume-*` repository shard.
  `lra-common/bibliography/` is a retired mirror, not a sync source. Mobile
  photo, screenshot, OCR, and extractor candidates must be searched and
  deduplicated before promotion to a canonical `.bib` file.
- Canonical YAML is owned by `lra-governance`; do not edit it here.

Success gates:

- Compile affected target volumes or a focused smoke build.
