# Audit One Topic's Semantic Artifacts

You are operating in a split `lra-volume-*` repository with canonical governance
available from `lra-governance`.

## User command

```text
LRA audit topic <topic>
```

Interpret `<topic>` as the exact topic directory under the owning chapter's
`notes/` directory. Do not infer a different topic from a PDF heading.

## Required mode

Begin in plan mode. Produce the inventory and transaction plan before editing.
Then execute the approved workflow serially, one formal environment at a time.
Do not use parallel reviewers.

## Read only

1. target repository `AGENTS.md`;
2. `lra-governance/AGENTS.md`;
3. `docs/agent-task-index.md`;
4. `capabilities/audit-semantic-topic/capability.md`;
5. `docs/workflows/topic-semantic-audit-loop.md`;
6. `docs/workflows/semantic-artifact-calibration.md`;
7. `docs/architecture/semantic-artifact-record.md`;
8. semantic-artifact, artifact-audit-validation, and topic-audit schemas;
9. the target volume overlay;
10. canonical root registries;
11. target topic router closure and one nearby governed example.

Do not load unrelated capability folders.

## Inventory

Discover all reachable primary `definition`, `axiom`, `theorem`, `lemma`,
`proposition`, and `corollary` environments in source order. Require exactly one
formal label per primary environment. Exclude proof restatements and nonprimary
remarks/examples.

Create the source-ordered queue at:

```text
notes/<topic>/semantic-topic-audit.yaml
```

Commit the queued inventory with:

```text
Initialize semantic audit for <topic>
```

Do not change mathematical source during inventory.

## Review loop

For each queue item:

1. Invoke the semantic reviewer with exactly one owning environment and its
   attached support blocks.
2. Write the complete nine-file review package to:
   `notes/<topic>/<label-with-colon-replaced-by-hyphen>/`.
3. Validate the returned package.
4. Commit only the nine reviewer-package files with:
   `Record semantic review for <label>`.
5. Record pre-application source blob hashes.
6. Replace only the reviewed environment/support blocks with `corrected.tex`.
7. Commit that temporary source edit with:
   `Temporarily apply semantic review for <label>`.
8. Run strict semantic-artifact validation, full-volume validation, applicable
   proof-layout validation, and the normal target build.
9. Invoke a separate read-only logic validator using
   `constitution/prompts/validate-semantic-artifact-logic.md`.
10. Capture deterministic and logic results outside changed source files.
11. Revert exactly the temporary source commit with `git revert --no-edit`.
12. Verify exact restoration of all changed source blobs.
13. Write one `audit-validation.yaml` after the revert. Leave it uncommitted until
    topic completion.
14. Continue to the next artifact in source order.

When committing a later reviewer package, stage only its nine review files. Do
not accidentally include earlier uncommitted `audit-validation.yaml` files.

If one item is blocked or fails, record it and continue unless source restoration
or repository integrity fails.

## Logic validation contract

The logic validator independently checks binder scope, object/meta-language level,
quantifier order, witness dependence, statement shape, mechanical and normalized
negations, required normalization assumptions, contrapositives, applicability
versus statement failure, order-strength assumptions, predicate signatures,
failure-mode exhaustiveness, and YAML/TeX semantic equivalence.

Allowed results are `pass`, `pass_with_warnings`, `fail`, and `blocked`.
The logic validator may not edit source or reviewer output.

## Topic closeout

When the queue is exhausted:

1. prove that no temporary source edit remains;
2. finalize every `audit-validation.yaml` and the topic manifest;
3. validate all per-artifact audit records and the topic manifest;
4. commit validation data with:
   `Record semantic validation for <topic>`;
5. leave a clean working tree;
6. stop and report the topic, counts, failed/blocked labels, branch, and final
   validation commit SHA.

Do not store the final commit SHA inside the same manifest commit. Do not
permanently apply corrected TeX. Do not begin another topic. The user will notify
the semantic reviewer or issue the next instruction after reviewing the committed
validation data.
