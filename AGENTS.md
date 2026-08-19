# LRA Governance Bootstrap

This file locates task instructions; it does not define task policy.

Locate the canonical `lra-governance` checkout from the current repository, an
adjacent sibling, `LRA_GOVERNANCE_ROOT`, or the build image. Then resolve the
user's task before doing task work:

```text
python <governance-root>/scripts/govpy.py capabilities/resolve.py --repo <repo> --task "<user task>" --root <repo-root>
```

If the command succeeds, follow its output. If it prints a route catalog
instead (exit code 2), pick the route whose description matches the task's
intent and re-run with `--route <id>` added; `--list` shows the catalog at any
time. If governance cannot be located or the resolver fails otherwise, stop
and report the error.
