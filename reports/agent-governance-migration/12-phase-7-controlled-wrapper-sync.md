# Phase 7: Controlled Wrapper Sync Pilot

## Reason

Phase 7 adds the controlled sync path needed after preview generation, preview
review, and drift reporting. The new tool can plan or, in a later approved task,
copy generated agent wrappers into selected downstream repos.

## Guarded Write Mode

Write mode is guarded because generated wrappers are full-replace files in
downstream repositories. The tool defaults to dry-run, requires explicit
`--repo` selection, refuses dirty target repos, refuses non-`main` target
branches unless explicitly allowed, and writes only the five expected generated
wrapper files.

The tool does not stage, commit, or push downstream repos.

## Pilot Repo

The planned first pilot target is `lra-numerical-analysis`. It is specialized,
new, comparatively low-risk, and not a mathematical volume repo.

## This PR Does Not Write Downstream

This PR adds the guarded tool and runs only a dry-run sync plan. No downstream
files are written, staged, committed, or pushed.

## Test Commands

```powershell
python tools/governance/generate_agent_wrappers.py --dry-run --out reports/generated-agent-wrapper-preview
python tools/governance/validate_repo_rules.py --preview reports/generated-agent-wrapper-preview
python tools/governance/report_wrapper_drift.py --root F:\repos --preview reports/generated-agent-wrapper-preview --out reports/wrapper-drift
python tools/governance/sync_agent_wrappers.py --root F:\repos --preview reports/generated-agent-wrapper-preview --repo lra-numerical-analysis --dry-run --out reports/wrapper-sync-pilot
```

## Next Recommended Task

After this PR is reviewed and merged, perform an explicitly authorized
one-repo write pilot for `lra-numerical-analysis`, inspect the downstream diff,
and open or prepare the downstream review path separately.

