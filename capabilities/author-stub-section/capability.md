# Capability: author-stub-section

## Trigger
Create a section stub inside an existing chapter ("stub a section X under chapter Y").
Usually invoked by `author-stub-chapter`, but valid standalone.

## Composition
global core (`ENTRYPOINT.md`) + `overlays/<repo>.md` + this capability + bound verifier.

## Behaviour (pure Python, no LLM)
Deterministic filesystem manipulation. For a section title:
1. create `notes/<slug>/index.tex` (section notes router; content authored later);
2. create the matching `proofs/<slug>/index.tex` (proof topic router) -- REQUIRED, the
   layout validator errors on a notes topic without a matching proofs topic;
3. route `notes/<slug>/index.tex` from `notes/index.tex` with its `\section{Title}` heading;
4. route `proofs/<slug>/index.tex` from `proofs/index.tex`.
`<slug>` is the title slugified (lowercase, hyphen-separated, ASCII).

## Bound verifier (MANDATORY -- task not complete until exit 0)
    python tools/governance/audit_volume_layout.py --root <volume-root> --chapter <chapter> --strict
The section is correct only if the whole chapter remains layout-compliant (topic
symmetry + routing). The section's own files are validated as part of that check.
