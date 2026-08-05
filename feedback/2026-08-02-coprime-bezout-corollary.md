# Search Feedback: Coprime Bezout Corollary

- Date: 2026-08-02
- Task: Place handwritten proof photos 20260318_182932 and 20260318_183109 for gcd(a,b)=1 iff 1 is an integer linear combination of a and b.
- Sought: An exact coprime/relatively-prime Bezout corollary, or the closest Bezout identity route.
- Query: gcd a b equals 1 iff there exist integers m n ma plus nb equals 1 coprime Bezout
- Tool: python F:\repos\lra-governance\tools\governance\search_internal_object_index.py --index D:\Readings\indexes\lra\internal\all-volumes-lean-tex-index.yaml --source-family tex --limit 8
- Suitable: Partial. The first query returned `thm:bezout-identity-on-z` as result 3. A synonym query using "relatively prime coprime integers linear combination equals one iff gcd one" did not return Bezout in the top 8.
- Best result: `thm:bezout-identity-on-z` was the closest vault route. No exact coprime corollary route was found.
- Missed or noisy results: The synonym query was dominated by unrelated linear-combination results from analysis and linear algebra.
- Notes for search tuning: Phrases "coprime", "relatively prime", "gcd equals one", "linear combination equals 1", and "Bezout corollary" should strongly boost integer divisibility/Bezout objects. Consider adding or indexing a corollary target for `gcd(a,b)=1 iff exists m,n in Z, ma+nb=1` if it exists canonically.
