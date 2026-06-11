# Capability Index

`manifest.yaml` is the machine source of truth. This file is the short human
view: choose one capability, load its doc and repo overlay, do the action, run
the success gates.

| Trigger | Capability | Overlay | Reads (load only these) | Bound verifier (must exit 0) |
|---|---|---|---|---|
| Write a theorem, lemma, proposition, corollary, axiom, or general statement | `author-statement/` | `overlays/<repo>.md` | capability doc, `proof_stub.py`, registries if needed, one nearby example | validation passes; `latexmk -lualatex main.tex` succeeds |
| Write a definition | `author-definition/` | `overlays/<repo>.md` | capability doc, `verify.py`, predicates registry if needed, one nearby example | validation passes; `latexmk -lualatex main.tex` succeeds |
| Scaffold a planned chapter | `author-stub-chapter/` | `overlays/<repo>.md` | capability doc, `stub_chapter.py` | validation passes; `latexmk -lualatex main.tex` succeeds |
| Scaffold a section in an existing chapter | `author-stub-section/` | `overlays/<repo>.md` | capability doc, `stub_section.py` | validation passes; `latexmk -lualatex main.tex` succeeds |
| Add or change a Lean theorem | `author-lean-theorem/` | `overlays/lra-lean.md` | capability doc, nearest matching Lean file | repo overlay success gates |
| Implement a C++ numerical task | `cpp-build-task/` | repo overlay | capability doc, relevant source/tests | repo overlay success gates |

Loading discipline: read this manifest, match one trigger, stop. Do not read other capability folders.
