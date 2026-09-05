#!/usr/bin/env python3
"""Build or validate one LRA repository.

The runner separates read-only validation from build/render steps:

1. local read-only checks can run in parallel;
2. local build commands run after those checks pass;
3. optional GitHub Actions dispatch/monitoring is a separate phase.

Exit codes:
  0 = all requested gates passed
  1 = local or remote gate failed
  2 = invalid invocation or unsupported repo kind
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


KNOWN_VOLUME_REPOS = {
    "lra-volume-i",
    "lra-volume-ii",
    "lra-volume-iii",
    "lra-volume-iv",
    "lra-volume-v",
    "lra-volume-vi",
    "lra-volume-vii",
    "lra-volume-viii",
}


@dataclass(frozen=True)
class Task:
    name: str
    command: list[str]
    cwd: Path
    stage: str
    optional: bool = False
    env: dict[str, str] | None = None


@dataclass
class TaskResult:
    name: str
    stage: str
    command: list[str]
    cwd: str
    status: str
    returncode: int | None = None
    seconds: float = 0.0
    optional: bool = False
    stdout_tail: str = ""
    stderr_tail: str = ""


@dataclass
class BuildReport:
    repo: str
    kind: str
    root: str
    local: list[TaskResult] = field(default_factory=list)
    remote: list[dict[str, Any]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        local_ok = all(r.status in {"pass", "skip", "dry-run"} or r.optional for r in self.local)
        remote_ok = all(r.get("status") in {"success", "skipped", "dry-run"} for r in self.remote)
        return local_ok and remote_ok


def tail(text: str, limit: int = 4000) -> str:
    text = text or ""
    return text[-limit:]


def print_task(task: Task) -> None:
    print(f"[{task.stage}] {task.name}")
    print(f"  cwd: {task.cwd}")
    print("  $ " + " ".join(task.command))


def run_task(task: Task, dry_run: bool) -> TaskResult:
    print_task(task)
    if dry_run:
        return TaskResult(
            name=task.name,
            stage=task.stage,
            command=task.command,
            cwd=str(task.cwd),
            status="dry-run",
            optional=task.optional,
        )

    started = time.monotonic()
    try:
        proc = subprocess.run(
            task.command,
            cwd=task.cwd,
            env=task.env,
            text=True,
            capture_output=True,
            shell=False,
        )
    except FileNotFoundError as exc:
        return TaskResult(
            name=task.name,
            stage=task.stage,
            command=task.command,
            cwd=str(task.cwd),
            status="skip" if task.optional else "fail",
            returncode=127,
            seconds=time.monotonic() - started,
            optional=task.optional,
            stderr_tail=str(exc),
        )

    status = "pass" if proc.returncode == 0 else ("skip" if task.optional else "fail")
    result = TaskResult(
        name=task.name,
        stage=task.stage,
        command=task.command,
        cwd=str(task.cwd),
        status=status,
        returncode=proc.returncode,
        seconds=time.monotonic() - started,
        optional=task.optional,
        stdout_tail=tail(proc.stdout),
        stderr_tail=tail(proc.stderr),
    )
    if result.stdout_tail:
        print(result.stdout_tail)
    if result.stderr_tail:
        print(result.stderr_tail, file=sys.stderr)
    print(f"  -> {result.status} ({result.returncode}) in {result.seconds:.1f}s")
    return result


def run_stage(tasks: list[Task], dry_run: bool, parallel: int) -> list[TaskResult]:
    if not tasks:
        return []
    if parallel <= 1 or len(tasks) == 1:
        return [run_task(task, dry_run) for task in tasks]

    results: list[TaskResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as pool:
        future_map = {pool.submit(run_task, task, dry_run): task for task in tasks}
        for future in concurrent.futures.as_completed(future_map):
            results.append(future.result())
    return sorted(results, key=lambda r: tasks.index(next(t for t in tasks if t.name == r.name)))


def has(path: Path) -> bool:
    return path.exists()


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def governance_root(start: Path) -> Path | None:
    for item in [start, *start.parents]:
        if (item / "capabilities" / "overlays-config.yaml").exists():
            return item
    sibling = start.parent / "lra-governance"
    if (sibling / "capabilities" / "overlays-config.yaml").exists():
        return sibling
    return None


def load_overlay_config(gov: Path | None) -> dict[str, dict[str, Any]]:
    if gov is None:
        return {}
    cfg = gov / "capabilities" / "overlays-config.yaml"
    if not cfg.exists():
        return {}
    try:
        import yaml

        data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return {entry.get("repo", ""): entry for entry in data.get("repos", []) if entry.get("repo")}


def infer_repo(root: Path, explicit: str | None, overlays: dict[str, dict[str, Any]]) -> tuple[str, str, dict[str, Any]]:
    repo = explicit or root.name
    entry = overlays.get(repo, {})
    if entry:
        return repo, entry.get("kind", "volume"), entry
    if repo in KNOWN_VOLUME_REPOS or has(root / "main.tex"):
        return repo, "volume", {}
    if has(root / "lakefile.lean") or has(root / "lean-toolchain"):
        return repo, "lean", {}
    if has(root / "CMakeLists.txt"):
        return repo, "cpp", {}
    if has(root / "capabilities" / "manifest.yaml"):
        return repo, "governance", {}
    return repo, "unknown", {}


def volume_validation_tasks(root: Path, args: argparse.Namespace, gov: Path | None, repo: str) -> list[Task]:
    tasks: list[Task] = []
    python = sys.executable
    local_tools = root / "tools" / "governance"
    gov_tools = gov / "tools" / "governance" if gov else None
    canonical = args.canonical_dir or (str(gov.parent) if gov else "")

    def tool(name: str) -> Path:
        local = local_tools / name
        if local.exists():
            return local
        if gov_tools:
            return gov_tools / name
        return local

    def add_if(path: Path, name: str, command: list[str], optional: bool = False) -> None:
        if path.exists():
            tasks.append(Task(name, command, root, "validate", optional=optional))

    scope: list[str] = ["--root", str(root)]
    if args.chapter:
        scope += ["--chapter", args.chapter]
    if args.section:
        scope += ["--section", args.section]

    decoration_path = tool("validate_decoration.py")
    decoration = [python, str(decoration_path), *scope]
    if repo == "lra-volume-iv":
        decoration.append("--no-require-box")
    if canonical:
        decoration += ["--canonical-dir", canonical]
    decoration.append("--fail-on-errors")
    add_if(decoration_path, "decoration validator", decoration)

    proof_layout_path = tool("audit_proof_layout.py")
    proof_layout = [python, str(proof_layout_path), *scope, "--strict"]
    add_if(proof_layout_path, "proof layout audit", proof_layout)

    volume_layout_path = tool("audit_volume_layout.py")
    volume_layout = [python, str(volume_layout_path), *scope, "--strict"]
    add_if(volume_layout_path, "volume layout audit", volume_layout)

    leaf_proofs = root / "scripts" / "validate_leaf_proofs.py"
    if leaf_proofs.exists():
        cmd = [python, str(leaf_proofs), "--root", str(root), "--strict"]
        if args.refactor_mode:
            cmd.append("--refactor-mode")
        tasks.append(Task("leaf proof validator", cmd, root, "validate"))

    note_blocks = root / "scripts" / "validate_note_blocks.py"
    if note_blocks.exists():
        tasks.append(Task("note block validator", [python, str(note_blocks), "--root", str(root)], root, "validate", optional=True))

    tasks.extend(script_help_tasks(root, repo, gov))
    return tasks


def volume_build_tasks(root: Path, args: argparse.Namespace) -> list[Task]:
    if args.validate_only:
        return []
    if has(root / "scripts" / "build_volume.py"):
        cmd = [sys.executable, str(root / "scripts" / "build_volume.py"), "--root", str(root)]
        if args.refactor_mode:
            cmd.append("--refactor-mode")
        if args.print_edition:
            cmd.append("--print-edition")
        return [Task("volume build wrapper", cmd, root, "build")]
    if has(root / "main.tex"):
        return [Task("latexmk main.tex", ["latexmk", "-lualatex", "main.tex"], root, "build")]
    return []


def lean_tasks(root: Path, args: argparse.Namespace, entry: dict[str, Any]) -> tuple[list[Task], list[Task]]:
    validate = script_help_tasks(root, entry.get("repo", root.name), governance_root(root), script_roots=["tools", "scripts", "reorder/tools"])
    if has(root / "build.ps1") and os.name == "nt":
        command = ["powershell", "-ExecutionPolicy", "Bypass", "-File", "build.ps1", "check", "-Native"]
        return validate, [Task("Lean build.ps1 check -Native", command, root, "build")]
    gates = entry.get("success_gates") or ["lake build"]
    return validate, [Task(f"Lean gate: {gate}", split_command(gate), root, "build") for gate in gates]


def cpp_tasks(root: Path, entry: dict[str, Any]) -> tuple[list[Task], list[Task]]:
    validate = code_layout_tasks(root, entry)
    validate.extend(script_help_tasks(root, entry.get("repo", root.name), governance_root(root)))
    gates = entry.get("success_gates") or []
    if gates:
        return validate, [Task(f"C++ gate: {gate}", split_command(gate), root, "build") for gate in gates]
    if has(root / "tools" / "build-msvc.ps1") and os.name == "nt":
        return validate, [Task("MSVC build helper", ["powershell", "-ExecutionPolicy", "Bypass", "-File", "tools\\build-msvc.ps1", "-Configuration", "Debug"], root, "build")]
    return validate, [
        Task("cmake configure", ["cmake", "-S", ".", "-B", "build", "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Debug"], root, "build"),
        Task("cmake build", ["cmake", "--build", "build"], root, "build"),
        Task("ctest", ["ctest", "--test-dir", "build", "--output-on-failure"], root, "build"),
    ]


def governance_tasks(root: Path) -> tuple[list[Task], list[Task]]:
    validate = [
        Task("capability resolver tests", [sys.executable, "capabilities/test_resolve.py"], root, "validate"),
        Task("generated task index check", [sys.executable, "capabilities/generate_task_index.py", "--check"], root, "validate"),
        Task("governance context audit", [sys.executable, "tools/governance/audit_governance_context.py"], root, "validate"),
        Task("decoration rule tests", [sys.executable, "tools/governance/test_decoration_rules.py"], root, "validate", optional=True),
        Task("parity fixtures", [sys.executable, "tools/governance/test_parity_fixtures.py"], root, "validate", optional=True),
    ]
    validate.extend(script_help_tasks(root, root.name, root))
    build = [
        Task("compile capability resolver", [sys.executable, "-m", "py_compile", "capabilities/resolve.py"], root, "build"),
        Task("compile task-index generator", [sys.executable, "-m", "py_compile", "capabilities/generate_task_index.py"], root, "build"),
        Task("compile governance context audit", [sys.executable, "-m", "py_compile", "tools/governance/audit_governance_context.py"], root, "build"),
        Task("compile code repo layout validator", [sys.executable, "-m", "py_compile", "tools/governance/validate_code_repo_layout.py"], root, "build"),
        Task("compile script help validator", [sys.executable, "-m", "py_compile", "tools/governance/validate_script_help.py"], root, "build"),
        Task("compile repo validator rollout", [sys.executable, "-m", "py_compile", "tools/governance/run_repo_validator_rollout.py"], root, "build"),
        Task("compile build_repo", [sys.executable, "-m", "py_compile", "capabilities/build-repo/build_repo.py"], root, "build"),
        Task("compile dependency graph tool", [sys.executable, "-m", "py_compile", "tools/governance/dependency_graph.py"], root, "build"),
        Task("compile dependency remark migration", [sys.executable, "-m", "py_compile", "tools/migration/migrate_dependency_remarks.py"], root, "build"),
    ]
    return validate, build


def generic_tasks(root: Path, entry: dict[str, Any]) -> tuple[list[Task], list[Task]]:
    gates = entry.get("success_gates") or []
    validate = code_layout_tasks(root, entry)
    validate.extend(script_help_tasks(root, entry.get("repo", root.name), governance_root(root)))
    return validate, [Task(f"gate: {gate}", split_command(gate), root, "build") for gate in gates]


def code_layout_tasks(root: Path, entry: dict[str, Any]) -> list[Task]:
    layout = entry.get("layout")
    if not layout:
        return []
    gov = governance_root(root)
    if not gov:
        return []
    tool = gov / "tools" / "governance" / "validate_code_repo_layout.py"
    if not tool.exists():
        return []
    return [
        Task(
            "code repository layout",
            [
                sys.executable,
                str(tool),
                "--root",
                str(root),
                "--repo",
                entry.get("repo", root.name),
                "--governance-root",
                str(gov),
            ],
            root,
            "validate",
        )
    ]


def script_help_tasks(root: Path, repo: str, gov: Path | None, script_roots: list[str] | None = None) -> list[Task]:
    if not gov:
        return []
    tool = gov / "tools" / "governance" / "validate_script_help.py"
    if not tool.exists():
        return []
    command = [
        sys.executable,
        str(tool),
        "--root",
        str(root),
        "--repo",
        repo,
    ]
    for item in script_roots or []:
        command.extend(["--script-root", item])
    return [Task("script help validator", command, root, "validate")]


def split_command(command: str) -> list[str]:
    import shlex

    if os.name == "nt":
        return shlex.split(command, posix=False)
    return shlex.split(command)


def plan_local(root: Path, repo: str, kind: str, entry: dict[str, Any], args: argparse.Namespace, gov: Path | None) -> tuple[list[Task], list[Task]]:
    if kind == "volume":
        return volume_validation_tasks(root, args, gov, repo), volume_build_tasks(root, args)
    if kind == "lean":
        return lean_tasks(root, args, entry)
    if kind == "cpp":
        return cpp_tasks(root, entry)
    if kind == "governance":
        return governance_tasks(root)
    return generic_tasks(root, entry)


def current_branch(root: Path) -> str:
    proc = subprocess.run(["git", "branch", "--show-current"], cwd=root, text=True, capture_output=True)
    branch = proc.stdout.strip()
    return branch or "main"


def workflow_files(root: Path, explicit: str | None) -> list[str]:
    if explicit:
        return [explicit]
    workflows = root / ".github" / "workflows"
    if not workflows.exists():
        return []
    return sorted(path.name for path in workflows.glob("*.yml")) + sorted(path.name for path in workflows.glob("*.yaml"))


def gh_json(root: Path, args: list[str]) -> Any:
    proc = subprocess.run(["gh", *args], cwd=root, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"gh {' '.join(args)} failed")
    return json.loads(proc.stdout or "[]")


def dispatch_workflow(root: Path, workflow: str, branch: str, dry_run: bool) -> dict[str, Any]:
    command = ["gh", "workflow", "run", workflow, "--ref", branch]
    print("[remote] dispatch " + workflow)
    print("  $ " + " ".join(command))
    if dry_run:
        return {"workflow": workflow, "status": "dry-run", "action": "dispatch"}
    proc = subprocess.run(command, cwd=root, text=True, capture_output=True)
    if proc.returncode != 0:
        return {"workflow": workflow, "status": "failure", "action": "dispatch", "stderr": tail(proc.stderr)}
    return {"workflow": workflow, "status": "success", "action": "dispatch"}


def monitor_workflow(root: Path, workflow: str, branch: str, timeout: int, interval: int, dry_run: bool) -> dict[str, Any]:
    print("[remote] monitor " + workflow)
    if dry_run:
        return {"workflow": workflow, "status": "dry-run", "action": "monitor"}
    deadline = time.monotonic() + timeout
    last: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        runs = gh_json(
            root,
            [
                "run",
                "list",
                "--workflow",
                workflow,
                "--branch",
                branch,
                "--limit",
                "1",
                "--json",
                "databaseId,status,conclusion,name,headSha,createdAt,url",
            ],
        )
        if runs:
            last = runs[0]
            status = last.get("status")
            conclusion = last.get("conclusion")
            print(f"  {workflow}: status={status} conclusion={conclusion or '-'} url={last.get('url', '')}")
            if status == "completed":
                ok = conclusion == "success"
                return {"workflow": workflow, "status": "success" if ok else "failure", "action": "monitor", "run": last}
        time.sleep(interval)
    return {"workflow": workflow, "status": "failure", "action": "monitor", "error": "timeout", "last": last}


def run_remote(root: Path, args: argparse.Namespace, dry_run: bool) -> list[dict[str, Any]]:
    if args.remote == "off":
        return []
    if not command_exists("gh") and not dry_run:
        return [{"status": "failure", "error": "gh CLI not found"}]
    branch = args.branch or current_branch(root)
    workflows = workflow_files(root, args.workflow)
    if not workflows:
        return [{"status": "skipped", "reason": "no workflow files found"}]

    results: list[dict[str, Any]] = []
    if args.remote in {"dispatch", "dispatch-monitor"}:
        for workflow in workflows:
            results.append(dispatch_workflow(root, workflow, branch, dry_run))
        if any(item.get("status") == "failure" for item in results):
            return results
    if args.remote in {"monitor", "dispatch-monitor"}:
        for workflow in workflows:
            results.append(monitor_workflow(root, workflow, branch, args.remote_timeout, args.remote_interval, dry_run))
    return results


def write_json_report(path: str | None, report: BuildReport) -> None:
    if not path:
        return
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, default=lambda obj: obj.__dict__, indent=2) + "\n", encoding="utf-8")
    print(f"json report: {out}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build or validate one LRA repository.")
    parser.add_argument("--root", type=Path, default=Path("."), help="Repository root.")
    parser.add_argument("--repo-name", help="Canonical repo name when root basename differs.")
    parser.add_argument("--chapter", help="Optional volume chapter scope.")
    parser.add_argument("--section", help="Optional volume section scope.")
    parser.add_argument("--canonical-dir", help="Canonical registry directory for decoration validation.")
    parser.add_argument("--validate-only", action="store_true", help="Run validation but skip render/build steps.")
    parser.add_argument("--refactor-mode", action="store_true")
    parser.add_argument("--print-edition", action="store_true")
    parser.add_argument("--parallel", type=int, default=max(1, min(4, (os.cpu_count() or 2))))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", help="Write machine-readable report.")
    parser.add_argument("--remote", choices=("off", "monitor", "dispatch", "dispatch-monitor"), default="off")
    parser.add_argument("--workflow", help="Workflow file/name to dispatch or monitor. Default: all workflow files.")
    parser.add_argument("--branch", help="Git branch/ref for remote workflow operations.")
    parser.add_argument("--remote-timeout", type=int, default=1800)
    parser.add_argument("--remote-interval", type=int, default=30)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    if not root.exists():
        print(f"fatal: root not found: {root}", file=sys.stderr)
        return 2

    gov = governance_root(root)
    overlays = load_overlay_config(gov)
    repo, kind, entry = infer_repo(root, args.repo_name, overlays)
    report = BuildReport(repo=repo, kind=kind, root=str(root))

    print(f"repo: {repo}")
    print(f"kind: {kind}")
    print(f"root: {root}")
    if kind == "unknown" and args.remote == "off":
        print("fatal: repo kind is unknown and no remote workflow mode was requested", file=sys.stderr)
        write_json_report(args.json, report)
        return 2

    validate_tasks, build_tasks = plan_local(root, repo, kind, entry, args, gov)

    report.local.extend(run_stage(validate_tasks, args.dry_run, args.parallel))
    failed_validation = any(result.status == "fail" and not result.optional for result in report.local)
    if failed_validation:
        print("local validation failed; skipping build stage", file=sys.stderr)
    else:
        report.local.extend(run_stage(build_tasks, args.dry_run, 1))

    local_failed = any(result.status == "fail" and not result.optional for result in report.local)
    if not local_failed:
        report.remote.extend(run_remote(root, args, args.dry_run))
    else:
        print("local build failed; skipping remote stage", file=sys.stderr)

    write_json_report(args.json, report)
    if report.ok:
        print("BUILD-REPO PASS")
        return 0
    print("BUILD-REPO FAIL", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
