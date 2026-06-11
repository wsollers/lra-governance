# Capability: author-stub-chapter

## Action

Scaffold a planned chapter in a volume repo. This is deterministic Python, not
LLM-authored LaTeX.

## Inputs

- `--volume-root`, `--subject`, `--title`.
- Optional `--sections "A; B; C"` in dependency order.
- Optional `--registry <json>` containing `{subject, display_title}` entries in
  dependency order for breadcrumb neighbors.

## Do

Run `stub_chapter.py`. It creates the chapter router, `chapter.yaml`,
`notes/index.tex`, `proofs/index.tex`, `proofs/exercises/.gitkeep`, optional
section stubs, and routes the chapter from `index.tex` and `main.tex` when those
routers exist.

The chapter router uses the thin canonical shape: `\chapter`, chapter label,
`\breadcrumb`, notes input, proof section, print-aware proofs input, capstone
section, and print-aware capstone input.

## Success Gates

- `python tools/governance/validate_decoration.py --root <volume-root> --chapter <subject> --fail-on-errors`
- `python tools/governance/audit_volume_layout.py --root <volume-root> --chapter <subject> --strict`
- `cd <volume-root> && latexmk -lualatex main.tex`

Stop if a target chapter already exists with content that would be overwritten,
or if either success gate fails.
