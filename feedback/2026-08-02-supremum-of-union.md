# Search Feedback: Supremum of Union

- Date: 2026-08-02
- Task: Place handwritten proof photo 20260309_180524 for `sup(A union B) = max{sup A, sup B}`.
- Sought: A theorem stating that for nonempty bounded-above sets A and B, `sup(A \cup B)=max{sup A,sup B}`.
- Query: supremum union equals max sup A sup B bounded above
- Tool: python F:\repos\lra-governance\tools\governance\search_internal_object_index.py --index D:\Readings\indexes\lra\internal\all-volumes-lean-tex-index.yaml --source-family tex --limit 8
- Suitable: Failed for placement. Search returned boundedness of union and pairwise maximum set results, but no exact union-supremum route.
- Best result: `prop:union-bounded-above-iff-pieces-bounded-above` was related to boundedness only. `thm:supremum-pairwise-maximum-set` concerns a pointwise maximum set, not a union.
- Missed or noisy results: No route-table match for `supremum union` or `union supremum` in the proof vault.
- Notes for search tuning: Phrases "supremum of union", "sup(A union B)", "max of suprema", and "finite union supremum" should surface this target if it exists. The handwritten attempt also appears incomplete: it proves only that `sup(A union B) >= max{sup A,sup B}` and does not prove the upper-bound direction.
