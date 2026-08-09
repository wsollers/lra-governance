# =============================================================
# Dockerfile - LRA exercises LaTeX build environment
# Project: Learning Real Analysis
#
# This image is the canonical Docker runtime for standalone
# lra-exercises worksheet/workbook PDF builds. It intentionally does
# not mount lra-common or set volume-edition environment variables.
# =============================================================

FROM texlive/texlive:latest@sha256:2f9918a156cfc6c7527590e06f69bfb4fbc827278e4736c90e567382855d7cd1

RUN apt-get update && apt-get install -y --no-install-recommends \
        biber \
        ca-certificates \
        chktex \
        fontconfig \
        ghostscript \
        git \
        latexmk \
        less \
        make \
        perl \
        poppler-utils \
        python3 \
        qpdf \
        ripgrep \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN fc-cache -fv

ENV TEXMFVAR=/tmp/texmf-var
ENV TEXMFCONFIG=/tmp/texmf-config
ENV max_print_line=1000

WORKDIR /workspace

CMD ["latexmk", "--version"]
