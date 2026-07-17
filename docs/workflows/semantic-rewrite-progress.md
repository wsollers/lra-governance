# Semantic Rewrite Progress

This tracker records which volume chapters or chapter-sized clusters have been
run through the semantic rewrite/support-block process.  It is a progress log,
not a source-of-truth mathematical index.

Last updated: 2026-07-17.

## Status Meanings

- `statement rewrite complete`: canonical formal statements were mechanically
  upgraded and locally validated for the recorded scope.
- `statement rewrite in progress`: source statement repairs have started, but
  validation or full chapter coverage is not yet complete.
- `support pilot complete`: provider/validator reports were generated and used
  to tune the semantic-support process, but the source may still need a later
  statement-by-statement pass.
- `inventory ready`: formal statements were listed for review, but rewrite work
  has not started.

## Completed or Run-Through Scopes

| Repo | Volume / Book | Chapter or Scope | Status | Validation / Notes |
|---|---|---|---|---|
| `lra-volume-iii` | Volume III / Analysis I | Bounding: bounds extremals | statement rewrite complete | Included upper/lower bounds, suprema/infima, epsilon characterizations, maxima/minima. Dependency extraction later found and fixed two stale `def:is-nonempty` links. |
| `lra-volume-iii` | Volume III / Analysis I | Bounding: bounds algebra | statement rewrite complete | Included set operations and bounds, bound algebra, pairwise maximum/minimum set operations, algebra of suprema/infima, image/inverse extrema. Style and scoped semantic validation were clean or pending only on missing package artifacts during the batch. |
| `lra-volume-iii` | Volume III / Analysis I | Bounding: completeness cluster | statement rewrite complete | Included least-upper-bound property, completeness equivalences, nested intervals, Archimedean property, density/order-separation items through `cor:no-gaps-in-r`. |
| `lra-volume-iii` | Volume III / Analysis I | Structure of the real line | support pilot complete | Used as the semantic-support provider/validator pilot: open covers, finite subcovers, compactness, Heine-Borel, closed-set closure operations, and related topology-on-`\mathbb R` statements. Generated process fixes for support-block closure, canonical predicate names, dependency roles, and implication transform policy. |

## Current / Next Candidate Scopes

| Repo | Volume / Book | Chapter or Scope | Status | Notes |
|---|---|---|---|---|
| `lra-volume-ii` | Volume II / Discrete Algebraic | Peano systems | statement rewrite in progress | Non-axiom formal statement inventory generated at `F:\repos\lra-volume-ii\build\peano-systems-formal-statements-no-axioms.md`. Count: 37 non-axiom formal statements; axioms excluded. First source pass applied ChatGPT/Codex feedback for Peano system typing, strong induction order assumptions, Presburger signature/arithmetic, and recursion terminology/state encoding. |

## Latest Extraction Check

After the Volume III dependency cleanup, Stage 2 knowledge extraction reported:

- formal nodes: `2546`
- combined edges: `7938`
- validation issues: `0`
- Volume III dependency validation: `0` errors, `0` warnings

Artifacts:

- `F:\repos\lra-governance\logs\extraction-report-20260717-volume-iii-dependency-check-after-fix.md`
- `F:\repos\lra-governance\runs\extraction-20260717-volume-iii-dependency-check-after-fix`

## Update Protocol

When a new chapter or chapter-sized scope is processed:

1. Add or update one row in the completed/run-through table.
2. Record whether the scope is only inventoried, support-pilot processed, or
   statement-rewrite complete.
3. Include the validation command outcome, not only the intended work.
4. Record any follow-up dependency or extraction fixes separately from the main
   rewrite row.
