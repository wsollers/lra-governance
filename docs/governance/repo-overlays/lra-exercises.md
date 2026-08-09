# lra-exercises Overlay

Specialist overlay for standalone exercise sheets, drill sheets, workbooks,
and their generated PDFs in `lra-exercises`.

Owned concerns:

- exercise and workbook `.tex` source files;
- generated exercise PDFs kept with their source folders when intended for
  distribution;
- standalone LaTeX build hygiene for printable student-facing materials.

`lra-exercises` is independent from the volume repositories. Do not route these
exercise artifacts through `lra-volume-*` chapter proof/exercise folders unless
a separate volume-content task explicitly imports or adapts the material.

## Build Runtime

Use the governance-owned Docker image for local LaTeX builds and PDF
generation. Build the image from `lra-governance`:

```powershell
docker build -t lra-exercises-latex -f docker\lra-exercises-latex\Dockerfile docker\lra-exercises-latex
```

From the `lra-exercises` repository, build a worksheet or workbook PDF by
mounting the repo at `/workspace` and running `latexmk` in the source folder:

```powershell
docker run --rm -v "${PWD}:/workspace" -w /workspace/Limits_Drill_Sheet_Source_and_PDF lra-exercises-latex latexmk -lualatex -interaction=nonstopmode -file-line-error -synctex=1 Limits_Drill_Sheet.tex
```

For a staged build directory that keeps auxiliary files out of the source
folder:

```powershell
docker run --rm -v "${PWD}:/workspace" -w /workspace/Algebraic_Techniques_for_Rational_Expressions_Source_and_PDF lra-exercises-latex sh -lc "mkdir -p build && latexmk -lualatex -interaction=nonstopmode -file-line-error -synctex=1 -outdir=build Algebraic_Techniques_for_Rational_Expressions.tex"
```

Use source-adjacent builds when the deliverable PDF is intentionally committed
or handed off next to its `.tex` file. Use `-outdir=build` for smoke tests,
draft builds, or diagnostics.

Clean generated auxiliary files in a mounted source folder:

```powershell
docker run --rm -v "${PWD}:/workspace" -w /workspace/Limits_Drill_Sheet_Source_and_PDF lra-exercises-latex latexmk -C Limits_Drill_Sheet.tex
```

Run `chktex` for a quick lint pass when editing source:

```powershell
docker run --rm -v "${PWD}:/workspace" -w /workspace/Limits_Drill_Sheet_Source_and_PDF lra-exercises-latex chktex -q Limits_Drill_Sheet.tex
```

## PDF Expectations

Exercise PDFs should be reproducible from committed `.tex` sources using the
Docker image above. When source and PDF are committed together, rebuild the PDF
after source changes and leave unrelated worksheet PDFs untouched.

The Docker image includes full TeX Live, `latexmk`, `biber`, TikZ support,
common worksheet packages such as `tcolorbox`, and PDF inspection/repair tools
including `poppler-utils`, `qpdf`, and Ghostscript.
