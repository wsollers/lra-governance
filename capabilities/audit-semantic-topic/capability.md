# Capability: audit-semantic-topic

## Action

Inventory and audit every atomic formal environment in one notes topic through a
serial external-GPT-review/temporary-application/revert loop.

## Trigger

```text
LRA audit topic <topic>
audit semantic topic <topic>
validate topic artifacts <topic>
```

## Inputs

- Target split volume repository and exact `notes/<topic>/` identifier.
- Clean target branch or permission to create `audit/<topic>-semantic-artifacts`.
- `lra-governance` checkout or `LRA_GOVERNANCE_ROOT`.
- External OpenAI Responses API credentials and network access.

## Required reviewer transport

Both semantic review and logic validation must use
`tools/governance/invoke_external_gpt_reviewer.py` with:

```yaml
provider: openai_responses_api
requested_model: gpt-5.6
reasoning_effort: high
```

The API-resolved model must be GPT-5.6 Sol. A Codex thread, Codex subagent,
custom Codex agent, or Workspace Agent trigger is not an accepted substitute.

## Do

1. Follow `docs/workflows/topic-semantic-audit-loop.md` and
   `docs/workflows/external-gpt-reviewer.md`.
2. Use `constitution/prompts/audit-topic-semantic-artifacts-external.md`.
3. Enter plan mode before edits and pass external-review preflight.
4. Inventory reachable primary formal environments in source order.
5. Commit the queued topic manifest before reviewer calls.
6. Send exactly one artifact per external GPT-5.6 semantic-review call.
7. Validate the returned package and live Responses API evidence before applying
   any TeX.
8. Commit the reviewer package and receipt.
9. Apply reviewed TeX in a separate temporary commit.
10. Run deterministic validators and the normal target build.
11. Use a second, distinct external GPT-5.6 response for logic validation.
12. Revert exactly the temporary source commit and verify source hashes.
13. Record both response IDs and live-verification results in
    `audit-validation.yaml`.
14. Continue until the topic queue is exhausted.
15. Commit all audit records and the completed topic manifest together.
16. Stop for user review.

## Do not

- reason through or author the semantic package in Codex;
- use a Codex subagent or second Codex pass as reviewer;
- proceed when external network access, response ID, or live verification is
  unavailable;
- accept a model other than requested `gpt-5.6` resolving to GPT-5.6 Sol;
- reuse the semantic response ID for logic validation;
- mark `REVIEW_PACKAGE_NOT_PRODUCED` as a terminal blocker;
- permanently apply corrected TeX;
- modify canonical registries, proof sources, Lean, or proof-vault data;
- begin another topic without a new user instruction.

## Success gates

- every terminal item has external semantic reviewer evidence;
- every terminal item has a distinct external logic reviewer response;
- all response IDs pass live retrieval, model, status, and output-hash checks;
- semantic package, audit record, and topic manifest schemas pass;
- full-volume validation and actual target build results are recorded;
- every temporary source commit has a matching revert;
- all source hashes match the topic baseline;
- final tree changes contain only audit data;
- working tree is clean.
