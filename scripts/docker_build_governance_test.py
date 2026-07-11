#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _load_support():
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "tools" / "governance"))
    import docker_support

    return docker_support


def main(argv: list[str] | None = None) -> int:
    docker_support = _load_support()
    parser = argparse.ArgumentParser(description="Build the LRA governance test Docker image.")
    parser.add_argument("--image", default=docker_support.DEFAULT_GOVERNANCE_TEST_IMAGE)
    args = parser.parse_args(argv)
    docker_support.build_governance_test_image(args.image)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
