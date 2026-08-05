# =============================================================
# Dockerfile - LRA TeX development environment
# Project: Learning Real Analysis
#
# This image is the canonical local TeX runtime for lra-volume-* repos.
# It is intentionally editor-neutral: VS Code Dev Containers use it, and
# governance build helpers use the same TeX/package surface.
# =============================================================

FROM texlive/texlive:latest@sha256:2f9918a156cfc6c7527590e06f69bfb4fbc827278e4736c90e567382855d7cd1

RUN apt-get update && apt-get install -y --no-install-recommends \
        biber \
        ca-certificates \
        chktex \
        fontconfig \
        git \
        latexmk \
        less \
        make \
        openssh-client \
        perl \
        python3 \
        python3-pip \
        ripgrep \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN fc-cache -fv

ENV LRA_GOVERNANCE_ROOT=/lra-governance
ENV LRA_COMMON_ROOT=/lra-common
ENV LRA_EDITION=digital
ENV LRA_PAPER=letter

WORKDIR /workspace

CMD ["latexmk", "--version"]
