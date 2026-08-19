# Governance Tools

This directory contains the canonical implementations of governance generation,
wrapper preview, validation, drift-check, and task-scope audit tools.

Leaf repositories may carry wrapper scripts with matching paths, but those
wrappers must delegate back here. They must not copy or fork the implementation.
If a wrapper cannot locate `lra-governance`, it should fail with a clear error
message such as "lra-governance is not present" and should not silently skip the
required check.

Available and planned tools:

- `audit_governance_context.py` - validates the authoritative route manifest,
  generated human task index, typed resource classes, wrapper resolver
  pointers, default-route uniqueness, local resource paths, and per-route
  governance-context budgets (including the worst provider-wrapper chain)
  using `ceil(unicode characters / 4)`.
- `audit_latex_decoration.py` - inventory-only scanner for volume theorem and
  definition decoration compliance.
- `audit_proof_layout.py` - deterministic scanner for proof file layout,
  proof-stub status, topic-mirrored proof folders, and proof index reachability.
- `audit_volume_layout.py` - deterministic scanner for volume, chapter, topic,
  and router layout.
- `export_flashcards.py` - read-only exporter for labeled notes definitions,
  theorems, lemmas, propositions, corollaries, and axioms as flashcard records.
- `generate_predicate_migration_contexts.py` - read-only generator for
  predicate/dependency migration issue reports and per-formal-item context
  packets.
- `index_internal_objects.py` - read-only source-style indexer for internal
  volume TeX objects and Lean declarations, used to seed Lean <-> TeX
  verification and linking.
- `index_cpp_objects.py` - read-only source-style indexer for C/C++ objects in
  specialist code repositories such as `lra-nurbs` and
  `lra-numerical-analysis`.
- `internal_object_sqlite.py` - atomic builder and query layer for the separate
  TeX, Lean, and C/C++ SQLite FTS5 databases.
- `search_internal_object_index.py` - read-only ranked search over an internal
  object index, with phrase, token, synonym, and character n-gram scoring for
  rough TeX/Lean/C++ lookup.
- `lra_lookup.py` - one compact lookup facade over the source-profile omnibus
  search, internal TeX/Lean/C++ object indexes, and canonical vocabulary index.
- `vocabulary.py` - builds and queries a disposable SQLite/FTS index of the
  canonical predicate, structure, notation, and relation registries so agents
  can load one compact result instead of all four YAML files.
- `plan_lean_tex_formalizations.py` - conservative planner/applicator for
  reviewed `\LeanFormalizes` tags from an internal object index.
- `validators/formal_names.py` - integrated volume validator requiring
  bracketed display names on all definition, axiom, and theorem-like
  environments.
- `generate_stub.py` - deterministic scaffold for canonical stub chapters and
  topic-paired stub sections.
- `install_volume_devcontainer.py` - dry-run-first installer for the small
  VS Code Dev Container shim used by `lra-volume-*` repositories. The shared
  TeX image stays in `lra-governance/docker/lra-tex-dev/`.
- `edit_latex.py` - launcher for the governed volume TeX editing environment.
  It refreshes the `.devcontainer/` shim and opens the selected
  `lra-volume-i` through `lra-volume-viii` repository in VS Code's Dev
  Containers flow.
- `set_latex_root_comments.py` - dry-run-first updater for `% !TEX root = ...`
  comments in volume source files so LaTeX Workshop opens the correct book PDF
  when editing nested files.
- `test_tex_generator/` - deterministic synthetic TeX universe generator used
  to calibrate semantic AST parsing against known canonical formula ASTs.
- `validate_test_tex_generator_ast.py` - compares generated TeX displays
  against expected governed ASTs with both semantic parsers.
- `generate_agent_wrappers.py`
- `merge_repo_overlays.py`
- `report_wrapper_drift.py` - read-only comparison tool for generated wrapper
  previews versus downstream files.
- `sync_agent_wrappers.py` - guarded wrapper sync tool; dry-run by default,
  requires explicit repo selection, and write mode is not used until a pilot is
  approved.
- `validate_volume.py` - integrated volume validator for current LRA house
  rules and volume acceptance.
- `validate_repo_rules.py`
- `audit_task_scope.py`
- `dry_run_sync.py`
- `sync_governance.py`

## Requirements

Future tools must support dry-run operation before writing downstream files.
They must refuse to touch the retired `Learning-Real-Analysis` monorepo and
must not print secret values.

## Route Resolution And Context Audit

Resolve one repository/task packet without loading the manifest or human index
into agent context:

```powershell
python capabilities\resolve.py --repo lra-volume-iii --task "add a theorem" --root ..\lra-volume-iii
python capabilities\resolve.py --repo lra-volume-iii --task "look up this theorem" --json
```

Regenerate or check the human view, then enforce resource classification,
wrapper pointers, transitive eager references, and route budgets:

```powershell
python capabilities\generate_task_index.py
python capabilities\generate_task_index.py --check
python tools\governance\audit_governance_context.py
python tools\governance\audit_governance_context.py --json
```

## Canonical Vocabulary Lookup

Build explicitly, or let any query rebuild a missing or stale index:

```powershell
python tools\governance\vocabulary.py reindex
python tools\governance\vocabulary.py exists UpperBound --kind predicate
python tools\governance\vocabulary.py get pred:upper-bound
python tools\governance\vocabulary.py search "least upper bound" --limit 5
python tools\governance\vocabulary.py validate
```

An addition is dry-run by default; pass `--write` only after reviewing the
single-entry candidate YAML:

```powershell
python tools\governance\vocabulary.py add predicate candidate.yaml
python tools\governance\vocabulary.py add predicate candidate.yaml --write
```

See `docs/architecture/canonical-yaml.md` for index resolution and authority
rules.

## Unified LRA Lookup

Search primary reading sources, LRA-authored TeX, Lean declarations, C++
objects, and canonical vocabulary without loading their indexes into context:

```powershell
python tools\governance\lra_lookup.py --status
python tools\governance\lra_lookup.py "least upper bound"
python tools\governance\lra_lookup.py "Heine Borel" --scope sources --scope tex
python tools\governance\lra_lookup.py "compactness" --scope sources --volume volume-iii
python tools\governance\lra_lookup.py "interval enclosure" --scope cpp
```

The tool reads the active `lra-sources/index.yaml` pointer when present,
delegates primary-source ranking to `lra-source-profiles`, and returns compact
lane-specific records. It does not copy source text or make generated indexes
canonical. See `capabilities/lookup-lra/capability.md` for agent rules.

## Proof Layout Audit

Run from `lra-governance` against a leaf repo, volume, chapter, or section.
If the target name is not obvious, discover the available targets first:

```powershell
python tools\governance\audit_proof_layout.py --root F:\repos\lra-volume-ii --list-targets
python tools\governance\audit_proof_layout.py --root F:\repos\lra-volume-ii --chapter whole-numbers --section extending-addition --strict
```

Use `--strict` when the target is expected to satisfy the current
topic-mirrored proof architecture. Use `--format json` for machine-readable
reports.

## Volume Layout Audit

Run from `lra-governance` against a leaf repo, volume, chapter, or section.
Section scope audits the containing chapter, because topic routing and
notes/proofs pairing are chapter-level invariants:

```powershell
python tools\governance\audit_volume_layout.py --root F:\repos\lra-volume-ii --chapter whole-numbers --strict
```

Use `--strict` when the target is expected to satisfy the current
volume/chapter/topic architecture. Use `--format json` for machine-readable
reports.

## Volume Validation

Run from `lra-governance` against the target leaf volume repository:

```powershell
python tools\governance\validate_volume.py F:\repos\lra-volume-ii --fail-on-errors
```

To reduce noise during chapter work, filter the report while still validating
the full volume:

```powershell
python tools\governance\validate_volume.py F:\repos\lra-volume-ii --chapter peano-systems
```

The filtered mode changes only the printed/JSON report. The validator still
runs every volume validator across the full volume, and `--fail-on-errors`
continues to use full-volume errors as the failure gate.

Use scoped audit tools such as `audit_proof_layout.py` and
`audit_volume_layout.py` only when a task needs a focused report.

The integrated validator also reports predicate-reading signature and
construction drift. These review-level findings compare `\operatorname{...}`
and `\mathsf{...}` calls in Predicate reading blocks against `predicates.yaml`
and `structures.yaml`, so legacy implicit ambient forms such as
`IsCauchy(x_n)` or two-argument `ConvergesTo(x_n,L)` are visible without making
the current migration backlog a hard failure gate. A companion construction
check flags under-built predicate arguments, such as a `ReplacementImage`
functional argument passed as an inline `\mapsto` rule or a symbolic domain
argument that was not constructed in the same Predicate reading block.

## Flashcard Export

Run from `lra-governance` against a volume repo, volume root, chapter root,
notes folder, or single `.tex` file. The exporter writes one card for each
labeled formal notes block.

```powershell
python tools\governance\export_flashcards.py F:\repos\lra-volume-ii --output build\flashcards\volume-ii.tsv
python tools\governance\export_flashcards.py F:\repos\lra-volume-ii\volume-ii\book-discrete-algebraic\whole-numbers --format jsonl --output build\flashcards\whole-numbers.jsonl
```

The default TSV has `Front`, `Back`, `Tags`, `Source`, and `Label` columns and
is suitable for Anki-style tab-separated imports.

## Predicate Migration Contexts

Generate a chapter-level issue summary and one context packet per formal item.
Outputs are written under ignored `migration-reports/` by default.

```powershell
python tools\governance\generate_predicate_migration_contexts.py --volume F:\repos\lra-volume-iii --chapter bounding
```

## Internal Object Index

Generate a source-style lookup index for LRA TeX and Lean objects before
Lean <-> TeX verification passes. TeX source and Lean source are the canonical
lookup surfaces; PDF page maps may be joined later as render evidence.

```powershell
python tools\governance\index_internal_objects.py `
  --tex-root F:\repos\lra-volume-iii `
  --lean-root F:\repos\lra-lean `
  --include-match-report `
  --output build\internal-object-index.yaml
```

The index emits `lra.internal-object-index/1.0` records for TeX definitions,
axioms, theorems, lemmas, propositions, and corollaries plus Lean `def`,
`theorem`, `lemma`, `axiom`, `structure`, `class`, and `inductive`
declarations. Prefer the default `--tex-artifact-source source` so artifact
directories with both `source.tex` and `corrected.tex` do not create duplicate
records.
Lean records include proof-completeness metadata under `metadata.has_sorry`,
`metadata.sorry_lines`, and `metadata.verification_status`; declarations with
no source-level `sorry` are marked `checked`, and declarations containing
`sorry` are marked `incomplete`.

With `--include-match-report`, the same payload includes candidate Lean matches,
TeX objects that already carry `\LeanFormalizes`, TeX objects without a Lean
candidate, and Lean declarations not yet referenced by any TeX formalization
tag. Use that report to populate reviewed `\LeanFormalizes{label}{repo}{module}{declaration}{status}`
entries in TeX.

Build a conservative exact-match plan:

```powershell
python tools\governance\plan_lean_tex_formalizations.py `
  --index build\internal-object-index.yaml `
  --output build\lean-tex-formalization-plan.yaml `
  --status pending
```

The planner requires a TeX label, skips proof-side starred restatements, uses
production Lean paths under `LRA/` by default, and chooses one preferred TeX
attachment target per label. Review the generated YAML before applying; exact
title matches can still be semantically broad for names such as "Model" or
"Subtraction." Apply only a reviewed plan:

```powershell
python tools\governance\plan_lean_tex_formalizations.py `
  --index build\internal-object-index.yaml `
  --output build\lean-tex-formalization-plan-applied.yaml `
  --status pending `
  --apply
```

Search the generated SQLite database with ranked fuzzy lookup when the exact
label or name is unknown. The YAML object payload is not loaded at query time:

```powershell
python tools\governance\search_internal_object_index.py `
  --index D:\Readings\indexes\lra\internal\sqlite\tex-search.sqlite `
  --source-family tex `
  --limit 8 `
  "suprema of a sum"
```

Index C/C++ source objects for specialist code repos and search the result:

```powershell
python tools\governance\index_cpp_objects.py `
  --cpp-root F:\repos\lra-nurbs `
  --cpp-root F:\repos\lra-numerical-analysis `
  --output D:\Readings\indexes\lra\internal\lra-cpp-object-index.yaml

python tools\governance\search_internal_object_index.py `
  --index D:\Readings\indexes\lra\internal\sqlite\cpp-search.sqlite `
  --source-family cpp `
  --limit 8 `
  "surface mesh cache"
```

The TeX/Lean full and delta indexers and the C/C++ indexer build their relevant
SQLite database by default. Use the host-level refresh command in
`lra-source-profiles` to refresh any family independently or all four search
surfaces together:

```powershell
python F:\repos\lra-source-profiles\scripts\refresh_lra_indexes.py --scope tex
python F:\repos\lra-source-profiles\scripts\refresh_lra_indexes.py --scope all
```

## Semantic AST Test Universe

Generate synthetic TeX cases with known canonical ASTs, then compare those ASTs
against the hand parser and Lark parser:

```powershell
python -m tools.governance.test_tex_generator.cli --config tools\governance\fixtures\test_tex_generator\deep-quantifiers.yaml --state build\semantic-audit\test-tex-generator\deep-generator-state.json --output build\semantic-audit\test-tex-generator\deep-generated-tests.yaml --coverage-report build\semantic-audit\test-tex-generator\deep-coverage-report.json --registry-output build\semantic-audit\test-tex-generator\deep-synthetic-registry.json --count 500
python tools\governance\validate_test_tex_generator_ast.py --cases build\semantic-audit\test-tex-generator\deep-generated-tests.yaml --output build\semantic-audit\test-tex-generator\deep-parser-roundtrip-report.json
```

See `tools/governance/semantic-ast-test-universe.md` for the full workflow.

## Stub Generation

Run from `lra-governance` against the target leaf volume repository. Generate
stubs with the deterministic scaffold first, then validate the target volume.

```powershell
python tools\governance\generate_stub.py chapter --book-root F:\repos\lra-volume-iii\volume-iii\book-analysis-i --subject completeness --title "Completeness" --section "Completeness"
python tools\governance\generate_stub.py section --chapter-root F:\repos\lra-volume-iii\volume-iii\book-analysis-i\completeness --section "Completion Fields"
python tools\governance\generate_stub.py promote-topic --source-chapter-root F:\repos\lra-volume-iii\volume-iii\book-analysis-i\bounding --topic completeness --destination-chapter completeness --title "Completeness" --update-registry
```

Use `--section` repeatedly or pass a semicolon-separated `--sections` list when
creating multiple section stubs in one command.

## Schema Coverage Rule

The integrated volume validator is the deterministic acceptance gate for
machine-checkable requirements from:

- `constitution/schema/file-schema.yaml`;
- `constitution/schema/block-registry.yaml`;
- `constitution/schema/artifact-matrix.yaml`.

When those schema files change, the same change must update the relevant
`validate_volume.py` module or document why a requirement is handled by another
deterministic tool. Semantic requirements such as whether a capstone truly
avoids later chapter material require source or knowledge-graph audits in
addition to structural validation.
