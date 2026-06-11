# Repo Overlay -- lra-nurbs

Repo identity: NURBS / numerical geometry.

C++ / numerical companion.

Build environment: MSVC x64 developer environment. Run the success gates from this environment.

Success gates:
- `cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build`
- `ctest --test-dir build --output-on-failure`

Capabilities (domain-specific to this repo; same author -> validate spine as the volumes):
- cpp-build-task: do the requested task and run the success gates below.

Capabilities here are scoped to repo kind `cpp` in the manifest, so volume LaTeX
capabilities will NOT resolve in this repo (and vice versa).
