# Search Feedback: Cauchy Subsequence Route Slug

- Date: 2026-08-01
- Task: Place handwritten proof photo `20260316_145118.jpg` from proof-photo-staging.
- Sought: The theorem that a Cauchy real sequence with a convergent subsequence converges to the subsequential limit.
- Query: `Cauchy sequence convergent subsequence converges`
- Tool: `python F:\repos\lra-governance\tools\governance\search_internal_object_index.py --index D:\Readings\indexes\lra\internal\all-volumes-lean-tex-index.yaml --source-family tex --limit 8 "Cauchy sequence convergent subsequence converges"`
- Suitable: Partially. The mathematical object was found immediately, but the returned theorem id did not match the proof-vault route id.
- Best result: `thm:cauchy-convergent-subsequence-converges` / Cauchy Sequence with a Convergent Subsequence.
- Missed or noisy results: The proof vault route expects `thm:cauchy-sequence-with-convergent-subsequence`; memorialization rejected the index id with "No route found". Local `rg` of `routing/theorem-routes.json` found the usable route.
- Notes for search tuning: Object index IDs and proof-vault route IDs should be checked for slug drift. The search result title was correct, but agents need either the vault route id included or a mapping between index ids and proof-vault ids.
