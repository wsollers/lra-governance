# Search Feedback: Iterator Relation

- Date: 2026-08-01
- Task: Route handwritten proof photos before memorializing them in `lra-proof-vault`.
- Sought: The theorem/proof target for photos mentioning Peano systems, iterator data, and the minimal iterator relation.
- Query: `iterator relation consistency Peano system minimal iterator relation`
- Tool: `python F:\repos\lra-governance\tools\governance\search_internal_object_index.py --index D:\Readings\indexes\lra\internal\all-volumes-lean-tex-index.yaml --source-family tex --limit 8`
- Suitable: Yes.
- Best result: `lem:iterator-relation-consistency` / "The Minimal Iterator Relation Is an Iterator Relation"; the proof source `prf-iterator-relation-consistency.tex` also appeared in the top results.
- Missed or noisy results: The related definition and totality/determinism lemmas appeared, but they were useful neighbors rather than harmful noise.
- Notes for search tuning: Phrases such as "minimal iterator relation", "iterator relation consistency", and "Peano system iterator data" should continue to rank this target highly.
