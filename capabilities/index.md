# Capability Index

`manifest.yaml` is the machine source of truth. This file is the short human
view: choose one capability, load its doc and repo overlay, do the action, run
the success gates.

| Trigger | Capability | Overlay | Reads (load only these) | Bound verifier (must exit 0) |
|---|---|---|---|---|
| Write a theorem, lemma, proposition, corollary, axiom, or general statement | `author-statement/` | `overlays/<repo>.md` | capability doc, `proof_stub.py`, registries if needed, one nearby example | `validate_decoration.py`; for provable statements also `audit_proof_layout.py --strict` |
| Write a definition | `author-definition/` | `overlays/<repo>.md` | capability doc, `verify.py`, predicates registry if needed, one nearby example | `validate_decoration.py`; `author-definition/verify.py` |
| Scaffold a planned chapter | `author-stub-chapter/` | `overlays/<repo>.md` | capability doc, `stub_chapter.py` | `audit_volume_layout.py --strict`; `validate_decoration.py` |
| Scaffold a section in an existing chapter | `author-stub-section/` | `overlays/<repo>.md` | capability doc, `stub_section.py` | `audit_volume_layout.py --strict` |
| Add or change a Lean theorem | `author-lean-theorem/` | `overlays/lra-lean.md` | capability doc, nearest matching Lean file | repo overlay success gates |
| Implement a C++ numerical task | `cpp-build-task/` | repo overlay | capability doc, relevant source/tests | repo overlay success gates |

Loading discipline: read this manifest, match one trigger, stop. Do not read other capability folders.
