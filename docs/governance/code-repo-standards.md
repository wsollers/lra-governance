# Code Repository Standards

These standards apply to specialist code repositories governed by
`capabilities/overlays-config.yaml`. They are enforced by
`tools/governance/validate_code_repo_layout.py`, which runs through the shared
`build-repo` path before repo build/test gates.

## Common Rule

Code layout is declared in governance, not inferred from the current directory
shape. A repository may have domain-specific folders, but executable validation
must come from its configured layout and success gates. Do not decide that a
repo is valid merely because it has, or lacks, `scripts/`, `tools/`, `src/`, or
`projects/`.

## Python Tool Repos

Python specialist repos use repo kind `python_tool`.

The shared target structure is:

```text
src/<package>/        importable Python package code
tools/                command-line wrappers and operator helpers
tests/                pytest tests
docs/ or workflows/   local operator documentation when needed
```

Existing script-heavy repos may keep `scripts/` as a declared code root while
they migrate toward the target shape. New shared implementation modules should
prefer `src/<package>/`; new thin command entrypoints may live in `tools/` or a
configured legacy `scripts/` directory. Tests belong under `tests/`.

Root-level Python files are not part of the standard layout. If a root-level
script is genuinely required, add an explicit governance exception rather than
letting it appear incidentally.

## C And C++ Repos

C/C++ specialist repos use repo kind `cpp`.

The shared contract is:

```text
CMakeLists.txt        root build entrypoint
cmake/                CMake helper modules
docker/               portable build images or wrappers
tools/                local build, validation, and developer helpers
src/                  application or library implementation code
include/              public headers for reusable libraries
tests/                repo-level tests, when used
projects/<name>/      self-contained lab/project trees
projects/<name>/src/  project-local implementation code
projects/<name>/tests/ project-local tests
```

A C++ repo may use root `src/` plus root `tests/`, or project-local
`projects/<name>/src` plus `projects/<name>/tests`. Reusable library headers
belong under `include/`. Build products, generated IDE trees, scratch outputs,
and transient runtime state are never architecture.

## Style

Code should match the existing LRA engineering style:

- small, explicit modules with clear ownership;
- typed, value-oriented APIs;
- no hidden global state unless a platform boundary requires it;
- no broad abstractions before two real callers exist;
- deterministic tests for changed behavior;
- generated artifacts kept separate from source and committed only when they are
  curated project inputs.

For C++, prefer modern C++23, RAII ownership, scoped enums, `std::span`,
`std::optional`, `std::expected`, `std::string_view`, and `[[nodiscard]]` when
they clarify contracts. Keep numerical kernels testable without UI or renderer
startup.

For Python, keep importable logic separate from operator entrypoints. Use
standard-library parsing and structured data APIs where available. Avoid
side-effect-heavy imports, hidden network calls, and unreviewed mutation of
files outside the owning repo.
