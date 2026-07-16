# Capability: cpp-build-task

Repo kind: `cpp` (`lra-numerical-analysis`).

## Action

Implement one requested C++/numerical change.

## Inputs

- User task.
- Repo overlay.
- Relevant source and test files found from local project structure.

## Do

1. Follow the repo overlay for placement, build environment, and test policy.
2. Make the smallest project-consistent code change.
3. Add or update tests when the repo has a nearby test pattern.
4. Preserve the shared C/C++ layout and style rules in
   `docs/governance/code-repo-standards.md`.

## Success Gates

Run the code layout validator before build gates:

```text
python <governance-root>/tools/governance/validate_code_repo_layout.py --root <repo-root> --repo <repo-name> --governance-root <governance-root>
```

Run the success gates listed in the repo overlay. On Windows/MSVC repos, run
CMake from the MSVC x64 developer environment or a repo script that enters it.

## Reference Escalation

Prefer local source, tests, build scripts, and the repo overlay. If repository
structure or generated-file ownership is still unclear, open
`capabilities/reference-index.md` and use only the C++ or cross-repo row needed
for the issue.

Stop if the build environment is unavailable or any gate fails.
