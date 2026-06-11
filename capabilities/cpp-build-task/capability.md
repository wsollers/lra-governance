# Capability: cpp-build-task

Repo kind: `cpp` (lra-numerical-analysis). Same author -> validate spine as the volume
capabilities, specialized to the C++/numerical companion.

## Trigger
"do task: X", "implement X", "build task X".

## What it does
1. **Do the task.** Make the requested change to the C++ project (add a solver, fix a
   routine, add a test, etc.).

2. **VERIFY (bound).** The project must still build:

       cd <cpp-root> && cmake --build build    # TODO: confirm exact build command (cmake/make)

   This is the gate -- the task is not "done" until the build is green. Add a test-suite
   run here too once the project's test command is settled.

## Notes
- Unlike the LaTeX capabilities there is no house-style validator yet; the build is the
  verifier. A linter / test gate can be added to the verify list later.
- Status: SCAFFOLD. The build verifier is wired; exact build/test commands are TODO.
