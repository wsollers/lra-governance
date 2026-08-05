# LRA Search Feedback

Use this folder for short search-quality reports from proof memorialization,
Lean verification, and LaTeX authoring work.

When a task searches for an existing proof, theorem, lemma, definition, or Lean
declaration, record enough detail to tune the search tool later:

- date and task context;
- proof or object being searched for;
- command or query terms used;
- top relevant results, including labels, declarations, paths, or line hints;
- whether the results were suitable;
- missing synonyms, notation, typos, or mathematical phrases that should have
  worked better;
- any proposed improvement to ranking, filtering, or query expansion.

Suggested filename pattern:

```text
YYYY-MM-DD-short-topic.md
```

Suggested entry shape:

```markdown
# Search Feedback: Short Topic

- Date:
- Task:
- Sought:
- Query:
- Tool:
- Suitable:
- Best result:
- Missed or noisy results:
- Notes for search tuning:
```
