# Capstone Exercise Standards

These standards govern chapter-level capstone exercises in LRA volume content.
They define how to choose, author, and lay out a capstone exercise once a
chapter has enough mathematical content to support one.

## Purpose

A capstone is not a review sheet. A review sheet exercises results the chapter
already owns one at a time. A capstone is the first problem that sits strictly
above the chapter: the smallest new result or task whose statement and proof
require the machinery the chapter just built.

A valid capstone must do three things:

- synthesize several chapter results in one logical chain;
- promote at least one existing chapter result by showing it as a special case
  or one-dimensional shadow of the capstone;
- pull toward the larger program, later book, or next structural layer.

If a candidate is merely a hard problem from the same chapter, it is an
exercise, not a capstone.

## Ownership And Location

The canonical chapter capstone file lives at:

```text
<chapter>/proofs/exercises/capstone-<chapter-slug>.tex
```

The router lives at:

```text
<chapter>/proofs/exercises/index.tex
```

The chapter router inputs the exercises router inside the print-edition
exclusion block, as described in `stub-chapter-standards.md` and
`volume-structure.md`.

Do not create root-level `exercises/` for capstones. Do not use legacy
`chapter/capstone.tex` paths.

## Generation Method

### 1. Inventory the chapter from disk

Enumerate every named result actually present in the chapter: definitions,
lemmas, propositions, theorems, corollaries, examples when structurally
relevant, and notation declarations when the capstone depends on them.

Do not rely on memory or the table of contents alone. The repository source is
the ground truth.

### 2. Locate the ceiling and the gap

Identify:

- the ceiling: the most structurally advanced result the chapter actually
  proves;
- the gap: the next structural kind of reasoning the chapter does not yet
  perform.

The capstone must stand above the ceiling, not beside it.

The gap should be structural, not merely topical. Good gap descriptions look
like "single-index reasoning to two-index nonfactoring reasoning",
"pointwise control to uniform control", or "existence to uniqueness plus
construction".

### 3. Score candidate targets

Generate two or three candidate capstones and score each against the three
requirements: synthesis, promotion, and telos pull. Keep only a candidate that
satisfies all three.

Reject candidates that:

- re-prove a theorem already in the notes;
- use only one local result;
- require results beyond the chapter dependency ceiling;
- are disconnected from the larger program.

### 4. Find the shadow

Before authoring the capstone, identify the existing theorem, proposition, or
lemma that the capstone generalizes or promotes. State the specialization
explicitly: which substitution, restriction, or degenerate case collapses the
capstone back to the existing result.

If no shadow exists, reconsider whether the candidate is earned by the chapter.

### 5. Decompose top-down

State the target first in full rigor. Then ask what must be true for the target
to be provable. Each answer is a prerequisite component.

Write the proof architecture as necessity, not as a shopping list:

```text
To establish X, first secure Y, because the main argument consumes Y at this
point. With Y available, the remaining obstruction is Z.
```

The component order is governed by the target theorem pulling prerequisites
into existence.

### 6. Scope honestly

State what the capstone does not prove: the converse that fails, the hypothesis
that is load-bearing, the equality condition that needs more machinery, or the
generalization deferred to a later chapter.

The boundary is part of the mathematical lesson and often supplies the bridge
to the next chapter.

## Authoring Layout

A capstone should read as a short mathematical exercise-essay, not as a boxed
theorem database. The default authored layout is:

1. main theorem or problem statement;
2. what it says;
3. architecture of the proof;
4. components to prove;
5. scope and honest limits;
6. instantiation toward the larger program;
7. optional formal appendix.

### Main theorem or problem statement

Open with the rigorous target statement. Include all quantifiers, hypotheses,
existence conditions, and dependency-ceiling assumptions needed to make the
problem well-posed.

### What it says

Give the geometric, mechanical, or conceptual picture before returning to the
symbols. The reader should understand why the statement is the next natural
object, not merely what the formal syntax says.

### Architecture of the proof

Decompose the target top-down. Each prerequisite should be introduced only when
the reader can see the role it plays in the main argument.

### Components to prove

State each component rigorously. Give a strategic pointer or trailhead, not a
full proof, unless the task explicitly asks for a solution key.

### Scope and honest limits

Record converse failures, load-bearing hypotheses, strictness of inequalities,
and deferred equality or compactness conditions.

### Instantiation toward the larger program

Close with a concrete instance, model, or future-facing specialization that
shows why this capstone belongs in the LRA program.

### Optional formal appendix

Use a formal appendix when the chapter has a formal-language layer or when the
capstone's logical form is itself pedagogically important. The appendix may
include predicate-logic renderings of the main definitions and principal claim.

## Solution Policy

The capstone file should normally provide the proof architecture and component
trailheads, not full solutions. A capstone that supplies all proofs is a worked
example.

Generate or commit a full solution only when the task explicitly requests a
solution key, instructor copy, or completed worked capstone. In that case, make
the solution status clear in prose or metadata, and keep dependencies and labels
valid.

## Dependency Ceiling

A capstone may reference:

- results from the current chapter;
- results from chapters that precede the current chapter in the volume or book
  dependency order.

A capstone must not reference:

- later chapters;
- unintroduced notation;
- future machinery used only because it makes the problem easier.

If the desired capstone needs later machinery, either weaken the statement or
record it as a future-facing limit.

## TeX Skeleton

Use the canonical path and router shape from `volume-structure.md`. A full
capstone file should follow this source shape unless a repo-local validator
requires a stricter template:

```latex
\newpage
\phantomsection
\label{prf:capstone-<chapter-slug>}

\begin{remark*}[Return]
\hyperref[ch:<chapter-slug>]{Return to Chapter: <Chapter Display Title>}
\end{remark*}

\subsection*{Capstone --- <Chapter Display Title>}

\begin{remark*}[Theorem]
<Full rigorous statement.>
\end{remark*}

\begin{remark*}[What it says]
<Physical or conceptual reading.>
\end{remark*}

\begin{remark*}[Architecture of the proof]
<Top-down necessity decomposition.>
\end{remark*}

\begin{remark*}[Components]
\begin{enumerate}
  \item <Component statement> \emph{Strategy:} <trailhead only>.
\end{enumerate}
\end{remark*}

\begin{remark*}[Scope and honest limits]
<Converse failures, load-bearing hypotheses, deferred generalizations.>
\end{remark*}

\begin{remark*}[Instantiation toward the program]
<Concrete bridge into the larger program.>
\end{remark*}

\begin{dependencies}
\begin{itemize}
  \item \hyperref[<label>]{<Readable dependency name>}
\end{itemize}
\end{dependencies}
```

The capstone should not use theorem-environment boxes unless the owning chapter
has already promoted the capstone result into settled notes. The capstone is
an exercise artifact first.

## Acceptance Checklist

Before accepting a generated capstone:

- the chapter inventory was taken from source files;
- the target stands above the chapter ceiling;
- the structural gap is named;
- synthesis, promotion, and telos pull are all present;
- the shadow theorem is identified;
- no dependency-ceiling violation is present;
- the layout follows the canonical capstone path;
- the file builds and validates with the owning volume.
