# LRA Document Design System

## Purpose And Authority

This standard governs human-facing LRA documents produced in Google Docs,
Word, PDF, Markdown renderers, and comparable publishing surfaces. It extends
the LaTeX book style without treating every document as a textbook page.

The standard separates stable semantic roles from medium-specific rendering:

```text
document purpose -> information architecture -> semantic component
                 -> medium profile -> rendered typography and layout
```

LaTeX source notation remains governed by `latex-math-style.md`. Mathematical
artifact types and dependency semantics remain governed by their existing
standards. This document owns document-level hierarchy, visual language,
diagram grammar, accessibility, and profile selection.

## Core Principles

1. Structure is semantic. Use real titles, headings, lists, tables, captions,
   links, and code blocks rather than visual imitations.
2. The document purpose selects the profile; the file format does not.
3. Color reinforces role but never carries meaning alone.
4. Tables compare repeated fields. Diagrams explain relationships, flow,
   hierarchy, or change. Prose explains reasoning.
5. Source authority and proof status remain explicit.
6. Dense material should be layered through summaries, navigation, and
   progressive detail rather than compressed into smaller type.
7. Reusable component roles take precedence over one-off decoration.

## Document Profiles

### Mathematical Exposition

Use for textbook chapters, lecture notes, worked mathematics, and formal
mathematical narratives.

Preferred rhythm:

```text
orientation -> exposition -> formal artifacts -> proofs -> remarks -> practice
```

Preserve LRA definition, axiom, theorem, proof, dependency, and notation roles.
Long-form mathematical prose may use a restrained serif face where the medium
supports it reliably. Theorems and formulas must remain legible when printed.

### Technical Architecture

Use for design documents, architecture descriptions, ADRs, interface maps,
data-flow explanations, and migration designs.

Required features:

- an executive summary and explicit scope;
- current-state and target-state distinctions;
- ownership and dependency boundaries;
- diagrams with typed nodes and labeled edges;
- decisions, alternatives, risks, and verification gates;
- revision state and source links.

### Lean Learning

Use for tutorials, proof walkthroughs, pain-point catalogs, and concept notes.

Required features:

- a visible learning objective;
- the theorem environment before tactics;
- incorrect and correct examples when explaining a misconception;
- the inferred type or goal transition;
- repository-specific context separated from general Lean behavior;
- links to authoritative Lean documentation.

Do not collapse code, proof state, explanation, and takeaway into one undivided
block.

### C/C++ Engineering

Use for C and C++ design notes, API references, debugging records,
portability analyses, implementation reviews, and performance reports.

Required features:

- language and dialect, including the standard version and enabled extensions;
- compiler, standard library, linker, target, ABI, flags, and build context;
- ownership, borrowing, lifetime, invalidation, bounds, and cleanup rules;
- a distinction between guaranteed, unspecified, implementation-defined, and
  undefined behavior;
- failure-stage classification across preprocessing, compilation, template
  instantiation, linking, loading, startup, runtime, and shutdown;
- exact commands and diagnostics for reproducible debugging or benchmark
  claims;
- incorrect and correct examples when explaining a language or lifetime trap.

Label code as a complete program, compilable excerpt, illustrative fragment,
pseudocode, or diagnostic transcript. Architecture diagrams must distinguish
source, translation-unit or module, library, executable, process, thread,
memory, and external-system boundaries. Use typed edges such as `includes`,
`imports`, `links`, `loads`, `calls`, `owns`, `borrows`, `allocates`, `frees`,
`transfers`, `synchronizes-with`, and `crosses ABI`.

Use the Technical Architecture profile for system-wide decisions and this
profile for language-, toolchain-, ABI-, ownership-, and runtime-specific
evidence. Link the two layers instead of duplicating their authoritative
content.

### Reference And Audit

Use for inventories, crosswalks, standards, checklists, status reports, and
search-oriented references.

Required features:

- scope and authority near the beginning;
- stable identifiers and precise labels;
- tables only when fields are genuinely comparable;
- filters, tags, or indexes when the medium supports them;
- explicit unknown, pending, deprecated, and verified states;
- dates only for observations that can become stale.

## Typography

Typography is profile-aware but role-stable.

### Preferred Families

- Technical, architecture, learning, C/C++ engineering, and reference body: `Inter` when
  available; use `Arial` as the Google Docs-safe fallback.
- Lean, C/C++, shell, diagnostic, and terminal code: `Roboto Mono`; use
  `Consolas` as the fallback.
- Mathematical exposition body: the project-approved book serif when a
  reliable mathematical font stack is available; otherwise use the technical
  body family for consistency.
- Displayed mathematics: use the native equation renderer or a math-capable
  font. Never fake formulas with plain Unicode spacing.

### Role Scale

The following screen-first defaults may be adjusted modestly to match a native
template, but relative hierarchy must remain clear:

| Role | Default size | Weight | Use |
| --- | ---: | --- | --- |
| Title | 26 pt | 700 | One document title |
| Subtitle | 14-16 pt | 400 | Scope or explanatory deck |
| Heading 1 | 18 pt | 700 | Major sections |
| Heading 2 | 14 pt | 700 | Subsystems or major concepts |
| Heading 3 | 11-12 pt | 700 | Local topics |
| Body | 10.5-11 pt | 400 | Main prose |
| Caption / metadata | 9-10 pt | 400-600 | Figures, tables, provenance |
| Code | 9.5-10.5 pt | 400 | Lean, shell, and structured data |

Use native named paragraph styles. Do not create headings by enlarging and
bolding normal text.

## Color System

The palette is restrained, accessible, and suitable for screen and print.

| Token | Hex | Role |
| --- | --- | --- |
| Ink | `#172033` | Primary text |
| Slate | `#516078` | Secondary text and metadata |
| Navy | `#173B65` | Titles and primary headings |
| Blue | `#2F6FED` | Links, selected state, active routes |
| Cyan | `#0E7490` | Semantic or model layer |
| Violet | `#6D4CC3` | Syntax or language layer |
| Green | `#18794E` | Verified or completed state |
| Amber | `#A15C00` | Caution, pending decision, assumption |
| Red | `#B42318` | Error, contradiction, blocked state |
| Surface blue | `#EAF2FF` | Primary callout fill |
| Surface gray | `#F4F6F8` | Code, metadata, alternating rows |
| Rule | `#D7DEE8` | Dividers and table borders |

Every status color must also have a text label, icon, line style, or pattern.
Keep ordinary body text on white. Avoid large saturated fills.

## Page And Navigation Modes

Choose the mode deliberately:

- **Paged:** print-oriented notes, formal handouts, and PDF deliverables.
- **Pageless:** living design documents, tutorials, large diagrams, and
  screen-first references.
- **Tabbed:** long native Google Docs references with clearly independent
  profiles or subsystems. Tabs are navigation, not a substitute for headings.

Long documents should include a short orientation, native heading structure,
and a table of contents or equivalent navigation. Use descriptive link labels.

## Component Library

Use a small, repeatable set of semantic components:

- **Summary:** what the reader needs to know before the details.
- **Scope / non-goals:** boundaries of the artifact.
- **Definition / theorem / proof:** formal mathematical roles governed by
  existing standards.
- **Decision:** chosen direction, rationale, and consequences.
- **Assumption:** unverified premise or environmental condition.
- **Warning:** a failure mode or unsafe interpretation.
- **Example pair:** incorrect example, diagnosis, correct pattern.
- **Lean environment:** imports, namespace, variables, instances, declaration
  header, local context, and goal.
- **Verification:** tests, build gates, source checks, and observed status.
- **Source / provenance:** canonical owner and supporting references.

Component labels must remain visible in plain text and export cleanly.

## Tables

Use tables for comparison, mappings, ownership matrices, inventories, or
repeated records. Avoid tables for multi-paragraph exposition.

- Prefer two to five columns.
- Use short, noun-based headers.
- Keep header fill light and body text at least 9.5 pt for net-new tables.
- Use white and `Surface gray` alternating rows when helpful.
- Align numbers consistently and keep prose left aligned.
- Repeat header rows across printed pages when supported.
- Include a caption or lead-in when the table's purpose is not obvious.

## Diagram Grammar

A diagram must answer a specific relationship question that prose or a small
table cannot answer as clearly.

### Node Semantics

- Rounded rectangle: component, module, document, or packaged structure.
- Plain rectangle: process step or transformation.
- Pill: state, status, or selected provider.
- Document shape: source artifact or generated output.
- Cylinder only for persistent data stores.
- Boundary container: ownership domain, logical level, or subsystem.

Never assign two meanings to the same shape in one figure.

### Edge Semantics

- Solid arrow: required flow, dependency, or construction.
- Dashed arrow: optional, inferred, planned, or not-yet-observed relation.
- Double-headed arrow: explicitly bidirectional relationship.
- Dotted line without arrow: association only.

Label edges with verbs or typed relations such as `imports`, `constructs`,
`satisfies`, `unfolds to`, `provides instance`, or `observed proof use`.

### Layout And Accessibility

- Prefer one reading direction: left-to-right for flow, top-to-bottom for
  hierarchy.
- Use lanes or boundary containers for ownership and logical levels.
- Place a legend whenever shape, color, or line style has non-obvious meaning.
- Keep labels readable at the document's normal zoom and in PDF export.
- Provide a caption plus concise alt text stating the figure's conclusion.
- Include source and revision metadata for generated diagrams.
- Do not use crossing edges when a lane, intermediate node, or second figure
  would be clearer.

### Standard Architecture Views

Use these reusable views instead of one overloaded diagram:

1. **Context:** system and external actors or sources.
2. **Ownership:** repositories, folders, modules, and canonical authorities.
3. **Dependency:** typed prerequisite or import edges.
4. **Runtime / elaboration flow:** ordered state changes.
5. **Data lineage:** source, extraction, transformation, storage, and consumer.
6. **State model:** lifecycle states and valid transitions.

## Lean-Specific Presentation

Lean documents must expose the difference between surface syntax and the
elaborated environment.

For theorem explanations, show these layers in order when relevant:

```text
imports -> namespace -> variables and instances -> theorem binders
        -> unfolded outer structure -> local context -> goal -> proof term
```

Code blocks use monospace type, preserve indentation, and identify whether
they are complete, illustrative, incorrect, or intentionally contain `sorry`.
Proof-state excerpts must distinguish hypotheses from the goal. When a hidden
instance matters, display its type and explain which projection depends on it.

Incorrect/correct examples must not differ only by unexplained tactic magic.
The correct example should name the source of the needed evidence and show the
resulting type or goal transition.

## Source, Status, And Revision Metadata

Living technical documents should record:

- canonical owner;
- scope;
- status (`draft`, `reviewed`, `accepted`, or `superseded`);
- last substantive review date when staleness matters;
- repository path or source links;
- verification state and known limitations.

Do not put volatile completion counts into durable standards. Put them in a
dated audit or status artifact.

## Accessibility And Export

- Use sufficient contrast and never rely on color alone.
- Use heading order without skipping levels for visual effect.
- Add alt text and captions to meaningful figures.
- Use descriptive hyperlinks rather than raw URLs in prose.
- Avoid font sizes below 9 pt.
- Verify tables, figures, code, and page breaks in the intended export format.
- Mark properties that were not visually verified as unverified.

## Quality Gate

Before handoff:

1. confirm the selected profile and document purpose;
2. confirm native heading, list, link, table, and code semantics;
3. check hierarchy, density, typography, and palette consistency;
4. confirm diagrams use the grammar and include captions and alt text;
5. confirm sources, status, proof status, and limitations are explicit;
6. verify every required section and remove scaffolding or placeholders;
7. inspect the final PDF or other target rendering when layout matters.

The quality gate verifies both meaning and presentation. A structurally
complete document with unreadable diagrams, weak navigation, or ambiguous
status is not complete.
