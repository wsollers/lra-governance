# Simulated response

The Volume I `Poset` supplies both the carrier and its non-strict ordering
relation. For a poset \(P\), a subset \(A\subseteq P\), and \(u\in P\), the
definition is

```latex
\[
  u\text{ is an upper bound of }A
  \quad\Longleftrightarrow\quad
  \forall x\in A,\; x\leq_P u.
\]
```

```lean
def UpperBound
    (poset : LRA.VolumeI.Relations.Order.Poset)
    {SetObject : Type v}
    [Membership poset.Carrier SetObject]
    (subset : SetObject)
    (bound : poset.Carrier) : Prop :=
  forall element, element ∈ subset -> poset.NonStrictOrder element bound
```

Requested family selection:

- Include the literal negation and its witnessed form: an upper-bound claim
  fails exactly when some member of the subset is not below the candidate.
- Include the contrapositive characterization. Its reverse direction uses
  classical logic for an arbitrary proposition-valued order relation.
- Do not assert the converse `x ≤ u → x ∈ A` or inverse
  `x ∉ A → ¬x ≤ u`; both are false. Include concrete counterexamples instead.
- Include the empty-set boundary and a finite positive example.
- Include counterexamples showing that an upper bound need not belong to the
  subset and that a poset subset need not have any upper bound.
- Do not generate a Volume III or real-number specialization: this request is
  scoped to Volume I.

The response is a proposal. The reviewed package owns the exact source sent to
the materializer, and theorem-like declarations remain explicit `sorry` stubs
until proof completion is separately requested.
