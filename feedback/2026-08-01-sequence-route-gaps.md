# Search Feedback: Sequence Route Gaps

- Date: 2026-08-01
- Task: Proof photo queue placement from lra-proof-vault temporary intake.
- Sought: Routes for unique limit of a convergent sequence and convergent sequences are bounded.
- Query: "convergent sequence limit is unique sequence limits unique"; "real sequence has unique limit if x_n tends to L1 and L2 then L1 equals L2"; "convergent sequence is bounded finite head tail bounded by limit".
- Tool: python F:\repos\lra-governance\tools\governance\search_internal_object_index.py --index D:\Readings\indexes\lra\internal\all-volumes-lean-tex-index.yaml --source-family tex --limit 8
- Suitable: Partially.
- Best result: thm:metric-convergent-sequences-unique-limits for uniqueness; prop:convergent-bounded for boundedness.
- Missed or noisy results: The index found plausible objects, but lra-proof-vault memorialize route lookup rejected both theorem ids. For uniqueness, the index did not surface a real-sequence-specific unique-limit result; only the metric-space theorem was exact.
- Notes for search tuning: Route-map parity should include prop:convergent-bounded and thm:metric-convergent-sequences-unique-limits if proof-vault intake is expected to place these photos. A synonym such as "limit of a convergent real sequence is unique" should ideally find the real sequence theorem if one exists.
