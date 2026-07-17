FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    LRA_GOVERNANCE_ROOT=/work/governance \
    PYTHONPATH=/work/governance/tools/governance:/work/governance/constitution

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/lra-governance-test-requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/lra-governance-test-requirements.txt

# NLTK is used only as a deterministic prose-cue extractor in the semantic AST
# ensemble.  Preload the small tokenizer/tagger corpora so validation runs do
# not reach out to the network at runtime.
RUN python - <<'PY'
import nltk

for package in (
    "punkt",
    "punkt_tab",
    "averaged_perceptron_tagger",
    "averaged_perceptron_tagger_eng",
):
    nltk.download(package, quiet=True)
PY

WORKDIR /work/governance

CMD ["bash"]
