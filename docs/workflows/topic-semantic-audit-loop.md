# Topic Semantic Audit Loop

## Goal

Audit every formal environment in one notes topic without leaving reviewed LaTeX
applied to canonical source. The durable outputs are external GPT-5.6 review
packages and validation evidence. Every candidate source replacement is committed,
validated, and reverted before the next artifact.

This is an audit/calibration workflow, not the permanent source-update workflow.

## Mobile command

```text
LRA audit topic <topic>
```

`<topic>` is the repository identifier under `notes/<topic>/`, not a rendered PDF
heading.

## Preconditions

1. Work on `audit/<topic>-semantic-artifacts` unless another isolated branch is explicitly selected.
2. Require a clean working tree.
3. Resolve `lra-governance` through `LRA_GOVERNANCE_ROOT` or a sibling checkout.
4. Pin target-volume and governance commits.
5. Enter plan mode before edits.
6. Process exactly one artifact at a time, in source order.
7. Pass the external-review preflight in `docs/workflows/external-gpt-reviewer.md`.

If external API credentials, Responses API access, or the governed reviewer executors are unavailable, stop. Codex must not substitute its own reasoning or a subagent.

## Inventory and artifact folder

Gather reachable primary `definition`, `axiom`, `theorem`, `lemma`, `proposition`, and `corollary` environments from the topic router closure. Exclude proof restatements, remarks, examples, duplicated PDF text, and unreachable files. Commit the queued inventory at `notes/<topic>/semantic-topic-audit.yaml` with `Initialize semantic audit for <topic>`.

For `<prefix>:<root>`, use `notes/<topic>/<prefix>-<root>/`. A reviewed folder contains the nine semantic-package files, `external-review-receipt.yaml`, and `audit-validation.yaml`.

## Required external reviewer

All model review is governed by `docs/workflows/external-gpt-reviewer.md`. Required evidence is:

```yaml
provider: openai_responses_api
requested_model: gpt-5.6
resolved_model: gpt-5.6-sol...
reasoning_effort: high
response_id: resp_...
self_review: false
```

A Codex thread, Codex subagent, custom Codex agent, second Codex pass, manually written receipt, or Workspace Agent trigger without a retrievable result is not an external reviewer.

## Per-artifact transaction

1. Build an ignored-run JSON packet containing exactly one source environment, its support blocks, exact commits, minimal context, canonical vocabulary, and known proof/Lean/Mathlib/proof-vault candidates.
2. Invoke external GPT-5.6 semantic review:

   ```powershell
   python <governance-root>\tools\governance\invoke_external_gpt_reviewer.py semantic `
     --input <run-dir>\semantic-input.json `
     --output <artifact-folder> `
     --prompt <governance-root>\constitution\prompts\calibrate-semantic-artifact.md
   ```

3. Codex must not rewrite, complete, or repair the returned package. A genuine blocked result requires an external response identifying a concrete compound artifact or unresolved mathematical ambiguity. Missing output or `REVIEW_PACKAGE_NOT_PRODUCED` is incomplete/infrastructure failure, not a terminal mathematical blocker.
4. Validate the package and live external evidence before source application:

   ```powershell
   python <governance-root>\tools\governance\validate_semantic_artifact.py `
     --artifact <artifact-folder>\artifact.yaml `
     --package-dir <artifact-folder> `
     --governance-root <governance-root> `
     --repos-root <repos-root> `
     --strict

   python <governance-root>\tools\governance\validate_external_reviewer_evidence.py `
     --package <artifact-folder>\package.yaml `
     --verify-live
   ```

5. Commit only the external semantic package and receipt with `Record semantic review for <label>`.
6. Record source blob hashes, apply only `corrected.tex`, and commit `Temporarily apply semantic review for <label>`.
7. Run strict semantic validation, live evidence validation, full-volume validation, applicable proof-layout validation, and the normal volume/book build. `--validate-only` is not a build substitute. Capture commands, timestamps, exit codes, tested commit, and log paths.
8. Build a separate logic packet and invoke a new external GPT-5.6 response:

   ```powershell
   python <governance-root>\tools\governance\invoke_external_gpt_reviewer.py logic `
     --input <run-dir>\logic-input.json `
     --output <run-dir>\logic-validation.yaml `
     --prompt <governance-root>\constitution\prompts\validate-semantic-artifact-logic.md
   ```

   Its response ID must differ from the semantic response ID. Copy the returned logic record without revision.
9. Revert exactly the temporary source commit with `git revert --no-edit <temporary_apply_commit>` and verify every changed source blob matches its pre-application hash.
10. Write `audit-validation.yaml`, then live-verify both reviewers:

    ```powershell
    python <governance-root>\tools\governance\validate_external_reviewer_evidence.py `
      --audit-record <artifact-folder>\audit-validation.yaml `
      --verify-live
    ```

11. Continue in source order. Never send multiple artifacts in one reviewer call or reuse a response ID.

## Topic completion

After each item has an actual external semantic response and is truthfully `validated`, `failed`, or genuinely `blocked`:

1. verify no temporary source replacement remains, all baseline blobs are restored, and no unrelated file changed;
2. finalize all audit records and `semantic-topic-audit.yaml`;
3. validate every package, audit record, and topic manifest;
4. live-verify every external response:

   ```powershell
   python <governance-root>\tools\governance\validate_external_reviewer_evidence.py `
     --topic-manifest <topic>\semantic-topic-audit.yaml `
     --repo-root <target-volume-root> `
     --verify-live
   ```

5. commit `Record semantic validation for <topic>` and stop for user review.

Do not permanently apply corrected TeX or begin another topic.

## Failure handling

- Missing API credentials/network/tooling: stop as infrastructure failure.
- Missing external response: leave queued; do not fabricate a blocker.
- Wrong provider/model/reasoning effort or unverifiable response evidence: fail before source application.
- Package validation failure: do not apply TeX.
- Logic validation failure: revert source, record failure, continue.
- Source changed since inventory: stop; do not silently rebase.
- Revert/hash mismatch: stop immediately.
- Never fix canonical registries, Lean declarations, proof-vault routes, or source mathematics inside this audit loop.
