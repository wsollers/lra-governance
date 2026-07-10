# lra-proof-vault Overlay

Overlay for handwritten proof records and memorialized proof artifacts.

Owned concerns:

- sanitized handwritten proof artifacts,
- route-style proof-vault metadata,
- OCR, Markdown, and TeX display artifacts for attempts,
- proof-vault validation and proof-vault index inputs,
- leaf backlinks only when a reviewed attempt is accepted for canonical use.

The proof vault is archival support only. Canonical theorem statements,
canonical proof bodies, theorem dependencies, and To Prove publication state
remain owned by the relevant `lra-volume-*` repositories and
`lra-knowledge-explorer`.

## Agent Scope

Proof-vault agents may edit vault records, routing snapshots, local scripts,
and local validation/docs. They must not edit canonical volume proof content
from this repository except through the explicit backlink workflow in the
owning volume repository.

## Photo Memorialization

For any user-supplied proof photo or image artifact, use the Docker photo
pipeline by default:

```powershell
docker build -t lra-proof-vault .
docker run --rm -v F:\repos:/repos -w /repos/lra-proof-vault lra-proof-vault --root /repos/lra-proof-vault --repos-root /repos --file /repos/path/to/photo.jpg --theorem-id <stable-theorem-label>
```

Do not run `scripts/memorialize_attempt.py` directly for photos unless Docker
is unavailable or the user explicitly asks to bypass Docker. Direct
memorialization is for already-sanitized non-photo artifacts or exceptional
manual recovery.

The Docker pipeline is the standard toolchain because it provides Pillow,
ExifTool, ImageMagick, OCR integration, text artifact generation, and vault
validation. It may use a configured local vision/OCR provider such as
Ollama/Qwen, falling back to Tesseract when configured or needed. Raw mobile
images must never be committed.

## Validation Commands

From `lra-proof-vault`, validate vault metadata with:

```powershell
python scripts\validate_vault.py --root .
```

When a reviewed-correct proof is used as canonical content and leaf backlinks
are required, validate with:

```powershell
python scripts\validate_vault.py --root . --repos-root F:\repos --require-leaf-backlinks
```

For full photo workflow details, use the local `README.md` and the canonical
standard `docs/governance/handwritten-proof-vault-standards.md` in
`lra-governance`.
