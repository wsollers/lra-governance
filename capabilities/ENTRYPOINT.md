# LRA Agent Entrypoint

You are an automated agent working inside an LRA repository. Keep the context
small: route to one capability, do the action, and run its success gates.

## How to work

1. Identify the repo you are in (e.g. `lra-volume-i`) and the task you were given.
2. Use `capabilities/manifest.yaml` through `capabilities/resolve.py` when possible.
   `capabilities/index.md` is the human view.
3. Load exactly one repo overlay and exactly one capability. Load only the files named
   by that capability plus one nearby example when authoring LaTeX.
4. Perform the capability action.
5. Run every listed success gate. If a gate fails, fix the artifact or the capability
   and run the gate again. Do not report success on a failing or skipped gate.

## Global Rules

- Use canonical names and notation from the registries when a capability asks for them.
  If the needed entry is missing, stop and report the missing registry entry.
- Keep generated shape separate from mathematical substance. Do not restate formulas,
  axioms, or signatures that already live in canonical files or labeled artifacts.
- Do not edit synced downstream copies or generated files when the canonical source is
  available.
- For structural tasks, move or route existing content; do not rewrite mathematics.
- For mechanics tasks, do not change mathematical content.

## Pointers

- Machine manifest: `capabilities/manifest.yaml`
- Human index: `capabilities/index.md`
- Repo overlays: `capabilities/overlays/`
- Capability docs: `capabilities/<capability>/capability.md`
