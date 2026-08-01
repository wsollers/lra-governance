# Internal Object Index Delta Workflow

Use this workflow after adding, deleting, moving, or editing LRA-authored TeX
formal artifacts or Lean source declarations. It keeps the governed Lean/TeX
lookup index current without forcing a full parse on every edit.

## Scope

The indexed source surfaces are:

- TeX formal environments in volume repos:
  `definition`, `axiom`, `theorem`, `lemma`, `proposition`, and `corollary`;
- Lean declarations in `lra-lean`: `abbrev`, `def`, `theorem`, `lemma`,
  `axiom`, `structure`, `class`, and `inductive`.

PDFs are not primary discovery inputs for this workflow. Use rendered PDFs only
for downstream page or visual QA after the source object has been identified.

## Command

Use the delta updater for ordinary edit loops:

```powershell
python F:\repos\lra-governance\tools\governance\update_internal_object_index.py `
  --tex-root F:\repos\lra-volume-iii `
  --lean-root F:\repos\lra-lean `
  --output D:\Readings\indexes\lra\internal\volume-iii-lean-tex-index.yaml `
  --include-match-report
```

On the first run, or when the state file is absent, the command performs a full
build. Later runs hash current source files, re-index changed files, remove
records for deleted files, and merge unchanged records from the previous index.

Force a self-healing rebuild when the index looks suspicious, parser behavior
changed, or roots/options changed:

```powershell
python F:\repos\lra-governance\tools\governance\update_internal_object_index.py `
  --tex-root F:\repos\lra-volume-iii `
  --lean-root F:\repos\lra-lean `
  --output D:\Readings\indexes\lra\internal\volume-iii-lean-tex-index.yaml `
  --include-match-report `
  --full
```

Use one `--tex-root` per volume repo and one `--lean-root` for `lra-lean`.
Pass the volume repository root, not a nested chapter or topic directory; the
TeX scanner indexes files whose relative path begins with `volume-`.

## Output

The updater writes:

- the internal object index at `--output`;
- a delta state file next to it by default, named `<output>.state.yaml`;
- a `delta` report inside the index payload with changed, unchanged, and
  deleted file counts.

Generated full indexes and state files belong in ignored build or external
index locations unless a small curated crosswalk is intentionally reviewed and
committed.

## Acceptance

After adding a TeX definition or theorem-like object, rerun the updater and
verify the object is discoverable by label or name:

```powershell
Select-String `
  -Path D:\Readings\indexes\lra\internal\volume-iii-lean-tex-index.yaml `
  -Pattern "def:your-label"
```

For stable lookup, every TeX object should have a bracketed display name and a
label. If a matching Lean declaration exists, record the link immediately after
the TeX formal artifact with `\LeanFormalizes{...}`. If Lean work does not yet
exist, create an explicit `lra-lean` follow-up task instead of leaving the object
silently untracked.
