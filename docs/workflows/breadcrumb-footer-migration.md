# Breadcrumb And Footer Migration

This workflow migrates LRA volume repos from legacy chapter breadcrumbs to the
new metadata-driven breadcrumb/footer system.

Use this as the volume-by-volume plan. Do not migrate volume content before the
common macro and build contracts exist.

## Goal

Each volume build should support:

- digital and print editions;
- explicit paper size;
- main-volume and individual-book roots;
- one metadata source for top breadcrumb and footer breadcrumb;
- no local copy of shared breadcrumb/footer implementation in volume repos.

## Phase 0: Common Macro Contract

Owner: `lra-common`.

Add or replace the shared breadcrumb/footer implementation in
`common/breadcrumb-macros.tex`.

The macro layer must provide a stable public API:

```latex
\lrasetup{edition=<digital|print>, paper=<letter|a4|sixbynine>, ...}
\lrameta{
  series = {...},
  volume = {...},
  book = {...},
  chapter = {...},
  topic = {...},
  current = <series|volume|book|chapter|topic>,
}
\LraBreadcrumb
\LraFooterBreadcrumb
```

Backward compatibility is required during migration:

```latex
\breadcrumb{<chapter-slug>}{<prior>}{<current>}{<next>}
```

The legacy macro may render through the old style or through a compatibility
adapter, but it must continue to compile until every volume is migrated.

The common implementation must read build-provided defaults:

- `LRA_EDITION=digital|print`;
- `LRA_PAPER=letter|a4|sixbynine`;
- legacy `LRA_PRINT_EDITION=1` remains accepted as an alias for
  `LRA_EDITION=print`.

## Phase 1: Build Contract

Owner: `lra-governance`.

Enhance `tools/governance/build_volume_docker.py` so edition and paper are
first-class build inputs.

Required CLI:

```powershell
python ..\lra-governance\tools\governance\build_volume_docker.py --root . --edition digital --paper letter --output-dir build\digital-letter
python ..\lra-governance\tools\governance\build_volume_docker.py --root . --edition print --paper sixbynine --output-dir build\print-sixbynine
```

Compatibility requirement:

```powershell
--print-edition
```

continues to work and maps to `--edition print`.

The Docker invocation must pass:

```text
LRA_EDITION=<edition>
LRA_PAPER=<paper>
```

and, for print compatibility:

```text
LRA_PRINT_EDITION=1
```

The helper already discovers and builds canonical main-volume and book roots.
Keep that behavior.

## Phase 2: Validator Contract

Owner: `lra-governance`.

Add validators before migrating volume content:

- no volume repo may define local breadcrumb/footer package files;
- no volume repo may redefine `\LraBreadcrumb`, `\LraFooterBreadcrumb`,
  `\lrameta`, or `\lrasetup`;
- migrated chapter/topic files use `\lrameta` before `\LraBreadcrumb`;
- legacy `\breadcrumb{...}` is allowed only for unmigrated chapters;
- footer breadcrumb, if locally wired, must use `\LraFooterBreadcrumb` and not
  duplicate trail text.

During migration, validator severity should be staged:

1. report-only inventory;
2. warnings for newly touched chapters;
3. errors once a volume is declared migrated.

## Phase 3: Volume Inventory

Owner: volume migration agent.

For each `lra-volume-*` repo, produce an inventory before edits:

- all `\breadcrumb{...}` call sites;
- all chapter routers and topic routers;
- all root TeX files;
- whether a footer is wired;
- whether local breadcrumb/footer macros exist;
- main-volume and book-root build list;
- current CI workflow build matrix.

The inventory output should be committed or archived in governance/hold only if
the task explicitly requests preserving reports. Otherwise, keep it as a local
working report.

## Phase 4: Pilot Volume

Pilot on one volume first, preferably the volume with the smallest active
surface or the one currently under reorganization.

Pilot steps:

1. Update the volume preamble/root wiring only as needed to consume
   `lra-common`.
2. Migrate one book from legacy `\breadcrumb` to metadata-driven
   `\lrameta` plus `\LraBreadcrumb`.
3. Wire footer breadcrumb through `\LraFooterBreadcrumb` if the root page style
   supports it.
4. Build digital and print editions for the main volume and every book root.
5. Inspect rendered PDFs for chapter openings, topic pages, and footers.
6. Run validators in report mode and fix real drift.

Do not continue to the next volume until the pilot proves that:

- legacy and new macros can coexist;
- both editions compile;
- paper selection reaches LaTeX;
- footer text matches breadcrumb metadata;
- print output has no interactive controls.

## Phase 5: Volume-By-Volume Migration

Proceed in reading order unless a specific volume is already under active work:

1. `lra-volume-i`
2. `lra-volume-ii`
3. `lra-volume-iii`
4. `lra-volume-iv`
5. `lra-volume-v`
6. `lra-volume-vi`
7. `lra-volume-vii`
8. `lra-volume-viii`

For each volume:

1. Create the inventory.
2. Migrate chapter-opening breadcrumbs.
3. Migrate topic-level breadcrumbs only where topic pages actually render
   independent orientation chrome.
4. Wire footer breadcrumb from the same metadata source.
5. Remove local breadcrumb/footer code if any exists.
6. Build:
   - digital main volume;
   - print main volume;
   - digital individual books;
   - print individual books.
7. Run validators.
8. Record the volume as migrated only after all checks pass.

## Phase 6: CI Workflow Migration

For each volume repo workflow:

- build a matrix over edition and paper size;
- include at least `digital/letter` and `print/sixbynine`;
- keep main-volume and individual-book roots in the build set;
- upload artifacts with edition and paper in the artifact name;
- run validation before PDF builds.

Example matrix shape:

```yaml
strategy:
  matrix:
    edition: [digital, print]
    paper: [letter, sixbynine]
```

The exact paper set may be narrowed later, but workflows must make edition and
paper explicit.

## Phase 7: Legacy Removal

Only after all volumes are migrated:

- remove the legacy `\breadcrumb{...}` compatibility path from `lra-common`;
- promote legacy breadcrumb use from warning to error;
- delete migration-only scripts that are no longer needed;
- update docs to describe only the final public API.

## Per-Volume Completion Checklist

- No local shared breadcrumb/footer implementation in the volume repo.
- No stale hand-rolled breadcrumb boxes.
- Metadata-driven top breadcrumb renders.
- Footer breadcrumb renders from the same metadata source.
- Print edition suppresses proof/exercise/capstone routes and interactive
  controls.
- Digital edition renders proof/exercise/capstone routes.
- Requested paper size reaches the LaTeX build.
- Main volume root builds in digital and print.
- Every book root builds in digital and print.
- Validator output is clean or contains only accepted pre-existing findings.

