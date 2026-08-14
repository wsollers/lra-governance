# LRA Governance Bootstrap

This file locates task instructions; it does not define task policy.

Locate the canonical `lra-governance` checkout from the current repository, an
adjacent sibling, `LRA_GOVERNANCE_ROOT`, or the build image. Then resolve the
user's task before doing task work:

```text
python <governance-root>/capabilities/resolve.py --repo <repo> --task "<user task>" --root <repo-root>
```

If the command succeeds, follow its output. If governance cannot be located or
the resolver exits unsuccessfully, stop and report the error.
