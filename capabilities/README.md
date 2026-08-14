# capabilities/ — LRA agent capability system (consolidation target)

Consolidated, skill-shaped replacement for the scattered standard + workflow + prompt triplication.
ONE capability = ONE folder = trigger + procedure + bound verifier.

## Layout
- `ENTRYPOINT.md`            active canonical global instruction layer selected by `manifest.yaml`
- `generate_entrypoints.py` emits full per-vendor copies (CLAUDE/AGENTS/GEMINI/copilot/cursor) — generated-full, CI-synced
- `index.md`                capability manifest (task -> capability)
- `overlays/<repo>.md`      per-repo overlay (the "you are working in lra-X" layer)
- `<capability>/`           `capability.md` (procedure) + `verify.py` (bound post-gen verifier)

## Hard invariant
A generate capability is NOT complete until its bound verifier exits 0 on the written artifact.

## Adding the next capability
1. Copy a small existing capability directory as a structural template.
2. Write `capability.md` (trigger, reads, procedure, bound verifier).
3. Write/point `verify.py` (runs on a single target file; exits nonzero on violation).
4. Add ONE row to `index.md`.
5. MOVE the old standard+workflow+prompt content into `capability.md` and DELETE the sources.
   Net file count must drop. Update the old task-index row to point here.

## Migration rule
Port by MOVING text, not rewriting rules. A diff should be mostly moves.

## Entrypoint and vendor wrappers

The root `AGENTS.md` is the repository bootstrap: it locates governance and
runs `resolve.py`. The active global instruction layer is selected by the
manifest's `entrypoint` field and is loaded by the resolver before one repo
overlay and one route packet.

Provider wrappers are generated pointer/bootstrap artifacts. They must not
fork the global instruction layer or embed a second routing table. Edit the
canonical bootstrap/template sources and regenerate; do not patch generated
downstream wrappers by hand.
