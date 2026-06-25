# Bibliography Entry Workflow

Bibliography is owned by the book that uses it. Do not add new canonical BibTeX
entries to `lra-common`.

Each book root has a matching bibliography shard:

- Book root: `lra-volume-iii/volume-iii-continuity.tex`
- Book bibliography: `lra-volume-iii/bibliography/volume-iii-continuity.bib`

The volume-level root, such as `volume-iii.tex`, cites every per-book `.bib`
file in that volume. It must not point at a retired aggregate volume `.bib`.

## Standard Process

1. Identify the book whose notes cite the source.
2. Search that book's bibliography shard for an existing entry or nearby key.
3. Add the entry to that book-owned `.bib` file only.
4. Use the entry from the volume content with natbib-compatible commands such
   as `\citep{...}` or `\citet{...}`.
5. Build the owning book root through governance, for example
   `python tools/governance/build_volume_docker.py --root ../lra-volume-iii --tex-root volume-iii-continuity.tex`.

## Independent Volume Builds

There is no monorepo and no common bibliography aggregation. Each book-level
root uses only its matching bibliography shard, and the volume-level root
combines those book shards only for the volume PDF. Make every bibliography
change in the owning volume repo.

## Candidate Material

Extractor-generated `.bib` output is candidate material only. Review candidate
entries before adding them to the owning book shard. Do not write candidate
entries into `lra-common` or an aggregate bibliography file.
