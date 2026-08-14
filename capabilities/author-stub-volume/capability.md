# Capability: author-stub-volume

## Action

Render or write a planned volume shell using deterministic Python. Do not use a
model to choose chapters, rewrite the scope, resolve biographical facts, or
select an image.

## Inputs

- Volume identifier, display title, and scope text.
- JSON chapter registry containing ordered `{subject, display_title}` records.
- Optional frontispiece triple: exact mathematician name, exact birth-death
  years, and an existing `images/<name>.png` path. Supply all three or none.

## Do

Run `tools/governance/generate_stub.py volume`. The renderer returns only
`<volume>/index.tex` and `<volume>/chapter.yaml`. Use `--write --repo-root
<target>` to create them. It refuses to overwrite either file.

The input registry owns chapter choice and dependency order. Create individual
chapters through `author-stub-chapter`; the volume renderer does not infer or
generate them.

## Success Gate

- `python tools/governance/validate_volume.py <target-volume> --fail-on-errors`

The integrated validator recognizes the root `chapter.yaml` marker and applies
the planned-volume validator until individual chapter stubs are created.

Stop if an output file already exists, an input record is incomplete, or the
layout audit fails.
