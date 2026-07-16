# Repo Overlay -- lra-numerical-analysis

Repo identity: C++ / numerical companion.

C++ / numerical companion.

Build environment: MSVC x64 developer environment. Run the success gates from this environment.

Layout gate:
- `python tools/governance/validate_code_repo_layout.py --root <repo-root> --repo lra-numerical-analysis --governance-root <lra-governance>`

Success gates:
- `powershell -ExecutionPolicy Bypass -File tools\build-msvc.ps1 -Configuration Debug`

Capabilities (domain-specific to this repo; same author -> validate spine as the volumes):
- cpp-build-task: do the requested task and run the success gates below.

Capabilities here are scoped to repo kind `cpp` in the manifest, so volume LaTeX
capabilities will NOT resolve in this repo (and vice versa).
