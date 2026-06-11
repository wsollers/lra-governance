#!/usr/bin/env python3
"""Generate capabilities/overlays/<repo>.md from overlays-config.yaml (single source).

Volume overlays are near-identical; this avoids copy-paste drift. Re-run after editing
the config. Non-volume repos get an overlay describing their OWN domain capabilities
(not "capabilities don't apply" -- "capabilities defined/planned for this repo kind").
Lives in capabilities/; writes to capabilities/overlays/.
"""
from __future__ import annotations
from pathlib import Path

def volume_overlay(repo, title, plain):
    box = ("Definitions are PLAIN (\\begin{definition} ... no box); verifiers run with "
           "`--no-require-box`." if plain else
           "Definitions are wrapped in the semantic `definitionbox` family (common/boxes.tex).")
    plainnote = ("\n- Plain-style volume: pass `--no-require-box` to `validate_decoration.py`."
                 if plain else "")
    vol = repo.replace('lra-', '')
    return f"""# Repo Overlay -- {repo}

Repo identity: {title}.

Local conventions:
- Content lives under `{vol}/<chapter>/notes/<section>/notes-<section>.tex`;
  proofs under `.../proofs/<section>/prf-<slug>.tex`.
- {box}
- Decoration blocks are unboxed `remark*`; dependencies use `\\begin{{dependencies}}` or `\\NoLocalDependencies`.
- Chapters route into BOTH `{vol}/index.tex` (monorepo) and `main.tex` (local build).
- Canonical YAML registries live at the monorepo root; cross-volume `\\hyperref` targets resolve
  only in the assembled monorepo build.

Applicable capabilities: author-statement, author-stub-chapter, author-stub-section.

Overlay-specific verifier args:{plainnote or ' none beyond the capability default.'}
Pass `--canonical-dir <monorepo-root>` to `validate_decoration.py` to enable formal-reading triggers.
"""

def nonvolume_overlay(repo, kind, title):
    blocks = {
        "library": (
            "Shared LaTeX macros, boxes, environments, and templates consumed by every volume. "
            "Changes here affect ALL volumes.",
            "edit-shared-macro (PLANNED): change a macro/box; verifier = a consuming volume still builds."),
        "lean": (
            "Lean formalization of the mathematics.",
            "author-lean-theorem: given \"formalize X\", add a descriptively-named theorem "
            "(e.g. RationalEquivalenceClassAdditionIsCommutative) in the right place, formalize it to "
            "the project's standards, then VERIFY with `lake build`, then sync the formalized statement "
            "into its owning LaTeX volume. Standards doc + volume-sync mapping: TODO (owner-defined)."),
        "cpp": (
            "C++ / numerical companion.",
            "cpp-build-task: do the requested task; verifier = the project still builds "
            "(`cmake --build build` / `make` -- TODO confirm)."),
        "vault": (
            "Handwritten proof records; volumes link here via \\ProofVaultURL.",
            "memorialize-record (PLANNED): register a handwritten record and link it from the owning proof."),
        "web": (
            "Knowledge Explorer web app consuming extracted knowledge-graph data.",
            "explorer-build (PLANNED): build/test the app against the latest extracted data."),
    }
    purpose, cap = blocks[kind]
    return f"""# Repo Overlay -- {repo}

Repo identity: {title}.

{purpose}

Capabilities (domain-specific to this repo; same author -> validate spine as the volumes):
- {cap}

Capabilities here are scoped to repo kind `{kind}` in the manifest, so volume LaTeX
capabilities will NOT resolve in this repo (and vice versa). Capabilities marked PLANNED are
not yet implemented -- the shape and verifier are recorded so they can be built to spec.
"""

def main():
    import yaml
    here = Path(__file__).resolve().parent
    cfg = yaml.safe_load((here / "overlays-config.yaml").read_text(encoding="utf-8"))
    outdir = here / "overlays"; outdir.mkdir(exist_ok=True)
    for r in cfg["repos"]:
        if r["kind"] == "volume":
            md = volume_overlay(r["repo"], r["title"], r.get("plain_style", False))
        else:
            md = nonvolume_overlay(r["repo"], r["kind"], r["title"])
        (outdir / f"{r['repo']}.md").write_text(md, encoding="utf-8")
        print(f"wrote overlays/{r['repo']}.md")

if __name__ == "__main__":
    main()
