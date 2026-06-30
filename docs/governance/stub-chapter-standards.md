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
    exercises/                  (optional)
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
`constitution/schema/file-schema.yaml`, enforced by
`tools/governance/validate_volume.py` and the focused layout audits.

## Generator Rule

Use the deterministic generator before hand-authoring a stub chapter:

```powershell
python tools\governance\generate_stub.py chapter --volume-root .\volume-ii --subject <chapter-slug> --title "<Chapter Display Title>" --section "<Section Title>"
```

From a checkout without the volume-local wrapper, call the canonical tool
through the sibling governance repo:

```powershell
python ..\lra-governance\tools\governance\generate_stub.py chapter --volume-root .\volume-ii --subject <chapter-slug> --title "<Chapter Display Title>"
```

Use repeated `--section` arguments or a semicolon-separated `--sections` list
when creating initial section stubs with the chapter. Hand-copy the skeleton
below only when the generator is unavailable, and report that fallback
explicitly.

## Canonical Stub-Chapter Skeleton

This is the expected generator output shape and the fallback hand-copy contract.
Substitute only the angle-bracketed parts; do not improvise a different
structure.

`<chapter-slug>/index.tex` (chapter router):

```latex
% =========================================================
% Chapter: <Chapter Display Title>
% =========================================================
\chapter{<Chapter Display Title>}
\label{ch:<chapter-slug>}
\lrameta{
  series = {<Series Display Title>},
  volume = {Volume <N>: <Volume Display Title>},
  book = {Book <N>: <Book Display Title>},
  chapter = {Chapter <N>: <Chapter Display Title>},
  current = chapter,
}
\LraBreadcrumb

\input{volume-<roman>/<book-slug>/<chapter-slug>/notes/index}

\LRAExcludeFromPrintEditionBegin
\section*{Proofs}
\input{volume-<roman>/<book-slug>/<chapter-slug>/proofs/index}

% Include the capstone route only when a strong capstone exists:
% \section*{Capstone}
% \input{volume-<roman>/<book-slug>/<chapter-slug>/proofs/exercises/index}
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

When a capstone exists, `<chapter-slug>/proofs/exercises/index.tex` is router only:

```latex
\input{volume-<n>/<chapter-slug>/proofs/exercises/capstone-<chapter-slug>}
```

Chapter-index points that are easy to get wrong:

- The chapter label is `\label{ch:<chapter-slug>}` — prefix `ch:`, not `chap:`.
- Current volume repos use `\lrameta{...}` followed immediately by
  `\LraBreadcrumb`. The metadata values are the rendered breadcrumb source of
  truth.
- Legacy routers may still use `\breadcrumb{...}{...}{...}{...}`. Do not
  introduce the legacy form in new stubs unless the repo-local convention
  requires it.
- The `Proofs` heading, and the optional `Capstone` heading and input, sit inside the
  `\LRAExcludeFromPrintEditionBegin ... \LRAExcludeFromPrintEditionEnd` block so
  print builds omit them.

For router semantics, topic matching, capstone routing, and reachability, use
`volume-structure.md` and the validator. The chapter router must not contain
definitions, theorems, examples, exercises, proof material, or long exposition
unless the task explicitly provides that content and authorizes active content
generation.

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

## Common Stub Guard Rails

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

After generating stub chapters, run the repo-local build or validation command.
For LRA volume repos, the validation command is:

```powershell
python ..\lra-governance\scripts\build_volume.py --root . --validate-only
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
