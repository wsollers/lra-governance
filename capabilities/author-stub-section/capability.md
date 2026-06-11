# Capability: author-stub-section

## Action

Scaffold one section topic inside an existing chapter. This is deterministic
Python, not LLM-authored LaTeX.

## Inputs

- Chapter root.
- Section title.

## Do

Run `stub_section.py` or call `stub_section(chapter_root, title)`. It creates
matching `notes/<slug>/index.tex` and `proofs/<slug>/index.tex`, then routes both
from the chapter routers. The slug is lowercase ASCII with hyphens.

## Success Gate

- `python tools/governance/audit_volume_layout.py --root <volume-root> --chapter <chapter> --strict`
- `cd <volume-root> && latexmk -lualatex main.tex`

Stop if the section already exists with content that would be overwritten, or if
the chapter is not layout-compliant after the change.
