#!/usr/bin/env python3
"""Launch VS Code for LRA volume LaTeX editing in the governed devcontainer."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from install_volume_devcontainer import common_root, governance_root, install, is_volume_repo


VALID_VOLUME_ROMANS = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii"]
ROMAN_BY_NUMBER = {
    "1": "i",
    "2": "ii",
    "3": "iii",
    "4": "iv",
    "5": "v",
    "6": "vi",
    "7": "vii",
    "8": "viii",
}
VALID_ROMANS = set(VALID_VOLUME_ROMANS)


def normalize_volume(value: str) -> str:
    cleaned = value.strip().lower().removeprefix("volume-").removeprefix("lra-volume-")
    roman = ROMAN_BY_NUMBER.get(cleaned, cleaned)
    if roman not in VALID_ROMANS:
        expected = ", ".join(VALID_VOLUME_ROMANS)
        raise SystemExit(f"unsupported volume {value!r}; expected 1-8 or one of: {expected}")
    return roman


def find_volume_from_cwd(cwd: Path) -> Path | None:
    for candidate in [cwd, *cwd.parents]:
        if is_volume_repo(candidate):
            return candidate.resolve()
    return None


def resolve_volume_root(args: argparse.Namespace) -> Path:
    if args.root and args.volume:
        raise SystemExit("--root and --volume are mutually exclusive")
    if args.root:
        root = args.root.expanduser().resolve()
    elif args.volume:
        root = args.workspace.expanduser().resolve() / f"lra-volume-{normalize_volume(args.volume)}"
    else:
        root = find_volume_from_cwd(Path.cwd())
        if root is None:
            raise SystemExit("not inside an lra-volume repository; pass --root or --volume")
    if not is_volume_repo(root):
        raise SystemExit(f"not an lra-volume repository root: {root}")
    return root


def encode_hex(text: str) -> str:
    return text.encode("utf-8").hex()


def devcontainer_folder_uri(root: Path) -> str:
    host_path = root.resolve().as_posix()
    container_workspace = f"/workspaces/{root.name}"
    return f"vscode-remote://dev-container%2B{encode_hex(host_path)}{container_workspace}"


def run_checked(command: list[str], cwd: Path | None = None) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def launch_with_code(args: argparse.Namespace, root: Path) -> None:
    code = args.code or shutil.which("code")
    if not code:
        raise SystemExit("VS Code CLI not found on PATH; install code CLI or pass --code")

    command = [code]
    if args.new_window:
        command.append("--new-window")
    elif args.reuse_window:
        command.append("--reuse-window")

    if args.launch_mode == "plain-code":
        command.append(str(root))
    else:
        command.extend(["--folder-uri", devcontainer_folder_uri(root)])
    subprocess.Popen(command, cwd=root)
    print("launched: " + " ".join(command))


def extension_installed(code: str) -> bool:
    try:
        result = subprocess.run([code, "--list-extensions"], check=True, capture_output=True, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False
    return "ms-vscode-remote.remote-containers" in {line.strip().lower() for line in result.stdout.splitlines()}


def ensure_extension(args: argparse.Namespace) -> None:
    if args.launch_mode == "plain-code" or args.no_extension_check:
        return
    code = args.code or shutil.which("code")
    if not code:
        return
    if extension_installed(code):
        return
    if args.install_extension:
        run_checked([code, "--install-extension", "ms-vscode-remote.remote-containers"])
        return
    print(
        "warning: VS Code Dev Containers extension is not installed. "
        "Install ms-vscode-remote.remote-containers or rerun with --install-extension."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, help="target lra-volume-* repository root")
    parser.add_argument("--volume", help="volume number or roman numeral, e.g. 3 or iii")
    parser.add_argument("--workspace", type=Path, default=Path.cwd().parent, help="workspace containing sibling lra-volume-* repos")
    parser.add_argument("--common-root", type=Path, help="lra-common checkout root")
    parser.add_argument("--code", help="VS Code CLI executable; defaults to code on PATH")
    parser.add_argument(
        "--launch-mode",
        choices=["devcontainer-uri", "plain-code"],
        default="devcontainer-uri",
        help="open directly through VS Code's Dev Containers URI or open the prepared folder normally",
    )
    parser.add_argument("--new-window", action="store_true", help="open VS Code in a new window")
    parser.add_argument("--reuse-window", action="store_true", help="reuse the active VS Code window")
    parser.add_argument("--no-launch", action="store_true", help="install the shim but do not start VS Code")
    parser.add_argument("--no-install", action="store_true", help="do not refresh the .devcontainer shim")
    parser.add_argument("--install-extension", action="store_true", help="install the VS Code Dev Containers extension if missing")
    parser.add_argument("--no-extension-check", action="store_true", help="skip checking for the VS Code Dev Containers extension")
    args = parser.parse_args(argv)

    if args.new_window and args.reuse_window:
        raise SystemExit("--new-window and --reuse-window are mutually exclusive")

    root = resolve_volume_root(args)
    gov_root = governance_root()
    common = common_root(gov_root, args.common_root)

    if not args.no_install:
        for path, status in install(root, gov_root, common, write=True):
            print(f"{status}: {path}")

    if args.no_launch:
        return 0

    ensure_extension(args)
    launch_with_code(args, root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
