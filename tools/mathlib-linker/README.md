# Mathlib Link Harvester

Resolves LRA predicate names to Mathlib4 documentation pages and
commit-pinned GitHub source links, for cross-referencing in
`.tex` notes/proofs (e.g. `\hyperref` targets or footnote citations).

## How it works

1. **Loogle** (`https://loogle.lean-lang.org/json?q=<name>`) is queried for
   each candidate Mathlib identifier; only an *exact* name match is kept,
   giving the defining module (e.g. `Mathlib.Order.Bounds.Defs`).
2. The static doc-gen4 page for that module is fetched directly (no JS
   execution needed -- the `/find` search box on the docs site is
   client-side JS reading a binary index and is NOT scriptable this way).
   The declaration's `<div class="gh_link">` block gives the exact GitHub
   permalink, pinned to the commit the docs were built from, with a line
   range (`#L48-L52`).

## Usage

```
pip install pyyaml beautifulsoup4 --break-system-packages
python3 mathlib_link_harvester.py example-mapping.yaml output.md
```

`example-mapping.yaml` is seeded from the `order` category of
`predicates.yaml` (UpperBound, BoundedAbove, IsLUB/IsGLB cluster, etc.) as
a worked example -- extend it with your other predicate categories as
needed. Each entry supports a list of `candidates`; the first Mathlib name
that resolves wins, and every attempt is logged to stderr.

## What "FOUND" does and doesn't mean

A `FOUND` status means the Mathlib declaration exists and both links are
correct. It does **not** assert that the Mathlib declaration is the same
mathematical construction as your LRA definition. Example: `DedekindCut`
resolves cleanly in Mathlib, but it names the generic Dedekind-MacNeille
completion of an arbitrary poset -- Mathlib actually builds `ℝ` via Cauchy
sequences of rationals, not cuts. The script deliberately does not try to
adjudicate "is this the same idea" -- only "does this name exist and where."

## Known limitations

- Aliased lemmas (Mathlib's `@[alias]` lemmas) are reported with a note
  (`ALIAS of \`X\` (not followed)`) rather than silently redirected --
  decide case by case whether you want the alias or the canonical name.
- Ambiguous concepts (e.g. "Bounded" could mean `Bornology.IsBounded`,
  `Metric.Bounded`, or something order-theoretic) need you to supply the
  right candidate list; the script won't guess for you.
- Requires network access to `loogle.lean-lang.org` and
  `leanprover-community.github.io`.
