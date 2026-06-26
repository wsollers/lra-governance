# Stub Section Standards

Stub section standards apply when a governance rebuild needs planned topic
locations inside an existing chapter before mathematical content has been
migrated or authored.

## Purpose

A section stub is used during governance rebuilds to establish the future
location of a topic before mathematical content is migrated.

A section stub is architecture, not content. It must not invent mathematical
material.

## Invocation Pattern

Typical instructions may be:

```text
Generate section stub:
  axioms
```

or:

```text
Generate section stubs:
  signatures
  theories
  models
  consistency
```

When such an instruction is encountered, create the required directory
structure and router wiring automatically, subject to local repo conventions
and idempotency rules.

## Required Notes Structure

Generating a notes section such as:

```text
axioms
```

inside a chapter should create:

```text
notes/
  axioms/
    index.tex
```

The file is the topic router. It may contain comments, the topic's rendered
`\section{...}` heading, and `\input` lines only. It must not contain
placeholder prose, formal content, labels, or proof material.

Do not add definitions, theorems, examples, dependencies, topic lists, or
labels unless they are already supplied by a canonical registry or by the task.

The machine-readable authority for matched `notes/{topic}/` and
`proofs/{topic}/` section architecture is
`docs/governance/volume-structure.schema.json`. Use
`tools/governance/validate_volume.py` to audit topic-pair routing.

## Required Proof Structure

For every notes section created, create the matching proof section:

```text
proofs/
  axioms/
    index.tex
```

The file is a router-only topic index. It may contain comments and `\input`
lines only. It must not contain proof-status prose, rendered headings, formal
content, or proof material.

Do not create proof files for nonexistent statements. Proof file creation must
also satisfy `proof-standards.md`.

## Canonical Topic-Pair Skeleton

Copy these verbatim and substitute only the angle-bracketed parts. This is the
real, validator-passing shape; do not invent a different structure. A new topic
`<topic>` in chapter `<chapter-slug>` of `volume-<n>` is exactly two files plus
two parent-router edits.

`notes/<topic>/index.tex` (topic router — rendered section plus body input):

```latex
\section{<Topic Display Title>}
\input{volume-<n>/<chapter-slug>/notes/<topic>/notes-<topic>}
```

`proofs/<topic>/index.tex` (router only — one `\input` per proof file in
dependency order; empty for a fresh stub with no proofs yet):

```latex
\input{volume-<n>/<chapter-slug>/proofs/<topic>/prf-<theorem-root>}
```

Then add the topic to the two chapter routers, in matching order — `notes/index.tex`:

```latex
\input{volume-<n>/<chapter-slug>/notes/<topic>/index}
```

and `proofs/index.tex` (topic index only — never the exercises router here):

```latex
\input{volume-<n>/<chapter-slug>/proofs/<topic>/index}
```

Real example (chapter `peano-systems`, topic `recursion-on-peano-systems`):

```latex
% notes/recursion-on-peano-systems/index.tex
\section{Recursion on Peano Systems}
\input{volume-ii/peano-systems/notes/recursion-on-peano-systems/notes-recursion-on-peano-systems}
```

Non-negotiable points:

- The topic identifier is shared: `notes/<topic>/` pairs with `proofs/<topic>/`,
  same slug, lowercase-hyphen ASCII.
- The topic router is the only place the `\section{...}` heading appears; the
  body file `notes-<topic>.tex` carries no heading.
- A fresh section stub creates the routers only. It creates no proof files for
  statements that do not exist, and invents no definitions, theorems, examples,
  or labels.
- `proofs/index.tex` lists topic indexes only. The `proofs/exercises/index`
  (capstone) router is input from the chapter `index.tex`, not here.

## Router Updates

After generating a section stub, update the chapter's notes router:

```text
notes/index.tex
```

to include the new topic router in the correct order, using the repository's
canonical routing style:

```latex
\input{volume-x/chapter-slug/notes/axioms/index}
```

The rendered topic heading belongs inside the topic router:

```latex
\section{Axioms}
\input{volume-x/chapter-slug/notes/axioms/notes-axioms}
```

For a fresh stub with no authored content yet, the topic router may contain the
section heading without body inputs.

Then update the chapter's proofs router:

```text
proofs/index.tex
```

to include the matching proof topic index, in the same order as the notes
router:

```latex
\input{volume-x/chapter-slug/proofs/axioms/index}
```

`proofs/index.tex` routes topic indexes only. Do not route
`proofs/exercises/index` here: the exercises/capstone router is input from the
chapter `index.tex` under `\section*{Capstone}` (see `stub-chapter-standards.md`).

## Ordering Rule

When multiple section stubs are generated, insert them in the order provided by
the request unless an explicit chapter roadmap, registry, or existing router
already defines a different order.

For example:

```text
signatures
axioms
theories
models
consistency
```

should be routed in that order unless local chapter structure says otherwise.

## Idempotency Rule

If:

```text
notes/<section>/index.tex
```

already exists:

- do not overwrite mathematical content;
- do not replace an existing section;
- only report that the section already exists.

If the notes section exists but the matching proof section or router entry is
missing, inspect the existing chapter structure before adding only the missing
architecture needed to restore consistency.

## Mathematical Content Rule

A section stub must not invent:

- definitions;
- theorems;
- proofs;
- examples;
- exercises;
- dependencies;
- labels for nonexistent content.

This restriction applies unless the task explicitly provides the content and
authorizes active content generation. Missing mathematical needs should be
reported instead of filled.

## Build Rule

After generating section stubs:

- update all affected routers;
- run the repo-local build command or documented build command;
- verify that all new sections resolve correctly.

Generated stubs must not break the build. If the build command is unavailable
or the repo lacks a build target, report that condition explicitly.

## Report Rule

Any section-stub generation task should report:

- sections created;
- notes files created;
- proof files created;
- routers updated;
- build result;
- warnings or errors.

## Example

A request such as:

```text
Generate section stubs:

signatures
axioms
theories
models
consistency
independence
```

should create:

```text
notes/
  signatures/index.tex
  axioms/index.tex
  theories/index.tex
  models/index.tex
  consistency/index.tex
  independence/index.tex

proofs/
  signatures/index.tex
  axioms/index.tex
  theories/index.tex
  models/index.tex
  consistency/index.tex
  independence/index.tex
```

and all parent index files should be updated automatically.
