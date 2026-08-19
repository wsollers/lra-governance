# Model View Standards


## Model Layers

The project maintains several views of the same mathematics:

- LaTeX source,
- rendered PDF/Overleaf view,
- logical block structure,
- dependency graph,
- theorem explorer data,
- audit reports.

Changes to one layer must preserve the contracts used by the others.

## Schema Boundary

Schemas for file structure, block registry, artifact matrix, and audit reports
currently live under `constitution/schema/` and `constitution/schemas/`. They
should be migrated or mirrored under `docs/schemas/` in a later phase.
