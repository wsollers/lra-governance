# Volume IV Algebraic Structures Extraction Baseline

This baseline archives the extraction run generated after re-enabling and
upgrading `volume-iv/algebra/algebraic-structures`.

Original run:

- Run directory: `F:\repos\lra-governance\runs\extraction-20260619-072204`
- Archived raw run: `raw-run/`
- Report: `F:\repos\lra-governance\logs\extraction-report-20260619-072204.md`

Rerun the extraction:

```powershell
python F:\repos\lra-governance\tools\governance\extraction_pipeline\generate_data.py --repos-root F:\repos
```

Compare a new run to this baseline:

```powershell
git diff --no-index -- F:\repos\lra-governance\baselines\extraction\volume-iv-algebraic-structures-20260619-072204\raw-run F:\repos\lra-governance\runs\<new-extraction-run>
```

For a narrower signal, compare these files first:

```powershell
git diff --no-index -- F:\repos\lra-governance\baselines\extraction\volume-iv-algebraic-structures-20260619-072204\raw-run\summary.json F:\repos\lra-governance\runs\<new-extraction-run>\summary.json
git diff --no-index -- F:\repos\lra-governance\baselines\extraction\volume-iv-algebraic-structures-20260619-072204\raw-run\universe.json F:\repos\lra-governance\runs\<new-extraction-run>\universe.json
git diff --no-index -- F:\repos\lra-governance\baselines\extraction\volume-iv-algebraic-structures-20260619-072204\raw-run\combined-edges.json F:\repos\lra-governance\runs\<new-extraction-run>\combined-edges.json
```
