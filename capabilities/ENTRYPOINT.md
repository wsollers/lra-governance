# LRA Agent Entrypoint

You are an automated agent working inside an LRA repository. Keep the context
small: resolve one route, do the action, and run its success gates.

## How to work

1. Identify the repo you are in (e.g. `lra-volume-i`) and the task you were given.
2. Run `capabilities/resolve.py --repo <repo> --task "<task>" --root <repo-root>`.
3. Load the returned eager packet only. Lazy references, executable tools,
   schemas/data, and examples stay out of context until the task requires them.
4. Perform the capability action.
5. Run every listed success gate. If a gate fails, fix the artifact or the capability
   and run the gate again. Do not report success on a failing or skipped gate.

## Global Rules

- Use canonical names and notation from the registries when a capability asks for them.
  If the needed entry is missing, stop and report the missing registry entry.
- For requests to find a theorem, definition, source passage, TeX/Lean object,
  C++ object, or canonical term, use the `lookup-lra` capability before loading
  large registries/indexes or scanning repositories broadly.
- Keep generated shape separate from mathematical substance. Do not restate formulas,
  axioms, or signatures that already live in canonical files or labeled artifacts.
- Do not edit synced downstream copies or generated files when the canonical source is
  available.
- For structural tasks, move or route existing content; do not rewrite mathematics.
- For mechanics tasks, do not change mathematical content.
- Lean formalization takes place in `lra-lean`. From any LRA repository, when
  asked to look up Lean-formalized proofs, checked Lean declarations, or Lean
  proof-completion status for a topic, resolve the sibling or external
  `lra-lean` checkout and search its `LRA/` modules first. Volume repositories
  may carry source prose and verification links, but they do not own Lean proof
  source.
- Do not preload architecture, workflow, tool source, schemas, examples, the
  generated task index, or registry bodies. Follow the resolver's typed pointers
  only when a concrete need arises.

## Pointers

- Machine manifest: `capabilities/manifest.yaml`
- Resolver: `capabilities/resolve.py`
- Generated human index: `docs/agent-task-index.md`
- Context audit: `tools/governance/audit_governance_context.py`
- Escalation references: `capabilities/reference-index.md`
- Repo overlays: `capabilities/overlays/`
- Capability docs: `capabilities/<capability>/capability.md`
