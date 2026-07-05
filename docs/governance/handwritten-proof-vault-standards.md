# Handwritten Proof Vault Standards

These standards apply to handwritten proof artifacts associated with the
Learning Real Analysis project.

## Purpose

The handwritten proof vault stores personal learning artifacts, proof attempts,
reviewed handwritten proofs, extracted proof records, and related metadata.

The proof vault is not the canonical source of mathematical content. Canonical
theorem statements and canonical proofs remain in the LRA volume repositories.

The proof vault repository is private by default because handwritten images may
contain unintended personal, device, location, or author information.

## Repository

The dedicated proof vault repository is:

```text
wsollers/lra-proof-vault
```

The local path is expected to be:

```text
F:\repos\lra-proof-vault
```

The repository must remain private unless a later task explicitly requests and
approves a visibility change.

## Repository Structure

The root structure is:

```text
lra-proof-vault/
  README.md
  index.json
  theorem-map.yaml
  metadata-template.yaml
  inbox/
  reviewed/
  extracted/
  rejected/
  volume-i/
  volume-ii/
  volume-iii/
  volume-iv/
  volume-v/
  volume-vi/
  volume-vii/
  volume-viii/
```

Future memorialized proofs should live under the relevant volume, book,
chapter, and theorem directory:

```text
volume-i/
  book-logic/
    propositional-logic/
      thm-unique-readability/
        attempts/
          proof-2026-05-31-001.jpg
        metadata.yaml
```

Use lowercase, hyphen-separated, ASCII paths. Do not store raw mobile images in
the repository.

## Metadata Requirements

Each memorialized proof folder must include a `metadata.yaml` file keyed by
the route snapshot imported into `lra-proof-vault/routing/`. The stable
identity is `theorem_id`; route fields such as `vault_path`, `theorem_tex`,
and `proof_tex` may move when leaf volume routes are regenerated.

The current route-style metadata shape is:

```yaml
theorem_id:
theorem_title:
route_confidence: confirmed
source_repo:
volume:
book:
book_slug:
book_title:
book_dir:
chapter:
section:
subsection:
theorem_tex:
proof_tex:
proof_label:
vault_path:
source_commit:
route_version:
canonical_routes:
  theorem_tex:
  proof_tex:
  proof_label:
  vault_path:
  book:
  book_slug:
  book_title:
  book_dir:
  source_repo:
  source_commit:
  route_version:
attempts:
- attempt_id:
  date:
  medium: handwritten-photo
  source_path: attempts/proof-YYYY-MM-DD-001.jpg
  rendered_html:
  ocr_text_path:
  markdown_path:
  tex_path:
  text_source:
  text_review_status:
  ocr_quality_status:
  ocr_selected_engine:
  ocr_selected_profile:
  ocr_selected_psm:
  ocr_attempt_count:
  ocr_attempts: []
  origin:
  review_status:
  notes:
  tags: []
```

Consumers such as the Knowledge Explorer should not depend on the legacy root
`theorem-map.yaml` file. The governance extraction pipeline builds
`lra-knowledge-explorer/proof-vault-index.json` directly from route-style
metadata and legacy markdown records where present.

After any volume/book/chapter refactor, regenerate each affected volume's
`build/knowledge/theorem-routes.json` artifact and import all available volume
route files into the proof vault. The standard dry-run command is:

```powershell
python scripts\sync_routes.py --root . `
  --source ..\lra-volume-i\build\knowledge\theorem-routes.json `
  --source ..\lra-volume-ii\build\knowledge\theorem-routes.json `
  --source ..\lra-volume-iii\build\knowledge\theorem-routes.json `
  --source ..\lra-volume-iv\build\knowledge\theorem-routes.json `
  --source ..\lra-volume-v\build\knowledge\theorem-routes.json `
  --source ..\lra-volume-vi\build\knowledge\theorem-routes.json `
  --source ..\lra-volume-vii\build\knowledge\theorem-routes.json `
  --source ..\lra-volume-viii\build\knowledge\theorem-routes.json `
  --migrate-paths --dry-run
```

Run the same command with `--apply` only after reviewing planned and blocked
moves. The proof vault must not run path migration against stale route
artifacts.

Allowed metadata includes:

- source filename;
- review date;
- theorem label;
- review status.

Forbidden embedded image metadata includes:

- GPS coordinates;
- camera serial numbers;
- device identifiers;
- author metadata;
- phone model metadata;
- embedded thumbnails;
- EXIF timestamps.

Forbidden embedded metadata must be removed before an image enters git.

## Review Statuses

Allowed review statuses are:

- `inbox`;
- `needs-review`;
- `reviewed-correct`;
- `reviewed-needs-revision`;
- `extracted`;
- `rejected`.

Do not invent additional statuses without updating this standard and the proof
vault index.

## EXIF Stripping

EXIF stripping is mandatory. The standard workflow is the Linux Docker pipeline
in `lra-proof-vault`, because it fixes the processing toolchain used for
metadata stripping, OCR, Markdown/TeX artifact generation, and validation.

Raw mobile images must never be committed. Only sanitized copies may enter git.

Required workflow:

```text
incoming image
       |
       v
staging area
       |
       v
metadata stripping
       |
       v
sanitized image
       |
       v
git commit
```

Acceptable sanitization methods include:

- `exiftool -all=`;
- ImageMagick `-strip`;
- Python Pillow re-save without metadata.

The Docker pipeline must run all three sanitization layers when the tools are
available: Pillow re-save, ExifTool metadata removal, and ImageMagick stripping.
Manual sanitization is only a fallback when the Docker pipeline is unavailable,
and the fallback must still produce a sanitized copy before git staging.

If sanitization cannot be verified, stop and report the issue instead of
committing the image.

## Future Memorialization Workflow

The command:

```text
Memorialize proof image
```

should perform the following steps:

1. Store the incoming image in a staging area outside tracked git content.
2. Run the Docker photo pipeline from `lra-proof-vault`.
3. Sanitize the image by removing embedded metadata with Pillow, ExifTool, and
   ImageMagick stripping.
4. Create or update route-style proof-vault metadata.
5. OCR the sanitized image into a plain-text artifact with the configured OCR
   provider. The default provider may be local Ollama/Qwen vision with
   Tesseract preprocessing retries as fallback. Preserve OCR mistakes in the
   OCR artifact rather than silently correcting them.
6. Verify the mathematics against the image and theorem route before accepting
   the attempt. OCR text is provisional evidence; it is not authoritative proof
   content.
7. Produce Markdown and TeX display artifacts. When a reviewed canonical proof
   already exists, reconstruct accepted display text from that canonical proof
   and keep the OCR text as evidence. Otherwise, only mark display text accepted
   after mathematical verification and review.
8. Record `ocr_text_path`, `markdown_path`, `tex_path`, `text_source`,
   `text_review_status`, OCR engine/profile, OCR quality, and OCR attempt
   summaries on the attempt metadata.
9. Commit the proof vault repository.
10. Push the proof vault repository.
11. Add a `\ProofVaultURL{...}` backlink to the canonical theorem proof file
    with `lra-proof-vault/scripts/apply_leaf_backlinks.py`, or an equivalent
    deterministic step that validates the exact leaf proof file.
12. If the proof was accepted as correct and memorialized, update the owning
   volume repo's tracked `proofs-to-do.md` artifact: change the proof label
   marker from `()` to `(✅)` and update the open/completed counts. The standard
   backlink applicator performs this tracker update by default only after the
   canonical proof file has both proof bodies and dependencies populated.
13. Commit the canonical repository.
14. Push the canonical repository.

No raw image may be committed at any stage of this workflow.

The standard one-photo command shape is:

```powershell
docker run --rm `
  -v F:\repos:/repos `
  -w /repos/lra-proof-vault `
  lra-proof-vault `
  --root /repos/lra-proof-vault `
  --repos-root /repos `
  --file /repos/path/to/photo.jpg `
  --theorem-id <stable-theorem-label> `
  --review-status <review-status> `
  --ocr-provider auto `
  --from-canonical-proof
```

In `auto` mode, the proof-vault tooling may try a configured local Ollama/Qwen
vision model first and use Tesseract retries when the vision pass is
unavailable or judged garbled. Docker Desktop users who want containerized
runs to reach host Ollama should pass an `--ollama-url` reachable from the
container, such as `http://host.docker.internal:11434`.

For existing vault records, the standard audit/backfill command is:

```powershell
docker run --rm `
  -v F:\repos:/repos `
  -w /repos/lra-proof-vault `
  lra-proof-vault `
  --backfill-existing `
  --root /repos/lra-proof-vault `
  --repos-root /repos `
  --refresh-placeholder-ocr
```

The backfill command must report every `medium: handwritten-photo` attempt as
complete, or the run must stop for repair before deployment.

## Backlink Rules

Backlinks from canonical proof files to proof-vault records are required for
proofs created from memorialized handwritten proof images.

The photo pipeline must either write the backlink or fail a strict validation
step. It must also mark the owning volume `proofs-to-do.md` tracker for
route-confirmed, reviewed-correct attempts. A successful vault-only validation
is not sufficient to close a memorialization task.

When a memorialized proof is used as canonical content, the canonical proof
file must populate both the Professional Standard Proof body and the Detailed
Learning Proof body. Populating only one of the two proof bodies is invalid.
If either proof body is populated, the dependencies block must also be
populated.

The backlink must use the shared macro:

```latex
\ProofVaultURL{https://github.com/wsollers/lra-proof-vault/tree/master/path/to/sanitized-record}
```

Place the macro immediately after the `Return` remark and before the
unnumbered theorem restatement:

```latex
\begin{remark*}[Return]
\hyperref[lem:example]{Return to Lemma}
\end{remark*}

\ProofVaultURL{https://github.com/wsollers/lra-proof-vault/tree/master/...}

\begin{theorem*}[Example]
...
\end{theorem*}
```

The macro is extraction-visible. Knowledge extraction and theorem-explorer
pipelines should treat the argument of `\ProofVaultURL{...}` as the
proof-vault record URL for the owning proof label.

Backlinks must satisfy the following rules:

- it must point to a sanitized proof-vault record, not to a raw image;
- it must not replace the canonical proof text;
- it must not make the handwritten proof the source of truth;
- it must preserve existing labels, dependency blocks, and extraction-visible
  structure.
- if the memorialized proof is reviewed correct and used to populate the
  canonical proof file, the owning volume's tracked `proofs-to-do.md` must mark
  the proof with `(✅)`.

If a canonical theorem or proof file does not exist, report the missing target
instead of inventing one.

## Canonical Proof Format

When a proof is generated from a handwritten image, the canonical proof file
must still follow `proof-standards.md`.

The extracted proof content must be converted into:

- a professional standard proof;
- a detailed learning proof;
- a proof-structure remark;
- a dependencies block using extraction-visible `\hyperref[...]` targets.

A direct transcription alone is not a complete canonical proof file.

## Explorer Text Artifacts

Each reviewed proof attempt should carry three text artifacts:

- `*.ocr.txt`: source-faithful OCR output from the sanitized image, including
  any OCR mistakes;
- `*.proof.md`: reviewed Markdown presentation of the proof;
- `*.proof.tex`: reviewed TeX presentation suitable for KaTeX rendering.

The governance extraction pipeline copies the contents of these files into
`lra-knowledge-explorer/proof-vault-index.json` as `ocr_text`, `markdown`, and
`tex`. The Knowledge Explorer renders `tex` with KaTeX and keeps the OCR and
Markdown artifacts available for inspection. The deployable proof-vault index
must include only attempts with `review_status: reviewed-correct` and
`text_review_status: accepted`.

When OCR runs and produces usable text, the attempt metadata should use
`text_source: canonical-proof-with-ocr` if the polished Markdown/TeX are
reconstructed from the accepted canonical proof. When OCR runs but produces no
usable text, the OCR artifact must say so explicitly, and the metadata should
use `text_source: canonical-proof-with-empty-ocr`. When OCR is unavailable
entirely, the OCR artifact must say so explicitly, and the metadata should use
`text_source: canonical-proof-reconstruction` rather than claiming OCR.

OCR quality metadata should record the selected OCR engine, selected profile or
model, selected Tesseract page-segmentation mode when applicable, attempt
count, and quality summary. A `garbled` OCR quality status is a validation
warning, not by itself a proof rejection. The proof is accepted or rejected by
mathematical verification, not by OCR confidence alone.
