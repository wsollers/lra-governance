# Search Feedback: Continuous Sign Preservation

- Date: 2026-08-02
- Task: Place handwritten proof photo 20260330_131835 for sign preservation of a continuous function near a point.
- Sought: A theorem stating that if `f:E -> R` is continuous at `x0` and `f(x0)>0`, then `f(x)>0` for all nearby `x in E`; analogously for `f(x0)<0`.
- Query: continuous function positive at c positive near c sign preservation
- Tool: python F:\repos\lra-governance\tools\governance\search_internal_object_index.py --index D:\Readings\indexes\lra\internal\all-volumes-lean-tex-index.yaml --source-family tex --limit 8
- Suitable: Failed for placement. No exact sign-preservation theorem route was found.
- Best result: `def:continuous-at-point` and `def:continuous-at-point-nbhd` were nearby definitions, but neither is the theorem being proved.
- Missed or noisy results: Search returned function boundedness and unrelated positive-dilation bounds above the continuity definition.
- Notes for search tuning: Phrases "sign preservation", "positive at a point positive nearby", "negative at a point negative nearby", "continuous at x0", and "choose epsilon f(x0)/2" should surface this theorem if it exists. The handwritten proof proves only the positive case explicitly and notes the negative case analogously.
