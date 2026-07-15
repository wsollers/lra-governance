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

## Transport-owned behavior

Do not manually copy schemas or registries into the input packet. The governed
executor automatically embeds the canonical schemas, registries, example artifact,
semantic-record architecture, and calibration/renderer contract.

The executor runs stored background Responses API requests, polls them until
terminal completion, stages returned files outside the artifact folder, and
validates the staged package before publishing it.

When validation fails, do not stop after the first malformed package and do not
repair it locally. Allow the executor's external repair loop to send the exact
validator commands, exit code, stdout, stderr, prior response ID, and prior output
to a new GPT-5.6 response. Stop only after the configured external attempts are
exhausted.

## Serial topic loop

1. Inventory reachable primary definitions, axioms, theorems, lemmas,
   propositions, and corollaries in source order.
2. Commit the queued topic manifest.
3. For one artifact only, prepare the artifact-specific input packet: exact source,
   source line bounds, support blocks, nearby context, and known verification links.
4. Invoke `tools/governance/invoke_external_gpt_reviewer.py semantic` with the
   calibration prompt, governance root, repositories root, and fixed GPT-5.6
   configuration.
5. Let the executor perform authority bundling, background polling, staged
   validation, and external repair retries.
6. Validate the published semantic package and live response evidence.
7. Commit the external package and receipt.
8. Apply `corrected.tex` in a separate temporary commit.
9. Run semantic, volume, proof-layout, and actual build checks.
10. Invoke `tools/governance/invoke_external_gpt_reviewer.py logic` with the logic
    prompt, using a new external response and the same automatic authority bundle.
11. Revert exactly the temporary source commit and verify source hashes.
12. Write `audit-validation.yaml` with both external reviewer receipts and live
    verification results.
13. Continue to the next artifact.

`REVIEW_PACKAGE_NOT_PRODUCED` is incomplete work, not a terminal mathematical
blocker. A genuine blocker requires an external GPT-5.6 response identifying a
specific compound artifact or unresolved mathematical ambiguity.

At topic closeout, live-verify every recorded response, validate the topic audit,
commit the validation data, leave canonical TeX restored, and stop for user review.
