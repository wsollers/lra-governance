# LRA Refactor — Continuation (Capability System / Resolver / Overlays / Validator Engine)

I'm William Sollers, an experienced SWE doing rigorous deep self-study math, building
"Learning Real Analysis" (LRA): a multi-volume LaTeX project (Vols I–VIII) + a governance
system + knowledge-graph extraction + Lean formalization + a web "Knowledge Explorer."
You are my engineering collaborator on the governance/tooling. Be candid, no sycophancy,
push back when I'm wrong.

## START HERE (first task this session)
Before building anything new, run a structured audit of the NEW system we've been building
(the validator engine + capability system + resolver + overlays), in this order:

1. **Bloat pass.** Look across the new code for redundancy, dead code, over-engineering,
   duplicated logic, unused knobs/flags, premature abstraction, and anything that earns its
   keep poorly. Call it out concretely (file + line + why) and propose cuts. Bias toward a
   lean system.
2. **Gap pass (new vs. current).** Compare the new system against what's ALREADY there (the
   old validators/generators it's meant to replace, plus the house rules actually enforced in
   the volumes today). Where does the new system NOT yet cover what the old one does? What
   house rules exist in practice but aren't encoded as rules yet? This is the EQUAL-COVERAGE
   ledger.
3. **Actionable activation + sweep plan.** Produce a concrete, ordered plan to (a) get the new
   system ACTIVE (wired in, default path, old system still parallel-running until parity),
   and (b) sweep ALL volumes and bring them into spec — chapter by chapter, with the exact
   commands to run and the order to run them. The plan must be checklist-grade: I should be
   able to execute it step by step.

Read the current repo state first (don't guess), then deliver the audit as bloat → gaps →
plan. Don't start cutting or building until we've agreed on the findings.

## Design philosophy (the lens for the whole audit)
MAXIMIZE COVERAGE, MINIMIZE BLOAT. The corpus is HIGHLY STRUCTURED TEXT, so deterministic
Python parsing/rules can resolve the overwhelming majority of it — lean into that.
- Fewer components, each resolving MORE. Prefer consolidation over proliferation: one
  engine + a small set of composable rules/primitives, not a sprawl of one-off scripts.
- Deterministic Python over LLM calls and loose tooling wherever the structure permits.
  Reserve LLM generation strictly for genuinely variable MATH CONTENT; everything
  structural (chrome, layout, routing, validation, naming, placement, sweeps) is a macro
  or a pure function.
- Every rule/flag/knob/file must earn its keep. If two things do almost the same thing,
  merge them. If a knob is never exercised, cut it. If a validator can be a rule in the
  engine, fold it in.
- North star: a SMALL number of powerful, well-tested deterministic pieces that together
  give MAXIMAL house-rule coverage across all volumes — judged by coverage gained per unit
  of surface area added.
Apply this lens in the bloat pass (what to cut/merge) AND the gap pass (close coverage by
extending existing pieces, not by adding new ones).

## Working style / HARD RULES
- Additive changes only. NEVER restart or rebuild from scratch.
- Parallel-run: do NOT delete any old generator/prompt/validator until the new system is
  proven at EQUAL COVERAGE on a real volume.
- Read before building — pull the CURRENT repo file and read it before editing. Don't guess
  at structure ("the box mistake" is the cautionary tale).
- Prove one slice, then replicate. Build-and-prove over propose.
- No skipped steps; I learn slowly and deeply.

## Environment facts (two filesystems)
- I edit on Windows at `F:\repos\...` via the Filesystem MCP (read_text_file, write_file
  [OVERWRITES whole file], edit_file [line-based diff], create_directory,
  copy_file_user_to_claude [user→Claude only, lands in /mnt/user-data/uploads/]).
- You have a Linux container (bash, /home/claude) that RESETS BETWEEN TURNS. /mnt/user-data
  persists within a session but uploads copies go STALE vs the repo across turns.
- RECURRING HAZARD: stale uploads copies. ALWAYS re-pull the current repo file via
  copy_file_user_to_claude before editing/testing; prefer edit_file (targeted) over
  write_file (wholesale) so you don't silently revert prior fixes. This has bitten twice.
- To test repo Python: copy_file_user_to_claude each dep → cp into a working dir →
  `pip install pyyaml --break-system-packages`.
- The test runner pattern in test files collects only `test_*` defined BEFORE the
  `if __name__ == "__main__":` block — append new tests ABOVE it.

## Repo landscape (paths verbatim)
- Volume repos `F:\repos\lra-volume-i` … `lra-volume-viii`. Volume root = `volume-X/index.tex`
  (monorepo assembly) + `volume-X/main.tex` (local build). BOTH get chapter `\input`s.
- Monorepo `F:\repos\Learning-Real-Analysis\` holds canonical YAML at root: `predicates.yaml`,
  `notation.yaml`, `relations.yaml`. `structures.yaml` does NOT exist yet (blocks model cards
  + structure triggers).
- Shared LaTeX `F:\repos\lra-common\common\`: boxes.tex, macros.tex, environments.tex,
  structural-presentations.tex, proof-template.tex, breadcrumb-macros.tex, etc.
- Governance `F:\repos\lra-governance\`: `tools/governance/` (the validator engine + helpers),
  `capabilities/` (the agent-capability system), `constitution/auditor/` (older LLM generators).

## What was just built (deployed, verified)
**Validator engine** (`tools/governance/`):
- `decoration_rules.py` — composable @rule/@file_rule engine. NEW this refactor:
  `formal_reading_required` (block rule) and `proof_stub_structure_blank` (file rule).
- `formal_reading.py` — trigger-dictionary loader: fixed LOGIC FLOOR (symbols + words) +
  concept surface forms regex-extracted from predicate `name:` fields (CamelCase→words),
  small COMMON_NOUN_STOPLIST, whole-word/hyphen-tolerant matching, `lra:simple` opt-out
  detector, `has_formal_reading` detector. 247 names → 238 trigger forms.
- `validate_decoration.py` — CLI; NEW flags `--canonical-dir` (loads triggers + prints gap
  report) and `--no-formal-reading`.
- `test_decoration_rules.py` — 37/37 passing.
- `tex_codec.py` — TeX↔base64 codec, self-marking `b64:` prefix, encode_fields/decode_fields.
- Standalone validators still living OUTSIDE the engine: `validate_note_blocks`,
  `validate_chapter_house_rules`, `audit_proof_layout`, `audit_volume_layout`, plus the
  legacy `audit_latex_decoration.py`. (These are the parity/fold-in targets.)

**Capability system** (`capabilities/`):
- `manifest.yaml` (v2) — each capability has `applies_to` (repo KINDS), triggers, reads,
  verify command templates. Capabilities: author-statement / author-stub-chapter /
  author-stub-section (applies_to [volume]); author-lean-theorem (applies_to [lean],
  verify `cd {root} && lake build`); cpp-build-task (applies_to [cpp], verify
  `cd {root} && cmake --build build`).
- `resolve.py` — (repo, task) resolver. Maps repo→kind via overlays-config.yaml, filters
  capabilities by applies_to, whole-word longest-match trigger matching, binds verifier(s)
  with {root}/{chapter}/{canonical}/{target}. `--emit` concatenates the bundle. Proven:
  volume tasks reject in lean; lean "formalize" → author-lean-theorem; cpp "do task" →
  cpp-build-task.
- `overlays-config.yaml` + `generate_overlays.py` — single-source overlay generator. Volume
  overlays (Vol IV plain_style → `--no-require-box`); non-volume overlays describe each repo's
  OWN domain capabilities (NOT "capabilities don't apply" — "capabilities not yet defined
  here"). 13 repos configured.
- `author-statement/` (proof_stub.py + capability.md), `author-stub-chapter/`,
  `author-stub-section/`, `author-lean-theorem/capability.md`, `cpp-build-task/capability.md`,
  `ENTRYPOINT.md`, `index.md`, `generate_entrypoints.py`.

**Verified:** `\LRAProofFor` IS defined in `lra-common/common/macros.tex` as a no-op marker —
generated proof stubs compile.

## Key decisions / conventions
- formal_reading_required: a statement invoking a logic-floor token OR a registered
  predicate/object/structure surface form needs a `remark*[Standard quantified statement]`
  reading. Trigger-without-reading = error; `% lra:simple` (no trigger) is the opt-out;
  marked-simple-but-triggers = error. Whole-word only. The dictionary IS the registry.
- proof_stub_structure_blank: while a proof is a STUB (both bodies TODO), the
  `remark*[Proof structure]` block must be blank; planned-proof prose in a stub = error.
  Complements audit_proof_layout (which checks PRESENCE).
- base64 [DECISION]: base64 ALL machine-extracted TeX (encode at extraction, decode at use) —
  use tex_codec.py. For hand-authored canonical registries (predicates.yaml): do NOT
  blanket-encode (destroys readability) — QUOTE the offending scalar
  (`formal: "|x - c| < r"`) OR encode only long-form non-validation fields, keeping
  structural fields (name/id/arity) plain.
- Capabilities are repo-KIND scoped; non-volume repos get domain-specific capabilities with
  domain verifiers (lean→lake build + sync to volume; cpp→project builds).
- Atomic author-statement: provable kinds (thm/lem/prop/cor) emit statement + linked proof
  stub in ONE step; def/axiom get no stub.

## Open findings (gaps)
- `predicates.yaml` does NOT parse as YAML: line ~903 `formal: |x - c| < r` — leading `|`
  read as a block-scalar indicator → yaml.safe_load throws. Quote it. (formal_reading.py
  regex-extracts names to sidestep this.)
- No explicit `surface_forms` field in predicates.yaml → forms derived from CamelCase names
  (imperfect; 8 single-words stoplisted).
- "bounded" / "continuous" / "monotone" MISS as triggers because there's no canonical
  `Bounded`/`Continuous`/`Monotone` predicate — they're monomorphized (BoundedSet,
  BoundedSequence, ContinuousAt, …). The predicate cleanup (R1 collapse) unblocks them.
  The Cauchy lemma still triggers via "cauchy sequence".
- `proof-template.tex`'s commented stub example is stale vs the current audit_proof_layout.

## Owner-defined TODOs I still owe you
1. Lean standards doc + lean-theorem→(volume, file, label) sync mapping (author-lean-theorem
   waits on these).
2. Confirm exact build commands: `lake build` (lean), `cmake --build build` vs `make` (cpp).
3. Fill volume titles ii–viii in overlays-config.yaml; confirm Vol IV is the only plain-style.
4. Run `python capabilities/generate_overlays.py` to materialize all 13 overlays.

## Pending next steps (priority order — AFTER the audit above)
1. **Predicate cleanup R1–R7** + apply sweeper (sweep_predicates.py). HIGHEST LEVERAGE —
   unblocks "bounded" trigger, canonical-name check, and model-card fan-in. Owner-driven
   rulings needed. (Fix the YAML quoting bug first.)
2. **Canonical-name check** for predicate readings (does the reading use the registered
   `\operatorname`?) — highest-value unported math-block rule; makes author-statement catch
   real errors, not just missing blocks.
3. Fold the 4 standalone validators (validate_note_blocks, validate_chapter_house_rules,
   audit_proof_layout, audit_volume_layout) into the engine → reach PARITY → only THEN delete
   old audit_latex_decoration.py + LLM generators/prompts.
4. Remaining ~7 analyze_block ports (required-block-per-kind schema-driven from
   artifact-matrix.yaml, negated-quantified, failure-modes, predicate-leak, multiple-objects,
   oversized-block, dependency-hyperref resolution). TOC validators "make better" (read them
   first).
5. Executable author-statement orchestrator (append + route + verify as one command;
   currently a documented procedure). Full-proof authoring (fill TODO bodies → compliant_full).
6. Make author-lean-theorem real once the standards doc exists (name-derivation + placement
   are deterministic).
7. structures.yaml + model cards + `\modelcard` macro (deferred — "lots of reading/thinking").
8. CI wiring (run validate_decoration + audit_* + tests). Per-volume registry file feeding
   breadcrumb/roadmap neighbors (currently hand-passed --registry JSON). Bulk regeneration
   pass (emit breadcrumb/roadmap, purge flagged Structural Roadmaps).

REMINDER OF THE HARD RULE: nothing old gets deleted until the new engine is proven at EQUAL
COVERAGE on a real volume.

To start: confirm you've read the current state, then deliver the START-HERE audit
(bloat → gaps → activation/sweep plan) before any new building.
