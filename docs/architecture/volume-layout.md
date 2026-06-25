# Volume Layout

Volume repos are self-contained and Overleaf-ready.

```text
lra-volume-N/
  main.tex
  .latexmkrc
  common/
  bibliography/
  volume-N/
    index.tex
    <chapter>/
      index.tex
      chapter.yaml
      notes/
      proofs/
      exercises/
```

Volume, chapter, topic-level note/proof folder pairing, and proof router
reachability are machine-readable in `constitution/schema/file-schema.yaml`.
Use `tools/governance/audit_volume_layout.py` for deterministic layout audits.

Top-level `exercises/` is reserved for the chapter exercise vault. It is
separate from theorem proof material under `proofs/`; stable exercise IDs are
canonical, while exercise paths are mutable routing details.

`common/` is supplied to the build by the environment (Docker image or explicit
`lra-common` checkout). It is not owned by, or stored as a synced copy in,
volume repos.

Volume repos own volume content only. They do not own Lean formalization,
C++/Vulkan simulation, numerical benchmarking, or global governance.
