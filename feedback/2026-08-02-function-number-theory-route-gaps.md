# Search Feedback: Function and Number Theory Route Gaps

- Date: 2026-08-02
- Task: Place handwritten proof photos from `tmp-proof-intake/2026-07-31-harvest/proof-photo-staging`.
- Sought: Coprime Bezout criterion; nonzero function-limit bounded-away-from-zero/sign-preservation facts; bounded-function absolute-value characterization.
- Query: `gcd a b equals 1 iff 1 linear combination ma nb`; `coprime relatively prime Bezout integer linear combination`; `if limit f at c is nonzero then f is bounded away from zero near c`; `continuous function sign preservation positive near point negative near point`; `function bounded on a set exists M such that absolute value f x less than M`
- Tool: `python F:\repos\lra-governance\tools\governance\search_internal_object_index.py --index D:\Readings\indexes\lra\internal\all-volumes-lean-tex-index.yaml --source-family tex --limit 8 <query>`
- Suitable: Mixed. Search found Bezout identity and bounded-function definitions/theorem candidates, but missed or could not route several proof targets.
- Best result: `thm:bezout-identity-on-z` worked for the main two-page Bezout identity proof. For bounded functions, search found `thm:bounded-iff-absolute-value-bounded-above`, but proof-vault routing did not contain that theorem id; local placement used `def:function-bounded` as a route-gap workaround.
- Missed or noisy results: No exact result for the coprime criterion `gcd(a,b)=1 iff 1=ma+nb`; no exact route for function-limit nonzero implies bounded away from zero near a point; no exact route for continuity sign preservation near a point. The sign-preservation searches mostly returned continuity definitions and unrelated sign/order facts.
- Notes for search tuning: Add synonyms/objects for `coprime`, `relatively prime`, `Bezout criterion`, `nonzero limit bounded away from zero`, `local sign preservation`, `same sign near a point`, and expose proof-vault route ids for theorem hits when they differ or are absent locally.
