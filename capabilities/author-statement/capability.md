# Capability: author-statement

## Trigger
Author a definition, axiom, theorem, lemma, proposition, or corollary
("define X", "generate the lemma ...", "append the theorem ... to <file>",
"generate the latex for ...").

## Composition
global core (`ENTRYPOINT.md`) + `overlays/<repo>.md` + this capability + bound verifier.

## Two output modes (the caller chooses by how they ask)
- **Append mode** -- "append the definition of X to `cauchy-sequences.tex`": write the decorated
  block to the END of the named file. Easy and verifiable; the bound verifier runs on the file.
- **Return mode** -- "generate the latex for X": produce the identical decorated block and return it
  to the caller (for manual insertion anywhere, including mid-file). The verifier runs on the block
  in isolation. NOTE: mid-file insertion is the caller's responsibility; after pasting, re-run the
  file validator on the destination to confirm it landed clean. This capability does not insert mid-file.

## Statement source (three-way; chrome is always deterministic)
- **Verbatim** -- pasted LaTeX, `lra-pdf-extractor` output, or an image transcription: reproduce the
  statement EXACTLY. Never paraphrase or "improve" a provided statement.
- **Composed** -- author the statement from a description.
The box wrapper, label, and decoration scaffolding are deterministic in all cases; only the
decoration *content* (quantified form, interpretation, dependencies) is composed.

## Procedure
1. Resolve `kind` and the box macro / label prefix:
   definition->`definitionbox`/`def:`, axiom->`axiombox`/`ax:`, theorem->`theorembox`/`thm:`,
   lemma->`lemmabox`/`lem:`, proposition->`propositionbox`/`prop:`, corollary->`corollarybox`/`cor:`.
2. Resolve the canonical predicate(s) for the concept in `predicates.yaml`; never coin a name inline.
3. Emit the decorated statement: `\begin{<kind>box}{<Title>}` wrapping `\begin{<env>}` + `\label{<prefix>:<slug>}`
   + the verbatim/composed statement; then the required decoration blocks (Standard quantified statement,
   Interpretation, `\begin{dependencies}` or `\NoLocalDependencies`).
4. **If the kind is provable (theorem/lemma/proposition/corollary): ALSO emit the linked proof stub**
   atomically -- one step, never deferred. Use `proof_stub.render_proof_stub(kind, slug, title,
   statement_body, deps)`; write it to `proofs/<section>/prf-<slug>.tex` (filename MUST be `prf-<slug>.tex`);
   ensure `proofs/<section>/index.tex` inputs it and `proofs/index.tex` inputs the section index.
   Definitions and axioms get NO proof stub.

## Invariant
Adding a provable environment adds its proof stub, full stop. The pair (statement + stub) is always
square -- the proof-availability check is an unconditional error, never a "maybe later" warning.

## Bound verifier (MANDATORY -- task not complete until exit 0)
- statement (chrome + decoration):
      python tools/governance/validate_decoration.py --root <volume-root> --chapter <chapter>
- proof stub (layer order, filename, topic, stub squareness):
      python tools/governance/audit_proof_layout.py --root <volume-root> --chapter <chapter> --strict
Append mode runs these on the chapter; return mode runs the statement rules on the returned block.

## Notes
- The proof stub matches the CURRENT `audit_proof_layout` contract (newpage/phantomsection/label/
  LRAProofFor/remark*[Return]/theorem*/two \begin{proof} TODO bodies/remark*[Proof structure]/
  dependencies/clearpage). Older hand-written proofs using `\clearpage`+bare `\hyperref` predate this
  and will not validate -- regenerate them via this capability.
- The Proof structure block is emitted BLANK (whitespace body) in a stub: present for the validator,
  blank in render. It is filled when the proof itself is authored.
