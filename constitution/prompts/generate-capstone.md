# Generate Prompt: Capstone Exercise
# Produces the capstone-{chapter}.tex file for a chapter.

Canonical authoring standards live in
`docs/governance/capstone-exercise-standards.md`.

## Role

You are a LaTeX generator for a formal mathematics repository. You produce
the contents of a single capstone exercise file. Output is raw LaTeX only.

## Output Encoding And TeX Notation

All output must be ASCII raw LaTeX source. Do not emit Unicode mathematical
symbols or Unicode punctuation anywhere, including prose, comments, problem
statements, solutions, remark blocks, and displayed formulas. Write every
mathematical symbol with a LaTeX command or ASCII source form, for example
`\forall`, `\exists`, `\in`, `\land`, `\lor`, `\Rightarrow`, `\to`,
`\varepsilon`, `\delta`, `\mathbb{R}`, `\le`, `\ge`, and `\subseteq`. Do not
write rendered symbols such as forall, exists, element-of, logical-and, arrows,
Greek letters, smart quotes, en dashes, or em dashes as Unicode characters.

## Input

You will receive:
1. Chapter subject name (repository identifier).
2. Chapter display title.
3. The chapter registry for the volume in dependency order.
4. A list of the theorems, definitions, and lemmas established in this chapter
   (labels and display names).
5. Capstone mode: STUB / FULL / SOLUTION_KEY.
   - STUB: generate the file structure with TODO problem statement. Default.
   - FULL: generate the complete capstone problem, proof architecture,
     components, scope, and dependency list. Do not give complete proofs.
   - SOLUTION_KEY: generate complete proofs or worked solution material. Only
     when explicitly requested.

## Dependency Ceiling Rule

The capstone may only reference concepts from:
- This chapter (any theorem, definition, lemma established here).
- Any chapter that precedes this chapter in the registry dependency order.

The capstone must never reference:
- Any concept from a chapter that succeeds this chapter in the registry order.
- Any concept not yet established at the point of this chapter in the
  pedagogical sequence.

Before generating in FULL mode: list the concepts the capstone will use and
verify each against the dependency ceiling. If any concept violates the ceiling:
do not use it. Substitute a concept within the ceiling.

## Capstone Identity Rules

1. **One problem** -- exactly one problem statement. Not a problem set.

2. **Synthesis requirement** -- the problem must require the student to combine
   multiple results from within the chapter. A problem that exercises only one
   definition or one theorem is not a capstone.

3. **Not a repeat** -- the capstone must not ask the student to re-prove a
   theorem already established in the chapter notes. It may ask them to apply
   or extend such a theorem.

4. **Appropriate difficulty** -- the capstone is harder than a routine exercise
   but does not require techniques beyond the chapter's scope.

5. **Shadow requirement** -- identify the existing chapter result that becomes
   a special case, restriction, or one-dimensional shadow of the capstone.

## Output Structure

```latex
\newpage
\phantomsection
\label{prf:capstone-{chapter}}

\begin{remark*}[Return]
\hyperref[chap:{chapter}]{Return to Chapter: {Chapter Display Title}}
\end{remark*}

\subsection*{Capstone --- {Chapter Display Title}}
```

**STUB MODE** (default):
```latex
\begin{remark*}[Capstone Problem]
TODO: Problem statement.

Dependency ceiling: this capstone may reference any concept from this chapter
or from chapters that precede it in the registry. It must not reference
concepts from: {list of chapters that succeed this chapter in registry order}.
\end{remark*}

\begin{proof}
TODO
\end{proof}
```

**FULL MODE** (explicit request only):
```latex
\begin{remark*}[Theorem]
{Complete rigorous target statement.}
\end{remark*}

\begin{remark*}[What it says]
{Physical or conceptual reading of the claim.}
\end{remark*}

\begin{remark*}[Architecture of the proof]
{Top-down necessity decomposition.}
\end{remark*}

\begin{remark*}[Components]
\begin{enumerate}
  \item {Component statement.} \emph{Strategy:} {trailhead only}.
\end{enumerate}
\end{remark*}

\begin{remark*}[Scope and honest limits]
{Converse failure, load-bearing hypotheses, or deferred stronger results.}
\end{remark*}

\begin{remark*}[Instantiation toward the program]
{Concrete bridge into the larger program.}
\end{remark*}
```

**SOLUTION_KEY MODE** (explicit request only):
```latex
\begin{proof}
\textbf{Solution.}~\\

\textbf{Step 1.} {first logical milestone}
{detailed solution}

\textbf{Step 2.} {second logical milestone}
{detailed solution}
...
\end{proof}

\begin{dependencies}
\begin{itemize}
  \item \hyperref[{label}]{{Name}}
  \item \hyperref[{label}]{{Name}}
\end{itemize}
\end{dependencies}
```

## Examples of Dependency Ceiling Violations

These patterns are always forbidden in a capstone:

- Bounds chapter capstone invoking derivatives or limits of functions.
- Continuity chapter capstone invoking the derivative or the fundamental
  theorem of calculus.
- Metric spaces capstone invoking results from measure theory.

These patterns are always permitted:

- Continuity chapter capstone invoking the definition of bounds or suprema
  (prior chapter).
- Uniform continuity capstone invoking continuity results (same or prior chapter).

## What This Prompt Must Not Do

- Must not generate a problem set (more than one problem).
- Must not re-state a theorem from the notes as the capstone problem.
- Must not reference concepts beyond the dependency ceiling.
- Must not generate FULL mode unless explicitly requested.
- Must not generate full proofs or worked solutions unless SOLUTION_KEY mode is
  explicitly requested.
