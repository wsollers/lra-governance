# Repo Overlay -- lra-exercises

Repo identity: Standalone exercise sheets, workbooks, and generated PDFs.

Standalone LaTeX exercise/workbook source and generated PDF artifacts. Use the governance-owned Docker LaTeX image described in docs/governance/repo-overlays/lra-exercises.md.

Success gates:
- `docker latexmk build for each changed exercise .tex source`

No manifest-backed LLM capability is exposed for repo kind `latex_artifact` yet.
