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

The proof-vault repository owns its local folder layout, scripts, Docker photo
pipeline, and operational commands. Governance records only the cross-repo
contract: memorialized proofs live under the relevant volume, book, chapter,
and theorem directory, using route-style metadata keyed by theorem identity.

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

Consumers such as the Knowledge Explorer must use route-style metadata and
current route snapshots, not the legacy root `theorem-map.yaml` file. After any
volume/book/chapter refactor, regenerate the affected volume route artifacts
and import current routes into the proof vault before migrating vault paths. The
proof vault must not run path migration against stale route artifacts.

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

## Memorialization Workflow Contract

The operational photo-pipeline commands live in `lra-proof-vault`. Any
memorialization workflow must satisfy these governance-level requirements:

1. Incoming images are staged outside tracked git content until sanitized.
2. The proof-vault Docker photo pipeline is the default workflow for
   sanitization, OCR, Markdown/TeX artifact generation, metadata updates, and
   validation.
3. OCR output is evidence, not authoritative proof content. Preserve OCR
   mistakes in the OCR artifact rather than silently correcting them.
4. Mathematics is verified against the image and theorem route before an
   attempt is marked accepted.
5. Route-style proof-vault metadata records OCR paths, display artifact paths,
   review status, OCR engine/profile/quality, and attempt summaries.
6. A reviewed-correct proof used as canonical content must update the owning
   canonical proof file with both proof bodies, dependencies, and the
   proof-vault backlink.
7. No raw image may be committed at any stage.

Existing-record backfills must report every `medium: handwritten-photo` attempt
as complete, or the run must stop for repair before deployment.

## Backlink Rules

Backlinks from canonical proof files to proof-vault records are required for
proofs created from memorialized handwritten proof images.

The photo pipeline must either write the backlink or fail a strict validation
step. It must also ensure route-confirmed, reviewed-correct attempts are
represented by canonical proof content and accepted proof-vault metadata. A
successful vault-only validation is not sufficient to close a memorialization
task.

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
  canonical proof file, Knowledge Explorer's generated To Prove data must be
  able to derive completion from the canonical proof file or accepted vault
  metadata.

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
