# Capability: audit-semantic-topic

## Action

Inventory and audit every atomic formal environment in one notes topic through a
serial reviewer/temporary-application/revert loop.

## Trigger

Use for commands such as:

```text
LRA audit topic <topic>
audit semantic topic <topic>
validate topic artifacts <topic>
```

## Inputs

- Target split volume repository.
- Exact topic identifier under `notes/<topic>/`.
- Clean target branch or permission to create `audit/<topic>-semantic-artifacts`.
- `lra-governance` checkout or `LRA_GOVERNANCE_ROOT`.
- Configured semantic reviewer and read-only logic reviewer.

## Do

1. Follow `docs/workflows/topic-semantic-audit-loop.md`.
2. Use `constitution/prompts/audit-topic-semantic-artifacts.md`.
3. Enter plan mode before edits.
4. Inventory reachable primary formal environments in source order.
5. Commit the queued topic manifest before reviewer calls.
6. Send exactly one artifact per semantic-review call.
7. Store each returned package beside the owning topic source in a folder named
   from its label, such as `def-supremum`.
8. Commit only the reviewer package.
9. Apply the reviewed TeX in a separate temporary commit.
10. Run deterministic validators, the target build, and the independent logic
    validator.
11. Revert exactly the temporary source commit.
12. Verify byte-for-byte/hash restoration of the source.
13. Write one `audit-validation.yaml` after restoration and leave it uncommitted.
14. Continue until the topic queue is exhausted.
15. Commit all audit-validation records and the completed topic manifest together.
16. Stop for user review.

## Do not

- process multiple artifacts in one reviewer call;
- permanently apply corrected TeX;
- leave a temporary source commit unreverted;
- commit per-item audit-validation before topic closeout;
- invent labels, predicates, structures, notation, proof routes, Lean links, or
  proof-vault records;
- modify canonical registries or proof sources;
- begin another topic without a new user instruction.

## Success gates

- topic audit manifest validates against
  `constitution/schema/topic-semantic-audit.schema.json`;
- each `audit-validation.yaml` validates against
  `constitution/schema/artifact-audit-validation.schema.json`;
- every nonblocked review package passes semantic-artifact validation before
  temporary application;
- full-volume validation and target build results are recorded for every tested
  artifact;
- every tested artifact has an independent logic-validation record;
- every temporary source commit has a matching revert commit;
- all source hashes match the topic-start state at closeout;
- final tree changes contain only audit folders and the topic audit manifest;
- working tree is clean.
