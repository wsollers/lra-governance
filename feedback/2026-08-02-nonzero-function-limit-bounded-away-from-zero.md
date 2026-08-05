# Search Feedback: Nonzero Function Limit Bounded Away From Zero

- Date: 2026-08-02
- Task: Place handwritten proof photo 20260325_175119 for a theorem that a function with nonzero limit is bounded away from zero near the limit point.
- Sought: A theorem/corollary of the form: if `lim_{x->c} f(x)=L` and `L != 0`, then there exist delta>0 and m>0 such that `|f(x)| >= m` for `x in A` with `0<|x-c|<delta`.
- Query: function limit nonzero bounded away from zero exists delta f x absolute value greater than half absolute L
- Tool: python F:\repos\lra-governance\tools\governance\search_internal_object_index.py --index D:\Readings\indexes\lra\internal\all-volumes-lean-tex-index.yaml --source-family tex --limit 8
- Suitable: Partial/failed for placement. Search found nearby definitions and consequences, but no exact limit theorem route.
- Best result: `def:function-bounded-away-from-zero-near` explains the target property, but it is not the theorem being proved. `prop:bounded-away-from-zero-near-implies-nonzero-near` and reciprocal boundedness theorems are downstream, not the target.
- Missed or noisy results: No exact object for "nonzero limit implies bounded away from zero near c" appeared. The routing table also did not show a function-limit route for this target.
- Notes for search tuning: Phrases "nonzero limit", "bounded away from zero near", "half absolute L", "deleted neighborhood", and "function limit" should surface this theorem if it exists. The handwritten attempt is incorrect as written because it uses `L - epsilon < |f(x)|` rather than the needed `|L| - epsilon < |f(x)|`.
