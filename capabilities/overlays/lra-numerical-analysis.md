# Repo Overlay -- lra-numerical-analysis

Repo identity: C++ / numerical companion.

Numerical-analysis software workbench: numerical methods, computational C++
experiments, project-local tests/benchmarks/fuzzing, plotting and Python
analysis, and LaTeX-ready numerical reports. These rules apply only here and
must not be injected into volume content instructions. This repo does not own
Lean formalization, NURBS/Vulkan simulation, or shared LaTeX infrastructure.

## Workspace Shape

C++23 numerical software laboratory:

```text
include/lra/numeric/        shared numerical library headers
src/numeric/                shared numerical library implementations
projects/<name>/            self-contained lab projects
analysis/                   Python analysis scripts and notes
docker/                     portable Clang and analysis images
tools/                      local build helpers
artifacts/                  generated data, plots, and reports
```

Each `projects/<name>/` is self-contained, with its own `CMakeLists.txt`,
`src/`, `tests/`, `benchmarks/`, `fuzz/`, and `README.md`. Shared reusable
numerical code belongs in `include/lra/numeric/` and `src/numeric/`; do not
promote project-specific experiments into the shared library until at least
two projects need the abstraction.

## Unit-Test Project Workflow

For a unit-test-only project, follow the existing `hello-unit` pattern unless
nearby files establish a newer convention:

1. Create `projects/<name>/` and `projects/<name>/tests/`.
2. Project `CMakeLists.txt` does `add_subdirectory(tests)`; the tests
   `CMakeLists.txt` defines one GoogleTest executable target.
3. Name the initial test source `<name>-test.cpp` unless nearby examples use
   `test_<name>.cpp`.
4. Link the test target to `lra::numeric` and `GTest::gtest_main`; apply
   `lra_configure_target` and `lra_enable_sanitizers` when available;
   register with `gtest_discover_tests`.
5. Add `add_subdirectory(projects/<name>)` to the root `CMakeLists.txt`.
6. Start with a compile-safe smoke test; build and run CTest before
   reporting completion.

Public reusable headers go under `include/lra/numeric/`; keep test fixtures
project-local until at least two projects need them.

## Dependency Boundaries

Core numerical code must not depend on Vulkan, ImGui, GLFW, or UI code.
Visual lab projects may use them, but below the project/application boundary.
Tests, benchmarks, fuzz targets, and Python analysis must be able to exercise
the shared numerical core without launching a graphical application.

## Validation Expectations

New numerical algorithms require tests; benchmark and fuzz coverage scale
with risk: floating-point representation, rounding, interval arithmetic, and
error-bound code should have unit tests plus focused fuzz/property tests;
performance-sensitive algorithms get project-local Google Benchmark targets;
visualization projects keep numerical correctness tests separate from
Vulkan/ImGui smoke tests.

Layout gate:

- `python tools/governance/validate_code_repo_layout.py --root <repo-root> --repo lra-numerical-analysis --governance-root <lra-governance>`

## Success gates

Both platform gates must be green before push: MSVC validates the Windows
Visual Studio toolchain; the Docker gate validates the Linux Clang/Ninja
toolchain and runs CTest inside the container.

- `powershell -ExecutionPolicy Bypass -File tools\build-msvc.ps1`
- `powershell -ExecutionPolicy Bypass -File tools\build-docker-clang.ps1`

Run MSVC commands from a Visual Studio developer environment
(`build-msvc.ps1` initializes `vcvars64.bat`); plain PowerShell is not a
valid substitute. If Docker fails with an engine pipe error such as
`open //./pipe/dockerDesktopLinuxEngine`, start Docker Desktop, wait for the
engine, and rerun the gate.

## Artifact And Analysis Flow

C++ projects write structured artifacts (JSON/CSV) under
`artifacts/<project>/`; Python analysis consumes them to produce plots,
tables, and reports. The analysis Docker image is the portable environment
for NumPy/SciPy/pandas/matplotlib/seaborn/notebooks; ordinary C++ unit-test
builds must not require it. Small curated plots may be committed as
curriculum inputs; large benchmark outputs, scratch data, and transient fuzz
corpora stay untracked unless explicitly promoted.
