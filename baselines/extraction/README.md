# Extraction Baselines

This directory stores committed comparison baselines for the governance-owned
knowledge extraction pipeline.

Use `tools/governance/extraction_pipeline/archive_baseline.py` to snapshot:

- current `chapter.yaml` files from `lra-volume-*` source trees;
- current `lra-knowledge-explorer` JSON artifacts;
- current `lra-knowledge-explorer/reorder` batches and prompt files;
- a manifest with source paths, byte counts, hashes, branches, commits, and
  working-tree status.

Timestamped extraction logs and reports belong under `logs/` and are ignored.
Baselines in this directory are intentionally committable when a pipeline change
needs a durable before/after comparison.

