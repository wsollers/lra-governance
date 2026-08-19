#!/usr/bin/env python3
"""Generate the volume overlays in capabilities/overlays/ from overlays-config.yaml.

Volume overlays are near-identical, so they are generated from one template to
avoid copy-paste drift; re-run after editing the config or this template.
Every non-volume repo has a hand-maintained canonical overlay file in
capabilities/overlays/ — this script verifies those exist but never writes
them. capabilities/overlays/<repo>.md is the canonical overlay the resolver
eager-loads for every task in that repo.
"""
from __future__ import annotations

import sys
from pathlib import Path

HEADER = (
    "<!-- GENERATED FILE. Source: capabilities/overlays-config.yaml via\n"
    "generate_overlays.py (volume overlays only). Edit the config or template,\n"
    "not this file. -->\n"
)


def volume_overlay(repo: str, title: str, plain: bool, notes: list[str]) -> str:
    box = (
        "Definitions are ordinary `definition` environments unless a rare "
        "load-bearing definition warrants a semantic box."
        if plain
        else "Definitions use ordinary `definition` environments by default; "
        "wrap only load-bearing definitions in the semantic `definitionbox` family."
    )
    plainnote = (
        "\n- Plain-style volume: prefer unboxed formal environments except for "
        "rare structural emphasis."
        if plain
        else ""
    )
    notes_block = ""
    if notes:
        notes_block = "\nRepo-specific rules:\n" + "\n".join(
            f"- {note}" for note in notes
        ) + "\n"
    vol = repo.replace("lra-", "")
    return f"""{HEADER}# Repo Overlay -- {repo}

Repo identity: {title}.

Scope:
- Volume content only. Edit only this volume's `{vol}/` content unless the
  task explicitly says otherwise.
- Shared LaTeX infrastructure is owned by `lra-common`, canonical YAML
  registries by `lra-governance`, and Lean proof source by `lra-lean`; do not
  edit or duplicate them here.
- Specialist rules (Lean, C++/Vulkan, numerical analysis, PDF extraction) do
  not apply in volume repos.
- Preserve Overleaf readiness and the independent volume build; there is no
  assembled monorepo to sync into.

Local conventions:
- Content lives under `{vol}/<chapter>/notes/<section>/notes-<section>.tex`;
  proofs under `.../proofs/<section>/prf-<slug>.tex`.
- {box}
- Decoration blocks are unboxed `remark*`; dependencies use
  `\\begin{{dependencies}}` or `\\NoLocalDependencies`.
- Chapters route through `{vol}/index.tex` and the owning book root. Chapter
  routers own the print-edition exclusion block around proof, exercise, and
  capstone routes.
- Digital, print, and reference editions are behavior modes, not paper sizes;
  breadcrumb/footer chrome is generated from one metadata source, and its
  shared implementation stays in `lra-common`.
- Cross-volume references must not rely on an assembled monorepo build.{plainnote}

Validate and build (from the volume root, with a sibling `lra-governance`;
forward-slash commands run unchanged in PowerShell and POSIX shells):
- `python ../lra-governance/scripts/build_volume.py --root . --validate-only`
- `python ../lra-governance/tools/governance/build_volume_docker.py --root . --common-root ../lra-common --edition <digital|print|reference> --paper <letter|sixbynine> --output-dir build/<edition>-<paper>`
  (discovers every canonical book root; add `--tex-root <book>.tex` for one book).
- "edit latex" means the governance devcontainer launcher (route
  `local-tex-devcontainer`); never build volumes with raw `latexmk`.
- After moving or adding active `.tex` files, refresh LaTeX Workshop root
  comments with `set_latex_root_comments.py --root . --write` then `--check`.
- After changing formal TeX artifacts, refresh the internal object index
  (route `prepare-lean-tex-lookup`); generated indexes stay uncommitted.
- Volume success requires governance validation and a successful independent
  volume/book build.
{notes_block}
Overlay-specific verifier args:{" none beyond the capability default." if not plain else ""}{" Verifiers pass `--no-require-box`." if plain else ""}
Pass `--canonical-dir <path-to-lra-governance>` to `validate_decoration.py` to enable formal-reading triggers.
"""


def main() -> int:
    import yaml

    here = Path(__file__).resolve().parent
    cfg = yaml.safe_load((here / "overlays-config.yaml").read_text(encoding="utf-8"))
    outdir = here / "overlays"
    outdir.mkdir(exist_ok=True)
    missing: list[str] = []
    for r in cfg["repos"]:
        target = outdir / f"{r['repo']}.md"
        if r["kind"] == "volume":
            md = volume_overlay(
                r["repo"], r["title"], r.get("plain_style", False), r.get("notes", [])
            )
            target.write_text(md, encoding="utf-8")
            print(f"wrote overlays/{r['repo']}.md")
        elif not target.is_file():
            missing.append(target.name)
    if missing:
        print(
            "fatal: missing hand-maintained overlays: " + ", ".join(missing),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
