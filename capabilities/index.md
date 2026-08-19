# Capability Routing

`capabilities/manifest.yaml` is the only route authority. Resolve a task with:

```text
python capabilities/resolve.py --repo <repo> --task "<user task>" --root <repo-root>
```

The generated human view is `capabilities/task-index.md`; it is a lazy reference,
not an instruction bundle. Regenerate it with
`python capabilities/generate_task_index.py`.
