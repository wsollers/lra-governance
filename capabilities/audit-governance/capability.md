# Governance Audit Workflow

Use this workflow when auditing governance bloat, authority leakage, task
routing, prompt size, or duplicate rule descriptions.

## Scope

Read the full governance corpus only when the user explicitly asks for a
governance audit or consolidation task. Ordinary implementation tasks should
start with `AGENTS.md` and the route resolver; the generated
`capabilities/task-index.md` is a lazy human reference and is not preloaded.

Do not create a new governance document unless no existing authority layer can
reasonably own the content.

## Checklist

1. Confirm `AGENTS.md` remains short and router-like.
2. Confirm `capabilities/manifest.yaml` is the only route authority and the
   generated task index is current.
3. Confirm each route separates eager instructions, lazy references,
   executable tools, schemas/data, and examples, and stays within budget.
4. Confirm constitution files answer what is valid, not repository layout or
   workflow procedure.
5. Confirm architecture docs own repo maps, volume maps, folder layout,
   integration topology, build boundaries, and generated-file ownership.
6. Confirm governance docs state authored-content rules without duplicating
   detailed workflow steps.
7. Confirm workflow docs state how to perform a task and point to canonical
   standards/schema for the rules.
8. Confirm repo overlays add local constraints without forking global rules.
9. Confirm prompts consume schema/data files instead of embedding large copied
   rule lists when the rule is machine-readable.
10. Confirm downstream repos resolve governance from `lra-governance` (a sibling
   checkout, `LRA_GOVERNANCE_ROOT`, or the build image) rather than carrying
   canonical copies; there are no synced governance copies by design.
11. Confirm machine-checkable rules are represented in existing schema/data
    files before proposing a new schema system.
12. When any file under `constitution/schema/` changes, update or explicitly
    audit the deterministic validators that enforce it in the same change.
    For volume, chapter, file, block, or artifact-matrix rules, update the
    relevant `tools/governance/validate_volume.py` module or document why the
    requirement is delegated to another deterministic validator.

## Mechanical Checks

Run the checks that are available for the audit target. Typical checks include:

```sh
python capabilities/generate_task_index.py --check
python tools/governance/audit_governance_context.py
python -m py_compile tools/governance/audit_proof_layout.py tools/governance/audit_volume_layout.py tools/governance/validate_volume.py
```

If schema files changed, also run the integrated validator against an affected
leaf volume:

```sh
python tools/governance/validate_volume.py <target-repo> --fail-on-errors
```

```sh
python - <<'PY'
from pathlib import Path
import json
import yaml

for path in Path("constitution/schema").glob("*.yaml"):
    yaml.safe_load(path.read_text(encoding="utf-8"))
json.loads(Path("constitution/schemas/audit-report.json").read_text(encoding="utf-8"))
print("schema parse: PASS")
PY
```

Use grep-based checks for repeated headings, repeated key phrases, and stale
path references when no dedicated validator exists. Do not claim full link or
markdown validation unless such a checker actually ran.

## Report

Report:

- authority leaks found,
- duplicated rules and their proposed canonical home,
- misplaced architecture/workflow/governance material,
- schema/data extraction candidates,
- task routes that need tightening,
- validation commands run,
- downstream generated wrappers that need regeneration.
