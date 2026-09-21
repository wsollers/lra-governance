# Repo Overlay -- lra-flashcards

Repo identity: Flashcard decks and companion web/mobile study app.

`lra-flashcards` owns study-card decks, spaced-repetition exports, and the
web/mobile app scaffold used to review LRA material. It is a consumer of
governed volume, Lean, and source-profile metadata, not the canonical owner of
mathematical statements, proof text, source bibliographies, or verification
records.

## Ownership Boundaries

Keep card content traceable to reviewed upstream artifacts. When a card exposes
a definition, theorem, example, or source reference, prefer stable labels,
object IDs, or generated exports over copied prose. Short prompts, answers,
mnemonics, tags, and review metadata belong here; corrections to canonical
math, labels, source profiles, or Lean declarations belong in the owning
repository first.

Do not commit raw source PDFs, large extracted source text, private reading
library artifacts, or generated upstream indexes unless the repo explicitly
documents them as app fixtures or card-export artifacts.

## App Expectations

Use the existing app framework and package manager already present in the
checkout. Keep deck data and app code separated so cards can be regenerated or
audited independently from UI changes. Prefer deterministic export formats for
cards intended for Anki-style imports or app ingestion.

## Success Gates

Run the narrowest repo-native checks that cover the changed deck or app files.
For app changes, run the package manager's build and tests when present. For
deck/export changes, run the repo's card validation or export script when
present.
