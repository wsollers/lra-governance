# Search Feedback: Monotone Approximation Bounds

- Date: 2026-08-02
- Task: Place handwritten proof photos 20260314_222351 and 20260314_230812 for monotone approximation of bounds.
- Sought: `prop:monotone-approx-bounds`, the proposition that every nonempty bounded subset of R admits monotone sequences in the set converging to its supremum and infimum.
- Query: monotone approximation bounds supremum sequence a_n in S increasing bounded above
- Tool: python F:\repos\lra-governance\tools\governance\search_internal_object_index.py --index D:\Readings\indexes\lra\internal\all-volumes-lean-tex-index.yaml --source-family tex --limit 8
- Suitable: Search succeeded; vault attachment failed.
- Best result: `prop:monotone-approx-bounds` was result 2 and matched the handwritten title/statement.
- Missed or noisy results: Result 1 was related but different (`thm:increasing-sequence-limit-as-supremum`).
- Notes for search tuning: The object exists in the index at `volume-iii/book-analysis-i/real-analysis/notes/proof-techniques/completeness-construction.tex`, but `lra-proof-vault` routing did not contain `prop:monotone-approx-bounds`, so `scripts/memorialize_attempt.py` rejected it without `--allow-unmapped`. The proof photos are also mathematically incorrect because they assert explicit interpolated points lie in an arbitrary set S.
