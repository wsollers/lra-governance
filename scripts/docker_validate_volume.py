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


def _default_report_name(volume_root: Path) -> str:
    return f"{volume_root.name}-validation.json"


def main(argv: list[str] | None = None) -> int:
    docker_support = _load_support()
    parser = argparse.ArgumentParser(description="Validate an LRA volume inside the governance test Docker image.")
    parser.add_argument("--root", type=Path, required=True, help="Target lra-volume-* repository root.")
    parser.add_argument("--image", default=docker_support.DEFAULT_GOVERNANCE_TEST_IMAGE)
    parser.add_argument("--build", action="store_true", help="Build the image before running validation.")
    parser.add_argument("--results", type=Path, help="Host directory for validation JSON and logs.")
    parser.add_argument("--json-name", help="Validation JSON filename inside the results directory.")
    parser.add_argument("--log-name", help="Validation log filename inside the results directory.")
    parser.add_argument("--book", help="Optional validate_volume.py book scope, e.g. book-sets.")
    parser.add_argument("--chapter", help="Optional validate_volume.py chapter report filter.")
    parser.add_argument("--fail-on-errors", action="store_true", help="Return nonzero when the full volume has errors.")
    parser.add_argument(
        "--no-stage-source",
        action="store_true",
        help="Validate directly from the mounted volume instead of copying scoped source to container-local /tmp first.",
    )
    args = parser.parse_args(argv)

    if args.build:
        docker_support.build_governance_test_image(args.image)
    else:
        docker_support.require_docker()

    gov_root = docker_support.governance_root()
    volume_root = args.root.expanduser().resolve()
    if not volume_root.exists():
        raise SystemExit(f"volume root does not exist: {volume_root}")

    results = docker_support.mounted_results_dir(args.results, f"{volume_root.name}-validation")
    json_name = args.json_name or _default_report_name(volume_root)
    log_name = args.log_name or f"{Path(json_name).stem}.log"
    setup = "target_root=/work/volume; "
    if not args.no_stage_source:
        if args.book:
            book = shlex.quote(args.book)
            setup = (
                "src_vol=$(find /work/volume -maxdepth 1 -type d -name 'volume-*' | head -n 1); "
                "if [ -z \"$src_vol\" ]; then src_vol=/work/volume; fi; "
                "vol_name=$(basename \"$src_vol\"); "
                "mkdir -p \"/tmp/lra-volume/$vol_name\"; "
                f"cp -a \"$src_vol\"/{book} \"/tmp/lra-volume/$vol_name/\"; "
                "target_root=\"/tmp/lra-volume/$vol_name\"; "
            )
        else:
            setup = (
                "src_vol=$(find /work/volume -maxdepth 1 -type d -name 'volume-*' | head -n 1); "
                "if [ -z \"$src_vol\" ]; then src_vol=/work/volume; fi; "
                "mkdir -p /tmp/lra-volume; "
                "cp -a \"$src_vol\" /tmp/lra-volume/; "
                "vol_name=$(basename \"$src_vol\"); "
                "target_root=\"/tmp/lra-volume/$vol_name\"; "
            )

    inner_args = [
        "python",
        "/work/governance/tools/governance/validate_volume.py",
        "__TARGET_ROOT__",
        "--json",
        f"/work/results/{json_name}",
        "--preprocess-dir",
        "/work/results/preprocessed",
    ]
    if args.chapter:
        inner_args.extend(["--chapter", args.chapter])
    if args.book:
        inner_args.extend(["--book", args.book])
    if args.fail_on_errors:
        inner_args.append("--fail-on-errors")
    quoted_inner = " ".join('"$target_root"' if arg == "__TARGET_ROOT__" else shlex.quote(arg) for arg in inner_args)
    quoted_log = shlex.quote(f"/work/results/{log_name}")
    inner = (
        f"{setup}{quoted_inner} > {quoted_log} 2>&1; "
        "status=$?; "
        f"tail -n 80 {quoted_log}; "
        "exit $status"
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
        f"{docker_support.docker_path(gov_root)}:/work/governance:ro",
        "-v",
        f"{docker_support.docker_path(volume_root)}:/work/volume:ro",
        "-v",
        f"{docker_support.docker_path(results)}:/work/results",
        "-w",
        "/work/volume",
        args.image,
        "bash",
        "-lc",
        inner,
    ]
    docker_support.run(cmd, cwd=gov_root)
    print(f"validation report: {results / json_name}")
    print(f"validation log: {results / log_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
