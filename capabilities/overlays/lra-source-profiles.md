# Repo Overlay -- lra-source-profiles

Repo identity: Source profiles, source indexes, and active profile exports.

Source-profile metadata, active source selections, volume/chapter source indexes, cached Markdown extracts, and attachment-slot exports. Outputs are staging/review inputs for owning repos.

Success gates:
- `python scripts\validate_source_indexes.py`
- `python -m pytest tests`

No manifest-backed LLM capability is exposed for repo kind `source_profiles` yet.
