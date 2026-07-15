# External GPT-5.6 Reviewer Transport

## Purpose

Semantic-artifact review and logic validation must be performed by an external
GPT-5.6 model call, not by the Codex thread that edits the repository and not by
a Codex subagent. This workflow uses the OpenAI Responses API because it returns
a retrievable response identifier and a resolved model name.

A published ChatGPT Workspace Agent trigger is not the transport for this loop.
The current trigger endpoint accepts work asynchronously but does not return a
review result or a retrievable public run identifier. It therefore cannot supply
the synchronous, verifiable package required before temporary TeX application.

## Governed model and transport

The fixed request configuration is:

```yaml
provider: openai_responses_api
requested_model: gpt-5.6
resolved_model: gpt-5.6-sol...
reasoning_effort: high
store: true
```

The `gpt-5.6` API alias resolves to GPT-5.6 Sol. Do not substitute a Codex model,
a lower GPT tier, a Workspace Agent trigger, or an unrecorded manual response.

Canonical executor:

```text
tools/governance/invoke_external_gpt_reviewer.py
```

## Authentication

The caller must provide `OPENAI_API_KEY` through the execution environment.
Never place the key in a prompt, YAML file, command-line argument, commit, log,
or pull request.

If the key or outbound API access is unavailable, stop the audit as an
infrastructure blocker. Codex must not fall back to its own reasoning.

## Semantic review call

Create one JSON input packet for one formal artifact and run:

```powershell
python <governance-root>\tools\governance\invoke_external_gpt_reviewer.py semantic `
  --input <run-dir>\semantic-input.json `
  --output <artifact-folder> `
  --prompt <governance-root>\constitution\prompts\calibrate-semantic-artifact.md
```

The executor requests structured output from `gpt-5.6`, writes the eight review
files, builds `package.yaml`, and writes `external-review-receipt.yaml`. The
receipt and package record:

- provider and reviewer role;
- requested and resolved models;
- reasoning effort;
- OpenAI `response_id` and request ID;
- governed prompt and executor;
- input and output hashes;
- start and completion timestamps;
- `self_review: false`.

A blocked semantic response still receives an external receipt. Absence of a
response is incomplete work, not a genuine mathematical blocker.

## Logic validation call

After deterministic validation of the temporarily applied TeX, create a separate
logic input packet and run:

```powershell
python <governance-root>\tools\governance\invoke_external_gpt_reviewer.py logic `
  --input <run-dir>\logic-input.json `
  --output <run-dir>\logic-validation.yaml `
  --prompt <governance-root>\constitution\prompts\validate-semantic-artifact-logic.md
```

The logic call must use a new Responses API request. Its `response_id` must differ
from the semantic reviewer response ID. Codex copies the returned
`logic_validation` object into `audit-validation.yaml` without revising it.

## Evidence validation

Before temporary source application, validate the semantic package and live
response evidence:

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

After logic validation and source reversion, validate the complete audit record:

```powershell
python <governance-root>\tools\governance\validate_external_reviewer_evidence.py `
  --audit-record <artifact-folder>\audit-validation.yaml `
  --verify-live
```

At topic closeout, validate all review evidence in one pass:

```powershell
python <governance-root>\tools\governance\validate_external_reviewer_evidence.py `
  --topic-manifest <topic>\semantic-topic-audit.yaml `
  --repo-root <target-volume-root> `
  --verify-live
```

Live verification retrieves each stored response from the Responses API and
checks the response ID, resolved GPT-5.6 Sol model, completion status, and output
hash. A locally written or falsified reviewer record cannot satisfy this gate.

## Forbidden fallbacks

The following never count as external review:

- reasoning in the main Codex thread;
- a Codex plan-mode response;
- a Codex subagent or custom `.codex/agents` reviewer;
- a second pass by the same Codex model;
- a manually authored YAML receipt;
- a Workspace Agent trigger without a returned review payload;
- a response with a missing or unverifiable response ID;
- any model other than requested `gpt-5.6` resolving to GPT-5.6 Sol.

If any forbidden fallback is attempted, stop before changing mathematical source.
