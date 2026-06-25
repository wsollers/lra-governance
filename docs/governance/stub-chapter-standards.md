# Stub Chapter Standards

Stub chapter standards apply when a governance rebuild needs planned chapter
locations before the mathematical content has been migrated or authored.

## Purpose

A stub chapter is an active placeholder used during a governance rebuild. It
establishes the intended chapter location, title, router structure, and future
work boundary.

A stub is architecture, not content. It must not invent mathematical material.

## When To Use

Use stub chapters when:

- a chapter is planned but not yet rebuilt;
- old content has been archived and a clean active structure is needed;
- a volume-wide refactor requires the final table of contents to exist before
  content migration;
- future content will be migrated topic by topic.

Do not use a stub chapter to bypass authoring, proof, notation, extraction, or
file-splitting rules for active mathematical content.

## Required Directory Shape

Unless a repo-local convention overrides it, each stub chapter should have:

```text
chapter-slug/
  chapter.yaml
  index.tex
  notes/
    index.tex
  proofs/
    index.tex
    exercises/
      index.tex
      capstone-{chapter-slug}.tex
```

Optional directories or files may be created only when the repo convention uses
them:

```text
figures/
README.md
capstone/
```

Do not create extra directories unless local conventions require them.

The machine-readable authority for volume, chapter, and topic layout is
`docs/governance/volume-structure.schema.json`.

## Canonical Stub-Chapter Skeleton

Copy these verbatim and substitute only the angle-bracketed parts. This is the
real, validator-passing shape; do not improvise a different structure.

`<chapter-slug>/index.tex` (chapter router):

```latex
% =========================================================
% Chapter: <Chapter Display Title>
% =========================================================
\chapter{<Chapter Display Title>}
\label{ch:<chapter-slug>}

\breadcrumb{<chapter-slug>}{<prior-neighbor>}{<Chapter Display Title>}{<next-neighbor>}

\input{volume-<n>/<chapter-slug>/notes/index}

\LRAExcludeFromPrintEditionBegin
\section*{Proofs}
\input{volume-<n>/<chapter-slug>/proofs/index}

\section*{Capstone}
\input{volume-<n>/<chapter-slug>/proofs/exercises/index}
\LRAExcludeFromPrintEditionEnd
```

`<chapter-slug>/notes/index.tex` (router only — one `\input` per topic, in chapter order):

```latex
\input{volume-<n>/<chapter-slug>/notes/<topic>/index}
```

`<chapter-slug>/proofs/index.tex` (router only — topic indexes only; the exercises router is NOT listed here, it is input from the chapter index above):

```latex
\input{volume-<n>/<chapter-slug>/proofs/<topic>/index}
```

`<chapter-slug>/proofs/exercises/index.tex` (router only):

```latex
\input{volume-<n>/<chapter-slug>/proofs/exercises/capstone-<chapter-slug>}
```

Chapter-index points that are easy to get wrong:

- The chapter label is `\label{ch:<chapter-slug>}` — prefix `ch:`, not `chap:`.
- `\breadcrumb` takes four arguments: current slug, prior neighbor, current
  display title, next neighbor. Neighbors come from the chapter registry (see
  the breadcrumb rules in `constitution/schema/file-schema.yaml`).
- The `Proofs` and `Capstone` headings and their `\input`s sit inside the
  `\LRAExcludeFromPrintEditionBegin ... \LRAExcludeFromPrintEditionEnd` block so
  print builds omit them.

Real example (`volume-ii/peano-systems/index.tex`):

```latex
\chapter{Peano Systems}
\label{ch:peano-systems}
\breadcrumb{peano-systems}{proof-techniques}{Peano Systems}{Identity, Equality, and Equivalence}
\input{volume-ii/peano-systems/notes/index}
\LRAExcludeFromPrintEditionBegin
\section*{Proofs}
\input{volume-ii/peano-systems/proofs/index}
\section*{Capstone}
\input{volume-ii/peano-systems/proofs/exercises/index}
\LRAExcludeFromPrintEditionEnd
```

## Chapter Index

The chapter `index.tex` is the chapter-level router. It should contain, in the
canonical shape:

- `\chapter{...}`;
- `\label{ch:...}`;
- `\breadcrumb{...}{...}{...}{...}`;
- `\input{volume-x/chapter-slug/notes/index}`;
- `\LRAExcludeFromPrintEditionBegin`;
- `\section*{Proofs}`;
- `\input{volume-x/chapter-slug/proofs/index}`;
- `\section*{Capstone}`;
- `\input{volume-x/chapter-slug/proofs/exercises/index}`;
- `\LRAExcludeFromPrintEditionEnd`.

The proof and capstone headings belong inside the print-edition exclusion
block, so print builds do not render empty `Proofs` or `Capstone` sections.
Within that block and everywhere below `proofs/`, routing uses ordinary
`\input{...}`.

The chapter `index.tex` should not contain long exposition. It should not
contain definitions, theorems, examples, exercises, or proof material unless
the task explicitly provides that content and authorizes active content
generation.

## Notes Index

The `notes/index.tex` file is the chapter notes router. For each topic, it
routes the topic index only:

```latex
\input{volume-x/chapter-slug/notes/topic-title/index}
```

The rendered topic heading belongs inside `notes/topic-title/index.tex`:

```latex
\section{Topic Title}
\input{volume-x/chapter-slug/notes/topic-title/notes-topic-title}
```

For a fresh stub with no authored content yet, the topic router may contain the
section heading without body inputs.

Do not add section names, dependencies, labels, or topic lists unless they are
already supplied by a canonical registry or by the task.

## Proofs Index

The `proofs/index.tex` file is router-only. It contains comments and `\input`
lines for `proofs/{topic}/index`, followed by
`proofs/exercises/index` as the final route.

Do not create proof files for nonexistent statements. Proof file creation must
also satisfy `proof-standards.md`.

## Exercises Index

The exercises router lives at `proofs/exercises/index.tex`. It is router-only
and routes `proofs/exercises/capstone-{chapter-slug}.tex`.

Do not create root-level `exercises/`. Do not invent exercises, capstone
prompts, solutions, or exercise labels unless the task explicitly provides that
content.

## Chapter Metadata

The `chapter.yaml` file must follow current repo conventions. Add only fields
already used by nearby chapters or documented by the local repo schema.

If no global or repo-local schema exists, match the shape nearby chapters use:

```yaml
subject: <chapter-slug>
display_title: <Chapter Display Title>
volume: volume-<n>
status: planned
dependencies:
  prior: ''
  next: ''
path: volume-<n>/<chapter-slug>
environments: []
proof_files: []
```

The `environments` and `proof_files` lists are populated as content is added or
regenerated from source; a fresh stub leaves them empty.

Do not invent a new metadata schema incompatible with existing extraction,
rendering, or sync tools.

## Status Language

Use impersonal status language. Allowed examples include:

```text
This chapter is in governance rebuild status.
The previous active material has been archived.
The active files are placeholders for a clean rebuild.
This chapter is planned.
Active mathematical content has not yet been added.
```

Avoid first-person or motivational phrasing such as:

```text
We introduce...
We study...
We will...
```

## Mathematical Content Rule

A stub must not invent:

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

## Label Rule

Stub labels should be minimal.

Do not create theorem, definition, proof, example, exercise, dependency, or
topic labels for planned but nonexistent content.

Chapter and section labels may be created only when consistent with local
conventions and only for actual chapter or section structure.

## Build Rule

After generating stub chapters, run the repo-local build command or the
documented build command.

For LRA volume repos, try:

```powershell
python ..\lra-governance\scripts\build_volume.py --root .
```

unless local instructions say otherwise.

Generated stubs must not break the build. If the build command is unavailable
or the repo lacks a build target, report that condition explicitly.

## Report Rule

Any stub-generation task should report:

- chapters created;
- files created;
- router or index files updated;
- archived material referenced, if applicable;
- build result;
- warnings or errors.
