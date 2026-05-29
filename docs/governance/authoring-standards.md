# Authoring Standards

Source sections: `DESIGN.md` sections 1, 4, 5, 6, 6.1, 7, 12, and 15.

## Purpose

The notes are a long-term mathematical reference. They preserve definitions,
theorems, proof structures, dependencies, and canonical notation in a form that
remains readable, rigorous, and stable across years of revision.

## Voice

Use a precise reference voice. Do not write as a course transcript, workbook,
chatty explanation, or motivational aside. Exposition should state what a
definition or result does mathematically and how it fits the local structure.

## Boxes

Boxes are structural, not decorative. Box first appearances of major
definitions, theorems, propositions, lemmas, corollaries, axioms, examples, and
toolkits according to the current house style. Remarks, examples, proofs, and
second appearances do not receive boxes unless a specific rule says otherwise.

## Chapter Entries

Chapter openings use the canonical entry pattern from `DESIGN.md`: breadcrumb,
status when needed, roadmap, and chapter structure. Breadcrumbs are structural
dependency statements, not motivational prose.

## Layered Exposition

Each layer has one job:

- formal environments state the mathematics,
- interpretation remarks explain meaning,
- logical blocks expose formal structure,
- dependency blocks support extraction,
- prose connects local context.

Do not over-symbolize exposition. Use prose where prose is the correct layer.
