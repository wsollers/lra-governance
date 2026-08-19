# Mathematician Medallion Image Prompts

This prompt sheet uses `lra-governance` as the source roster for
mathematician frontispiece images.

Source directories:

- `mathemeticians`
- `mathemeticians/lra-primary-series`
- `mathemetician-plagues`, unique non-duplicate names only

The visual reference is:

```text
lra-governance/mathemeticians/lra-primary-series/cantor.png
```

Reference dimensions: `1365x2048`.

## Generation Workflow

Generate these portraits one mathematician at a time.

Each image-generation request must target exactly one mathematician and must
produce exactly one finished portrait image. Do not ask ChatGPT or any image
model to create a contact sheet, multi-panel sheet, comparison grid, collage,
batch layout, or any image containing more than one mathematician.

For every mathematician, start a separate generation request using the house
prompt template below with that mathematician's name, dates, and math
background detail filled in.

## House Prompt Template

```text
Create a black-and-white engraved line drawing medallion portrait in the same
style, proportions, and layout as the Georg Cantor reference image: vertical
1365x2048 composition, large circular medallion at top, thick black circular
border, bust portrait inside, light paper background, fine hatch shading,
clean monochrome ink/woodcut look.

Subject: {name}, historically recognizable, bust portrait, formal
period-appropriate clothing.

Inside the circular medallion background, include sparse mathematical notation
and diagrams associated with their most famous work: {math_background}. Keep
the math secondary, behind and around the portrait, not covering the face.

Below the medallion, add a rectangular engraved plaque connected to the
medallion by a thin support line. The plaque text must read exactly:

{name}
{dates}

Style constraints:
- Match the Cantor image closely.
- Generate exactly one mathematician in exactly one image.
- Do not create a contact sheet, grid, collage, or multi-panel layout.
- Black ink on off-white paper.
- No color.
- No modern graphic design effects.
- No photographic realism.
- No extra labels outside the plaque.
- No watermark.
- Keep the medallion and plaque centered.
- Preserve generous white margin around the full figure.
```

For production use, prefer generating the image with a blank plaque and adding
the plaque text afterward in a controlled layout step. If ChatGPT renders the
text directly, inspect spelling and dates before accepting the image.

## Roster

| Slug | Name | Dates | Math background prompt detail |
|---|---|---:|---|
| al-khwarizmi | Muhammad ibn Musa al-Khwarizmi | c. 780-c. 850 | algebraic equations, balancing and completion, decimal numerals, algorithmic tables |
| aluffi | Paolo Aluffi | 1958- | algebraic geometry, Chern classes, intersection theory, schemes, blowup diagrams, projective varieties |
| apollonius | Apollonius of Perga | c. 240-c. 190 BCE | conic sections, ellipse/parabola/hyperbola diagrams, tangent lines to conics |
| archimedes | Archimedes | c. 287-c. 212 BCE | spiral of Archimedes, exhaustion method polygons, lever balance, sphere and cylinder |
| artin | Emil Artin | 1898-1962 | Artin reciprocity, field extensions, Galois groups, algebraic number theory symbols |
| banach | Stefan Banach | 1892-1945 | normed vector spaces, ||x|| notation, fixed point iteration, complete metric space diagrams |
| birkhoff | Garrett Birkhoff | 1911-1996 | lattice diagrams, meet and join symbols, ordered sets, universal algebra notation |
| bolzano | Bernard Bolzano | 1781-1848 | intermediate value theorem graph, nested intervals, Bolzano-Weierstrass sequence marks |
| boole | George Boole | 1815-1864 | Boolean algebra, 0/1 logic tables, AND/OR/NOT gates, set diagrams |
| borel | Emile Borel | 1871-1956 | Borel sets, sigma-algebra symbols, measurable intervals, countable unions |
| cantor | Georg Cantor | 1845-1918 | cardinality notation, aleph-null, power sets, diagonal argument marks |
| caratheodory | Constantin Caratheodory | 1873-1950 | outer measure, measurable sets, extension theorem notation, variational curves |
| cavalieri | Bonaventura Cavalieri | 1598-1647 | indivisibles, sliced regions, area summation, parallel cross-sections |
| cauchy | Augustin-Louis Cauchy | 1789-1857 | Cauchy sequences, epsilon notation, complex contour integral, residue-style loops |
| church | Alonzo Church | 1903-1995 | lambda calculus terms, beta reduction arrows, Church numerals, computability notation |
| de-morgan | Augustus De Morgan | 1806-1871 | De Morgan laws, logical negation, set complements, union and intersection diagrams |
| dedekind | Richard Dedekind | 1831-1916 | Dedekind cuts, ordered rationals, real-line partition, ideal notation |
| descartes | Rene Descartes | 1596-1650 | Cartesian axes, analytic geometry curves, coordinate pairs, algebraic equations |
| euclid | Euclid | fl. c. 300 BCE | Euclidean propositions, triangle construction, parallel lines, compass-and-straightedge marks |
| fermat | Pierre de Fermat | 1607-1665 | Fermat's Last Theorem, modular arithmetic, tangent method, number theory symbols |
| fibonacci | Leonardo Fibonacci | c. 1170-c. 1250 | Fibonacci sequence, spiral rectangles, recurrence F_n = F_{n-1}+F_{n-2}, abacus numerals |
| fourier | Joseph Fourier | 1768-1830 | Fourier series, sine waves, heat equation, frequency spectrum lines |
| frechet | Maurice Frechet | 1878-1973 | metric spaces, distance function d(x,y), neighborhoods, compactness notation |
| frege | Gottlob Frege | 1848-1925 | Begriffsschrift-style logic, quantifiers, predicates, implication strokes |
| frenkel | Edward Frenkel | 1968- | Langlands program, representation theory, algebraic geometry sheaves, gauge theory connections |
| galois | Evariste Galois | 1811-1832 | Galois groups, field extensions, polynomial roots, subgroup lattice |
| gentzen | Gerhard Gentzen | 1909-1945 | sequent calculus, turnstile symbols, proof trees, natural deduction rules |
| grassmann | Hermann Grassmann | 1809-1877 | exterior algebra, wedge products, vector spaces, oriented parallelograms |
| green | George Green | 1793-1841 | Green's theorem, boundary integrals, potential functions, vector fields |
| grothendieck | Alexander Grothendieck | 1928-2014 | schemes, arrows and commutative diagrams, sheaves, topos-style category symbols |
| halmos | Paul Halmos | 1916-2006 | measure theory, Hilbert space operators, set notation, QED square |
| hamilton | William Rowan Hamilton | 1805-1865 | quaternions i,j,k, Hamiltonian equations, vector rotations, phase curves |
| hausdorff | Felix Hausdorff | 1868-1942 | Hausdorff separation, topological neighborhoods, metric spaces, set families |
| hero | Hero of Alexandria | c. 10-c. 70 | Heron's formula, triangle area diagram, mechanical geometry, square root expression |
| hilbert | David Hilbert | 1862-1943 | Hilbert space, axioms, basis vectors, geometry foundations, proof symbols |
| hopper | Grace Hopper | 1906-1992 | compiler flowcharts, early programming notation, subroutine blocks, machine-code tables |
| hypatia | Hypatia | c. 350-415 | conic sections, astronomical curves, geometric constructions, commentary scroll marks |
| jacob-bernoulli | Jacob Bernoulli | 1655-1705 | law of large numbers, Bernoulli numbers, probability sums, logarithmic spiral |
| johann-bernoulli | Johann Bernoulli | 1667-1748 | brachistochrone curve, calculus of variations, cycloid diagram, differential notation |
| khayyam | Omar Khayyam | 1048-1131 | cubic equations, conic intersections, geometric algebra constructions |
| kolmogorov | Andrey Kolmogorov | 1903-1987 | probability axioms, sigma-algebras, stochastic processes, conditional probability |
| lagrange | Joseph-Louis Lagrange | 1736-1813 | Lagrange multipliers, variational mechanics, Euler-Lagrange equation, constraint curves |
| laplace | Pierre-Simon Laplace | 1749-1827 | Laplace transform, celestial mechanics orbits, probability density curves, differential equations |
| legendre | Adrien-Marie Legendre | 1752-1833 | Legendre polynomials, least squares, elliptic integrals, number theory symbols |
| lebesgue | Henri Lebesgue | 1875-1941 | Lebesgue integral, measurable sets, sigma-algebra notation, simple functions approximating a curve |
| leibniz | Gottfried Wilhelm Leibniz | 1646-1716 | differential notation dx and dy, integral sign, product rule, binary arithmetic |
| lipschitz | Rudolf Lipschitz | 1832-1903 | Lipschitz condition, bounded slopes, metric inequalities, continuity diagrams |
| lovelace | Ada Lovelace | 1815-1852 | analytical engine tables, Bernoulli number algorithm, punched-card style sequences |
| mac-lane | Saunders Mac Lane | 1909-2005 | category theory arrows, functors, natural transformations, commutative diagrams |
| napier | John Napier | 1550-1617 | logarithm tables, Napier rods, exponential curves, log notation |
| nash | John Nash | 1928-2015 | Nash equilibrium, payoff matrix, fixed point diagram, game theory notation |
| newton | Isaac Newton | 1643-1727 | fluxions, inverse-square law, orbital diagram, binomial series, calculus notation |
| noether | Emmy Noether | 1882-1935 | Noether's theorem, symmetry and conservation symbols, ideals, rings and modules |
| pascal | Blaise Pascal | 1623-1662 | Pascal triangle, binomial coefficients, probability combinations, cycloid marks |
| peano | Giuseppe Peano | 1858-1932 | Peano axioms, successor function S(n), natural numbers, induction ladder |
| pythagoras | Pythagoras | c. 570-c. 495 BCE | right triangle theorem, square-on-side diagram, ratios, geometric harmony marks |
| riemann | Bernhard Riemann | 1826-1866 | Riemann integral sums, curved manifold grid, zeta function, metric tensor notation |
| rudin | Walter Rudin | 1921-2010 | real and complex analysis, contour integrals, harmonic functions, normed spaces |
| russell | Bertrand Russell | 1872-1970 | type theory, set paradox notation, logical classes, Principia-style symbols |
| stokes | George Gabriel Stokes | 1819-1903 | Stokes' theorem, surface boundary curve, curl vector field, integral notation |
| tarski | Alfred Tarski | 1901-1983 | model theory, truth definition, satisfaction relation, logical structures |
| thales | Thales of Miletus | c. 624-c. 546 BCE | similar triangles, circle theorem, shadow measurement geometry, proportional lines |
| turing | Alan Turing | 1912-1954 | Turing machine tape, state transition arrows, lambda/computability symbols |
| von-neumann | John von Neumann | 1903-1957 | game theory payoff matrix, operator algebra symbols, cellular automaton grid |
| wallis | John Wallis | 1616-1703 | infinity symbol, Wallis product, infinite series, quadrature curves |
| weierstrass | Karl Weierstrass | 1815-1897 | epsilon-delta limits, convergent series, pathological function graph, analytic rigor |
| zermelo | Ernst Zermelo | 1871-1953 | Zermelo-Fraenkel set theory, choice function, well-ordering, set membership symbols |
