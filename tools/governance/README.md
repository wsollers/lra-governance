# Governance Tools

This directory contains the canonical implementations of governance generation,
wrapper preview, validation, drift-check, and task-scope audit tools.

Leaf repositories may carry wrapper scripts with matching paths, but those
wrappers must delegate back here. They must not copy or fork the implementation.
If a wrapper cannot locate `lra-governance`, it should fail with a clear error
message such as "lra-governance is not present" and should not silently skip the
required check.

Available and planned tools:

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
- `generate_stub.py` - deterministic scaffold for canonical stub chapters and
  topic-paired stub sections.
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

## Stub Generation

Run from `lra-governance` against the target leaf volume repository. Generate
stubs with the deterministic scaffold first, then validate the target volume.

```powershell
python tools\governance\generate_stub.py chapter --volume-root F:\repos\lra-volume-ii\volume-ii --subject ordered-fields --title "Ordered Fields" --section "Order"
python tools\governance\generate_stub.py section --chapter-root F:\repos\lra-volume-ii\volume-ii\ordered-fields --section "Completion Fields"
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
