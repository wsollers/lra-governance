from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


DEFAULT_GOVERNANCE_TEST_IMAGE = "lra-governance-test"


def governance_root() -> Path:
    return Path(__file__).resolve().parents[2]


def docker_path(path: Path) -> str:
    return str(path.expanduser().resolve())


def require_docker() -> None:
    if shutil.which("docker") is None:
        raise SystemExit("required tool not found on PATH: docker")


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+ " + " ".join(str(part) for part in cmd))
    try:
        subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from None


def build_governance_test_image(image: str = DEFAULT_GOVERNANCE_TEST_IMAGE) -> None:
    require_docker()
    root = governance_root()
    docker_dir = root / "docker" / "governance-test"
    run(["docker", "build", "-t", image, "-f", str(docker_dir / "Dockerfile"), str(docker_dir)], cwd=root)


def mounted_results_dir(path: Path | None, default_name: str) -> Path:
    root = governance_root()
    results = path.expanduser().resolve() if path else root / "build" / "docker-results" / default_name
    results.mkdir(parents=True, exist_ok=True)
    return results
