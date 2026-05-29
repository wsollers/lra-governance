# Phase 3 Follow-Up: Decoration Audit Tool

## Reason

The LRA notes need an inventory of theorem-like decoration compliance before
large cleanup work begins. The audit tool gives a repo-wide view of which
definitions, axioms, theorems, lemmas, propositions, and corollaries appear to
have the expected nearby labels, remarks, dependency blocks, and proof
availability signals.

## Inventory Only

The tool is intentionally read-only for scanned repos. It does not rewrite
LaTeX, generate source patches, run bulk standardization, or sync downstream
repositories. It writes only report files to the requested output directory.

This keeps the audit useful for planning without accidentally changing
mathematical note content.

## Ollama Use

Ollama support is optional and opt-in. Deterministic checks run by default and
should classify as much as possible before a local model is considered.

When enabled, Ollama receives compact context consisting of the detected block,
nearby decoration, and deterministic findings. The model is instructed to
return strict JSON only. Invalid JSON is recorded as an audit issue, and model
output never modifies source files.

Recommended local models:

- primary: `qwen2.5-coder:7b`
- larger local option: `qwen2.5-coder:14b`
- fallback: `llama3.1:8b` or a similar local model

Local model output is advisory only because it may miss context, hallucinate
standards, or overstate confidence. Human review remains required before any
note or bibliography change.

## Refactor Planning

The JSON, CSV, and Markdown reports help estimate Volume I through Volume V
refactor scope by counting missing labels, dependency issues, missing
interpretation remarks, suspected predicate leakage, oversized blocks, and
other likely decoration gaps.

