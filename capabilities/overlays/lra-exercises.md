# Repo Overlay -- lra-exercises

Repo identity: Standalone exercise sheets, workbooks, and generated PDFs.

Standalone LaTeX exercise/workbook source and generated PDF artifacts,
independent from the volume repositories. Do not route these exercise
artifacts through `lra-volume-*` chapter proof/exercise folders unless a
separate volume-content task explicitly imports or adapts the material.

Owned concerns: exercise and workbook `.tex` source files; generated
exercise PDFs kept with their source folders when intended for distribution;
standalone LaTeX build hygiene for printable student-facing materials.

## Build Runtime

Use the governance-owned Docker image for LaTeX builds and PDF generation.
Build the image from `lra-governance`:

```powershell
docker build -t lra-exercises-latex -f docker\lra-exercises-latex\Dockerfile docker\lra-exercises-latex
```

From `lra-exercises`, build a worksheet/workbook PDF by mounting the repo at
`/workspace` and running `latexmk` in the source folder:

```powershell
docker run --rm -v "${PWD}:/workspace" -w /workspace/<Source_Folder> lra-exercises-latex latexmk -lualatex -interaction=nonstopmode -file-line-error -synctex=1 <sheet>.tex
```

Use a staged build directory (`sh -lc "mkdir -p build && latexmk ... -outdir=build <sheet>.tex"`)
for smoke tests, draft builds, or diagnostics; use source-adjacent builds
when the deliverable PDF is intentionally committed next to its `.tex` file.
Clean auxiliary files with `latexmk -C <sheet>.tex`; lint with
`chktex -q <sheet>.tex` inside the same image.

The image includes full TeX Live, `latexmk`, `biber`, TikZ, common worksheet
packages such as `tcolorbox`, and PDF inspection/repair tools
(`poppler-utils`, `qpdf`, Ghostscript).

## PDF Expectations

Exercise PDFs must be reproducible from committed `.tex` sources using the
image above. When source and PDF are committed together, rebuild the PDF
after source changes and leave unrelated worksheet PDFs untouched.

## Success gates

- Run the Docker `latexmk` build for every changed `.tex` source.
