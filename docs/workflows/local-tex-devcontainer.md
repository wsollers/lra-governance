# Local TeX Dev Container

LRA volume repositories can use one governance-owned TeX runtime for local
editing and builds. The image lives in `lra-governance/docker/lra-tex-dev/` and
is based on full TeX Live with `latexmk`, `biber`, `chktex`, Python, Git, and
small shell utilities.

The intended workflow is:

1. Keep `lra-governance`, `lra-common`, and the target `lra-volume-*` checkout
   as sibling repositories.
2. Install a generated `.devcontainer/` shim into the target volume repo.
3. Open the volume repo in VS Code and run `Dev Containers: Reopen in
   Container`.
4. Use VS Code and LaTeX Workshop for source editing, PDF preview, and SyncTeX.
   Project build scripts may remain the canonical build entrypoint.

Generate the shim from `lra-governance`:

```powershell
python tools\governance\install_volume_devcontainer.py --root F:\repos\lra-volume-iii --write
```

Install into every sibling `lra-volume-*` checkout:

```powershell
python tools\governance\install_volume_devcontainer.py --workspace F:\repos --all-sibling-volumes --write
```

Add or refresh book-root magic comments in active volume `.tex` files:

```powershell
python tools\governance\set_latex_root_comments.py --root F:\repos\lra-volume-iii --write
```

Check for missing or stale comments without modifying files:

```powershell
python tools\governance\set_latex_root_comments.py --root F:\repos\lra-volume-iii --check
```

`--check` exits nonzero when an active included `.tex` file is missing its
root comment or points at the wrong book root.

The generated devcontainer mounts:

- the volume repo as the workspace;
- `lra-governance` at `/lra-governance`;
- `lra-common` at `/lra-common`;
- `lra-common/common` over the workspace `common/` directory.

LaTeX Workshop auto-build is disabled by default. Use the repo's own build
scripts, the VS Code tasks, or manual `latexmk` commands. The PDF preview still
refreshes when output files change.
