# Mathematical Authoring Prompt: One Full Capstone

## Role

Author the mathematical content fields for exactly one chapter capstone. This
prompt is used only for explicit full-capstone authoring. Deterministic capstone
stubs never pass through it, and complete solutions require a separate explicit
proof-authoring request.

The caller supplies a validated compact JSON request, renders the canonical
LaTeX structure deterministically, and rejects invalid output.

## Input Boundary

Treat these request fields as authoritative:

- `chapter_subject`, `chapter_display_title`, and `capstone_label`;
- `registry_ceiling`;
- `state_dependencies` and `proof_dependencies`;
- `selected_source_statements`; and
- `output_schema`.

The source records are exact current-chapter formal statements extracted from
the notes tree. Use only their mathematics. Do not invent labels, prerequisites,
or statements, and do not use results from later chapters.

## Mathematical Contract

- State one theorem-shaped capstone target, not an imperative problem prompt.
- Require genuine synthesis of at least two selected current-chapter results.
- Do not merely ask for an existing theorem to be reproved.
- Make the architecture top-down and identify components without supplying a
  complete proof.
- Identify an existing result that is a special case, restriction, or shadow
  when the supplied records support that claim.
- State honest limits, load-bearing hypotheses, and deferred stronger results.
- Keep every proposed strategy within the supplied registry ceiling.

## Output Contract

Return exactly one JSON object with exactly these fields:

```json
{
  "theorem": "...",
  "what_it_says": "...",
  "architecture_of_proof": "...",
  "components": [
    {"statement": "...", "strategy": "..."},
    {"statement": "...", "strategy": "..."}
  ],
  "scope_and_honest_limits": "...",
  "instantiation_toward_program": "..."
}
```

Use ASCII LaTeX strings. Every field must be nonempty, and `components` must
contain at least two items. Strategies are trailheads only, not worked proof
steps. Do not emit labels, boxes, dependency environments, page commands,
Markdown fences, or any surrounding explanation; the deterministic renderer
owns all structural LaTeX.
