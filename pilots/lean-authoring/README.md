# Lean Authoring Pilot

This directory is a disposable calibration area for the proposed Lean-first
topic-authoring workflow. It is not yet canonical governance. The pilot keeps
its standard, schemas, chat fixtures, and materializer together so the entire
experiment can be removed or revised before it is promoted into governed
workflows.

The first vertical test is the Poset-based Upper Bound concept requested as:

> generate the definition of upper bound in volume 1 order theory. Leverage
> the volume 1 poset to provide the ordering relation. Include negations,
> examples, counter examples, variant forms inverse, converse, contrapositive
> if mathematically interesting

The reviewed package places the Poset-owned predicate and its selected
declaration family in the Volume I pilot. It deliberately generates no Volume
III specialization because the request does not ask for one. Run the
materializer from `lra-governance`:

```powershell
python pilots\lean-authoring\materialize.py `
  --package pilots\lean-authoring\test-cases\upper-bound\concept-package.json `
  --lean-root ..\lra-lean
```

Use `--check` after generation to verify that every generated artifact and
wiring block matches the package byte for byte.
