# Repo Overlay -- lra-nurbs

Repo identity: NURBS / numerical geometry.

C++ / Vulkan / geometry / simulation codebase: C++ and CMake build rules,
Vulkan rendering, geometry and NURBS implementation, simulation and DDE
implementation, and local validators/CI expectations. These rules apply only
here and must not be injected into volume content instructions.

## Implementation Standards

Keep new C++ modern, typed, and explicit: prefer scoped enums, value types,
RAII ownership, `std::span`, `std::optional`, `std::expected`,
`std::string_view`, and `[[nodiscard]]` where they clarify contracts. Avoid
raw ownership, hidden global state, and stringly typed protocols unless a
boundary API requires them.

Follow the architecture visible in the source tree: domain code under the
appropriate `ndde` namespace, rendering/platform concerns separated from math
and simulation kernels, and reusable abstractions promoted only once they
have a clear caller. Names describe the domain concept or service
responsibility, not implementation mechanics.

Never break encapsulation or straddle established design isolation points to
complete a change. If an implementation appears to require engine code to own
app-specific behavior, rendering/platform code to absorb domain logic,
math/simulation kernels to depend on UI or renderer services, or any other
boundary-crossing shortcut, stop and ask for design discussion before
editing. Keep `Engine` focused on reusable orchestration; scene-specific
behavior goes behind explicit app/domain abstractions.

Keep the C++ Core Guidelines in mind (ownership, lifetime, copy/move,
slicing, explicit contracts). The local clang-tidy configuration checks
selected `cppcoreguidelines-*` rules; do not work around those warnings
without documenting the reason in code or tests.

## Layout

- C++ production code under `src/` by domain boundary; tests under `tests/`
  exercising kernels/services without an interactive renderer where possible.
- GLSL shaders under `shaders/`; CMake helpers under `cmake/`; portable Linux
  build definitions under `docker/`; tools and one-off helpers under
  `tools/`; curated design notes under `docs/`.
- Do not commit generated build trees, transient runtime UI state, or scratch
  artifacts.

Layout gate:

- `python tools/governance/validate_code_repo_layout.py --root <repo-root> --repo lra-nurbs --governance-root <lra-governance>`

## Success gates

CI uses a build matrix: Windows x64 with MSVC + Vulkan SDK + CMake/CTest, and
Linux x64 with Clang inside `docker/linux-clang.Dockerfile`. The Linux
container build is the portable path when MSVC is unavailable; Release
matches CI. CodeQL runs as a separate native Linux job.

- `docker build -t lra-nurbs-linux -f docker/linux-clang.Dockerfile .`
- `docker run --rm -v "$PWD:/workspace" -w /workspace lra-nurbs-linux bash -lc 'cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-18 -DCMAKE_CXX_COMPILER=clang++-18 -DCMAKE_CXX_FLAGS="-stdlib=libc++ -fexperimental-library" -DCMAKE_EXE_LINKER_FLAGS="-stdlib=libc++ -fexperimental-library" -DENABLE_SANITIZERS=OFF -DNDDE_ENABLE_CLANG_TIDY=OFF && cmake --build build --parallel && ctest --test-dir build --output-on-failure --parallel 4'`
