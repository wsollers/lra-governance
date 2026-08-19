# Active Content Promotion Gate

This standard separates planned mathematical architecture from active
mathematical content.

## Core Rule

Routers, folder structure, empty topic indexes, and other stubs may be created
from an approved roadmap before the mathematics is worked.

Substantive non-stub note or proof material must not be promoted into active
volume routers until the relevant mathematics has been worked. For theorem-like
items, "worked" means both:

1. the corresponding Lean formalization exists when the item is in Lean scope;
2. the hand proof exists in the volume proof files.

For definitions and notation, "worked" means the formal Lean declaration exists
when the item is in Lean scope, and the TeX statement has been aligned with that
formal declaration. A definition may be marked manual-only only when the task or
chapter plan explicitly excludes it from Lean scope.

## Allowed Early Structure

The following are architecture, not active content, and may be created early:

- chapter routers and topic routers;
- matched `notes/<topic>/` and `proofs/<topic>/` folders;
- empty or comment-only topic indexes;
- figure source files that support planned topics;
- parked draft material outside active routers.

These artifacts may establish the intended growth path, but they must not imply
that the mathematics has been completed.

## Promotion Requirements

Before moving non-stub material into active notes/proofs routers:

- verify the Lean declaration or theorem when the item is in Lean scope;
- verify the hand proof for theorem, lemma, proposition, and corollary items;
- align the TeX statement with the Lean statement when Lean exists;
- add `\LeanFormalizes` only for actual Lean declarations;
- reserve `checked` for declarations whose Lean proof has no local `sorry`;
- keep partial Lean declarations with `sorry` out of `checked` metadata;
- route only proof files whose proof bodies are populated, unless the task is
  explicitly a proof-stub generation task.

## Parking Rule

Draft notes, theorem inventories, imported source text, partial proof stubs,
and material for future topics must live in a parked or holding area until the
promotion requirements are met.

Parking is preservation, not publication. Parked material may be useful for a
future pass, but validators, generated PDFs, and formalization crosswalks should
not treat it as completed active content.

## Figures

Figures may be created before the corresponding topic is promoted. A figure does
not promote a definition, theorem, or proof. When the topic is still parked, the
figure may remain in the chapter's figure directory, but the explanatory note
text that depends on unworked mathematics must remain parked.

## Analysis Redo Emphasis

For Analysis redo work, this gate is mandatory. Avoid bulk theorem inventories
or large batches of active proof stubs. Build each topic by proving in Lean,
writing or aligning the TeX statement, proving by hand, and then memorializing
the crosswalk metadata.
