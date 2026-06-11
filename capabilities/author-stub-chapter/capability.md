# Capability: author-stub-chapter

## Trigger
Scaffold a planned chapter ("stub a chapter X under <volume>", optionally "with sections A, B, C").

## Composition
global core (`ENTRYPOINT.md`) + `overlays/<repo>.md` + this capability + bound verifier.

## Behaviour (pure Python, no LLM)
Deterministic filesystem manipulation -- this capability calls NO model. It scaffolds the
minimum layout-compliant chapter and, if sections are named, invokes `author-stub-section`
for each (in the given order) directly in Python.

Creates in `<volume-root>/<subject>/`:
1. `index.tex` (chapter router): `\chapter{Title}`, then `\breadcrumb{...}` (from the registry
   neighbours) + `\stubstatus` + `\chapterroadmap{prior}{next}{topics}` as the first content,
   then `\input{notes/index}` and `\input{proofs/index}`. No Structural Roadmap. No capstone.
2. `chapter.yaml` (subject, display_title, volume, status: planned, sections, prior/next).
3. `notes/index.tex` (notes router; sections get `\section` + `\input` here, in order).
4. `proofs/index.tex` (proofs router; matching proof topics get `\input` here, in order).
5. `proofs/exercises/` (required dir; `.gitkeep`). Capstone is deferred to `author-capstone`.
Then routes the chapter into BOTH volume routers if present: `<volume-root>/index.tex`
(monorepo assembly) and `<volume-root>/main.tex` (local build).

Section names are passed on the command line in dependency order (`--sections "A; B; C"`);
the Python splits and iterates -- the LLM never orchestrates the loop.

## Inputs
- `--volume-root` (e.g. `.../volume-iii`), `--subject`, `--title`
- `--sections "Title 1; Title 2; ..."` (optional, dependency order)
- `--registry <json>` (list of {subject, display_title} in dependency order; supplies breadcrumb/roadmap neighbours)

## Bound verifier (MANDATORY -- task not complete until exit 0)
    python tools/governance/audit_volume_layout.py --root <volume-root> --chapter <subject> --strict
Also clean under the decoration validator (breadcrumb is first content):
    python tools/governance/validate_decoration.py --root <volume-root> --chapter <subject>
A generated stub that does not pass these is a defect in this capability, not in the artifact.
