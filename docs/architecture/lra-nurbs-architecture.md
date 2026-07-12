# lra-nurbs Architecture

`lra-nurbs` is the standalone C++23 / Vulkan / geometry / simulation workspace.
It owns rendering, geometry kernels, simulation runtime services, numerical
kernels used by the NURBS application, shaders, CMake configuration, tests, and
local design notes.

## Workspace Layout

```text
CMakeLists.txt         root CMake project and FetchContent dependencies
cmake/                 local CMake helper modules
docker/                portable Linux Clang build image
docs/                  local design notes and service architecture
assets/                runtime assets such as fonts or sample resources
shaders/               GLSL shaders compiled by the build
src/                   production C++ source
tests/                 GoogleTest and policy tests
tools/                 local helper scripts
engine_config.json     runtime configuration copied into builds
```

Generated build directories, local UI state such as `imgui.ini`, and transient
prototype outputs are not architecture. Keep generated artifacts out of source
unless a task explicitly promotes them to curated design material.

## Source Architecture

Production source is organized by domain boundary under the `ndde` namespace:

```text
src/app/          application composition and user-facing panels
src/engine/       runtime services and cross-service coordination
src/math/         geometry, surfaces, integration, and mathematical kernels
src/memory/       Vulkan memory helpers and allocation services
src/numeric/      low-level numerical utilities
src/platform/     GLFW, Vulkan instance/device, and platform bindings
src/renderer/     rendering, swapchain, text overlay, and frame submission
src/sim/          simulation implementations
src/simulation/   simulation metadata, events, and state contracts
src/telemetry/    telemetry records and writers
src/units/        quantity and unit integration
```

Math and simulation kernels should not depend on renderer, platform, ImGui, or
Vulkan UI layers. Rendering and platform code may depend on math, simulation
snapshots, resources, and engine services through explicit interfaces.

## Build Architecture

CI has three independent jobs:

- Windows MSVC build and CTest using Ninja from a Visual Studio developer
  environment.
- Linux Clang build and CTest inside `docker/linux-clang.Dockerfile`.
- Native Linux CodeQL build so GitHub can trace C++ compilation.

The Linux container is the portable non-MSVC build path. It uses Clang 18,
libc++, and the project C++23 feature set.

## Design Policy

Agent-facing C++ / Vulkan / geometry / simulation implementation standards live
in `docs/governance/repo-overlays/lra-nurbs.md`. This architecture document
records ownership, layout, service boundaries, and build architecture.
