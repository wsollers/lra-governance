# Capability: author-lean-theorem

Repo kind: `lean` (`lra-lean`).

## Action

Add or change one Lean theorem or proof in the Lean project.

## Inputs

- Informal claim or existing theorem reference.
- Repo overlay.
- Relevant Lean file/namespace found from local project structure.

## Do

1. Follow the repo overlay for placement, naming, and allowed proof state.
2. Use the existing file and namespace patterns near the target.
3. Add the theorem with a descriptive name consistent with nearby code.
4. Prefer a complete proof. Use `sorry` only if the repo already permits it for
   comparable work or the user explicitly asks for a stub.

## Success Gates

Run the success gates listed in the repo overlay.

Stop if placement cannot be inferred from local structure or any gate fails.
