# Repo Overlay -- lra-proof-vault

Repo identity: Handwritten proof records.

Handwritten proof records and memorialized proof artifacts; volumes link here
via `\ProofVaultURL`. The proof vault is archival support only: canonical
theorem statements, canonical proof bodies, theorem dependencies, and
To Prove publication state remain owned by the relevant `lra-volume-*`
repositories and `lra-knowledge-explorer`.

Owned concerns:

- sanitized handwritten proof artifacts,
- route-style proof-vault metadata,
- OCR, Markdown, and TeX display artifacts for attempts,
- proof-vault validation and proof-vault index inputs,
- leaf backlinks only when a reviewed attempt is accepted for canonical use.

Agent scope: edit vault records, routing snapshots, local scripts, and local
validation/docs. Do not edit canonical volume proof content from this
repository except through the explicit backlink workflow in the owning
volume repository.

## Photo Memorialization

For any user-supplied proof photo or image artifact, use the Docker photo
pipeline by default:

```powershell
docker build -t lra-proof-vault .
docker run --rm -v F:\repos:/repos -w /repos/lra-proof-vault lra-proof-vault --root /repos/lra-proof-vault --repos-root /repos --file /repos/path/to/photo.jpg --theorem-id <stable-theorem-label>
```

Do not run `scripts/memorialize_attempt.py` directly for photos unless Docker
is unavailable or the user explicitly asks to bypass Docker; direct
memorialization is for already-sanitized non-photo artifacts or exceptional
manual recovery. The Docker pipeline provides Pillow, ExifTool, ImageMagick,
OCR integration, text artifact generation, and vault validation; it may use a
configured local vision/OCR provider (Ollama/Qwen) with Tesseract fallback.
Raw mobile images must never be committed.

When automated OCR is poor but the agent can read the image, use a reviewed
AI-assisted transcription as the OCR evidence input instead of committing
garbled OCR: pass it with `--ocr-text-file`, and record the source in attempt
metadata (for example `ocr_selected_engine: ai-assisted` and
`text_source: canonical-proof-with-ai-assisted-ocr` when polished text is
reconstructed from the accepted canonical proof). The transcription stays
source-faithful to the photo; canonical proof improvements belong in the
proof file and reviewed Markdown/TeX artifacts, not in the OCR artifact.

## Success gates

- `python scripts\validate_vault.py --root .`
- when a reviewed-correct proof is used canonically and leaf backlinks are
  required: `python scripts\validate_vault.py --root . --repos-root F:\repos --require-leaf-backlinks`

For full photo workflow details use the local `README.md`; the cross-repo
contract (privacy, sanitization, route metadata, backlinks) is the
handwritten-proof-vault standard in `lra-governance`.
