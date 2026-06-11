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

def _bullets(items):
    return "\n".join(f"- `{item}`" for item in items)

def nonvolume_overlay(repo, kind, title, build_environment=None, success_gates=None):
    blocks = {
        "library": (
            "Shared LaTeX macros, boxes, environments, and templates consumed by every volume. "
            "Changes here affect ALL volumes.",
            None),
        "lean": (
            "Lean formalization of the mathematics.",
            "author-lean-theorem: given \"formalize X\", add a descriptively-named theorem "
            "in the locally inferred file/namespace and run the success gates below."),
        "cpp": (
            "C++ / numerical companion.",
            "cpp-build-task: do the requested task and run the success gates below."),
        "vault": (
            "Handwritten proof records; volumes link here via \\ProofVaultURL.",
            None),
        "web": (
            "Knowledge Explorer web app consuming extracted knowledge-graph data.",
            None),
    }
    purpose, cap = blocks[kind]
    if not cap:
        return f"""# Repo Overlay -- {repo}

Repo identity: {title}.

{purpose}

No manifest-backed LLM capability is exposed for repo kind `{kind}` yet.
"""
    env_block = (
        f"\nBuild environment: {build_environment}. Run the success gates from this environment.\n"
        if build_environment else ""
    )
    gate_block = _bullets(success_gates or [])
    return f"""# Repo Overlay -- {repo}

Repo identity: {title}.

{purpose}
{env_block}
Success gates:
{gate_block}

Capabilities (domain-specific to this repo; same author -> validate spine as the volumes):
- {cap}

Capabilities here are scoped to repo kind `{kind}` in the manifest, so volume LaTeX
capabilities will NOT resolve in this repo (and vice versa).
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
            md = nonvolume_overlay(
                r["repo"],
                r["kind"],
                r["title"],
                r.get("build_environment"),
                r.get("success_gates"),
            )
        (outdir / f"{r['repo']}.md").write_text(md, encoding="utf-8")
        print(f"wrote overlays/{r['repo']}.md")

if __name__ == "__main__":
    main()
