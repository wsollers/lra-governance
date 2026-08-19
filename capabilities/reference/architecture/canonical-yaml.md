# Canonical YAML

Source: consolidated from the retired DESIGN.md router.

The source-of-truth YAML files live in `lra-governance`:

- `predicates.yaml`
- `structures.yaml`
- `notation.yaml`
- `relations.yaml`

They live at the repository root, not under a volume repo and not under a
chapter-local `docs/` directory.

They moved here when the assembled monorepo (`Learning-Real-Analysis`) was
retired. They are not duplicated into volume repos. Automated authoring,
auditing, and extraction tools read them from `lra-governance`, resolved the same
way as the rest of governance.

## Tool Access

Tools that run outside `lra-governance` resolve the canonical YAML through the
governance root: `LRA_GOVERNANCE_ROOT`, a sibling `../lra-governance` checkout,
or the build Docker image. Older auditor entry points that accept an explicit
root (for example a `REPO_ROOT` environment variable or a `--repoDir` / `--root`
option) should be pointed at the `lra-governance` checkout rather than a
monorepo.

Agents should not load all four registries into context for ordinary lookup.
Use `tools/governance/vocabulary.py` to query the generated SQLite index:

```sh
python tools/governance/vocabulary.py exists UpperBound --kind predicate
python tools/governance/vocabulary.py get pred:upper-bound
python tools/governance/vocabulary.py search "least upper bound" --limit 5
```

`exists` and `search` return compact summaries; `get` returns one complete YAML
record. A missing or stale index is rebuilt automatically from the canonical
YAML. Exact aliases may be overloaded, in which case the tool returns all
matches and `get` reports ambiguity rather than choosing one.

The generated index is disposable and is never canonical. Its location is
resolved from `LRA_VOCABULARY_INDEX`, then `LRA_SOURCE_INDEX_ROOT`, then the
`source_index_root` pointer in `LRA_SOURCES_ROOT/index.yaml` or an adjacent
`lra-sources` checkout, with `build/canonical-vocabulary.sqlite` as the local
fallback. This shares the external generated-index root without making
`lra-sources` the owner of governance vocabulary.

To propose a registry addition without loading or rewriting the whole file,
put exactly one entry in a YAML file and run:

```sh
python tools/governance/vocabulary.py add predicate candidate.yaml
python tools/governance/vocabulary.py add predicate candidate.yaml --write
```

The first command is a dry run. `--write` validates the current registries,
rejects an existing ID, appends the candidate, validates again, restores the
original file on failure, and rebuilds the index. Mathematical and governance
review is still required; the tool does not invent or approve vocabulary.

No agent may invent predicate, structure, relation, or notation names locally in
content files. Missing canonical vocabulary must be reported as a governance or
YAML update need. Predicate names, structure constructors, signatures, and
ambient-structure polymorphism are governed by
`capabilities/reference/predicate-standards.md`.
