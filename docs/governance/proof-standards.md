# Proof Standards

The enforced shape authority is `constitution/schema/file-schema.yaml`
(`proof_file.required_layers_in_order`), checked by
`tools/governance/validate_volume.py`. This document is the human-readable
companion and carries the canonical copy-paste template.

## Proof Ownership

No proof file may be created for a statement unless the corresponding statement
label already exists in the notes file.

Leaf volume repositories own theorem and proof source files and build
independently. There is no assembled monorepo.

Handwritten proof artifacts, reviewed handwritten proof attempts, and
proof-vault backlinks are governed by `handwritten-proof-vault-standards.md`.
The proof vault is archival support only; canonical proof content remains in
the volume repositories.

## Theorem Proof-Stub Invariant

Every top-level `theorem`, `proposition`, `lemma`, and `corollary` in a leaf
repo `notes/**/*.tex` file that is expected to have a proof must have a
compile-safe proof stub in that leaf repo's `proofs/**/*.tex` tree at creation
time.

Definitions and axioms are stable knowledge nodes, but they are not proof
obligations unless explicitly marked by a local workflow or governance task.
Local claims inside proof files do not create proof-stub obligations.

Note files may contain `derivationbox` passages for pedagogical calculations
and proof-like teaching, but those passages are not canonical proofs and do not
satisfy proof-stub obligations. A note file must not contain a `proof`
environment. When a theorem-like statement is expected to have a proof, create
or update the corresponding `proofs/**/*.tex` proof file.

The proof-to-theorem association is the source-visible macro:

```latex
\LRAProofFor{thm:example-label}
```

`lra-common` owns this macro. It is render-inert and exists for validators and
knowledge extraction. Proof files should not rely on title or path inference as
the primary theorem association.

## Proof File Structure

Proof files live under the owning chapter's `proofs/{topic}/` tree and use
lowercase, hyphen-separated ASCII filenames of the form `prf-<theorem-root>.tex`.

There is exactly one authority for the proof-file shape, and it is enforced:
`proof_file.required_layers_in_order` in `constitution/schema/file-schema.yaml`,
checked by `tools/governance/validate_volume.py`. The same schema defines folder
architecture, topic matching, and index reachability (mirrored in
`docs/governance/volume-structure.schema.json`). Use
`tools/governance/audit_proof_layout.py` for compliant/non-compliant proof-file
lists.

Do not paraphrase, reorder, abbreviate, or "improve" this shape from memory. If a
generated stub does not match the template below layer-for-layer, it is wrong
even if it looks reasonable.

The required layers, in order, are exactly twelve:

1. `\newpage`
2. `\phantomsection`
3. `\label{prf:<theorem-root>}`
4. `\LRAProofFor{<theorem-label>}`
5. return-navigation `remark*` titled `Return`
6. optional `\ProofVaultURL{...}` (only for memorialized handwritten proofs)
7. unnumbered `theorem*` restatement (no `\label` inside)
8. `proof` titled `Professional Standard Proof`
9. `proof` titled `Detailed Learning Proof`
10. `remark*` titled `Proof structure`
11. `dependencies` environment with `\hyperref` links
12. `\clearpage`

A full proof and a proof stub use the **same twelve layers in the same order**.
The only difference is content: a stub keeps TODO-safe placeholders in the
restatement, both proof bodies, the proof-structure remark, and the dependency
block, and both proof bodies must still be present.

## Canonical Proof-Stub Template

Copy this verbatim and substitute only the angle-bracketed parts. It is a real,
validator-passing stub shape and is the source of truth for "generate a proof
stub" tasks.

```latex
\newpage
\phantomsection
\label{prf:<theorem-root>}
\LRAProofFor{thm:<theorem-root>}

\begin{remark*}[Return]
\hyperref[thm:<theorem-root>]{Return to Theorem}
\end{remark*}

\begin{theorem*}[<Theorem Display Title>]
<verbatim restatement of the theorem-like statement; no \label here>
\end{theorem*}

\begin{proof}[Professional Standard Proof]
\LRAProofBodyStart
TODO: professional standard proof for <theorem-root>.
\end{proof}

\begin{proof}[Detailed Learning Proof]
\LRAProofBodyStart
TODO: detailed learning proof for <theorem-root>.
\end{proof}

\begin{remark*}[Proof structure]
\end{remark*}

\begin{dependencies}
\begin{itemize}
  \item \hyperref[<dep-label>]{<Readable Dependency Name>}
\end{itemize}
\end{dependencies}

\clearpage
```

Things that are easy to get wrong, and are non-negotiable:

- The proof label root, the `\LRAProofFor{...}` argument, and the `Return`
  hyperref all share the same `<theorem-root>`. The proof label uses `prf:`; the
  theorem references use the statement's actual prefix
  (`thm:`/`lem:`/`prop:`/`cor:`).
- Each proof body opens with `\LRAProofBodyStart` on its own line, before the
  `TODO` line. This macro is required and is easy to omit.
- The `Proof structure` remark is present but **empty** in a stub.
- Include `\ProofVaultURL{...}` (layer 6) only for proofs memorialized from a
  handwritten artifact; otherwise omit it. When present it sits immediately
  after the `Return` remark and before the `theorem*` restatement and points to
  the sanitized record, never a raw image.
- Every dependency item targets a mathematical statement label
  (`def:`/`ax:`/`thm:`/`lem:`/`prop:`/`cor:`), never a `prf:` label. If the
  target is not yet formalized, write a `TODO` dependency line instead of
  inventing a label.

For a full (non-stub) proof, replace each `TODO` body with real content: the
professional body is compact and rigorous; the detailed body teaches the same
proof using inline bold step headings only (`\textbf{Step 1.} ...`) with no step
macros and no flash macros.

## Proof Stub Durability

Proof stubs are durable canonical containers. Later proof population modifies the
existing proof file in place and preserves the proof label, `\LRAProofFor{...}`,
return navigation, any `\ProofVaultURL{...}`, the theorem restatement, the
proof-structure remark, the dependency block, and extraction metadata, unless an
explicit refactor task says otherwise.

If a theorem-like statement changes while its proof file is still a stub, the
proof restatement must be synchronized to the theorem source. A proof is still a
stub when both proof bodies remain TODO/reset placeholders. In that case, replace
only the unnumbered theorem/proposition/lemma/corollary restatement inside the
proof file with the current theorem statement, preserving every other proof-file
layer. This automatic synchronization is not allowed for authored proofs; once a
proof body has real content, a restatement disagreement is a blocking review
issue rather than an automatic overwrite.

## Two-Layer Proof Rule

The professional proof is compact and rigorous. The detailed learning proof
teaches the same proof with explicit step structure. Explanationless proof mode
is opt-in only and does not waive notation, label, dependency, or architecture
rules.

Proofs generated from handwritten proof images must still be converted into the
full two-layer proof-file format. The handwritten proof may inform the
professional and detailed layers, but it must not replace the required
structure with a single transcription block.

## Label Rule

Proof labels use `prf:` and align with the theorem label root. Proof files must
not put `\label{...}` inside theorem environments; proof labels sit at proof
file level according to the current compatibility rule.

## Dependency Rule

Dependency remarks record mathematical dependencies, not proof-file
dependencies.

A dependency item must target a mathematical statement label such as `def:`,
`ax:`, `thm:`, `lem:`, `prop:`, or `cor:`.

Dependency items should be human-readable in the PDF and machine-readable for
extraction. The preferred form is:

```latex
\begin{dependencies}
\begin{itemize}
  \item \hyperref[def:supremum]{Supremum}
  \item \hyperref[ax:least-upper-bound-property]{Least Upper Bound Property}
  \item \hyperref[thm:epsilon-characterization-of-supremum]{Epsilon Characterization of Supremum}
\end{itemize}
\end{dependencies}
```

The machine-readable dependency target is the label inside the `\hyperref[...]`
brackets.

Use the shared `dependencies` environment for dependency blocks. Do not write
dependency blocks as raw `remark*` environments with a `Dependencies` title;
that bypasses the shared alignment rule used by volume builds.

Proof labels such as `prf:` identify proof files or proof locations. They may
be used for theorem-proof navigation and theorem-proof association, but they
must not appear as mathematical dependency targets.

If a dependency cannot be linked because the target statement has not yet been
formalized, write a TODO dependency note rather than inventing a label.
