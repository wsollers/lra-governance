# Capability: author-definition

## Trigger
Author or generate a mathematical definition ("define X", "generate the definition for X",
"write the def for X").

## Composition
global core (`ENTRYPOINT.md`) + `overlays/<repo>.md` + this capability + bound verifier.

## Read (load ONLY these)
- this file
- `constitution/schema/artifact-matrix.yaml`  — which decoration blocks a Definition requires
- `constitution/schema/block-registry.yaml`   — the exact block titles/identities
- canonical `predicates.yaml`, `notation.yaml` — canonical predicate name and notation for the concept
- `overlays/<repo>.md`                          — the repo's definition house-style (boxed vs plain, paths)
- ONE nearby existing definition in the target repo — to mirror exact macro usage

## Procedure
1. Resolve the canonical predicate for the concept in `predicates.yaml`. If none exists and one is
   clearly warranted, STOP and flag a missing-predicate; do not coin a name inline.
2. Write the definition:
   - a `definition` environment with `\label{def:<slug>}`, in the repo house style (see overlay);
   - the decoration blocks REQUIRED for a Definition by `artifact-matrix.yaml`, in the order fixed by
     `decoration-box-standards`, as unboxed `remark*`. Minimum: Standard quantified statement,
     Interpretation, and Dependencies (or `\NoLocalDependencies`);
   - a Definition predicate reading using `\operatorname{<CanonicalName>}` ONLY if a canonical
     predicate exists; otherwise omit (do not invent);
   - statement body uses standard notation; predicate names appear only in the predicate-reading block.
3. Append the result to the target file.

## Output
Compliant LaTeX appended to the target file.

## Bound verifier (MANDATORY — task not complete until exit 0)
    python author-definition/verify.py --target <file> --kind definition \
        [--matrix constitution/schema/artifact-matrix.yaml --predicates predicates.yaml]

In a real chapter tree, ALSO run the canonical chapter validator
(`tools/governance/validate_note_blocks.py --chapter <name> --section <name>`) before commit.
The scratch verifier here is this capability's self-check; it reads the same schema files and
never forks the canonical validator's rule logic.
