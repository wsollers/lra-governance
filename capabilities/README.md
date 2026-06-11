# capabilities/ — LRA agent capability system (consolidation target)

Consolidated, skill-shaped replacement for the scattered standard + workflow + prompt triplication.
ONE capability = ONE folder = trigger + procedure + bound verifier.

## Layout
- `ENTRYPOINT.md`            canonical agent entrypoint (the only routing file edited by hand)
- `generate_entrypoints.py` emits full per-vendor copies (CLAUDE/AGENTS/GEMINI/copilot/cursor) — generated-full, CI-synced
- `index.md`                capability manifest (task -> capability)
- `overlays/<repo>.md`      per-repo overlay (the "you are working in lra-X" layer)
- `<capability>/`           `capability.md` (procedure) + `verify.py` (bound post-gen verifier)

## Hard invariant
A generate capability is NOT complete until its bound verifier exits 0 on the written artifact.

## Adding the next capability
1. Copy `author-definition/` as template.
2. Write `capability.md` (trigger, reads, procedure, bound verifier).
3. Write/point `verify.py` (runs on a single target file; exits nonzero on violation).
4. Add ONE row to `index.md`.
5. MOVE the old standard+workflow+prompt content into `capability.md` and DELETE the sources.
   Net file count must drop. Update the old task-index row to point here.

## Migration rule
Port by MOVING text, not rewriting rules. A diff should be mostly moves.

## Vendor entrypoints
`generate_entrypoints.py` produces full copies of `ENTRYPOINT.md` under each vendor's expected
filename (CLAUDE.md, AGENTS.md, GEMINI.md, .github/copilot-instructions.md, .cursor/rules/lra.mdc).
These are GENERATED and CI-synced; never hand-edit them. Edit `ENTRYPOINT.md` and regenerate.
