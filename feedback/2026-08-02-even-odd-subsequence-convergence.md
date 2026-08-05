# Search Feedback: Even Odd Subsequences Convergence

- Date: 2026-08-02
- Task: Place handwritten proof photo 20260315_164958 for convergence via even and odd subsequences.
- Sought: A theorem stating that if `(a_{2n}) -> L` and `(a_{2n+1}) -> L`, then `(a_n) -> L`.
- Query: sequence converges iff even and odd subsequences converge to same limit
- Tool: python F:\repos\lra-governance\tools\governance\search_internal_object_index.py --index D:\Readings\indexes\lra\internal\all-volumes-lean-tex-index.yaml --source-family tex --limit 8
- Suitable: Failed for placement. Search returned related general subsequence theorems but no exact parity/even-odd recombination theorem.
- Best result: `thm:subsequences-preserve-limits` and `thm:bounded-sequence-converges-iff-unique-subsequential-limit` are related but not the target.
- Missed or noisy results: No exact object for even/odd subsequences determining convergence appeared in the top 8 or local route grep.
- Notes for search tuning: Phrases "even and odd subsequences", "a_2n", "a_{2n+1}", "parity subsequences", "same limit implies sequence converges", and "finite partition convergence" should surface this target if it exists.
