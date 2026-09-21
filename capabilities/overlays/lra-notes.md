# Repo Overlay -- lra-notes

Repo identity: Lean/mathlib study notes.

`lra-notes` is a coached learning workspace for Lean translations, examples,
exercises, proof attempts, and distilled study notes tied to current reading.
It is not the canonical LRA formalization repository. Checked source-aligned
formalization work, verification metadata for volume artifacts, and theorem
explorer extraction targets remain owned by `lra-lean` unless a task explicitly
asks to promote reviewed material across repositories.

## Implementation Standards

Favor learning clarity over maximal abstraction. Lean files should show the
mathematical idea, the relevant mathlib interface, and the proof pattern being
practiced. Prefer small named examples, theorem statements, and exercises that
can be read beside the source text. Avoid rebuilding foundations that mathlib
already provides unless the task is explicitly about understanding such a
construction.

Use mathlib idiom as the default boundary: import existing APIs, state results
in terms of mathlib structures where practical, and add local definitions only
when they clarify a book-to-mathlib translation. Keep exploratory failed
attempts in `study/` notes or clearly local examples; public library modules
should remain buildable Lean source.

Names should be descriptive and source-facing. For textbook tracks, place
material under the source root and subject path already in the repository, such
as `Munkres/Topology/...`, `Searcoid/MetricSpaces/...`,
`Bruckner/RealAnalysis/...`, or `Integration/...`. Aggregator files at the repo
root and subject roots import the modules for their track in deterministic
order.

When a result might later belong in `lra-lean`, keep the statement easy to
promote: avoid private abbreviations in theorem statements, name the source
and chapter in nearby comments, and separate source translation from personal
proof commentary. Do not add `lra-lean` verification metadata here; promotion
and metadata attachment belong to a separate reviewed task in `lra-lean`.

Respect source boundaries. Textbook PDFs, scans, extracted Markdown, and long
verbatim passages are local references only and must not be committed. Proofs
and explanations committed here should be independently written personal work
or short factual summaries, not copied source prose.

## Layout

- Lean libraries are declared in `lakefile.lean`; the active roots are
  `Munkres`, `LRANotes`, `Searcoid`, `Bruckner`, and `Integration`.
- Source tracks live under top-level source/subject directories. Current roots
  include `Munkres/Topology/`, `Searcoid/MetricSpaces/`,
  `Bruckner/RealAnalysis/`, and `Integration/`.
- Personal process notes, proof sketches, RemNote queues, and learning logs
  live under `study/`.
- Docker and devcontainer support live at the repo root and under `docker/`.
- Do not commit `.lake/`, build products, raw source PDFs, large extracted
  source text, or private reading-library artifacts.

## Success Gates

Run the narrowest Lake build that covers the changed material, then a broader
build before larger changes land.

- `lake build`
- For focused track edits, also run the relevant target, for example
  `lake build Munkres` or `lake build LRANotes`.

Do not use `lra-lean` Docker or volume LaTeX render checks as substitutes for
this repo's Lake build.
