# Search Feedback: List Equality

- Date: 2026-08-02
- Task: Proof photo intake placement for handwritten list equality proof.
- Sought: A theorem/proposition stating that two lists are equal iff they have the same length and the same entries in the same order.
- Query: "two lists are equal iff same length and same elements in same order list equality"
- Tool: python F:\repos\lra-governance\tools\governance\search_internal_object_index.py --index D:\Readings\indexes\lra\internal\all-volumes-lean-tex-index.yaml --source-family tex --limit 8
- Suitable: No.
- Best result: def:set-equality, which is related only by the word equality and is not a list theorem.
- Missed or noisy results: Results were dominated by set equality, nested intervals with vanishing length, and unrelated order lemmas.
- Notes for search tuning: Phrases such as "list equality", "same length", "same entries", "same elements in same order", and "indexed entries determine a list" should surface a list/finite-sequence equality object if one exists.
