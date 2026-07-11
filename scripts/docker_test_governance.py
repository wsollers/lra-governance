#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path


def _load_support():
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "tools" / "governance"))
    import docker_support

    return docker_support


def main(argv: list[str] | None = None) -> int:
    docker_support = _load_support()
    parser = argparse.ArgumentParser(description="Run deterministic governance tests inside Docker.")
    parser.add_argument("--image", default=docker_support.DEFAULT_GOVERNANCE_TEST_IMAGE)
    parser.add_argument("--build", action="store_true", help="Build the image before running tests.")
    parser.add_argument("--results", type=Path, help="Host directory for pytest cache and logs.")
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Optional pytest arguments after --, default: tools/governance/test_*.py",
    )
    args = parser.parse_args(argv)

    if args.build:
        docker_support.build_governance_test_image(args.image)
    else:
        docker_support.require_docker()

    root = docker_support.governance_root()
    results = docker_support.mounted_results_dir(args.results, "governance-tests")
    pytest_args = args.pytest_args
    if pytest_args and pytest_args[0] == "--":
        pytest_args = pytest_args[1:]
    if not pytest_args:
        pytest_args = ["tools/governance/test_*.py"]

    pytest_cmd = " ".join(shlex.quote(arg) for arg in pytest_args)
    inner = (
        "python -m compileall constitution/auditor tools/governance "
        "&& python -m pytest -o cache_dir=/work/results/.pytest_cache "
        f"{pytest_cmd}"
    )
    cmd = [
        "docker",
        "run",
        "--rm",
        "-e",
        "LRA_GOVERNANCE_ROOT=/work/governance",
        "-e",
        "PYTHONDONTWRITEBYTECODE=1",
        "-e",
        "PYTHONPYCACHEPREFIX=/work/results/pycache",
        "-v",
        f"{docker_support.docker_path(root)}:/work/governance",
        "-v",
        f"{docker_support.docker_path(results)}:/work/results",
        "-w",
        "/work/governance",
        args.image,
        "bash",
        "-lc",
        inner,
    ]
    docker_support.run(cmd, cwd=root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
