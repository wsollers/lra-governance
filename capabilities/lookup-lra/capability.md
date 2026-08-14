# Capability: lookup-lra

## Action

Find a theorem, definition, concept, formal declaration, implementation object,
or canonical vocabulary entry across the generated LRA indexes without loading
the indexes into agent context.

## Tool

```powershell
python <governance-root>\tools\governance\lra_lookup.py "<query>"
```

The default searches separate result lanes for primary reading sources,
authored TeX, Lean declarations, C++ objects, and canonical vocabulary. Use
`--scope sources`, `tex`, `lean`, `cpp`, `vocabulary`, or `internal`; repeat
`--scope` to combine lanes. Use `--volume`, `--book`, `--chapter`, `--author`,
`--source-id`, `--source-list`, or `--profile` to constrain primary-source
lookup. Run `--status` to inspect index availability.

Primary-source lookup is strict first and loose by default. If the source lane
returns no hits, `lra_lookup.py` automatically retries bounded looser forms of
the query, such as normalizing `def` to `definition`, removing prompt filler,
repairing reviewed typo aliases, and interpreting weak author hints like
`from zorich` or `tao sigma algebra`. Inspect `loose_attempts`,
`matched_query`, and `matched_author_filter` before relying on a loose hit.
Pass `--no-loose-sources` only when a strict zero-hit result is required.

## Refresh

When a lane is stale or unavailable, refresh one independent family or all
families through the source-profile orchestrator:

```powershell
python <source-profiles-root>\scripts\refresh_lra_indexes.py --scope tex
python <source-profiles-root>\scripts\refresh_lra_indexes.py --scope all
```

Ordinary PDF ingestion refreshes the primary-source SQLite database
automatically. TeX and Lean delta updates and C/C++ indexing likewise replace
their family database after successful CUD processing.

## Rules

- Query first; do not open the full generated YAML/JSON indexes or canonical
  vocabulary registries for ordinary lookup.
- Treat each lane according to its authority. Reading-source hits are external
  evidence; TeX/Lean/C++ hits identify LRA-authored objects; vocabulary hits
  identify governed names and signatures.
- A hit is a discovery result, not automatic mathematical authority. Read the
  surrounding source text or repository file before quoting, changing, or
  relying on it.
- Use `rg` after an indexed code/object hit when exact raw implementation text
  is needed. The C++ lane indexes declarations and objects, not every source
  line.
- If a lane is unavailable, report its warning rather than pretending the
  corpus was searched.

## Success Gate

```powershell
python <governance-root>\tools\governance\lra_lookup.py --status
```
