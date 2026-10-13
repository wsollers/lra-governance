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
verbatim passages are local references only and must not be committed.
The book PDFs are available in the user's Google Drive under
`Readings/Sources/<subject>/...` (for example `Readings/Sources/Analysis/Real
Analysis/`), mirroring the local `D:\Readings\Sources\` tree. Read them through
the Google Drive connector when a task needs the source text; never copy,
upload, or commit them, and never publish Drive links in this repository. Proofs
and explanations committed here should be independently written personal work
or short factual summaries, not copied source prose.

## Track Layout

A track mirrors its book's own numbering, using one of three layouts:

- chapters only: `Author/Topic/ChapterNN/`;
- chapters with sections: `Author/Topic/ChapterNN/SectionNN/`;
- sections only: `Author/Topic/SectionNN/`.

Topic folders use a fixed vocabulary, not book titles (`RealAnalysis`,
`ComplexAnalysis`, `ModernAnalysis`, `FunctionalAnalysis`, `MeasureTheory`,
`Probability`, `Topology`, `MetricSpaces`, `Logic`, `SetTheory`,
`NumberSystems`, `LinearAlgebra`, `BooleanAlgebras`, `RelationAlgebras`,
`Calculus`, `CalculusOnManifolds`, `DifferentialGeometry`). A multi-volume work
on one topic takes a volume suffix (`RealAnalysisI`, `RealAnalysisII`). Distinct
authors who share a surname get distinct roots (`MendelsonE`, `MendelsonB`).

Each unit (a chapter, or a section where the book has them) holds
`Definitions.lean`, optional `Connections.lean` (iff bridges from local
definitions to mathlib), `Theorems.lean`, `Examples.lean`, and
`Exercises.lean`, importing in that order. Create section folders only when the
work reaches them; do not pre-scaffold empty ones. Material that precedes a
chapter's first section lives in the chapter-level unit files. The book's
axioms belong in `Definitions.lean` with its definitions, since later
definitions may be built from them. When moving or relabelling material, check
it against the book: labels, numbering, and section follow the book, not the
file it happened to be written in.

Namespaces stop at the chapter (`Bruckner.RealAnalysis.Chapter01`), or at the
book for section-only tracks (`Halmos.SetTheory`), so moving a result between
sections never renames it.

## Source Verification

Every formalized statement is checked against its book. Each track root
(`Author/Topic/`) has a `SOURCE.md` naming the book's source record, local PDF,
Markdown extract, and Google Drive folder; it is generated from the
`lra-source-profiles` manifest by `scripts/source_files.py`, so fix the manifest
rather than the file. Read the book through the extract or the Google Drive
connector.

Whenever a task adds, moves, or changes a definition, axiom, theorem, example,
or exercise:

- **Verify the statement, not the proof.** The Lean statement must mean what
  the book states: the same hypotheses, quantifiers, strict or non-strict
  inequalities, domains and conventions (for example ℕ starting at 1). An
  intended deviation is named in the docstring.
- **Verify, insert, or update the location comment.** The docstring opens with
  the book's own label and number, section, and printed page, for example
  `**Definition 1.1** [Thomson2008, §1.5, p. 11]`. Insert one when missing and
  correct one that is wrong; material that is not in the book says so.
- **Place it by the book.** Label, number, and section decide the unit and file,
  not where the declaration happened to be written.
- **Report mathematical mismatches; do not silently fix them.** Change a
  statement only when the user asks for a mathematical correction. Otherwise
  record the problem and the book-faithful statement in `study/source-audit.md`.
- **Paraphrase the book.** Docstring quotations stay under 15 words.

## TeX Notes

Prose — intuition, recollections, why a proof works — is written in TeX in the
chapter's `notes.tex`, not in Lean. Formal statements are never retyped in TeX:
`\leanstatement{Full.Name}` (from `tex/leanstatement.sty`) inputs the
statement exported by `lake exe texexport`, `\leanstatement*{Full.Name}` adds
the Lean source, and `\leanref{Full.Name}` cross-references it. The exporter
renders into `lra-common` environments (`definition`, `theorem`) with
`\coloniff`, and takes symbols from `lra-governance/notation.yaml`; add missing
notation to the registry rather than to `lra-notes`. Proofs containing `sorry`
are marked unproved. Build notes with `scripts/build-notes.sh <notes.tex>`
(LuaLaTeX, `lra-common` checkout); `generated/` and `build/` are not committed.

## Layout

- Lean libraries and their roots are declared in `lakefile.lean`, which is the
  authoritative list of tracks; the README lists each track's source.
- Source tracks live under top-level `Author/Topic/` directories, for example
  `Munkres/Topology/`, `Searcoid/MetricSpaces/`, `Bruckner/RealAnalysis/`.
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
- When `notes.tex` files or the exporter change, also run
  `scripts/build-notes.sh` on the affected notes.

Do not use `lra-lean` Docker or volume LaTeX render checks as substitutes for
this repo's Lake build.
