#!/usr/bin/env python3
r"""One-shot standardization driver for an LRA volume (or the whole work).

This SEQUENCES the proven migration tools in canonical run-book order via
subprocess -- it does NOT re-implement any of their logic, so this driver and the
individual tools agree by construction (same pattern as recon_volumes.py). One
command runs the whole pipeline; there is no multi-line copy-paste to fat-finger.

Every sub-tool runs in DRY-RUN by default. Pass --apply once and the entire
pipeline writes. The read-only recon gate (identify_*) always runs so you can see
the state between relocate and stub-gen.

Per-volume pipeline (--root <volume content dir>):
  A. cleanup    remove_status_planned, remove_legacy_chrome [, purge_archives]
  B. relocate   relocate_misplaced_notes, relocate_misplaced_files
  C. repair     repair_generated_latex
  D. gate       identify_misplaced_files, identify_missing_proofs   (read-only)
  E. fill       create_missing_proofs, ensure_capstones --upgrade-empty

Whole work (--all under --repos-root): runs A-D for every volume found, then
populates the GLOBAL breadcrumb chain once at the end (reading order i..viii).

Safe by design: relocate skips 'needs-human' items and create_missing_proofs
skips 'no-topic'/'unlabeled' theorems, so deferred chapters like integers are
correct no-ops -- no special-casing needed. Stops on the first tool that errors.

Examples:
  python standardize.py --root F:\repos\lra-volume-ii\volume-ii
  python standardize.py --root F:\repos\lra-volume-ii\volume-ii --apply
  python standardize.py --root F:\repos\lra-volume-ii\volume-ii --archive-name archive-current-live --apply
  python standardize.py --repos-root F:\repos --all
  python standardize.py --repos-root F:\repos --all --apply
  python standardize.py --repos-root F:\repos --breadcrumbs --apply
"""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

MIG = Path(__file__).resolve().parent
ROMANS = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii"]
# run-book review order (volumes are independent; breadcrumbs run last, globally)
DEFAULT_ORDER = ["vii", "vi", "viii", "v", "i", "iv", "ii", "iii"]


def run(script: str, args: list[str]) -> int:
    """Run a migration tool from the migration dir; stream its output live."""
    cmd = [sys.executable, str(MIG / script), *args]
    print(f"\n$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=str(MIG)).returncode


def stage(title: str) -> None:
    print("\n" + "=" * 72)
    print(f"== {title}")
    print("=" * 72)


def standardize_volume(vol: Path, apply: bool, *, require_proof_link=False,
                       topic=None, archive_names=None) -> bool:
    """Run stages A-D on one volume. Returns True iff every tool exited 0."""
    write = ["--apply"] if apply else []
    scope = ["--topic", topic] if topic else []

    def step(script: str, extra: list[str]) -> bool:
        rc = run(script, ["--root", str(vol), *extra])
        if rc != 0:
            print(f"\n!! {script} exited {rc} -- stopping pipeline for {vol.name}.")
        return rc == 0

    stage(f"{vol.name}: A. cleanup")
    if not step("remove_status_planned.py", write):
        return False
    if not step("remove_legacy_chrome.py", write):
        return False
    for name in (archive_names or []):
        if not step("purge_archives.py", ["--name", name, *write]):
            return False

    stage(f"{vol.name}: B. relocate (notes first, then proofs)")
    if not step("relocate_misplaced_notes.py", [*scope, *write]):
        return False
    if not step("relocate_misplaced_files.py", [*scope, *write]):
        return False

    stage(f"{vol.name}: C. repair generated LaTeX")
    if not step("repair_generated_latex.py", write):
        return False

    stage(f"{vol.name}: D. recon gate (read-only)")
    step("identify_misplaced_files.py", [])
    step("identify_missing_proofs.py", [])

    stage(f"{vol.name}: E. fill genuine gaps")
    cargs = list(scope) + (["--require-proof-link"] if require_proof_link else [])
    if not step("create_missing_proofs.py", [*cargs, *write]):
        return False
    if not step("ensure_capstones.py", ["--upgrade-empty", *write]):
        return False
    return True


def run_breadcrumbs(repos: Path, apply: bool) -> bool:
    """Populate the GLOBAL breadcrumb chain across all volumes, reading order."""
    stage("GLOBAL breadcrumbs (reading order i..viii)")
    args: list[str] = []
    for r in ROMANS:
        idx = repos / f"lra-volume-{r}" / f"volume-{r}" / "index.tex"
        if idx.exists():
            args += ["--volume-index", str(idx)]
    if not args:
        print("No volume index.tex files found; skipping breadcrumbs.")
        return True
    if apply:
        args.append("--apply")
    return run("populate_breadcrumbs.py", args) == 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="One-shot LRA standardization driver (dry-run by default).")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--root", help=r"One volume's CONTENT dir, e.g. F:\repos\lra-volume-ii\volume-ii")
    g.add_argument("--all", action="store_true",
                   help="Run every volume under --repos-root, then global breadcrumbs.")
    g.add_argument("--breadcrumbs", action="store_true",
                   help="Only (re)populate the global breadcrumb chain.")
    ap.add_argument("--repos-root", default=r"F:\repos",
                    help=r"Where the lra-volume-* repos live (default F:\repos).")
    ap.add_argument("--volumes", help="Comma list of romans to limit --all (e.g. vii,vi).")
    ap.add_argument("--apply", action="store_true",
                    help="Write changes. Omit for a full-pipeline dry-run.")
    ap.add_argument("--topic", help="Scope relocate/create to one notes/{topic}.")
    ap.add_argument("--require-proof-link", action="store_true",
                    help="create_missing_proofs only fills theorems that already declare a proof link.")
    ap.add_argument("--purge-archives", action="store_true",
                    help="Include archive purge in cleanup (name 'archive').")
    ap.add_argument("--archive-name", action="append", default=None,
                    help="Extra archive dir name(s) to purge (repeatable; implies --purge-archives).")
    ap.add_argument("--no-breadcrumbs", action="store_true",
                    help="With --all, skip the final breadcrumb step.")
    a = ap.parse_args()

    print(f"### LRA standardize -- {'APPLY (writing changes)' if a.apply else 'DRY-RUN (no writes)'}")
    repos = Path(a.repos_root).resolve()

    archive_names: list[str] = []
    if a.purge_archives or a.archive_name:
        archive_names = ["archive"] + [n for n in (a.archive_name or []) if n != "archive"]

    if a.breadcrumbs:
        return 0 if run_breadcrumbs(repos, a.apply) else 1

    if a.root:
        vol = Path(a.root).resolve()
        if not vol.is_dir():
            print(f"!! {vol} is not a directory.")
            return 2
        ok = standardize_volume(vol, a.apply, require_proof_link=a.require_proof_link,
                                topic=a.topic, archive_names=archive_names)
        print(f"\n### {'DONE' if ok else 'STOPPED ON ERROR'}: {vol.name}")
        return 0 if ok else 1

    # --all
    order = [r.strip() for r in a.volumes.split(",")] if a.volumes else DEFAULT_ORDER
    results: dict[str, bool] = {}
    for r in order:
        vol = repos / f"lra-volume-{r}" / f"volume-{r}"
        if not vol.is_dir():
            print(f"(skip volume-{r}: not found at {vol})")
            continue
        results[r] = standardize_volume(vol, a.apply, require_proof_link=a.require_proof_link,
                                        topic=a.topic, archive_names=archive_names)
        if not results[r]:
            print(f"\n!! Stopping --all at volume-{r} due to error.")
            break
    else:
        if not a.no_breadcrumbs:
            run_breadcrumbs(repos, a.apply)

    stage("SUMMARY")
    for r in order:
        if r in results:
            print(f"  volume-{r}: {'ok' if results[r] else 'ERROR'}")
    return 0 if results and all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
