| LRA predicate | Mathlib name | Doc link | Source (commit-pinned) | Status | Notes |
|---|---|---|---|---|---|
| Sequence | Set.range | [Set.range](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Data/Set/Operations.html#Set.range) | [source](https://github.com/leanprover-community/mathlib4/blob/14c4b77b0c8c8fe5e0fbc8753e3d7e43f66678d3/Mathlib/Data/Set/Operations.lean#L158-L162) | FOUND | **BAD MAPPING** -- Set.range is the image of a function, not "a sequence". Mathlib has no reified Sequence type (a sequence is just x : Nat -> X); correct table entry is NOT_FOUND / no reification. |
| ConvergesTo | Filter.Tendsto | [Filter.Tendsto](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Order/Filter/Defs.html#Filter.Tendsto) | [source](https://github.com/leanprover-community/mathlib4/blob/14c4b77b0c8c8fe5e0fbc8753e3d7e43f66678d3/Mathlib/Order/Filter/Defs.lean#L318-L322) | FOUND | Correct correspondence, but register differs: Mathlib's primitive is filter convergence (Tendsto x atTop (nhds L)); your epsilon-N form is a derived characterization for metric/normed spaces, not the base definition. |
| uniqueness-of-limits | tendsto_nhds_unique | [tendsto_nhds_unique](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Topology/Separation/Hausdorff.html#tendsto_nhds_unique) | [source](https://github.com/leanprover-community/mathlib4/blob/14c4b77b0c8c8fe5e0fbc8753e3d7e43f66678d3/Mathlib/Topology/Separation/Hausdorff.lean#L179-L181) | FOUND | Mathlib's version is stated for Hausdorff spaces generally, matching your interpretation-block remark about the Hausdorff axiom. |
| limit-preserves-eventual-order | le_of_tendsto_of_tendsto | [le_of_tendsto_of_tendsto](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Topology/Order/OrderClosed.html#le_of_tendsto_of_tendsto) | [source](https://github.com/leanprover-community/mathlib4/blob/14c4b77b0c8c8fe5e0fbc8753e3d7e43f66678d3/Mathlib/Topology/Order/OrderClosed.lean#L470-L473) | FOUND |  |
| constant-squeeze-theorem | tendsto_const_nhds | [tendsto_const_nhds](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Topology/Neighborhoods.html#tendsto_const_nhds) | [source](https://github.com/leanprover-community/mathlib4/blob/14c4b77b0c8c8fe5e0fbc8753e3d7e43f66678d3/Mathlib/Topology/Neighborhoods.lean#L190-L191) | FOUND | Your "degenerate squeeze" framing isn't how Mathlib states this -- it's just "constant sequences tend to their value," worth a note in the crossref table that these are the same fact via different proof routes. |
| sequence-squeeze-theorem | tendsto_of_tendsto_of_tendsto_of_le_of_le | [tendsto_of_tendsto_of_tendsto_of_le_of_le](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Topology/Order/Basic.html#tendsto_of_tendsto_of_tendsto_of_le_of_le) | [source](https://github.com/leanprover-community/mathlib4/blob/14c4b77b0c8c8fe5e0fbc8753e3d7e43f66678d3/Mathlib/Topology/Order/Basic.lean#L227-L234) | FOUND |  |
| absolute-value-squeeze-theorem | squeeze_zero | [squeeze_zero](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Topology/MetricSpace/Pseudo/Lemmas.html#squeeze_zero) | [source](https://github.com/leanprover-community/mathlib4/blob/14c4b77b0c8c8fe5e0fbc8753e3d7e43f66678d3/Mathlib/Topology/MetricSpace/Pseudo/Lemmas.lean#L36-L40) | FOUND | Candidate only -- confirm the exact hypothesis shape (Mathlib's version may use |.| <= u_n differently than your le vs L bound); review before citing. |
| NullSequence | tendsto_zero_iff_norm_tendsto_zero | [tendsto_zero_iff_norm_tendsto_zero](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Analysis/Normed/Group/Continuity.html#tendsto_zero_iff_norm_tendsto_zero) | [source](https://github.com/leanprover-community/mathlib4/blob/14c4b77b0c8c8fe5e0fbc8753e3d7e43f66678d3/Mathlib/Analysis/Normed/Group/Continuity.lean#L67-L67) | FOUND | Candidate only -- Mathlib doesn't name "null sequence" as such; this is an iff-lemma about norm convergence, not a definition. Review whether a plainer `Tendsto _ atTop (nhds 0)` citation serves better. |
| Eventually | Filter.Eventually | [Filter.Eventually](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Order/Filter/Defs.html#Filter.Eventually) | [source](https://github.com/leanprover-community/mathlib4/blob/14c4b77b0c8c8fe5e0fbc8753e3d7e43f66678d3/Mathlib/Order/Filter/Defs.lean#L279-L282) | FOUND | Correct correspondence -- your "Eventually(x_n, P)" is literally `∀ᶠ n in atTop, P n`, i.e. `Filter.Eventually P atTop`. |

## Takeaway for the crossref table

Barebone name -> name lookup works reliably as a *mechanical* step, but this
run confirms your suspicion: a crossref table needs a curation pass on top
of the raw harvest, because:

1. Some LRA concepts have no Mathlib reification at all (Sequence itself).
2. Some correspondences are real but cross a definitional register (your
   epsilon-N convergence vs. Mathlib's filter-based Tendsto) -- true, but
   worth documenting *why*, not just *that*.
3. Some candidate resolutions are plausible guesses that need verification
   against the actual Lean signature (squeeze_zero, tendsto_zero_iff_norm...)
   before being cited as authoritative.

A practical next step: add a `verified: true/false` and `register_note`
field to the mapping YAML schema, so the harvester's raw output and your
human sign-off are tracked separately.
