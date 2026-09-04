# Repo Overlay -- lra-ingestion-harness

Repo identity: Model-neutral orchestration for local LRA ingestion workers.

This repository owns the worker contract, deterministic orchestration CLI,
diagnostics, and recovery-oriented workflow coordination. Its commands may
invoke tools owned by `lra-governance` and `lra-source-profiles`, but it does
not duplicate their indexer or source-profile implementations.

Owned concerns: worker TOML configuration; status and doctor checks; explicit
dry-run/apply commands; generated-artifact verification; run diagnostics; and
adapters that make the same workflow usable from Codex, Claude, Gemini,
Copilot, scheduled jobs, or a shell.

Not owned: raw PDFs; full OCR or extracted book text; source-profile metadata;
source indexes; final notes; bibliography shards; canonical YAML; theorem
explorer data; or governance policy.

## Safety Rules

- Keep the worker contract and CLI model-neutral. Agent instruction files are
  advisory interfaces, never durable workflow state.
- Write commands must be explicit, dry-run by default, and verify their
  expected outputs after completion.
- Do not place worker secrets, raw PDFs, or generated corpus artifacts in Git.
- Preserve underlying repository ownership; report required implementation
  changes to the owning repository rather than copying its tools here.
- Prefer native Linux worker paths for container-bound corpus operations; do
  not silently operate across Windows-mounted `/mnt/*` paths.

## Success Gates

- `python -m unittest discover -s tests`
- `python scripts/lra_harness.py --config <worker.toml> doctor`
- `python scripts/lra_harness.py --config <worker.toml> status`
