# Agent Task Index

Repository scope: repositories are independent. There is no assembled monorepo
(`Learning-Real-Analysis` is retired) and no volume-to-monorepo sync; each
`lra-volume-*` repo builds independently.

Governance scope: `lra-governance` is the master governance and script
repository; shared scripts, rules, prompts, schemas, workflows, and the
canonical YAML vocabulary (`predicates.yaml`, `structures.yaml`,
`notation.yaml`, `relations.yaml`)
belong here. They are not fan-out synced into leaf repositories; repos resolve
them through `LRA_GOVERNANCE_ROOT`, a sibling `../lra-governance` checkout, or
the build Docker image.

This index tells agents which authority to load for common LRA tasks. It is a
router, not a replacement for the referenced standards.

## Repository Scope Rule

When working from a local multi-repo checkout such as `F:\repos`, prefer the
canonical files in `lra-governance` for shared governance, architecture,
workflow, prompt, schema, tool, and overlay rules.

When an agent is running inside an isolated repository checkout, such as a
GitHub workflow or a single leaf repo clone without adjacent `lra-governance`,
use the build image or an explicit `lra-governance` checkout. Do not rely on
synced local copies under `docs/`.

Do not read every governance, workflow, architecture, schema, and prompt file by
default. Select the smallest file set that matches the task.

External repository references are marked with `[external:<repo>]`. They are
task inputs, not local `lra-governance` files.

## Governance Tool Resolution

Governance tool implementations are canonical in
`lra-governance/tools/governance/`.

Leaf repositories must not carry copied governance implementations. Volume build
wrappers and governance validators must resolve the canonical implementation
from `lra-governance` directly, not from legacy leaf-local validator copies.

When a task requires a governance validator:

1. Run the leaf-local wrapper if it exists.
2. If no wrapper exists and an adjacent `lra-governance` checkout exists, run
   the canonical tool from `lra-governance/tools/governance/`.
3. If neither is available, stop the task and report that `lra-governance` is
   not present, so governance compliance cannot be certified.

Wrappers may locate the canonical repo through `LRA_GOVERNANCE_ROOT`; otherwise
they should look for a sibling `lra-governance` checkout in a local multi-repo
workspace.

Codex desktop cross-project or worktree tasks may run under
`C:\Users\<user>\.codex`, where sibling discovery cannot see
`F:\repos\lra-governance`. Persistent setup should set Windows user or machine
environment variables for both canonical roots and restart Codex before
spawning more tasks:

```powershell
[Environment]::SetEnvironmentVariable('LRA_GOVERNANCE_ROOT','F:\repos\lra-governance','User')
[Environment]::SetEnvironmentVariable('LRA_COMMON_ROOT','F:\repos\lra-common','User')
```

## Validator Targeting

Governance validators should keep full-volume acceptance as the gate. Use
scoped report modes only to reduce noise while working on a chapter or section.
Prefer named targets over hand-built paths when the validator supports them.

If the correct target is not obvious, run the validator's discovery mode first:

```powershell
python tools\governance\validate_volume.py <target-repo> --fail-on-errors
python tools\governance\audit_volume_layout.py --root <target-repo> --list-targets
python tools\governance\audit_proof_layout.py --root <target-repo> --list-targets
```

Then run the scoped check, for example:

```powershell
python tools\governance\validate_volume.py <target-repo> --chapter <chapter-name>
python tools\governance\audit_proof_layout.py --root <target-repo> --chapter <chapter-name> --section <topic-name> --strict
```

Before commit or push, run the unfiltered gate:

```powershell
python tools\governance\validate_volume.py <target-repo> --fail-on-errors
```

For generated notes, use `validate_volume.py` as the integrated acceptance
validator; use `--chapter` or scoped audit tools only when a task needs a
focused inventory or refactor report.

## Loading Discipline

1. Read `AGENTS.md`.
2. Read this task index.
3. Read only the task's required docs, schema/data files, and tool help.
4. Inspect nearby source examples before editing.
5. Load optional files only when required files leave a concrete question
   unresolved.
6. Load constitution prompts only when the user explicitly asks for that
   prompted generation or audit mode.
7. Full-corpus governance reading is reserved for explicit governance audit or
   consolidation tasks.
8. For canonical predicate, structure, notation, or relation lookup, run
   `tools/governance/vocabulary.py`; do not load the four complete YAML
   registries unless the task is a registry-wide audit or coordinated edit.

## Schema Authority

Machine-checkable layout and artifact rules should live in structured schema
or data files. Prose docs should point to them instead of restating them.

- Statement and decoration block identity:
  `constitution/schema/block-registry.yaml`
- Required block matrix by artifact type:
  `constitution/schema/artifact-matrix.yaml`
- Volume, chapter, topic, proof folder, proof file, stub, capstone, and
  breadcrumb layout:
  `constitution/schema/file-schema.yaml`
- Audit response shape:
  `constitution/schemas/audit-report.json`

## Primary Source Lookup

Primary mathematical source PDFs are external to the repos under
`D:\Readings\Sources`, with generated LRA lookup artifacts under
`D:\Readings\indexes\lra`. When theorem-like statements or definitions need
source authority, use `docs/governance/source-indexing-policy.md`: if an
explicit `LRA_SOURCES_ROOT` or adjacent `[external:lra-sources]` catalog exists,
read its overarching pointer index first to resolve the active source-profile
checkout, raw reading root, generated index root, topic indexes, and omnibus
indexes. Then check the reviewed topic source indexes in
`[external:lra-source-profiles] volumes/<volume>/<topic...>/source-index.yaml`,
the volume aggregate `volumes/<volume>/_sources/source-index.yaml`, and the
global omnibus indexes under `D:\Readings\indexes\lra\omnibus`. Search both
topic-specific indexes and the omnibus before concluding that no primary source
evidence exists.

## Task Routes

| Task | Required docs | Required schema/data | Required tools | Optional docs | Output artifacts | Validation checks |
| --- | --- | --- | --- | --- | --- | --- |
| Generate chapter artifacts from payload | `docs/workflows/artifact-payload-generation.md`, `docs/governance/atomic-artifact-standards.md`, `docs/governance/notation-standards.md`, `docs/governance/dependency-standards.md` | ordered JSON/JSONL payload, appendable artifact registries, canonical predicates/notation/relations YAML | `tools/import_artifact_payload.py`, `tools/chapter_artifact.py`, deterministic local audit commands | `docs/workflows/proof-layout-audit.md` | payload file, appendable YAML registry, generated notation page, generated LaTeX blocks, proof stubs, chapter manifest, audit report | importer dry-run/write, artifact validate, true-up, box-color audit, proof-layout audit, latexmk build, local registry/symbol check when available without AI |
| Generate section through Codex loop | `docs/workflows/section-generation-codex-loop.md`, `docs/governance/active-content-promotion-gate.md`, `docs/governance/atomic-artifact-standards.md`, `docs/governance/dependency-standards.md`, `docs/governance/proof-standards.md`, `docs/governance/notation-standards.md` | active label map, approved ASCII topic outline, `constitution/schema/block-registry.yaml`, `constitution/schema/artifact-matrix.yaml`, `constitution/schema/file-schema.yaml` | disposable target-repo `codex-prompt`, `tools/governance/validate_volume.py`, volume build wrapper | `docs/governance/extraction-standards.md`, `docs/governance/repo-overlays/lra-volume.md` | topic-split notes files, proof stubs, updated notes/proofs indexes, deleted `codex-prompt`, commit report | user approval before prompt, integrated volume validation, index reachability, LuaLaTeX/build status, prompt deletion before commit |
| Validate volume house rules | `docs/governance/authoring-standards.md`, `docs/governance/dependency-standards.md`, `docs/governance/proof-standards.md`, `docs/governance/exercise-vault-standards.md` | `constitution/schema/block-registry.yaml`, `constitution/schema/artifact-matrix.yaml`, `constitution/schema/file-schema.yaml` | `tools/governance/validate_volume.py` | `docs/workflows/proof-layout-audit.md`, nearby chapter examples | integrated compliance report | `python tools\governance\validate_volume.py <target-repo> --fail-on-errors`; use `--chapter <chapter-name>` only to filter the report while still running the full volume |
| Add theorem with proof stub | `docs/workflows/add-theorem-with-proof-stub.md`, `docs/governance/active-content-promotion-gate.md`, `docs/governance/proof-standards.md`, `docs/governance/dependency-standards.md`, `docs/architecture/local-semantic-logic-verifier.md`; `docs/governance/source-indexing-policy.md` when source authority must be looked up | `constitution/schema/file-schema.yaml`, `constitution/schema/artifact-matrix.yaml`, semantic artifact package; optional `[external:lra-sources]` catalog, topic source index, and omnibus index when source authority is used | `tools/governance/validate_volume.py`, `tools/governance/audit_proof_layout.py`, `tools/governance/validate_semantic_artifact.py`, `tools/governance/validate_semantic_logic.py`, `tools/governance/compare_semantic_ast_extractors.py`, `tools/governance/index_internal_objects.py` | `docs/governance/atomic-artifact-standards.md`, `docs/governance/volume-structure.md` | theorem/proposition/lemma/corollary source with a bracketed display name, canonical proof stub, semantic artifact evidence, `\LeanFormalizes` tag or explicit lra-lean follow-up task | semantic artifact validation, local semantic logic validation, independent AST extractor comparison, integrated volume validation including formal names and LeanFormalizes shape, proof layout audit, volume build |
| Add definition | `docs/governance/active-content-promotion-gate.md`, `docs/governance/authoring-standards.md`, `docs/governance/atomic-artifact-standards.md`, `docs/governance/notation-standards.md`, `docs/governance/latex-math-style.md`, `docs/governance/dependency-standards.md`, `docs/architecture/local-semantic-logic-verifier.md`; `docs/governance/source-indexing-policy.md` when source authority must be looked up; `docs/workflows/internal-object-index-delta.md` when updating lookup | `constitution/schema/artifact-matrix.yaml`, `constitution/schema/block-registry.yaml`, semantic artifact package; optional `[external:lra-sources]` catalog, topic source index, and omnibus index when source authority is used | `tools/governance/validate_volume.py`, `tools/governance/validate_latex_math_style.py`, `tools/governance/validate_semantic_artifact.py`, `tools/governance/validate_semantic_logic.py`, `tools/governance/compare_semantic_ast_extractors.py`, `tools/governance/update_internal_object_index.py`, `tools/governance/index_internal_objects.py`, volume build | `docs/governance/model-standards.md` | definition source with a bracketed display name, semantic artifact evidence, `\LeanFormalizes` tag or explicit lra-lean follow-up task, refreshed internal object index when lookup is part of the task, and any notation/predicate updates | semantic artifact validation, notation/style validation for changed TeX, local semantic logic validation, independent AST extractor comparison, integrated volume validation including formal names and LeanFormalizes shape, internal object delta update/YAML parse when lookup is part of the task, YAML parse when data changes, volume build |
| Add or revise TikZ figure | `docs/governance/atomic-artifact-standards.md`, `docs/governance/tikz-style-guide.md`, `docs/architecture/latex-build-and-rendering.md` | `constitution/schema/file-schema.yaml` when placing figure source in a volume repo | `tools/governance/validate_volume.py`, volume build wrapper when the figure affects rendered output | nearby rendered figure examples, shared styles in `[external:lra-common] common/figures-macros.tex` and `common/boxes.tex` | dedicated figure source file and inclusion block; no local style-guide copy | integrated volume validation, volume build or documented no-build reason |
| Edit LaTeX locally in a volume devcontainer | `docs/workflows/local-tex-devcontainer.md`, `docs/governance/repo-overlays/lra-volume.md` | target `lra-volume-i` through `lra-volume-viii` checkout; adjacent or explicit `lra-common` checkout | `tools/governance/edit_latex.py` | `tools/governance/install_volume_devcontainer.py`, `tools/governance/set_latex_root_comments.py` when active source roots changed | refreshed `.devcontainer/` shim in the target volume and VS Code opened through the Dev Containers flow | launcher exits successfully; VS Code Dev Containers extension or documented plain-code fallback |
| Add proof or populate existing proof stub | `docs/workflows/populate-proof-stub.md`, `docs/governance/active-content-promotion-gate.md`, `docs/governance/proof-standards.md`, `docs/governance/dependency-standards.md`, nearby populated proof files | `constitution/schema/file-schema.yaml`; semantic artifact package when formal logical content changes | `tools/governance/validate_volume.py`, `tools/governance/audit_proof_layout.py`, semantic AST gate tools when formal logical content changes | `docs/governance/handwritten-proof-vault-standards.md`, `docs/architecture/local-semantic-logic-verifier.md` | existing proof file populated in place; semantic artifact evidence when needed | integrated volume validation, proof layout audit, volume build; semantic artifact validation, local semantic logic validation, and independent AST extractor comparison when formal logical content changes |
| Validate or migrate proof stubs | `docs/workflows/proof-stub-invariant-migration.md`, `docs/workflows/proof-layout-audit.md`, `docs/governance/proof-standards.md` | `constitution/schema/file-schema.yaml` | `tools/governance/validate_volume.py`, `tools/governance/audit_proof_layout.py` | `docs/governance/refactoring-standards.md`, `docs/governance/volume-structure.md` | compliance report or targeted stub edits | integrated volume validation plus proof audit when a proof-specific report is needed |
| Audit proof layout | `docs/workflows/proof-layout-audit.md`, `docs/governance/proof-standards.md` | `constitution/schema/file-schema.yaml` | `tools/governance/audit_proof_layout.py` | nearby proof examples | compliant/non-compliant proof list | `python tools\governance\audit_proof_layout.py --root <target> --format json` |
| Generate or validate theorem routes | `docs/workflows/knowledge-extraction.md`, `docs/governance/extraction-standards.md`, `docs/governance/dependency-standards.md` | `constitution/schema/file-schema.yaml` plus route schema in the target leaf repo | target extractor scripts, `tools/governance/validate_volume.py` | `docs/architecture/knowledge-pipeline.md`, `docs/architecture/theorem-explorer-pipeline.md` | theorem route JSON/YAML and route diff artifacts | route generator, route validate-only, integrated volume validation, build wrapper |
| Refactor chapter | `docs/governance/refactoring-standards.md`, `docs/governance/volume-structure.md` | `constitution/schema/file-schema.yaml` | `tools/governance/audit_volume_layout.py`, `tools/governance/audit_proof_layout.py` | `docs/workflows/volume-cleanup.md`, `docs/governance/file-splitting-standards.md` | moved source/proof files, updated indexes, regenerated route metadata, route diff | volume layout audit, proof layout audit, build, theorem-route regeneration/validation when paths move |
| Refactor volume folders or source layout | `docs/governance/refactoring-standards.md`, `docs/governance/volume-structure.md`, `docs/workflows/volume-layout-audit.md` | `constitution/schema/file-schema.yaml` | `tools/governance/audit_volume_layout.py`, `tools/governance/audit_proof_layout.py` | `docs/architecture/multi-repo-sync.md`, `docs/governance/file-splitting-standards.md` | topic-mirrored notes/proofs layout, updated routers, regenerated route metadata, migration report | volume layout audit with `--refactor-mode` during migration and `--strict` after; theorem-route regeneration/validation when paths move |
| Create stub chapter | `docs/governance/stub-chapter-standards.md`, `docs/governance/volume-structure.md` | `constitution/schema/file-schema.yaml` | `tools/governance/generate_stub.py`, `tools/governance/audit_volume_layout.py` | `docs/workflows/volume-cleanup.md` | chapter skeleton, chapter metadata, notes/proofs routers | generate stub chapter, volume layout audit, build or documented no-build reason |
| Create stub section | `docs/governance/stub-section-standards.md`, `docs/governance/volume-structure.md` | `constitution/schema/file-schema.yaml` | `tools/governance/generate_stub.py`, `tools/governance/audit_volume_layout.py` | `docs/governance/stub-chapter-standards.md` | paired `notes/{topic}/` and `proofs/{topic}/` folders and routers | generate stub section, volume layout audit, build |
| Memorialize exercise artifacts | `docs/workflows/exercise-vault-memorialization.md`, `docs/governance/exercise-vault-standards.md` | `exercise-ledger.yaml` in the owning chapter | YAML parser, route existence checks, build command | `docs/governance/refactoring-standards.md`, `docs/governance/volume-structure.md` | copied source photo when present, TeX exercise set, updated ledger, regenerated reports, exercise index routing | ledger parse, duplicate-ID check, route check, build |
| Extract knowledge | `docs/workflows/knowledge-extraction.md`, `docs/governance/extraction-standards.md`, `docs/governance/dependency-standards.md` | `constitution/schema/block-registry.yaml`, `constitution/schema/artifact-matrix.yaml`, target repo route schema | target extractor scripts | `docs/architecture/knowledge-pipeline.md`, `docs/architecture/canonical-yaml.md` | knowledge artifacts and route artifacts | extractor validation, schema parse, route validation |
| Update predicates, structures, relations, or notation | `docs/governance/notation-standards.md`, `docs/governance/latex-math-style.md`, `docs/governance/predicate-standards.md`, `docs/architecture/canonical-yaml.md` | candidate entry plus only the affected canonical YAML file; all four files only for registry-wide audit | `tools/governance/vocabulary.py`, `tools/governance/validate_latex_math_style.py`, symbol audit when available | `docs/governance/dependency-standards.md`, `constitution/prompts/audit-chapter-symbols.md` | canonical YAML changes or audit report plus refreshed disposable index | `vocabulary.py validate`, notation/style validator tests, extractor/build if affected |
| Generate local governance wrappers | `docs/workflows/generated-wrapper-sync.md`, `docs/governance/agent-instruction-policy.md` | wrapper manifest/config files when present | `tools/governance/generate_agent_wrappers.py`, `tools/governance/report_wrapper_drift.py`, `tools/governance/validate_repo_rules.py` | `docs/governance/repo-overlays/README.md`, exactly one relevant overlay | generated wrapper previews only; no fan-out sync | drift report, repo-rule validation |
| Edit shared LaTeX infrastructure | `docs/governance/repo-overlays/lra-common.md`, `docs/architecture/repository-layout.md` | affected macro/schema docs if any | target repo build/tests using the Docker image or explicit `lra-common` checkout | `docs/governance/notation-standards.md`, `docs/governance/decoration-box-standards.md` | macro/package changes in `lra-common`; no fan-out sync | compile target volumes or affected smoke build |
| Work in `lra-lean` | `docs/governance/repo-overlays/lra-lean.md`, `docs/architecture/lra-lean-architecture.md`, `[external:lra-lean] README.md` | Lean modules under `[external:lra-lean] LRA/`, `lakefile.lean`, `lean-toolchain` | `[external:lra-lean] .\build.ps1 docker-build`, `[external:lra-lean] .\build.ps1 build-all`, or Docker/Lake gates from the overlay | `docs/architecture/semantic-artifact-record.md` only when mapping formal verification metadata | Lean declarations, modules, verification metadata comments | Lean build gates; no LaTeX build substitute |
| Prepare Lean <-> TeX verification lookup | `docs/governance/source-indexing-policy.md`, `docs/workflows/internal-object-index-delta.md`, `docs/governance/repo-overlays/lra-lean.md`, `docs/architecture/lra-lean-architecture.md`, `docs/governance/repo-overlays/lra-volume.md` | `docs/governance/source-indexing-policy.yaml`; target TeX volume repo(s); `[external:lra-lean] LRA/` | `tools/governance/update_internal_object_index.py`, `tools/governance/index_internal_objects.py`, downstream crosswalk or verifier scripts | `docs/architecture/local-semantic-logic-verifier.md`, `docs/architecture/semantic-artifact-record.md` when comparing formal statement ASTs | ignored internal object index plus ignored delta state, curated reviewed crosswalk candidates when requested, optional PDF page-map enrichment | delta or full index generation succeeds; YAML/JSON parses; changed TeX/Lean objects are discoverable by stable label/declaration; deleted-file records are removed; do not use PDFs as primary object-discovery source |
| Work in `lra-knowledge-explorer` | `docs/governance/repo-overlays/lra-knowledge-explorer.md`, `docs/governance/code-repo-standards.md`, `docs/architecture/knowledge-pipeline.md`, `docs/architecture/theorem-explorer-pipeline.md`, `docs/workflows/knowledge-extraction.md`, `[external:lra-knowledge-explorer] README.md` | explorer JSON schemas/data conventions in local README/PIPELINE, generated graph artifacts when relevant | `[external:lra-knowledge-explorer] python -m pytest tests`, extraction smoke commands when graph output changes | `docs/governance/extraction-standards.md`, `docs/architecture/local-semantic-logic-verifier.md` when semantic AST fields affect explorer display | extractor/UI changes, graph data refreshes, proof/verification display changes | code layout validator, tests, extraction smoke report, no direct canonical YAML edits |
| Work in `lra-pdf-extractor` | `docs/governance/repo-overlays/lra-pdf-extractor.md`, `docs/governance/code-repo-standards.md`, `[external:lra-pdf-extractor] README.md` | `pyproject.toml`, local `src/`, `tests/`, prompt/config files, staged output schemas | `[external:lra-pdf-extractor] python -m pytest tests` | `docs/architecture/repository-layout.md`, `docs/architecture/multi-repo-sync.md`, `docs/governance/authoring-standards.md` only for candidate-output shape, `docs/governance/repo-overlays/lra-source-profiles.md` only when coordinating source-profile handoff | ingestion/extraction tooling, staged candidate LaTeX/BibTeX/JSON/review outputs | code layout validator, pytest, no direct writes to volume notes, volume bibliography shards, canonical YAML, or explorer generated data |
| Work in `lra-reading-categorizer` | `docs/governance/repo-overlays/lra-reading-categorizer.md`, `docs/governance/code-repo-standards.md`, `[external:lra-reading-categorizer] README.md` | `taxonomy/subjects.yaml`, local `src/`, `scripts/`, `tests/`, review exports when relevant | `[external:lra-reading-categorizer] python -m pytest tests` | `docs/architecture/repository-layout.md`, `docs/architecture/multi-repo-sync.md`, `docs/governance/repo-overlays/lra-source-profiles.md` only when coordinating imported queue data | UI changes, taxonomy/scaffold changes, queue import/export behavior, review exports | code layout validator, pytest, no destructive source-PDF moves, no direct source-profile/extractor/volume/YAML edits |
| Work in `lra-source-profiles` | `docs/governance/repo-overlays/lra-source-profiles.md`, `docs/governance/code-repo-standards.md`, `[external:lra-source-profiles] README.md` | source manifests, folder-to-volume maps, volume workbench profiles, `volumes/<volume>/<chapter>/source-index.yaml`, `active-sources.yaml`, named-profile indexes, active-profile index; `docs/governance/source-indexing-policy.yaml` when scanning the external reading library | `[external:lra-source-profiles] scripts/validate_source_indexes.py`, relevant local source-profile scripts | `docs/architecture/repository-layout.md`, `docs/governance/source-indexing-policy.md` when changing source-index eligibility or volume workbench contracts, `docs/governance/repo-overlays/lra-pdf-extractor.md` only when comparing ingestion boundaries | source profile metadata, volume workbench selections, active-profile exports, category placements, review queues, markdown cache | code layout validator, source index validation, YAML parse, no destructive PDF moves, no direct downstream note/bibliography/YAML edits |
| Work in `lra-exercises` | `docs/governance/repo-overlays/lra-exercises.md`, `docs/architecture/repository-layout.md` | target worksheet/workbook `.tex` source and generated PDF when committed together | Docker `latexmk` build using `docker/lra-exercises-latex/Dockerfile`; `chktex` when useful | nearby worksheet/workbook examples | standalone exercise source and PDF artifacts; no direct volume-repo writes unless explicitly requested | Docker PDF build succeeds; source-adjacent PDF refreshed when source changes; unrelated exercise PDFs untouched |
| Work in a leaf volume repo | `docs/governance/repo-overlays/lra-volume.md`, `docs/architecture/volume-architecture.md` | task-specific schema rows above | task-specific validators above | relevant workflow row for the task | leaf source, proof, route, or build artifacts | leaf build wrapper and task-specific validators |
| Memorialize handwritten proof artifacts | `[external:lra-proof-vault] AGENTS.md`, `[external:lra-proof-vault] README.md`, `[external:lra-proof-vault] routing/theorem-routes.json`, `docs/governance/repo-overlays/lra-proof-vault.md` | route snapshot in `[external:lra-proof-vault] routing/` and canonical proof state in the owning volume | Docker `lra-proof-vault` photo pipeline via `[external:lra-proof-vault] scripts/vault_photo_pipeline.py`, `[external:lra-proof-vault] scripts/apply_leaf_backlinks.py`, `[external:lra-proof-vault] scripts/validate_vault.py --require-leaf-backlinks` | `docs/governance/handwritten-proof-vault-standards.md` | sanitized attempt image, OCR text, Markdown and TeX display artifacts, vault metadata, canonical backlink when accepted, both canonical proof bodies populated, and dependencies populated | Docker photo pipeline validation, proof-vault validator with leaf backlink enforcement when accepted, proof-layout validator, exact route match or explicit user choice, volume validator when canonical proof content changes |
| Audit decoration boxes | `docs/workflows/decoration-audit.md`, `docs/governance/decoration-audit-standards.md` | `constitution/schema/block-registry.yaml`, `constitution/schema/artifact-matrix.yaml` | `tools/governance/audit_latex_decoration.py` when available | `docs/governance/decoration-box-standards.md` | decoration inventory/audit report | decoration audit, statement audit when available |
| Add bibliography entries | `docs/workflows/bibliography-entry.md` | bibliography layout docs/data in target repo | bibliography build/check scripts when present | `docs/governance/authoring-standards.md` | `.bib` entries or split bibliography files | BibTeX/biber parse or target build |
| Audit governance | `docs/workflows/governance-audit.md`, `docs/reports/governance-bloat-audit.md`, this index | `constitution/schema/*.yaml`, `constitution/schemas/*.json` | grep/path/schema sanity scripts | full corpus only as explicit audit exception | audit report or consolidation plan | schema parse, task-index path check, repeated-heading/phrase scan |
| Shrink constitution or move architecture facts | `docs/reports/governance-bloat-audit.md`, `constitution/master.md`, `docs/architecture/repository-layout.md`, `docs/architecture/multi-repo-sync.md` | relevant schema files only where pointers need updates | grep/path sanity checks | affected governance docs | mechanical move plan or small pointer edits | no authority loss, no new duplicate documents |
| Reduce workflow duplication | `docs/reports/governance-bloat-audit.md`, target workflow, canonical governance standard | relevant schema authority for the repeated rule | grep repeated phrases/headings | nearby workflow docs for consistency | shortened workflow with pointers | confirm workflow still has steps, outputs, validation |
| Make prompts consume schema | `docs/reports/governance-bloat-audit.md`, target prompt file | `constitution/schema/block-registry.yaml`, `constitution/schema/artifact-matrix.yaml`, `constitution/schema/file-schema.yaml` as applicable | prompt/schema reference sanity checks | prompt-builder docs if present | prompt with schema pointers or generated schema excerpt plan | prompt still names required inputs and output contract |

## Prompt Routes

Only load constitution prompts when the user is explicitly asking for that
prompted generation or audit mode.

| Prompted task | Prompt file | Schema/data inputs | Deterministic tools/checks |
| --- | --- | --- | --- |
| Generate a proof | `constitution/prompts/generate-proof.md` | `constitution/schema/file-schema.yaml`, `docs/governance/dependency-standards.md` | proof layout audit after writing |
| Generate a theorem statement | `constitution/prompts/generate-statement.md` | `constitution/schema/block-registry.yaml`, `constitution/schema/artifact-matrix.yaml`, `docs/governance/dependency-standards.md` | statement/block audit when available |
| Generate a stub chapter | `constitution/prompts/generate-stub-chapter.md` | `constitution/schema/file-schema.yaml` | volume layout audit |
| Generate a stub volume | `constitution/prompts/generate-stub-volume.md` | `constitution/schema/file-schema.yaml` | volume layout audit |
| Generate a capstone | `constitution/prompts/generate-capstone.md`, `docs/governance/capstone-exercise-standards.md` | `constitution/schema/file-schema.yaml`, `constitution/schema/artifact-matrix.yaml` | volume build or chapter audit |
| Generate breadcrumbs | `constitution/prompts/generate-breadcrumb.md` | `constitution/schema/file-schema.yaml` | path/layout sanity check |
| Audit a proof | `constitution/prompts/audit-proof.md` | `constitution/schema/file-schema.yaml`, `constitution/schemas/audit-report.json` | proof layout audit |
| Audit a statement | `constitution/prompts/audit-statement.md` | `constitution/schema/block-registry.yaml`, `constitution/schema/artifact-matrix.yaml`, `constitution/schemas/audit-report.json` | statement/block audit when available |
| Audit a stub | `constitution/prompts/audit-stub.md` | `constitution/schema/file-schema.yaml`, `constitution/schemas/audit-report.json` | volume layout audit |
| Audit chapter symbols | `constitution/prompts/audit-chapter-symbols.md` | canonical notation/predicate/relation YAML in the owning repo | YAML parse, symbol audit when available |
| Fix logical block gaps | `constitution/prompts/fix-logical-block-gaps.md` | `constitution/schema/block-registry.yaml`, `constitution/schema/artifact-matrix.yaml` | statement/block audit when available |
| Plan toolkits | `constitution/prompts/plan-toolkits.md` | `constitution/schema/block-registry.yaml`, `constitution/schema/artifact-matrix.yaml` | toolkit/decoration audit when available |

