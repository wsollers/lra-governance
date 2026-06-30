# TikZ Style Guide

This guide defines the house visual language for nontrivial TikZ figures in
the LRA volumes. It is the canonical author-facing style guide. The reusable
TikZ keys, colors, and helper macros are implemented in `lra-common`; volume
repositories consume those shared definitions and must not carry local copies
of this guide as source-of-truth documents.

The current house style is the Structural Atlas style: warm paper, muted
jewel-tone curves, soft curve glows, gray probe lines, and compact captions.
Figures should read as probes of mathematical structure, not as decoration.

## Ownership

- Governance policy and style guidance live in `lra-governance`.
- Shared TikZ implementation lives in `lra-common`, principally
  `common/figures-macros.tex` and shared figure styles in `common/boxes.tex`.
- Volume repositories own figure content only. They may contain figure source
  files, but not local style-guide copies or local color-system definitions.

## Figure Artifact Rules

Every nontrivial TikZ figure follows the atomic figure rules in
`atomic-artifact-standards.md`:

- one nontrivial figure maps to one dedicated figure source file;
- note, proof, exercise, exposition, and statement files do not embed
  nontrivial `tikzpicture` environments;
- figure source files contain only the `tikzpicture` environment;
- captions, labels, placement, and explanatory prose live at the inclusion
  point;
- local color definitions and local style systems are prohibited.

Trivial inline marks, such as tiny arrows or ticks with no caption, label,
reuse value, or independent mathematical role, are the only embedded TikZ
exception. When in doubt, extract the figure.

## Design Principles

| Principle | Practice |
| --- | --- |
| The curve carries the figure | Use one dominant visual element: a gradient fill or glow under/around the main curve, with a crisp stroke on top. |
| Gray is scaffolding | Axes, droplines, and construction guides stay muted so they do not compete with the mathematical object. |
| One hue per concept | Reuse a color for the same theorem, construction, or role across related figures. |
| Probes, not clutter | Secants, tangents, level lines, and comparison bounds are thin auxiliary probes. Keep them few and purposeful. |
| Text is secondary | Labels identify mathematical features; they do not narrate the figure. Put prose in the surrounding note. |

## Palette

Use the shared atlas palette from `lra-common`. Do not redefine these colors in
volume-local figure files.

| Name | Role |
| --- | --- |
| `atlaspaper` | warm figure background when a background is used |
| `atlasink` | axes, text, and feature dots |
| `atlasgray` | dashed droplines and construction guides |
| `atlasblue` | primary curve, mean-value/Lipschitz figures |
| `atlasgreen` | continuity paths, secants, positive structure |
| `atlasred` | tangents, Rolle-type or warning structure |
| `atlasgold` | convexity |
| `atlasmagenta` | inflection or sign-change structure |
| `atlasteal` | local-minimum or stable comparison structure |
| `atlasorange` | local-maximum or exceptional tag structure |
| `atlasconegreen` | cones, gauges, and bounding regions |

## Core TikZ Keys

Use the shared TikZ keys instead of hand-rolled local styles:

- `atlas` on the `tikzpicture` environment for the Structural Atlas figure
  context;
- `atlas axes` for muted arrowed axes;
- `atlas curve` for the crisp main curve stroke;
- `atlas probe` for secants, tangents, level lines, and comparison lines;
- `dropline` for dashed gray guides;
- `atlas dot` for feature points;
- `atlas label` for compact mathematical labels.

Example figure source file:

```latex
\begin{tikzpicture}[atlas, scale=0.9]
  \glowcurve{color=atlasblue, domain=0:4, axis=0, top=4,
    expr={0.2*\x*\x}}
  \draw[atlas axes] (0,0)--(4.6,0);
  \draw[atlas axes] (0,0)--(0,4);
  \node[atlas dot] at (2,0.8){};
  \draw[dropline] (2,0.8)--(2,0);
  \node[atlas label,below] at (2,-0.05){$c$};
\end{tikzpicture}
```

## Glow Curves

Use `\glowcurve` for the signature Structural Atlas curve. A single call draws
the fill, halo, and final stroke. Always brace `expr`.

```latex
\glowcurve{color=atlasblue, domain=0.5:4.5, axis=0, top=4.6,
  expr={0.16*\x*\x+0.2*\x+0.55}}
```

Common keys:

| Key | Meaning |
| --- | --- |
| `color` | curve and glow color |
| `domain` | x-range as `a:b` |
| `axis` | baseline y-value for the fill |
| `top` | top of the fill rectangle; set it at or above the curve maximum |
| `expr` | plotted expression in `\x`; always braced |
| `samples` | plot samples; raise for high-frequency curves |
| `stroke` | crisp stroke width |
| `fillmax` | fill strength near the curve |
| `fillmin` | fill strength near the baseline |
| `halo` | width of the soft halo |

Use `\glowstroke` when the figure needs a haloed curve without a filled region.

## Captions And Inclusion

Ordinary volume figures use the caption and label at the inclusion point:

```latex
\begin{figure}[htbp]
\centering
\input{figure-mean-value}
\caption{Mean value geometry for a differentiable function.}
\label{fig:mean-value-geometry}
\end{figure}
```

Atlas plates may use `\atlascaption` inside a composite plate when the plate is
itself the figure source. Do not use `\atlascaption` to replace the canonical
LaTeX `\caption` and `\label` owned by the inclusion point unless the plate is a
self-contained rendered artifact with its own local panel captions.

## Layout

Single mathematical figures should stay compact and focused. Prefer one panel
per source file unless a multi-panel plate is mathematically necessary.

Multi-panel atlas plates should use consistent panel scale, aligned baselines,
and short captions. A plate should compare related structures, not collect
unrelated illustrations.

## Common Pitfalls

- Set `top` at or above the maximum y-value of a `\glowcurve`; otherwise the
  fill clips with a hard horizontal edge.
- `pgfmath` trigonometric functions use degrees. Use the `r` suffix for radians
  when needed, for example `sin(2*\x r)`.
- Brace every `expr`; unbraced commas break the key parser.
- Raise `samples` for oscillatory curves.
- Tangent and secant probes must match the plotted expression. Recompute slopes
  from the same function used in `expr`.
- Do not introduce a local palette to solve a one-off figure. Extend shared
  infrastructure in `lra-common` only when a reusable style is genuinely needed.
