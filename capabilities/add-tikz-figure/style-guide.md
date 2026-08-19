# TikZ Style Guide

House visual language for nontrivial TikZ figures: the Structural Atlas style
(warm paper, muted jewel-tone curves, soft curve glows, gray probe lines,
compact captions). Figures read as probes of mathematical structure, not
decoration. Shared implementation lives in `lra-common`
(`common/figures-macros.tex`, figure styles in `common/boxes.tex`); volume
repositories must not carry local style-guide or color-system copies.

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

## Categorical Renderings

Categorical diagrams in the learning volumes are structural memory devices, not
decorative illustrations. Use them when a topic has a reusable interface:
subobjects, joins/meets, images/preimages, quotient maps, pullbacks,
pushforwards, adjunctions, products, coproducts, limits, colimits, or canonical
factorizations.

Use the shared categorical keys from `lra-common`:

- `lra categorical diagram` on the `tikzpicture`;
- `lra cat native object` for given inputs or ambient objects;
- `lra cat left object` and `lra cat right object` for parallel construction
  paths;
- `lra cat result object` for the shared result, quotient, classifier, limit,
  colimit, or canonical target;
- `lra cat arrow` for ordinary maps or inclusions;
- `lra cat left arrow` and `lra cat right arrow` for the two highlighted paths;
- `lra cat result arrow` for convergence into the shared result;
- `lra cat universal arrow` for unique maps supplied by universal properties;
- `lra cat label` for compact arrow labels;
- `lra cat note` for short diagram-level memory hooks.

A categorical rendering should make the following visible:

| Requirement | Practice |
| --- | --- |
| One object per box | Each box names exactly one object, operation result, quotient, classifier, or universal target. |
| Native logic inside boxes | When an object is defined by a condition, put the defining condition below the object name in smaller type. |
| Arrows have mathematical roles | Arrows represent inclusions, maps, injections, projections, quotient maps, substitutions, factor maps, or universal maps. |
| Labels teach, not decorate | Label only arrows whose role is not visually obvious or whose label is the memory hook. |
| Hasse-style layouts first | Prefer top inputs, middle constructions, and a lower shared result. Avoid crossing arrows. |
| Color encodes structure | Neutral boxes are given/native objects; left and right construction paths use the shared left/right styles; shared results use the result style; universal maps use dashed universal arrows. |
| The theorem is the commuting claim | The caption or nearby prose should state what commutes, factors, or agrees. |

Use `\LraCatObject{...}{...}` for a box with a mathematical object name and a
mathematical logic line. Use `\LraCatObjectText{...}{...}` when the second line
is short prose, and `\LraCatObjectPlain{...}` when no second line is needed.

Example dedicated figure source file:

```latex
\begin{tikzpicture}[lra categorical diagram]
  \node[lra cat native object] (A) at (0,2)
    {\LraCatObject{A}{\{x:x\in A\}}};
  \node[lra cat native object] (B) at (3,2)
    {\LraCatObject{B}{\{x:x\in B\}}};
  \node[lra cat native object] (C) at (6,2)
    {\LraCatObject{C}{\{x:x\in C\}}};

  \node[lra cat left object] (AB) at (1.5,0.6)
    {\LraCatObject{A\cup B}{\{x:x\in A\lor x\in B\}}};
  \node[lra cat right object] (BC) at (4.5,0.6)
    {\LraCatObject{B\cup C}{\{x:x\in B\lor x\in C\}}};
  \node[lra cat result object] (ABC) at (3,-0.9)
    {\LraCatObject{A\cup B\cup C}{\{x:x\in A\lor x\in B\lor x\in C\}}};

  \draw[lra cat left arrow] (A) -- node[lra cat label,above left]{group \(A,B\)} (AB);
  \draw[lra cat left arrow] (B) -- (AB);
  \draw[lra cat right arrow] (B) -- (BC);
  \draw[lra cat right arrow] (C) -- node[lra cat label,above right]{group \(B,C\)} (BC);
  \draw[lra cat result arrow] (AB) -- (ABC);
  \draw[lra cat result arrow] (BC) -- (ABC);

  \node[lra cat note] at (3,-1.75)
    {both paths land on the same membership condition};
\end{tikzpicture}
```

The source file still follows the atomic figure rule: it contains only the
`tikzpicture`. Put the surrounding card, caption, label, and explanatory prose
at the inclusion point. For example, a note may place `\input{figure-union-assoc}`
inside an `lracategoricalcard`, but the figure source itself remains standalone.

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

## Layout

Single mathematical figures should stay compact and focused. Prefer one panel
per source file unless a multi-panel plate is mathematically necessary.

Multi-panel atlas plates should use consistent panel scale, aligned baselines,
and short captions. A plate should compare related structures, not collect
unrelated illustrations.

Atlas plates may use `\atlascaption` inside a composite plate when the plate is
itself the figure source. Do not use `\atlascaption` to replace the canonical
LaTeX `\caption` and `\label` owned by the inclusion point unless the plate is a
self-contained rendered artifact with its own local panel captions.

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
