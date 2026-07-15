# Audit One Topic with External GPT-5.6 Review

Use for:

```text
LRA audit topic <topic>
```

Begin in plan mode. Follow:

- `capabilities/audit-semantic-topic/capability.md`;
- `docs/workflows/topic-semantic-audit-loop.md`;
- `docs/workflows/external-gpt-reviewer.md`.

## Non-negotiable reviewer boundary

Codex is the repository executor, not the mathematical reviewer. For every formal
environment, Codex must invoke the governed external reviewer executor. It must
not generate, repair, supplement, or self-certify the semantic package.

Accepted reviewer evidence is exactly:

```yaml
provider: openai_responses_api
requested_model: gpt-5.6
resolved_model: gpt-5.6-sol...
reasoning_effort: high
response_id: resp_...
self_review: false
```

The semantic review and logic validation must have distinct response IDs. A Codex
subagent, custom Codex agent, second Codex pass, manually written receipt, or
unretrievable Workspace Agent trigger is not accepted.

If the external executor or live evidence verification is unavailable, stop before
changing mathematical source. Never fall back to Codex reasoning.

## Serial topic loop

1. Inventory reachable primary definitions, axioms, theorems, lemmas,
   propositions, and corollaries in source order.
2. Commit the queued topic manifest.
3. For one artifact only, prepare the governed semantic input packet.
4. Invoke `tools/governance/invoke_external_gpt_reviewer.py semantic` with the
   calibration prompt and fixed GPT-5.6 configuration.
5. Validate the semantic package and live response evidence.
6. Commit the external package and receipt.
7. Apply `corrected.tex` in a separate temporary commit.
8. Run semantic, volume, proof-layout, and actual build checks.
9. Invoke `tools/governance/invoke_external_gpt_reviewer.py logic` with the logic
   prompt, using a new external response.
10. Revert exactly the temporary source commit and verify source hashes.
11. Write `audit-validation.yaml` with both external reviewer receipts and live
    verification results.
12. Continue to the next artifact.

`REVIEW_PACKAGE_NOT_PRODUCED` is incomplete work, not a terminal mathematical
blocker. A genuine blocker requires an external GPT-5.6 response identifying a
specific compound artifact or unresolved mathematical ambiguity.

At topic closeout, live-verify every recorded response, validate the topic audit,
commit the validation data, leave canonical TeX restored, and stop for user review.
