# Capability Manifest (router)

> **Continuing this refactor?** Read `capabilities/CONTINUATION.md` first — it carries the
> working rules, current state, open findings, and the START-HERE audit (bloat → gaps →
> activation/sweep plan).
>
> **Machine source of truth:** `capabilities/manifest.yaml` (consumed by `resolve.py`) is now
> authoritative for triggers / `applies_to` / verifiers. This table is the human view and is
> KNOWN-STALE (still lists `author-definition`; missing lean/cpp); reconcile it in the audit.

Match your task to ONE row. Load only the files that row names, then stop.

| Trigger | Capability | Overlay | Reads (load only these) | Bound verifier (must exit 0) |
|---|---|---|---|---|
| Author/generate a definition ("define X", "generate the definition for X") | `author-definition/` | `overlays/<repo>.md` | `author-definition/capability.md`; `constitution/schema/artifact-matrix.yaml`; `constitution/schema/block-registry.yaml`; canonical `predicates.yaml`, `notation.yaml`; one nearby example definition | `python author-definition/verify.py --target <file> --kind definition` |
| Author/generate any statement -- definition, axiom, theorem, lemma, proposition, corollary ("append the lemma ... to <file>", "generate the latex for ...") | `author-statement/` | `overlays/<repo>.md` | `author-statement/capability.md`; `author-statement/proof_stub.py`; canonical `predicates.yaml`, `notation.yaml`; one nearby example | `python tools/governance/validate_decoration.py --root <root> --chapter <c>` and (provable kinds) `python tools/governance/audit_proof_layout.py --root <root> --chapter <c> --strict` |
| Scaffold a planned chapter ("stub a chapter X", "with sections A, B, C") | `author-stub-chapter/` | `overlays/<repo>.md` | `author-stub-chapter/capability.md` | `python tools/governance/audit_volume_layout.py --root <volume-root> --chapter <subject> --strict` |
| Create a section stub in a chapter ("stub a section X under Y") | `author-stub-section/` | `overlays/<repo>.md` | `author-stub-section/capability.md` | `python tools/governance/audit_volume_layout.py --root <volume-root> --chapter <chapter> --strict` |

Loading discipline: read this manifest, match one trigger, stop. Do not read other capability folders.
