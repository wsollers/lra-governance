# Capability Routing

`capabilities/manifest.yaml` is the only route authority. Resolve a task with:

```text
python scripts/govpy.py capabilities/resolve.py --repo <repo> --task "<user task>" --root <repo-root>
```

`scripts/govpy.py` provisions the pinned governance venv on first use and is
the canonical way to run every governance Python tool.

The generated human view is `capabilities/task-index.md`; it is a lazy reference,
not an instruction bundle. Regenerate it with
`python scripts/govpy.py capabilities/generate_task_index.py`.
