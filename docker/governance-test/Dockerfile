FROM python:3.13-slim

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

WORKDIR /work/governance

CMD ["bash"]
