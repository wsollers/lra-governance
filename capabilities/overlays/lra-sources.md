# Repo Overlay -- lra-sources

Repo identity: Private source catalog and pointer indexes.

Metadata-only pointer catalog for acquired and scanned Learning Real Analysis
sources: source IDs, bibliographic metadata, hashes, local path pointers,
topic/author/volume indexes, and pointers into the reviewed
`lra-source-profiles` metadata and generated local indexes. The acquisition,
scan, extraction, and classification tooling lives in `lra-source-profiles`
and `lra-pdf-extractor`; this repo records the resulting catalog.

Owned concerns:

- `index.yaml` (primary lookup entry) and the `indexes/` tree
  (`all-sources.yaml`, `by-topic/`, `by-author/`,
  `by-volume/<volume>/<book>/<chapter>.yaml`),
- per-source records under `sources/<source_id>.yaml`.

Hard prohibitions (privacy and size):

- No raw PDFs, full OCR output, full extracted Markdown, or source snippets.
- No final notes, bibliography shards, canonical YAML, or theorem-explorer
  generated data — those stay with their owning repositories.
- The repository stays private unless a task explicitly requests and approves
  a visibility change.

Agent scope: maintain catalog records and indexes; keep lookup order
(`index.yaml` first, then the `indexes/` tree, then `sources/<id>.yaml`)
intact; preserve source IDs, hashes, and review notes when reorganizing.
Report needed tooling changes to `lra-source-profiles` rather than adding
processing code here.

Success gates:

- Every changed `.yaml` file parses
  (`python -c "import sys,yaml; [yaml.safe_load(open(p,encoding='utf-8')) for p in sys.argv[1:]]" <changed files>`).
- Changed per-source records remain reachable from `index.yaml` or an
  `indexes/` file.
