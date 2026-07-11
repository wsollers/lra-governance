# Docker Validation Workflow

`lra-governance` owns the lightweight deterministic validation image for
governance tests and volume validation. The image is intentionally separate
from the heavier TeX build image owned by `lra-common/docker`.

## Image

Build the governance test image from the governance repo:

```powershell
python scripts\docker_build_governance_test.py
```

The default image tag is `lra-governance-test`. Override it with `--image`.

## Governance Tests

Run deterministic governance tests in the container:

```powershell
python scripts\docker_test_governance.py --build
```

The script mounts:

- the governance checkout at `/work/governance`;
- a results/cache directory at `/work/results`.

By default it runs `python -m compileall constitution/auditor tools/governance`
and `pytest tools/governance/test_*.py`. Pass pytest arguments after `--`:

```powershell
python scripts\docker_test_governance.py -- --maxfail=1 tools/governance/test_validate_volume.py
```

## Volume Validation

Validate a mounted volume repo and write the JSON report to a mounted results
directory. The full text output is written to a log file in the same results
directory, and the wrapper prints only the last 80 log lines.

```powershell
python scripts\docker_validate_volume.py --build --root ..\lra-volume-i
```

Useful options:

```powershell
python scripts\docker_validate_volume.py --root ..\lra-volume-i --results build\volume-i-validation
python scripts\docker_validate_volume.py --root ..\lra-volume-i --json-name volume-i.json --log-name volume-i.log
python scripts\docker_validate_volume.py --root ..\lra-volume-i --book book-sets
python scripts\docker_validate_volume.py --root ..\lra-volume-i --chapter book-sets/functions
python scripts\docker_validate_volume.py --root ..\lra-volume-i --fail-on-errors
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
