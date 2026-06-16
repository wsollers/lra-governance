# LRA Refactor — Continuation (Phase: Capabilities Finish · De-Bloat · Account-For)

I'm William Sollers, an experienced SWE doing rigorous deep self-study math, building
"Learning Real Analysis" (LRA): a multi-volume LaTeX project (Vols I–VIII) + a governance
system + knowledge-graph extraction + Lean formalization + a web "Knowledge Explorer," aimed
ultimately at Brownian motion on a torus rendered via Vulkan. You are my engineering
collaborator on the governance/tooling. Be candid, no sycophancy, push back when I'm wrong,
verify before asserting, and don't skip logical steps — I learn slowly and deeply.

## STATUS LINE
The **volume structural refactor just ran** (relocation + cleanup + capstones + breadcrumbs
across all 8 volumes). The new mission is to **finish the capability system**, **slim the
whole governance toolchain (de-bloat)**, and **account for everything** — nothing orphaned,
legacy retired only at proven parity.

## START HERE (first task this session)
Audit the WHOLE governance toolchain as it stands now — validator engine (`tools/governance/`)
+ capability system (`capabilities/`) + resolver/overlays + the migration toolchain
(`tools/migration/`, incl. the new `standardize.py`). Read current repo state first; don't
guess ("the box mistake"). Deliver as **bloat → gaps → plan**, and do not cut or build until
we've agreed on the findings.

1. **Bloat pass.** Redundancy, dead code, over-engineering, duplicated logic, unused
   knobs/flags, premature abstraction. Concrete (file + line + why) + proposed cuts. Specific
   targets to scrutinize this round:
   - `tools/migration/` now holds ~15 scripts. Several are one-shots that have **served their
     purpose** in the sweep (e.g. `migrate_chrome_boxes`, `remove_structural_roadmap`,
     `blank_stub_proof_structure`) — candidates to archive. The `identify_*`/`relocate_*`
     pairs and `standardize.py` are the keep-and-consolidate core.
   - Standalone validators that overlap the engine (see Gap pass).
   - Legacy `audit_latex_decoration.py` + LLM generators/prompts (retire at parity only).
2. **Gap / coverage pass (the EQUAL-COVERAGE ledger).** Where does the new engine NOT yet
   cover what the old validators do? What house rules are enforced in practice but not yet
   encoded? Extend existing pieces to close gaps — don't add new one-offs.
3. **Account-for + activation/retire plan.** Checklist-grade, ordered: what to wire as the
   default path, what legacy to retire now that parity is proven, what one-shot migration
   scripts to archive, and the exact commands/order. Fold the capability-system open TODOs
   (below) into this same plan.

## Design philosophy (the lens for the whole audit)
**MAXIMIZE COVERAGE, MINIMIZE BLOAT.** The corpus is HIGHLY STRUCTURED TEXT, so deterministic
Python parsing/rules resolve the overwhelming majority — lean into that.
- Fewer components, each resolving MORE. Consolidation over proliferation: one engine + a
  small set of composable rules/primitives, not a sprawl of one-off scripts.
- Deterministic Python over LLM calls wherever structure permits. Reserve LLM generation
  strictly for genuinely variable MATH CONTENT; everything structural (chrome, layout,
  routing, validation, naming, placement, sweeps) is a macro or a pure function.
- Every rule/flag/knob/file must earn its keep. If two things do almost the same thing, merge.
  If a knob is never exercised, cut. If a validator can be a rule in the engine, fold it in.
- North star: a SMALL number of powerful, well-tested deterministic pieces giving MAXIMAL
  house-rule coverage across all volumes — coverage gained per unit of surface area added.

## Working style / HARD RULES
- **Additive only.** NEVER restart or rebuild from scratch.
- **Parallel-run.** Do NOT delete any old generator/prompt/validator until the new system is
  proven at EQUAL COVERAGE on a real volume.
- **Read before building.** Pull the CURRENT repo file and read it before editing. Don't guess
  structure. (I have twice asserted volume structure without checking and been wrong — verify.)
- **Prove one slice, then replicate.** Build-and-prove over propose.
- **No skipped steps.**

## Environment facts (two filesystems — critical)
- I edit on Windows at `F:\repos\...` via the **Filesystem MCP**: `read_text_file`,
  `write_file` [OVERWRITES whole file], `edit_file` [line-based diff, PREFER this],
  `create_directory`, `directory_tree`, `search_files`, `copy_file_user_to_claude`
  [user→Claude only]. **The Filesystem MCP has NO move/delete/execute verb.**
- You have a Linux container (`bash`, `/home/claude`) that **RESETS BETWEEN TURNS** and
  **CANNOT see `F:\`**. Use it only to mirror/syntax-test code (`py_compile`, unit cases),
  never as the live filesystem.
- Therefore the loop is: **read live `F:\` → mirror/test in the sandbox → write/edit live →
  re-verify.** Anything that must RUN a script, MOVE/DELETE a file, or use `git` is run **by
  me in PowerShell**. Hand me exact commands.
- Allowed dirs: `F:\repos`, `D:\Readings`. Call `list_allowed_directories` once before other FS
  tools. CI syncs read-only `common/`+`governance/`+`constitution/` overlays into each volume
  repo root — that is INTENTIONAL downstream copy, not drift.

## Repo landscape (paths verbatim)
- Governance source of truth: `F:\repos\lra-governance\` — `tools/governance/` (engine +
  standalone validators), `tools/migration/` (migration + sweep tools), `capabilities/`
  (agent-capability system), `constitution/` (schema + auditor/generators), `reports/`,
  `prompts/`, `docs/`.
- Volume repos `F:\repos\lra-volume-i` … `lra-volume-viii`; content at
  `volume-<r>/` (chapters are immediate subdirs; `volume-<r>/index.tex` is the assembly).
- Monorepo `F:\repos\Learning-Real-Analysis\` holds canonical `predicates.yaml`,
  `notation.yaml`, `relations.yaml` at root. `structures.yaml` does NOT exist yet.
- Shared LaTeX `F:\repos\lra-common\common\`: boxes.tex, macros.tex (`\LRAProofFor` is a no-op
  marker here), breadcrumb-macros.tex, structural-presentations.tex, proof-template.tex, etc.

## What was just built / current ground truth

### Volume refactor (this just happened)
- **`tools/migration/standardize.py`** — one-shot orchestrator. Sequences the proven tools via
  subprocess (does NOT re-implement them): per volume **A.** cleanup (`remove_status_planned`,
  `remove_legacy_chrome`, optional `purge_archives`) → **B.** relocate (`relocate_misplaced_notes`
  then `relocate_misplaced_files`) → **C.** read-only recon gate (`identify_*`) → **D.** fill
  (`create_missing_proofs`, `ensure_capstones --upgrade-empty`); `--all` runs A–D for every
  volume then GLOBAL breadcrumbs once. Dry-run by default, `--apply` writes, stops on first
  error. Modes: `--root <vol>`, `--all`, `--breadcrumbs`. Syntax-validated.
- **Migration toolchain** (`tools/migration/`): `recon_volumes`, `identify_misplaced_files`,
  `identify_misplaced_notes`, `identify_missing_proofs`, `relocate_misplaced_files`,
  `relocate_misplaced_notes`, `create_missing_proofs`, `ensure_capstones`,
  `remove_status_planned`, `remove_legacy_chrome`, `purge_archives`, `populate_breadcrumbs`,
  plus older one-shots (`blank_stub_proof_structure`, `migrate_chrome_boxes`,
  `remove_structural_roadmap`). All dry-run by default + `--apply`; idempotent; CRLF preserved;
  archive/ + .git excluded.
- **Ran `standardize.py --all --apply` across all 8 volumes — all reported `ok`.** Working
  trees are now DIRTY (uncommitted), fully revertable. Review/commit per volume, or
  `git checkout` to revert and re-run (everything is idempotent).
- **CORRECTION locked in:** Vol II (and *likely* III — VERIFY before assuming) notes ARE
  topic-ized, so relocation is **MECHANICAL** — `relocate_misplaced_files` resolves each legacy
  proof's topic from its note's `\LRAProofFor`/return-link/`% Source:`/shared-root. NOT a
  guided build. Needs-human residue only: **integers (DEFERRED** until after ℕ→𝕎; it's the
  first quotient/equivalence-class construction), flat stragglers (`natural-numbers/notes.tex`,
  `reals/notes.tex`, `notes-nz-axioms.tex`, `reals/capstone.tex` legacy), the misnamed
  `natural-numbers/notes/archive-current-live` (purge with `--name archive-current-live`), and
  stub chapters (nothing to move). Tao-vs-Mendelson is parked for a closing expository chapter.
- **Breadcrumb parser bug FIXED:** `populate_breadcrumbs.yaml_field` now strips one layer of
  matching YAML quotes and treats empty as absent (slug fallback) — was emitting
  `{"Quoted Title"}` and `{''}`. Added `display_title` to 6 chapters (Vol VIII: model-theory,
  proof-theory, type-theory, lambda-calculus, algebras-of-sets; Vol VII: numerical-analysis).
  **PENDING: re-run `standardize.py --breadcrumbs --apply`** to propagate the new titles
  (replaces existing macros in place — no revert needed).

### Validator engine (`tools/governance/`)
- `decoration_rules.py` — composable `@rule`/`@file_rule` engine. Per the recent fold-in, file
  rules now include `chapter_identity`, `section_router_heading`, `note_body_heading`,
  `reference_voice`, `latex_integrity`, `formal_block_decoration` (ported from
  `validate_chapter_house_rules` at EQUAL COVERAGE on fixtures), plus the earlier
  `formal_reading_required` + `proof_stub_structure_blank` + the original decoration/label/box
  rules. **VERIFY the exact current rule set by reading the file** before folding in more.
- `validate_decoration.py` (CLI; `--canonical-dir`, `--no-formal-reading`, `--chapter/--volume/
  --section`), `formal_reading.py` (trigger dictionary from predicate names), `tex_codec.py`
  (TeX↔base64), `test_decoration_rules.py`.
- **Remaining fold-in / parity targets** (still standalone):
  `audit_proof_layout`, `audit_volume_layout`, and the REST of `validate_chapter_house_rules`
  (proof-file structure suite, exercises, dependency-target resolution, generated-artifact
  markers, formal-tcolorbox styles). The monster's breadcrumb/toolkit CHROME checks are STALE
  (the `\breadcrumb{}`/`\toolkitbox` macros are canonical) → DROP, do not port.
- **Retire ONLY at parity:** `audit_latex_decoration.py` + LLM generators/prompts.

### Capability system (`capabilities/`)
- `manifest.yaml` v2 + `resolve.py` (repo→kind via `overlays-config.yaml`, applies_to filter,
  whole-word longest-match triggers, bound verifiers). `test_resolve.py` 8/8.
- Capabilities: author-statement / author-definition / author-stub-chapter / author-stub-section
  (volume); author-lean-theorem (lean); cpp-build-task (cpp). `ENTRYPOINT.md` (canonical agent
  entrypoint) + `generate_entrypoints.py` (vendor copies, CI-synced); `index.md`;
  `overlays/<repo>.md` + `generate_overlays.py`.

## Key decisions / conventions
- **Relocation resolves topic FROM the note**, so a chapter whose notes are topic-ized is fully
  mechanical; a chapter with flat notes (integers) is needs-human and correctly skipped.
- **Engine vs monster:** macro files are canonical → the engine's macro-based chrome rules are
  correct; the monster's tcolorbox-chrome checks are stale and get dropped, not ported.
- **base64** all machine-extracted TeX (encode at extraction, decode at use; `tex_codec.py`).
  Do NOT blanket-encode hand-authored registries (`predicates.yaml`) — QUOTE offending scalars
  instead (keeps readability).
- **Capabilities are repo-KIND scoped**; non-volume repos get domain capabilities + domain
  verifiers. Atomic author-statement: provable kinds emit statement + linked proof stub in one
  step; def/axiom get no stub.
- **Test-runner pattern:** test files collect only `test_*` defined ABOVE the
  `if __name__ == "__main__":` block — append new tests above it.

## Open findings (gaps)
- `predicates.yaml` does NOT parse as YAML (~line 903 `formal: |x - c| < r` — leading `|` is a
  block-scalar indicator → `yaml.safe_load` throws). QUOTE it. (`formal_reading.py` regex-
  extracts names to sidestep this for now.)
- No explicit `surface_forms` in predicates.yaml → forms derived from CamelCase names
  (imperfect; small stoplist). "bounded"/"continuous"/"monotone" MISS because they're
  monomorphized (BoundedSet, ContinuousAt, …) with no canonical base predicate — the predicate
  cleanup (R1 collapse) unblocks them.
- `proof-template.tex`'s commented stub example is stale vs current `audit_proof_layout`.

## Owner-defined TODOs I still owe you (decisions tools can't guess)
1. **`overlays-config.yaml` volume titles ii–viii** are still `TODO` (Vol I = "Logic, Sets, and
   Proof"; IV `plain_style: true` set). Fill them, confirm IV is the only plain-style, then run
   `python capabilities/generate_overlays.py` to materialize all 13 overlays.
2. Confirm exact build commands in `manifest.yaml`: `lake build` (lean), `cmake --build build`
   vs `make` (cpp).
3. Lean standards doc + lean-theorem→(volume, file, label) sync mapping (author-lean-theorem
   waits on these).
4. **Full cross-volume `display_title` scan** — only the last 8 chapters of the global chain
   were checked; earlier volumes likely have missing/empty titles that render as slugs.
5. Record in `reports/standardization-runbook.md`: *integers deferred (build after ℕ→𝕎); Vol II
   relocation mechanical via topic-ized notes; III to verify the same way* (supersedes the old
   "Vol II/III guided build" note).
6. Add a **movable/needs-human split column** to `recon_volumes.py` (`identify_misplaced_files`
   already computes per-item `status`; recon currently tallies KIND only).
7. Open rulings: proof-obligation default (broad vs `--require-proof-link`); rename-to-`prf-`
   default in relocate; delete vestigial empty `proofs/notes/` dirs; root `exercises/` + root
   `capstone.tex` legacy disposition.
8. **IV/V flatten** still queued (nested chapters up one level; I edit the index `\input` paths
   via `edit_file`, you run the `git mv` for the dir moves).

## Pending next steps (priority order — AFTER the START-HERE audit)
1. Re-run `standardize.py --breadcrumbs --apply` to propagate the 6 new display titles; review
   and commit the `--all --apply` working trees (or revert + re-run).
2. **De-bloat sweep of `tools/migration/`** — archive served-purpose one-shots, consolidate the
   identify/relocate pairs behind `standardize.py`. Parallel-run: keep until confirmed unused.
3. **Finish capabilities:** fill volume titles → `generate_overlays.py`; confirm build commands;
   regenerate vendor entrypoints (`generate_entrypoints.py`).
4. **Engine parity:** fold the remaining standalone validators (`audit_proof_layout`,
   `audit_volume_layout`, rest of `validate_chapter_house_rules`) into the
   engine; reach parity; ONLY THEN delete `audit_latex_decoration.py` + LLM generators/prompts.
5. Predicate cleanup R1–R7 + sweeper (fix the YAML quoting bug first) → unblocks "bounded"
   trigger, canonical-name check, model-card fan-in.
6. Canonical-name check for predicate readings (highest-value unported math-block rule).
7. CI wiring (run `validate_decoration` + `audit_*` + tests). Then `structures.yaml` + model
   cards (deferred — "lots of reading/thinking").

REMINDER OF THE HARD RULE: nothing old gets deleted until the new engine is proven at EQUAL
COVERAGE on a real volume. To start: confirm you've read the current state, then deliver the
START-HERE audit (bloat → gaps → account-for/activation plan) before any new building.
