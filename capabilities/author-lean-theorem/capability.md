# Capability: author-lean-theorem

Repo kind: `lean` (lra-lean). Same author -> validate spine as the volume capabilities,
specialized to Lean formalization.

## Trigger
"formalize X", "let Claude formalize that", "add a lean theorem for X".

## What it does
Given an informal mathematical claim (often pointed at from a volume -- e.g. "addition is
commutative on the rational equivalence classes"):

1. **Name it.** Derive a canonical, descriptive PascalCase theorem name that reads as the
   claim, e.g. `RationalEquivalenceClassAdditionIsCommutative`. The name is the durable
   handle that links the Lean theorem to its LaTeX counterpart.

2. **Place it.** Add the theorem to the appropriate file in the Lean library.
   TODO (owner-defined): the placement rule -- which file/namespace a given subject maps to.

3. **Formalize to standards.** State and prove (or stub) the theorem to the project's Lean
   standards. TODO (owner-defined): the standards doc -- naming, namespaces, `simp` usage,
   proof-style conventions, whether stubs (`sorry`) are permitted at authoring time.

4. **VERIFY (bound).** The Lean library must still build:

       cd <lean-root> && lake build      # TODO: confirm exact build command

   This is the gate -- the capability is not "done" until the build is green.

5. **Bookkeeping / sync.** Copy the formalized statement to where it belongs in its owning
   LaTeX volume (e.g. Volume II), keeping the two representations in lockstep.
   TODO (owner-defined): the lean-theorem -> (volume, file, label) mapping.

## Notes
- Steps 1-2 (name + placement) are deterministic once the placement rule and naming
  convention exist; only the proof content needs genuine formalization work.
- The standards doc and the sync mapping are the two owner-defined pieces this capability
  waits on; everything else is mechanical and scriptable.
- Status: SCAFFOLD. The build verifier is wired; standards, placement, and sync are TODO.
