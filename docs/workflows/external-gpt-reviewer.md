# External GPT-5.6 Reviewer Transport

## Purpose

Semantic-artifact review is performed by an external GPT-5.6 Responses API
call, not by the Codex thread and not by a Codex subagent. Logic validation
defaults to the local semantic AST validator; an external logic call is allowed
only when explicitly requested for review or calibration. The transport returns
retrievable response identifiers and refuses to proceed when external review
cannot be verified.

## Governed model and transport

```yaml
provider: openai_responses_api
requested_model: gpt-5.6
resolved_model: gpt-5.6-sol...
reasoning_effort: high
store: true
background: true
```

Canonical executor:

```text
tools/governance/invoke_external_gpt_reviewer.py
```

Do not substitute a Codex model, a lower GPT tier, a manually authored response,
or an unverified trigger.

## Authentication

Provide the API credential through `OPENAI_API_KEY`. Never place the value in a
prompt, YAML file, command-line argument, commit, diagnostic, or pull request.
When credentials or outbound access are unavailable, stop as infrastructure
failure. Codex must not fall back to its own reasoning.

## Automatic governance-authority bundle

The executor—not Codex—loads and embeds the canonical authority bundle on every
external semantic request and every explicitly requested external logic request.
The bundle contains the exact file path, SHA-256 hash, and full UTF-8 contents
of:

```text
constitution/schema/semantic-artifact.schema.json
constitution/schema/semantic-artifact-package.schema.json
constitution/schema/semantic-artifact-support.schema.json
constitution/schema/external-review-receipt.schema.json
constitution/schema/artifact-audit-validation.schema.json
constitution/schema/topic-semantic-audit.schema.json
constitution/schema/artifact-matrix.yaml
constitution/schema/block-registry.yaml
constitution/schema/examples/semantic-artifact.example.yaml
predicates.yaml
structures.yaml
notation.yaml
relations.yaml
docs/architecture/semantic-artifact-record.md
docs/workflows/semantic-artifact-calibration.md
```

A missing authority file stops the request before an API call. The calling input
packet may add artifact-specific source and context, but it cannot remove or
replace canonical authority files.

## Background execution and polling

Every request is created with `background: true` and `store: true`. The initial
POST is expected to return quickly with a response ID. The executor polls
`GET /v1/responses/{response_id}` while status is `queued` or `in_progress` and
accepts output only after terminal status `completed`.

Defaults:

```text
poll interval: 2 seconds
poll timeout: 1800 seconds
```

They can be changed with `--poll-interval` and `--poll-timeout`. A timeout or
non-completed terminal status is an infrastructure failure; it is not a
mathematical blocker.

## Semantic review call

```powershell
python <governance-root>\tools\governance\invoke_external_gpt_reviewer.py semantic `
  --input <run-dir>\semantic-input.json `
  --output <artifact-folder> `
  --prompt <governance-root>\constitution\prompts\calibrate-semantic-artifact.md `
  --governance-root <governance-root> `
  --repos-root <repos-root>
```

The executor requests strict structured output, stages the eight review files,
builds `package.yaml`, writes `external-review-receipt.yaml`, and runs:

```text
validate_semantic_artifact.py --strict
validate_external_reviewer_evidence.py --package ...
```

Nothing is published to the artifact folder until the staged package passes.

## External repair retries

When a staged semantic package fails deterministic validation, the executor does
not edit it. It preserves the response and validator report under:

```text
<artifact-parent>/.external-review-diagnostics/<artifact-name>/attempt-NN/
```

It then creates a new external GPT-5.6 response containing:

- the same complete authority bundle;
- the original artifact input packet;
- the prior external response ID and reviewer output;
- exact validator commands, exit code, stdout, and stderr;
- an instruction to return a complete replacement package.

The replacement receives a distinct response ID. The default is two repair
attempts after the initial call, controlled by `--max-repair-attempts`. Codex may
not patch or complete any attempt locally.

If all external attempts fail, the executor returns infrastructure failure and
leaves the canonical artifact folder unpublished. Failed attempts remain in
ignored diagnostics.

## Logic validation call

After deterministic validation of temporarily applied TeX, use the local
semantic logic verifier by default:

```powershell
python <governance-root>\tools\governance\invoke_external_gpt_reviewer.py logic `
  --input <run-dir>\logic-input.json `
  --output <run-dir>\logic-validation.yaml `
  --artifact <artifact-folder>\artifact.yaml `
  --corrected-tex <artifact-folder>\corrected.tex `
  --governance-root <governance-root>
```

The local logic result is deterministic validation evidence, not external
review evidence, and it does not have a response ID.

Use an external GPT-5.6 logic request only when explicitly requested:

```powershell
python <governance-root>\tools\governance\invoke_external_gpt_reviewer.py logic `
  --logic-reviewer external `
  --input <run-dir>\logic-input.json `
  --output <run-dir>\logic-validation.yaml `
  --prompt <governance-root>\constitution\prompts\validate-semantic-artifact-logic.md `
  --governance-root <governance-root>
```

When external logic review is used, the logic response uses the same automatic
authority bundle and background polling. Its response ID must differ from every
semantic attempt. Codex copies the returned logic record without revising it.

## Evidence validation

Before source application:

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

After external logic validation and source reversion:

```powershell
python <governance-root>\tools\governance\validate_external_reviewer_evidence.py `
  --audit-record <artifact-folder>\audit-validation.yaml `
  --verify-live
```

At topic closeout:

```powershell
python <governance-root>\tools\governance\validate_external_reviewer_evidence.py `
  --topic-manifest <topic>\semantic-topic-audit.yaml `
  --repo-root <target-volume-root> `
  --verify-live
```

Live verification retrieves each stored external response and checks response
ID, resolved GPT-5.6 Sol model, completion status, and output hash. Local logic
validation outputs are checked by their deterministic validator result instead.

## Forbidden fallbacks

The following never count as external review:

- reasoning in the main Codex thread;
- a Codex plan-mode response;
- a Codex subagent or custom `.codex/agents` reviewer;
- a second pass by the same Codex model;
- local repair of external output;
- a manually authored receipt;
- a response with a missing or unverifiable response ID;
- any model other than requested `gpt-5.6` resolving to GPT-5.6 Sol.

If any fallback is attempted, stop before changing mathematical source.
