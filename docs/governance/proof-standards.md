# Proof Standards

Source sections: `DESIGN.md` sections 8, 9, 10.4, 14, and proof lifecycle
rules after section 14.

## Proof Ownership

No proof file may be created for a statement unless the corresponding statement
label already exists in the notes file.

## Proof File Structure

Proof files live under the owning chapter's `proofs/` tree and use lowercase,
hyphen-separated ASCII filenames. Each notes proof file begins on a new page.

A full proof file contains:

1. proof-level label,
2. unnumbered theorem-like restatement,
3. theorem-side navigation link when applicable,
4. professional standard proof,
5. detailed learning proof,
6. proof structure remark,
7. dependencies remark.

## Two-Layer Proof Rule

The professional proof is compact and rigorous. The detailed learning proof
teaches the same proof with explicit step structure. Explanationless proof mode
is opt-in only and does not waive notation, label, dependency, or architecture
rules.

## Label Rule

Proof labels use `prf:` and align with the theorem label root. Proof files must
not put `\label{...}` inside theorem environments; proof labels sit at proof
file level according to the current compatibility rule.

## Dependency Rule

Dependency remarks list mathematical dependencies, not proof labels. They are
extraction infrastructure and should use stable `\hyperref` links.
