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
5. Send exactly one artifact per semantic-review call.
6. Store each returned package beside the owning topic source in a folder named
   from its label, such as `def-supremum`.
7. Commit the reviewer package.
8. Apply the reviewed TeX in a separate temporary commit.
9. Run deterministic validators, build, and the independent logic validator.
10. Revert exactly the temporary source commit.
11. Verify byte-for-byte/hash restoration of the source.
12. Continue until the topic queue is exhausted.
13. Commit all validation records and the completed topic manifest together.
14. Stop for user review.

## Do not

- process multiple artifacts in one reviewer call;
- permanently apply corrected TeX;
- leave a temporary source commit unreverted;
- commit per-item validation before topic closeout;
- invent labels, predicates, structures, notation, proof routes, Lean links, or
  proof-vault records;
- modify canonical registries or proof sources;
- begin another topic without a new user instruction.

## Success gates

- topic audit manifest validates against
  `constitution/schema/topic-semantic-audit.schema.json`;
- every nonblocked review package passes semantic-artifact validation before
  temporary application;
- full-volume validation and target build results are recorded for every tested
  artifact;
- every tested artifact has an independent logic-validation record;
- every temporary source commit has a matching revert commit;
- all source hashes match the topic-start state at closeout;
- final tree changes contain only audit folders and the topic audit manifest;
- working tree is clean.
