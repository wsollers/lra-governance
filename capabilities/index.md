# Capability Index

`manifest.yaml` is the machine source of truth. This file is the short human
view: choose one capability, load its doc and repo overlay, do the action, run
the success gates.

| Trigger | Capability | Overlay | Reads (load only these) | Bound verifier (must exit 0) |
|---|---|---|---|---|
| Build, validate, check, run CI, or monitor workflows for a repo | `build-repo/` | `overlays/<repo>.md` | capability doc, `reference-index.md`, `build_repo.py` | `build_repo.py` exits 0 |
| Audit every formal environment in one notes topic through serial external review, temporary application, validation, and revert | `audit-semantic-topic/` | `overlays/<repo>.md` | capability doc, topic audit workflow, external GPT reviewer workflow, semantic calibration design/prompts, schemas, validators, registries, topic router closure | every semantic and logic review has distinct live-verifiable GPT-5.6 evidence; every temporary edit has a matching revert; topic audit validation passes; final source is restored |
| Calibrate one formal environment into reviewed semantic YAML and governed LaTeX | `calibrate-semantic-artifact/` | `overlays/<repo>.md` | capability doc, semantic-artifact workflow/design, external GPT reviewer workflow, calibration prompt, schemas, validators, registries, one nearby example | external GPT-5.6 evidence and semantic artifact/package validation pass; volume validation and build pass |
| Write a theorem, lemma, proposition, corollary, axiom, or general statement | `author-statement/` | `overlays/<repo>.md` | capability doc, `reference-index.md`, `proof_stub.py`, registries if needed, one nearby example | validation passes; governance book build succeeds |
| Write a definition | `author-definition/` | `overlays/<repo>.md` | capability doc, `reference-index.md`, `verify.py`, predicates registry if needed, one nearby example | validation passes; governance book build succeeds |
| Scaffold a planned chapter | `author-stub-chapter/` | `overlays/<repo>.md` | capability doc, `reference-index.md`, `stub_chapter.py` | validation passes; governance book build succeeds |
| Scaffold a section in an existing chapter | `author-stub-section/` | `overlays/<repo>.md` | capability doc, `reference-index.md`, `stub_section.py` | validation passes; governance book build succeeds |
| Add or change a Lean theorem | `author-lean-theorem/` | `overlays/lra-lean.md` | capability doc, `reference-index.md`, nearest matching Lean file | repo overlay success gates |
| Implement a C++ numerical task | `cpp-build-task/` | repo overlay | capability doc, `reference-index.md`, relevant source/tests | repo overlay success gates |

Loading discipline: read this manifest, match one trigger, stop. Do not read other capability folders.
