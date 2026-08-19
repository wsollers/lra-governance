# Capability: add-tikz-figure

Create or revise a TikZ figure as a dedicated figure source file.

## Trigger

Requests to add, draw, or revise a figure, diagram, plate, or categorical
rendering in volume content.

## Rules

- One nontrivial figure -> one dedicated figure source file containing only
  the `tikzpicture` environment. Note, proof, exercise, exposition, and
  statement files never embed nontrivial `tikzpicture` environments; trivial
  inline marks (no caption, label, reuse value, or independent mathematical
  role) are the only exception. When in doubt, extract.
- Captions, labels, placement options, and explanatory prose live at the
  inclusion point, not in the figure source file.
- Use the shared Structural Atlas styles from `lra-common` (`atlas`,
  `atlas axes`, `atlas curve`, `atlas probe`, `dropline`, `atlas dot`,
  `atlas label`, `\glowcurve`; `lra categorical diagram` and the `lra cat *`
  keys for categorical renderings). Local color definitions and local style
  systems are prohibited; extend `lra-common` only when a reusable style is
  genuinely needed.
- Style guidance is canonical here in `lra-governance`; shared implementation
  is owned by `lra-common`; volume repositories own figure content only.

## Procedure

1. Write the figure source file with only the `tikzpicture` body, using the
   shared keys and palette. Follow the style detail, palette roles, key
   references, worked examples, and pitfalls in
   `capabilities/add-tikz-figure/style-guide.md`.
2. Add the inclusion block (`figure` environment, `\input`, caption, label)
   at the call site.
3. Verify.

Inclusion pattern:

```latex
\begin{figure}[htbp]
\centering
\input{figure-mean-value}
\caption{Mean value geometry for a differentiable function.}
\label{fig:mean-value-geometry}
\end{figure}
```

## Verify

Run governance validation for the volume; the figure must render through the
volume build without local style or color definitions.
