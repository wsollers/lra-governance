# Book Addition Standards

Use this standard when adding a new book to an existing `lra-volume-*`
repository. A book is a subject partition inside one volume. It must have its
own source directory, TeX root, bibliography shard, registry entry, and build
coverage.

## Source Of Truth

`docs/architecture/book-registry.json` is the canonical book inventory. Do not
add an unregistered book root or route a book only by local convention.

Every new book entry must define:

- owning volume;
- stable `slug`;
- display `title`;
- integer `order` within the volume;
- `book_dir`, formatted as `volume-{roman}/book-{slug}`;
- `expected_toc`, with routed chapter order and notes-topic order.

The registry, filesystem, TeX routers, bibliography shard, local build roots,
knowledge extraction, and generated repo documentation must agree.

## Required Files

For volume `{roman}` and book `{slug}`, add or update:

- `volume-{roman}/book-{slug}/index.tex`;
- `volume-{roman}-{slug}.tex`;
- `bibliography/volume-{roman}-{slug}.bib`;
- `volume-{roman}/index.tex`;
- `docs/architecture/book-registry.json`;
- the owning volume `README.md` and `bibliography/README.md`.

Each chapter listed under `expected_toc` must have:

- `volume-{roman}/book-{slug}/{chapter}/index.tex`;
- `volume-{roman}/book-{slug}/{chapter}/chapter.yaml`;
- `volume-{roman}/book-{slug}/{chapter}/notes/index.tex`;
- `volume-{roman}/book-{slug}/{chapter}/proofs/index.tex`.

Add `exercises/` only when the chapter has exercise-vault content. Do not route
chapter exercises through proof routers.

## Routing Rules

The routing chain is:

```text
volume-{roman}.tex
  -> volume-{roman}/index.tex
    -> volume-{roman}/book-{slug}/index.tex
      -> volume-{roman}/book-{slug}/{chapter}/index.tex
        -> notes/index.tex and proofs/index.tex
```

The full-volume root must include every active book through
`volume-{roman}/index.tex`. The book root must include only that book's
frontmatter and chapters. Do not bypass the book tier by routing chapters
directly from the volume index.

## Naming Rules

Use readable lowercase kebab-case names:

- book directory: `book-{slug}`;
- book TeX root: `volume-{roman}-{slug}.tex`;
- output PDF: `volume-{roman}-{slug}.pdf`;
- bibliography shard: `bibliography/volume-{roman}-{slug}.bib`.

Do not introduce `main.tex`, `main-book-*.tex`, or
`volume-{roman}-{slug}-main.tex` for new books. Those names are migration
compatibility only.

## Frontmatter And Bibliography

Each new book root must have book-specific frontmatter and a book-local table
of contents. Book frontmatter must not overwrite the volume frontispiece
assignment.

The book root cites its own bibliography shard. The full-volume root cites all
book bibliography shards needed by the volume build. Do not move bibliography
ownership to `lra-common`.

## Validation And Build Gates

Before committing a new book, run from the volume repo:

```powershell
python ..\lra-governance\scripts\build_volume.py --root . --validate-only
python ..\lra-governance\tools\governance\build_volume_docker.py --root . --common-root ..\lra-common --edition digital --paper letter --tex-root volume-{roman}-{slug}.tex --output-dir build\digital-letter
python ..\lra-governance\tools\governance\build_volume_docker.py --root . --common-root ..\lra-common --edition print --paper sixbynine --tex-root volume-{roman}-{slug}.tex --output-dir build\print-sixbynine
python ..\lra-governance\tools\governance\build_volume_docker.py --root . --common-root ..\lra-common --edition digital --paper letter --output-dir build\digital-letter
python ..\lra-governance\tools\governance\build_volume_docker.py --root . --common-root ..\lra-common --edition print --paper sixbynine --output-dir build\print-sixbynine
```

The first pair checks the new book directly. The second pair confirms that the
full discovered volume/book build still works in both digital and print modes.

## Extraction And Downstream Updates

After adding a book with routed chapters, refresh any downstream data that
depends on the canonical book registry:

- knowledge extraction routes and explorer metadata;
- proof-vault theorem routes;
- source-profile target lists;
- generated volume README/bibliography summaries, when those are regenerated.

Do not hand-edit generated wrappers or downstream generated summaries when a
registry-driven generator owns the file.

## Scope Limits

Adding a book is not permission to migrate unrelated chapters, rename existing
books, rewrite labels, or reassign volume titles. Keep the commit scoped to one
book unless the task explicitly authorizes a broader volume refactor.
