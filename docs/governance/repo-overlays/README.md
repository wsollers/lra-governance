# Repo Overlays

Repo overlays are additive rule layers. They clarify how global governance
applies to one repository or repository class.

They must not become divergent forks of global rules.

Specialist rule placement:

- Lean-specific rules belong only in `lra-lean.md`.
- C++ / Vulkan / simulation rules belong only in `lra-nurbs.md`.
- Numerical-analysis / benchmark / plotting rules belong only in
  `lra-numerical-analysis.md`.
- Volume repos receive only volume-content guidance.

Each generated downstream wrapper should combine the global rules with exactly
the matching overlay. Overlays should link to local README or workflow files
for operational details instead of copying large local technical manuals.
