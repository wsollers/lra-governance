# Learning-Real-Analysis Overlay (Retired)

`Learning-Real-Analysis`, the former assembled monorepo, is **retired**. There
is no omnibus assembly target, no volume-to-monorepo content sync, and no
mono-side rebuild dispatch.

This overlay is kept only as a tombstone so older references resolve. It carries
no active rules. Do not generate agent wrappers for this repo.

Where its former responsibilities went:

- **Canonical YAML** (`predicates.yaml`, `notation.yaml`, `relations.yaml`) →
  `lra-governance` (see `docs/architecture/canonical-yaml.md`).
- **Integration / omnibus build** → retired; each `lra-volume-*` repo builds its
  own digital and print PDFs independently and publishes to
  `lra-volumes-output` (see `docs/architecture/latex-build-and-rendering.md`).
- **Knowledge rebuild dispatch** → governance-orchestrated refresh over the
  volume repos (see `docs/workflows/knowledge-extraction.md`).
