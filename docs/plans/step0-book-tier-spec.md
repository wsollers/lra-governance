# Step 0 — `book-*` Tier: Schema & Validator Change-Set (DRAFT for review)

> **Status: DRAFT — nothing applied.** Precise change-set to teach the governance
> tooling the `volume-*/book-*/chapter-*/` grammar. Moves zero content files.
> Review, then apply changes 1-2 (backward-compatible) and re-run the validator on
> the *current* un-partitioned volumes to confirm green before any folder moves.

## Finding: the tier is mostly free

Investigated `core/volume.py`, `core/file_inventory.py`, `validate_volume.py`, and
the structural validators. Chapter handling is already depth-agnostic:

- **`core.volume.chapter_roots()`** uses `os.walk` and identifies a chapter by
  "has `notes/` + `proofs/`". A `book-*/` directory between volume and chapter is
  walked through automatically — discovery is unaffected.
- **`core.file_inventory.reachable_files()`** follows the `\input` chain from
  `index.tex`. If `volume/index.tex` inputs `book/index.tex` which inputs
  `chapter/index.tex`, the chapter is reachable with no code change.
- **`core.volume.latex_input_path()`** returns the path from the `volume-*`
  segment onward, so it *already* includes the `book-*` segment.
- **`chapter_router.py`, `notes_structure.py`, `proof_routing.py`,
  `input_resolution.py`** all operate per-chapter with chapter-relative paths —
  depth-agnostic, no change.

So the only things that hardcode "chapter is a direct child of volume" are listed
below. Everything else just works.

## Change 1 — `validators/volume_shape.py` (the one real code fix)

`_validate_chapter_reachability()` checks each chapter is a **direct** `\input` of
`volume_root/index.tex` (via `_volume_index_inputs`, which reads only that one
file). With the book router layer, chapters are inputs of `book-*/index.tex`, so
this would wrongly flag every chapter as `chapter_not_in_volume_index`.

**Fix:** check reachability through the router chain instead of direct input.
`reachable_files` is already imported in this file.

```python
# BEFORE
def _validate_chapter_reachability(volume_root, chapters, findings):
    routed = _volume_index_inputs(volume_root)
    for chapter in chapters:
        canonical = f"{latex_input_path(chapter / 'index.tex')}"
        local = f"{chapter.name}/index"
        if canonical not in routed and local not in routed:
            _add(findings, volume_root, chapter / "index.tex",
                 "chapter_not_in_volume_index",
                 f"Canonical chapter root is not routed from {volume_root.name}/index.tex: ...")

# AFTER  (book-aware; follows volume -> book -> chapter)
def _validate_chapter_reachability(volume_root, chapters, findings):
    reachable = reachable_files(volume_root)
    for chapter in chapters:
        if (chapter / "index.tex").resolve() not in reachable:
            _add(findings, volume_root, chapter / "index.tex",
                 "chapter_not_in_volume_index",
                 f"Canonical chapter root is not reachable from {volume_root.name}/index.tex "
                 f"through the router chain (volume -> book -> chapter).")
```

`_volume_index_inputs` becomes unused (remove or keep). **Backward-compatible:** a
directly-routed chapter (no book tier) is still reachable, so current single-tier
volumes pass unchanged. Apply and validate *before* any moves.

## Change 2 — `audit_volume_layout.py` (standalone auditor)

`find_chapter_roots()` uses `volume.iterdir()` — direct children only — so chapters
under `book-*/` are invisible to it. (This is the auditor `file-schema.yaml`
names as `audit_tool`; the main `validate_volume.py` path already uses the
depth-agnostic `core.volume`, so it does not have this bug.)

**Fix:** descend recursively. Either delegate to `core.volume.chapter_roots`, or
replace the `iterdir` loop with an `os.walk` that collects dirs having `notes/` +
`proofs/`. Backward-compatible (recursion still finds direct-child chapters).

## Change 3 — `core/volume.py :: IGNORED_RELATIVE_DIRS` (data, during moves)

These hardcoded relative paths move when chapters go under a book:

| Current | After partition |
|---|---|
| `analysis/real-analysis` | `book-analysis-i/real-analysis` |
| `volume-iii/analysis/real-analysis` | `volume-iii/book-analysis-i/real-analysis` |
| `volume-ii/integers/notes/{mendelson,tao}-construction` | `volume-ii/book-discrete-algebraic/integers/notes/...` |
| `volume-ii/integers/proofs/{mendelson,tao}-construction` | `volume-ii/book-discrete-algebraic/integers/proofs/...` |

Update **when the corresponding chapter moves** (enactment step 3), not now.
Listed here so the sweep doesn't forget them.

## Change 4 — schema & human docs (add the book layer)

- **`docs/governance/volume-structure.md`** — update the canonical-shape block to
  show `volume-root/index.tex` -> `book-*/index.tex` -> `chapter/index.tex`, and
  restate the contract: *"Every canonical chapter root must be reachable from the
  volume root index.tex through the book router layer,"* example
  `\input{volume-ii/book-continuum/complex-numbers/index}`.
- **`docs/governance/volume-structure.schema.json`** — add
  `"required_book_files": ["index.tex"]` as recorded contract. (Not consumed until
  an optional `book_router` validator is added; doc-only for now.)
- **`constitution/schema/file-schema.yaml`** — in `volume_chapter_topic_layout`,
  insert the book tier: `chapter_location: volume-{n}/book-{b}/{chapter}/` and
  matching `topic_location`/`router_files`; add a `book` router rule ("volume
  index inputs book indexes; book index inputs chapter indexes, in order"); add a
  `book:` field to the `chapter.yaml` schema description.

## Change 5 — `chapter.yaml` (metadata, during moves)

Add `book: book-<slug>` to each chapter's `chapter.yaml`. The validator does not
parse layout fields from `chapter.yaml` (it only checks the file exists), so this
is harmless metadata that records which book a chapter belongs to. Populate during
the move.

## What we deliberately are NOT doing in step 0

- No `book_router` *shape* validator yet (book index = `\part` + ordered chapter
  `\input`s, router-only). The chain is already validated transitively by
  reachability (Change 1) + the per-chapter `chapter_router`. A dedicated book
  shape check can be added later if desired; keeping step 0 minimal.

## Apply order

1. Change 1 + Change 2 (backward-compatible code). Re-run `validate_volume.py` on
   current Vols I-III **before any moves** — expect no new findings (single-tier
   chapters still reachable). This proves the change is safe.
2. Change 4 (schema/docs) — paper, no build impact.
3. Changes 3 + 5 happen later, per chapter, during the enactment moves.
