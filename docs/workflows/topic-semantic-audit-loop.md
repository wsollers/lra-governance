# Topic Semantic Audit Loop

## Goal

Audit every formal environment in one notes topic without leaving the reviewed
LaTeX applied to the book source. The durable output is the reviewer package and
validation evidence. Each candidate source replacement is committed, validated,
and then reverted before the next artifact.

This is an audit and calibration workflow. It is not the permanent source-update
workflow in `semantic-artifact-calibration.md`.

## Mobile command

From the target volume repository, the user may invoke the whole workflow with:

```text
LRA audit topic <topic>
```

The topic is the repository topic identifier under `notes/<topic>/`, not a PDF
heading guessed from rendered output.

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

Each folder contains:

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
logic-validation.yaml
execution-validation.yaml
```

The first eight files are the semantic-review package. The final two are produced
by the repository audit loop.

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

If the artifact is compound or has blocking ambiguity, record the blocker in the
artifact folder and skip temporary source application. Continue only when the
queue entry can truthfully be marked `blocked`.

## Per-artifact commit and validation transaction

For each nonblocked artifact, execute this transaction serially.

### 1. Record the reviewer response

Write the returned package to `notes/<topic>/<label-slug>/` and validate its
schema and registry references.

Commit only that reviewer package:

```text
Record semantic review for <label>
```

Record the commit as `review_commit` in the queue entry.

### 2. Apply the reviewed TeX temporarily

Before editing, record the blob hash of every source file that will be changed.
Apply only `corrected.tex` to the selected owning environment and its attached
support blocks. Do not alter another artifact, registry, proof, figure, index, or
layout file.

Commit the temporary source replacement:

```text
Temporarily apply semantic review for <label>
```

Record the commit as `temporary_apply_commit`.

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
Raw logs may remain in ignored run output; durable results go in
`execution-validation.yaml`.

### 4. Run logic validation

Invoke a second read-only reviewer call whose job is validation, not rewriting.
It receives the original source, reviewed artifact YAML, temporarily applied TeX,
and deterministic validator results.

The logic validator must independently check:

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

Write `logic-validation.yaml`. The validator may return `pass`,
`pass_with_warnings`, `fail`, or `blocked`. It must not edit the package or source.

### 5. Revert the temporary source commit

After all validator output is safely captured outside changed source files, revert
exactly the temporary application commit:

```text
git revert --no-edit <temporary_apply_commit>
```

Do not reset or revert the earlier reviewer-package commit.

Record the generated revert commit as `revert_commit`.

Verify all source blobs changed by the temporary commit exactly match their
pre-application hashes. A mismatch is a blocking audit failure.

Only after the revert succeeds, write or finalize `execution-validation.yaml` and
`logic-validation.yaml` in the artifact folder. Leave those validation files
uncommitted until the topic is exhausted.

### 6. Continue

Update the in-memory and working-copy queue entry, then process the next primary
environment in source order. Never send multiple artifacts in one reviewer call.

## Topic completion

After every queue item is `validated`, `failed`, or `blocked`:

1. verify no temporary source replacement remains;
2. verify the topic router and all original source blobs match the topic-start
   state except for audit folders;
3. finalize `semantic-topic-audit.yaml` with counts, commits, validator results,
   and unresolved items;
4. validate the topic audit manifest;
5. commit all per-artifact validation files and the topic manifest together:

```text
Record semantic validation for <topic>
```

6. stop and report to the user. Do not permanently apply corrected TeX and do not
   begin another topic without a new user instruction.

## Durable branch state

At completion, the branch may contain:

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
