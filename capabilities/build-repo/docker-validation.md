# Docker Validation Workflow

`lra-governance` owns the lightweight deterministic validation image for
governance tests and volume validation. The image is intentionally separate
from the heavier TeX build image owned by `lra-common/docker`.

## Canonical Python Runtime

The canonical runtime definition lives only in `lra-governance`:

- `.python-version` selects Python 3.12.13 as the reproducible baseline;
- `pyproject.toml` owns direct dependencies and supported Python versions;
- `requirements.lock` pins the complete governance environment with hashes;
- `.venv/` is an ignored local environment and is never copied downstream.

Create or refresh the local environment with:

```sh
py -3.12 scripts/bootstrap_python.py
```

Python 3.13 remains a supported compatibility target. Docker and downstream
validation use the canonical Python 3.12.13 baseline; core CI runs both 3.12.13
and 3.13.9. Downstream repositories invoke this runtime through a governance
checkout or the governance image; they do not carry copies of the governance
project or lock files.

Regenerate `requirements.lock` from `pyproject.toml` with a reviewed `uv`
release and an explicit Python 3.12 target:

```sh
uv pip compile pyproject.toml --extra test --extra validation --extra ai --python-version 3.12 --generate-hashes --output-file requirements.lock
```

Commit direct-dependency changes and the regenerated lock together.

## Image

Build the governance test image from the governance repo. The repository root
is the Docker build context so the image installs the canonical lock file:

```sh
python scripts/docker_build_governance_test.py
```

The default image tag is `lra-governance-test`. Override it with `--image`.

## Governance Tests

Run deterministic governance tests in the container:

```sh
python scripts/docker_test_governance.py --build
```

The script mounts:

- the governance checkout at `/work/governance`;
- a results/cache directory at `/work/results`.

By default it runs `python -m compileall constitution/auditor tools/governance`
and `pytest tools/governance/test_*.py`. Pass pytest arguments after `--`:

```sh
python scripts/docker_test_governance.py -- --maxfail=1 tools/governance/test_validate_volume.py
```

## Volume Validation

Validate a mounted volume repo and write the JSON report to a mounted results
directory. The full text output is written to a log file in the same results
directory, and the wrapper prints only the last 80 log lines.

```sh
python scripts/docker_validate_volume.py --build --root ../lra-volume-i
```

Useful options:

```sh
python scripts/docker_validate_volume.py --root ../lra-volume-i --results build/volume-i-validation
python scripts/docker_validate_volume.py --root ../lra-volume-i --json-name volume-i.json --log-name volume-i.log
python scripts/docker_validate_volume.py --root ../lra-volume-i --book book-sets
python scripts/docker_validate_volume.py --root ../lra-volume-i --chapter book-sets/functions
python scripts/docker_validate_volume.py --root ../lra-volume-i --fail-on-errors
```

`--book` is a true scoped validation gate. It limits the file inventory to the
chosen book directory and runs the validators that are meaningful for a scoped
source pass. `--chapter` remains a report filter unless combined with `--book`.

The wrapper mounts:

- `lra-governance` at `/work/governance`;
- the target volume at `/work/volume`;
- the host results directory at `/work/results`.

It sets `LRA_GOVERNANCE_ROOT=/work/governance`, so validators load canonical
YAML and governance rules from the mounted governance checkout.

By default, the Docker wrapper copies the target volume source into
container-local `/tmp` before validation. This avoids repeated validator reads
and path checks over slow host bind mounts. Pass `--no-stage-source` to validate
directly from `/work/volume`.
