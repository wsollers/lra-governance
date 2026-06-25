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
from the chapter routers. The notes topic index owns the rendered
`\section{...}` heading and may route topic body files with `\input`; the parent
`notes/index.tex` only routes the topic index. The slug is lowercase ASCII with
hyphens.

## Success Gate

- `python tools/governance/validate_volume.py <volume-root> --fail-on-errors`
- `cd <volume-root> && python ../lra-governance/scripts/build_volume.py --root .`

## Reference Escalation

If the generator behavior or local routers do not answer a layout question,
open `capabilities/reference-index.md` and use only the `Chapter And Section
Scaffolding` row needed for the issue.

Stop if the section already exists with content that would be overwritten, or if
the chapter is not layout-compliant after the change.
