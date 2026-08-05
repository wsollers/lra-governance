# Search Feedback: Finite Partition Convergence Principle

- Date: 2026-08-02
- Task: Place handwritten proof photo 20260315_170053 for a finite-partition convergence principle.
- Sought: A theorem stating that if N is a finite union of pairwise disjoint infinite index sets and each induced subsequence converges to the same limit L, then the original sequence converges to L.
- Query: finite partition subsequences converge same limit sequence converges
- Tool: python F:\repos\lra-governance\tools\governance\search_internal_object_index.py --index D:\Readings\indexes\lra\internal\all-volumes-lean-tex-index.yaml --source-family tex --limit 8
- Suitable: Failed for placement. Search returned general subsequence convergence/unique subsequential limit theorems but no finite-partition recombination target.
- Best result: `thm:bounded-sequence-converges-iff-unique-subsequential-limit` is related but has additional boundedness/unique-subsequential-limit hypotheses and is not the handwritten statement.
- Missed or noisy results: `thm:subsequences-preserve-limits` and Cauchy subsequence results are adjacent but not suitable routes.
- Notes for search tuning: Phrases "finite partition convergence principle", "finite union of index sets", "each subsequence converges to same limit", "partition of N", and "recombine subsequences" should surface this target if it exists. The handwritten attempt also has a threshold/index gap: it takes a maximum over subsequence thresholds without carefully converting arbitrary large original indices to sufficiently large subsequence positions.
