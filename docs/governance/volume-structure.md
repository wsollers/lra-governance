# Volume Structure Contract

The volume validator treats the volume tree as the atomic validation target.
`volume_shape` runs first. If the shape gate fails, downstream validators do not
run.

The machine-readable contract lives in `docs/governance/volume-structure.schema.json`.

Canonical shape:

```text
volume-root/
  index.tex

repo-root-or-volume-root/
  volume-{roman}.tex           (full volume root)
  volume-{roman}-{book-slug}.tex
                               (one root per book)
  volume-{roman}-{book-slug}-main.tex
                               (legacy migration alias)
  main-book-{book}.tex         (legacy migration alias)
  main.tex                     (transitional single-root alias)

book/                       (book-{slug}/; subject partition inside a volume)
  index.tex

chapter/
  index.tex
  chapter.yaml
  notes/index.tex
  proofs/index.tex
  proofs/exercises/index.tex
  proofs/exercises/capstone-{chapter}.tex

notes/
  {topic}/index.tex
  {topic}/*.tex

proofs/
  {topic}/index.tex
  {topic}/prf-*.tex
```

Every canonical chapter root must be reachable from the volume root `index.tex`
through the router chain. Chapters live under a book tier
(`volume/book-{slug}/{chapter}/`): the volume index routes each
`book-{slug}/index.tex`, and each book index routes its chapter routers — for
example `\input{volume-ii/book-continuum/complex-numbers/index}`. A volume may
also route a chapter directly (`\input{volume-ii/complex-numbers/index}`) where
no book tier is present; both are accepted because reachability follows the
`\input` chain rather than a fixed depth. A chapter directory that has the
canonical shape but is not reachable from the volume root router is an orphaned
chapter and must fail validation.

Topic index files under `notes/{topic}/` and `proofs/{topic}/` are router-only:
comments and input lines only. Rendered sectioning belongs in chapter-level
notes routing or body files, not topic routers.

A matching `proofs/{topic}/` directory is required only when the corresponding
`notes/{topic}/` contains proof-bearing theorem-like environments listed in
`proof_topic_required_envs` in the schema. Pure reference, exposition, notation,
or other note-only topics do not need empty proof-topic mirrors.

`proofs/index.tex` routes proof topics in the same order as `notes/index.tex`;
`proofs/exercises/index.tex` is the final route in that file.
`proofs/exercises/index.tex` is router-only, and `proofs/exercises/` contains
only `index.tex` and `capstone-{chapter}.tex`.

Legacy `chapter/capstone.tex`, legacy `chapter/exercises/`, flat note bodies
under `notes/`, and flat proof files under `proofs/` are shape failures.
