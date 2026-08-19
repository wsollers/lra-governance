# Repo Overlay -- lra-nurbs

Repo identity: NURBS / numerical geometry.

C++ / numerical companion.

Build environment: CI matrix of Windows x64 MSVC + Vulkan SDK and Linux Clang via docker/linux-clang.Dockerfile; the Docker gates below are the portable path when MSVC is unavailable, with Release matching CI. Run the success gates from this environment.

Layout gate:
- `python tools/governance/validate_code_repo_layout.py --root <repo-root> --repo lra-nurbs --governance-root <lra-governance>`

Success gates:
- `docker build -t lra-nurbs-linux -f docker/linux-clang.Dockerfile .`
- `docker run --rm -v "$PWD:/workspace" -w /workspace lra-nurbs-linux bash -lc 'cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-18 -DCMAKE_CXX_COMPILER=clang++-18 -DCMAKE_CXX_FLAGS="-stdlib=libc++ -fexperimental-library" -DCMAKE_EXE_LINKER_FLAGS="-stdlib=libc++ -fexperimental-library" -DENABLE_SANITIZERS=OFF -DNDDE_ENABLE_CLANG_TIDY=OFF && cmake --build build --parallel && ctest --test-dir build --output-on-failure --parallel 4'`

Capabilities (domain-specific to this repo; same author -> validate spine as the volumes):
- cpp-build-task: do the requested task and run the success gates below.

Capabilities here are scoped to repo kind `cpp` in the manifest, so volume LaTeX
capabilities will NOT resolve in this repo (and vice versa).
