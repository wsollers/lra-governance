# LaTeX Math Style Guide

## Purpose

LRA source TeX should be readable mathematical LaTeX, not parser-shaped
surrogate notation. Validators and semantic artifact tools must learn the
house notation rather than forcing authors to degrade ordinary mathematical
style.

This guide governs source-level math style. The canonical symbols and their
parser roles are registered in `notation.yaml`; this document explains the
human-facing authoring convention.

## Function Notation

Use `\colon` for function signatures and `\to` for the function type arrow:

```latex
f\colon A\to B
```

Do not write `f: A\to B` for a function signature. The plain colon is reserved
for set-builder separators and ordinary punctuation.

Use `\mapsto` for a function rule:

```latex
x\mapsto x^2
```

Do not replace `\mapsto` with `\to` merely to appease a parser. The semantic
pipeline must classify `\to` as a function type arrow in signatures and
`\mapsto` as a function rule arrow.

## Logical Connectives

For displayed formal logic, prefer the long connectives:

```latex
P\Longrightarrow Q
P\Longleftrightarrow Q
```

`\Rightarrow` and `\iff` remain acceptable for compact inline logic when they
are visually clearer, but displayed quantified statements should use the long
forms.

Function arrows are not logical connectives. In particular, `\to` in
`f\colon A\to B` must not be parsed as implication.

## Set Builders

Use ordinary set-builder notation. The house-preferred separator is a plain
colon:

```latex
\{x\in X: x>0\}
```

`\mid` is also registered as set-builder notation when it better matches a
source or avoids ambiguity:

```latex
\{x\in X\mid x>0\}
```

Do not write malformed delimiter commands such as `\left{...\right}`. Use
escaped braces:

```latex
\left\{x\in X: x>0\right\}
```

## Quantified Statement Blocks

A `Standard quantified statement` block should contain a mathematical formula,
not a prose restatement. Put prose in the formal environment or an
interpretation remark, and put the symbolic quantified form in the quantified
statement block.

Every displayed formal support block must be closed relative to an explicitly
visible context. Hidden semantic artifact metadata does not rescue a displayed
formula whose variables, index sets, or family domains are not bound or locally
declared. A support block may rely on immediately visible prose in the same
block, but standalone displayed formulas should bind their quantified variables
and family domains themselves.

Good:

```latex
\[
\forall x\in A,\ x\leq u.
\]
```

Avoid:

```latex
\[
\text{Let } A\subseteq\mathbb{R}.
\]
```

## Families and Indexed Families

Use one representation for a family of sets within a support block unless the
relationship between the representations is declared explicitly.

Good set-family style:

```latex
\[
\forall \mathcal U\,
\left(
\operatorname{OpenCover}(\mathcal U,K,\mathbb R)
\Longrightarrow
\exists \mathcal V\subseteq\mathcal U,\quad
K\subseteq\bigcup_{V\in\mathcal V}V
\right).
\]
```

Good indexed-family style:

```latex
\[
\forall \{U_i\}_{i\in I}\,
\left(
K\subseteq\bigcup_{i\in I}U_i
\Longrightarrow
\exists \text{finite }J\subseteq I,\quad
K\subseteq\bigcup_{i\in J}U_i
\right).
\]
```

Avoid mixing the two styles without a declaration:

```latex
\[
\forall \mathcal U\,
\left(
\operatorname{OpenCover}(\mathcal U,K,\mathbb R)
\Longrightarrow
\exists J\;(J\subseteq I\land K\subseteq\bigcup_{i\in J}U_i)
\right).
\]
```

Here \(I\) and \(U_i\) are not bound by the displayed formula, and no relation
between \(\mathcal U\) and \(\{U_i\}_{i\in I}\) has been declared.  Either use
only \(\mathcal U,\mathcal V\), or quantify the indexed family
\(\{U_i\}_{i\in I}\) explicitly.

Avoid standalone support formulas whose index sets are supplied only by hidden
metadata:

```latex
\[
\{U_i\}_{i\in J} \text{ is a finite subcover of } E
\Longleftrightarrow
\bigl(J\subseteq I \land J \text{ is finite}
\land E\subseteq\bigcup_{i\in J}U_i\bigr).
\]
```

The symbol \(I\) is not visibly declared in the formula. Prefer a set-family
formulation:

```latex
\[
\operatorname{FiniteSubcover}(\mathcal V,\mathcal U,K)
\Longleftrightarrow
\left[
\mathcal V\subseteq\mathcal U
\land
\operatorname{FiniteSet}(\mathcal V)
\land
\forall x\in K\ \exists V\in\mathcal V,\ x\in V
\right].
\]
```

Support blocks must also preserve spacing and delimiters around membership and
subset domains.  In particular, malformed generated fragments such as
`\forall i\in IU_i` or `J\subseteq IK\not\subseteq` are invalid; they usually
mean that a separator such as `\;`, `,`, or a parenthesis was lost.

## House Normalizations

Use the notation normalizations in `notation-standards.md`. In particular:

- use `\mathbb{R}` for the real numbers;
- use `\subseteq`, `\in`, and `\notin` for set relations;
- use `\leq` and `\geq` as the house relation forms;
- use `\sup`, `\inf`, `\min`, and `\max` as operators.

## Validator

The focused style validator is:

```powershell
python tools\governance\validate_latex_math_style.py --target <tex-file-or-directory>
```

It checks the source against the notation roles in `notation.yaml`, including
the distinction between function arrows, function-rule arrows, set-builder
separators, and logical connectives.
