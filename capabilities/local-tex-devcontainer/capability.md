# Local TeX Dev Container

LRA volume repositories can use one governance-owned TeX runtime for local
editing and builds. The image lives in `lra-governance/docker/lra-tex-dev/` and
is based on full TeX Live with `latexmk`, `biber`, `chktex`, Python, Git, and
small shell utilities.

The intended workflow is:

1. Keep `lra-governance`, `lra-common`, and the target `lra-volume-*` checkout
   as sibling repositories.
2. Install a generated `.devcontainer/` shim into the target volume repo.
3. Open the volume repo in VS Code's Dev Containers environment.
4. Use VS Code and LaTeX Workshop for source editing, PDF preview, and SyncTeX.
   Project build scripts may remain the canonical build entrypoint.

When the user says `edit latex` while working in `lra-volume-i` through
`lra-volume-viii`, launch this governed local editing path. From
`lra-governance`, target a sibling volume by number:

```sh
python tools/governance/edit_latex.py --volume iii
python tools/governance/edit_latex.py --volume 3
```

From inside a volume repository or one of its subdirectories, the root is
inferred:

```sh
python ../lra-governance/tools/governance/edit_latex.py
```

The launcher refreshes the generated `.devcontainer/` shim and opens VS Code
with a `vscode-remote://dev-container...` folder URI. If the Dev Containers URI
path is unavailable on a machine, use:

```sh
python tools/governance/edit_latex.py --volume iii --launch-mode plain-code
```

Then run `Dev Containers: Reopen in Container` from VS Code.

Generate the shim from `lra-governance`:

```sh
python tools/governance/install_volume_devcontainer.py --root ../lra-volume-iii --write
```

Install into every sibling `lra-volume-*` checkout:

```sh
python tools/governance/install_volume_devcontainer.py --workspace <repos-root> --all-sibling-volumes --write
```

Add or refresh book-root magic comments in active volume `.tex` files:

```sh
python tools/governance/set_latex_root_comments.py --root ../lra-volume-iii --write
```

Check for missing or stale comments without modifying files:

```sh
python tools/governance/set_latex_root_comments.py --root ../lra-volume-iii --check
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
