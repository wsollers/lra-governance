# Topic Semantic Audit Loop

## Goal

Audit every formal environment in one notes topic without leaving the reviewed
LaTeX applied to the book source. The durable output is the semantic-review
package and validation evidence. Each candidate source replacement is committed,
validated, and then reverted before the next artifact.

This is an audit and calibration workflow. It is not the permanent source-update
workflow in `semantic-artifact-calibration.md`.

## Mobile command

From the target volume repository, the user invokes the whole workflow with:

```text
LRA audit topic <topic>
```

The topic is the repository identifier under `notes/<topic>/`, not a heading
guessed from rendered PDF output.

## Preconditions

1. Work on an isolated branch named `audit/<topic>-semantic-artifacts` unless the
   user names another branch.
2. Require a clean working tree before inventory or commits.
3. Resolve `lra-governance` from `LRA_GOVERNANCE_ROOT` or a sibling checkout.
4. Pin and record the target-volume and governance commits used for the run.
5. Enter plan mode before changing files.
6. Do not process more than one artifact concurrently. Review order is source
   order from the reachable `notes/<topic>/index.tex` closure.

## Formal environment inventory

Gather exactly these primary environments:

- `definition`
- `axiom`
- `theorem`
- `lemma`
- `proposition`
- `corollary`

Exclude:

- proof-file restatements such as `theorem*`;
- `remark`, `remark*`, `example`, and `restatement` environments;
- duplicated rendered text from PDFs;
- unreachable files outside the topic router closure.

For every primary environment, attach the governed support blocks that belong to
it, ending immediately before the next primary environment, section boundary, or
unattached exposition block.

Create `notes/<topic>/semantic-topic-audit.yaml` with the source-ordered queue.
The queue is governed by
`constitution/schema/topic-semantic-audit.schema.json`.

Commit the initial inventory before reviewer calls:

```text
Initialize semantic audit for <topic>
```

The committed initial manifest keeps every entry at `queued`. Per-item commit IDs
and results are written into the manifest only at topic closeout. This keeps the
working tree clean for every temporary source transaction.

## Artifact folder

For label `<prefix>:<root>`, use the direct sibling folder:

```text
notes/<topic>/<prefix>-<root>/
```

For example:

```text
notes/bounds-extremals/def-supremum/
```

The folder is audit data and must not be input by the topic router.

Each reviewed folder contains:

```text
package.yaml
artifact.yaml
corrected.tex
source.patch
validation.yaml
source-map.yaml
registry-needs.yaml
formalization-links.yaml
proof-vault-links.yaml
audit-validation.yaml
```

The first nine files are the semantic-review package. The final file records the
actual repository validation transaction and independent logic validation.

A blocked artifact may contain only `audit-validation.yaml` plus any reviewer
response needed to explain the blocker.

## Reviewer call

While remaining in plan mode, invoke the configured semantic reviewer for one
artifact only. Supply:

- exact source repository and commit;
- exact governance commit;
- source file, label, title, and environment kind;
- the complete owning environment and attached support blocks;
- minimal nearby context and one nearby compliant artifact;
- matched canonical vocabulary and signatures;
- canonical proof, Lean, Mathlib, and proof-vault candidates when present.

Use `constitution/prompts/calibrate-semantic-artifact.md` as the reviewer contract.
The reviewer must return the complete semantic-artifact package. Do not silently
repair or supplement a partial response.

If the artifact is compound or has blocking ambiguity, create its folder, record
the blocker in `audit-validation.yaml`, skip temporary source application, and
continue only when the queue entry can truthfully be marked `blocked`.

## Per-artifact commit and validation transaction

For each nonblocked artifact, execute this transaction serially.

### 1. Record the reviewer response

Write the returned package to `notes/<topic>/<label-slug>/` and validate its
schema and registry references.

Commit only the nine reviewer-package files:

```text
Record semantic review for <label>
```

Do not include `audit-validation.yaml` in this commit. Record the resulting SHA
outside the manifest until topic closeout.

### 2. Apply the reviewed TeX temporarily

Before editing, record the blob hash of every source file that will be changed.
Apply only `corrected.tex` to the selected owning environment and its attached
support blocks. Do not alter another artifact, registry, proof, figure, index, or
layout file.

Commit the temporary source replacement:

```text
Temporarily apply semantic review for <label>
```

Record the temporary commit SHA outside the manifest until topic closeout.

### 3. Run deterministic validators

Run at least:

```powershell
python <governance-root>\tools\governance\validate_semantic_artifact.py `
  --artifact <artifact-folder>\artifact.yaml `
  --package-dir <artifact-folder> `
  --governance-root <governance-root> `
  --repos-root <repos-root> `
  --strict

python <governance-root>\tools\governance\validate_volume.py `
  <target-volume-root> --fail-on-errors
```

For theorem-like artifacts, also run the strict proof-layout audit for the owning
chapter/topic. Run the normal target volume or book build.

Capture command, start/end time, exit code, source commit under test, and log path.
Raw logs may remain in ignored run output. Keep the durable structured results in
memory or ignored run state until the source revert succeeds.

### 4. Run logic validation

Invoke a second read-only reviewer call whose job is validation, not rewriting.
Use `constitution/prompts/validate-semantic-artifact-logic.md`.

It receives the original source, reviewed artifact YAML, temporarily applied TeX,
and deterministic validator results. It independently checks:

- parameter and binder declaration and scope;
- object-language versus metalanguage level;
- assumptions versus conclusions;
- definition equivalence or theorem implication shape;
- quantifier order and witness dependencies;
- mechanical negation versus approved normalized negation;
- assumptions required for every normalization;
- contrapositive correctness and usefulness when present;
- applicability failure versus actual predicate/theorem failure;
- partial-order versus total/linear-order transformations;
- predicate signatures and ambient-structure arguments;
- failure-mode exhaustiveness;
- semantic equivalence between `artifact.yaml` and the applied TeX.

The logic reviewer returns only the `logic_validation` record. It may report
`pass`, `pass_with_warnings`, `fail`, or `blocked`. It must not edit the package or
source.

### 5. Revert the temporary source commit

After all validator output is safely captured outside changed source files, revert
exactly the temporary application commit:

```text
git revert --no-edit <temporary_apply_commit>
```

Do not reset or revert the earlier reviewer-package commit.

Record the generated revert SHA. Verify every source blob changed by the temporary
commit exactly matches its pre-application hash. A mismatch is a blocking audit
failure.

### 6. Write the audit record

Only after the revert succeeds, create or finalize:

```text
notes/<topic>/<label-slug>/audit-validation.yaml
```

The file is governed by
`constitution/schema/artifact-audit-validation.schema.json` and records:

- reviewer-package validation;
- temporary application commit and changed-file hashes;
- deterministic validator/build commands and results;
- independent logic validation;
- revert commit and source-restoration evidence;
- overall result and findings.

Leave every per-item `audit-validation.yaml` uncommitted until the topic is
exhausted. When committing the next reviewer package, stage only that package's
nine review files explicitly.

### 7. Continue

Update run state outside the committed manifest, then process the next primary
environment in source order. Never send multiple artifacts in one reviewer call.

## Topic completion

After every queue item is `validated`, `failed`, or `blocked`:

1. verify no temporary source replacement remains;
2. verify the topic router and all original source blobs match the topic-start
   state except for audit folders;
3. finalize `semantic-topic-audit.yaml` with counts, per-item commits, validator
   results, and unresolved items;
4. validate every `audit-validation.yaml` and the topic manifest;
5. commit all per-artifact audit records and the finalized topic manifest together:

```text
Record semantic validation for <topic>
```

6. stop and report to the user. Do not permanently apply corrected TeX and do not
   begin another topic without a new user instruction.

The final validation commit SHA is reported in the Codex result. It is not stored
inside the same commit's manifest, because a commit cannot contain its own SHA.

## Durable branch state

At completion, the branch may contain:

- one initial inventory commit;
- one reviewer-package commit per artifact;
- one temporary-application commit and one matching revert commit per tested
  artifact;
- one final topic-validation commit.

The branch working tree must be clean. The final tree must differ from the topic
start only by the audit folders and `semantic-topic-audit.yaml`.

## Failure handling

- If package validation fails, do not apply TeX. Record `failed` and continue.
- If a source file changed since inventory, stop the topic; do not rebase the
  artifact silently.
- If a validator crashes, record the command and error as `infrastructure_error`.
- If logic validation fails, still revert the temporary source commit, record the
  failure, and continue.
- If the revert does not restore the exact source hashes, stop immediately.
- Never fix canonical registries, Lean declarations, proof-vault routes, or source
  mathematics inside this audit loop.
