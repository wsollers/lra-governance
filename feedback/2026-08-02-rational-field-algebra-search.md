# Search Feedback: Rational Field Algebra Queries

- Date: 2026-08-02
- Task: Proof photo intake placement for rational field algebra proofs.
- Sought: Multiplicative cancellation on Q and reciprocal-on-Q-classes routes.
- Query: "multiplication cancellation if ac equals bc and c not zero then a equals b field rational"; "rational reciprocal of nonzero rational (a/b)^-1 equals b/a"
- Tool: python F:\repos\lra-governance\tools\governance\search_internal_object_index.py --index D:\Readings\indexes\lra\internal\all-volumes-lean-tex-index.yaml --source-family tex --limit 8
- Suitable: Partially.
- Best result: Exact follow-up queries found cor:multiplicative-cancellation-on-q and def:reciprocal-on-q-classes.
- Missed or noisy results: The first cancellation query ranked inequality cancellation and natural-number cancellation ahead of the rational equality corollary. The first reciprocal query ranked real reciprocal/cut/function reciprocal objects ahead of def:reciprocal-on-q-classes.
- Notes for search tuning: For rational-field photos, phrases such as "field", "rational", "ac=bc", "c not zero", "a/b inverse", "b/a", and "nonzero rational reciprocal" should boost Q field-structure and Q-class routes before real-analysis reciprocal/cut objects.
