# Extraction Standards

Source sections: `DESIGN.md` sections 2.4, 8, 10, 13, and the knowledge
explorer pipeline notes in `REPOSITORY_STRUCTURE.md`.

## Extraction Contract

Extraction depends on stable labels, one theorem-like object per environment,
dependency remarks, and canonical logical blocks. Authoring changes must
preserve those structures unless the extraction pipeline is explicitly updated.

## Dependency Blocks

Every definition, axiom, theorem, lemma, proposition, and corollary carries an
attached `remark*` titled `Dependencies` after its interpretation/logical block
sequence. Foundational items may state that no prior formal dependencies are
required within the current extraction scope.

## Logical Blocks

Logical blocks must be ordered and named consistently. Predicate-reading blocks
may use canonical predicates only where their layer permits them.

## Labels

Formal environments require stable labels with approved prefixes. Labels should
be ASCII, descriptive, and aligned with filenames and proof labels.

## Theorem Explorer

The theorem explorer implementation is owned by `lra-knowledge-explorer`.
`Learning-Real-Analysis` remains the integration point for LaTeX source and
rebuild dispatch.
