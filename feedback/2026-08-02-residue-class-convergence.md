# Search Feedback: Residue Class Convergence

- Date: 2026-08-02
- Task: Place handwritten proof photo 20260315_174105 for residue-class convergence of a sequence.
- Sought: A theorem stating that if, for each residue `r in {0,...,k-1}`, the subsequence `(a_{kn+r})` converges to the same limit `L`, then `(a_n)` converges to `L`.
- Query: residue class subsequences modulo k converge same limit sequence converges
- Tool: python F:\repos\lra-governance\tools\governance\search_internal_object_index.py --index D:\Readings\indexes\lra\internal\all-volumes-lean-tex-index.yaml --source-family tex --limit 8
- Suitable: Failed for placement. Search returned the residue-class definition and general subsequence theorems, but no exact convergence recombination route.
- Best result: A second query, "subsequence residue class modulo diverges sequence diverges", found `prop:residue-divergence`, which is the related opposite/divergence criterion but not this convergence theorem.
- Missed or noisy results: `def:residue-class-modulo-n` and broad subsequence/Cauchy results ranked above the desired target.
- Notes for search tuning: Phrases "residue class convergence", "a_{kn+r}", "all residues converge to L", "mod k subsequences", and "residue partition convergence" should surface the convergence theorem if it exists. The divergence criterion exists in the index, suggesting a sibling convergence result may be missing or unindexed.
