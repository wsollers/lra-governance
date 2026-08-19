# Capability: build-repo

Build or validate the current repository.

## Trigger

Requests to build, validate, or check a repository, run CI-equivalent gates,
or dispatch/monitor build workflows.

## Procedure

1. The resolver has already loaded this repository's overlay. Its
   `Success gates` section is the authoritative gate list; run those commands
   from the repository root in the listed order.
2. For repos with a layout gate, run
   `python tools/governance/validate_code_repo_layout.py --root <repo-root>
   --repo <repo> --governance-root <lra-governance>` before the build gates.
3. Volume repos: governance validation
   (`python <governance-root>/tools/governance/validate_volume.py <root>
   --fail-on-errors`) plus the repo's independent volume/book build wrapper.
   Never build volumes with raw `latexmk`.
4. Governance repo: run the resolver tests and focused validator tests named
   in the overlay; do not substitute LaTeX render checks for governance tests.
5. Report each gate's outcome explicitly. A skipped gate must be named as
   skipped with the reason; success may be reported only when every required
   gate passed.

## Environment notes

- Gates that name PowerShell scripts require a Windows environment; the
  overlay lists a Docker alternative when one exists. If neither can run in
  the current environment, stop and report the blocking gate rather than
  inventing a substitute.
- Docker engine unavailability (for example the Docker Desktop pipe error on
  Windows) is a blocking condition to report, not a reason to skip the gate.
