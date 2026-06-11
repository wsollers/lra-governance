#!/usr/bin/env python3
r"""Recon driver: run every read-only / dry-run migration tool across the volume
content trees (volume-i .. volume-viii) and emit one divergence matrix + report.

It targets the INNER content dir of each volume repo (lra-volume-<r>/volume-<r>),
so the CI-synced common/, governance/, constitution/ overlays at each repo root --
and the monorepo -- are never scanned. Read-only: every tool runs in its default
(identify / dry-run) mode; nothing is written to any volume.

Usage:
  python recon_volumes.py --repos-root F:\repos --out reports\recon-matrix.md
"""
from __future__ import annotations
import argparse, json, re, subprocess, sys
from collections import Counter
from pathlib import Path

ROMANS = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii"]
MIG = Path(__file__).resolve().parent

def run(script, root, extra):
    cmd = [sys.executable, str(MIG / script), "--root", str(root), *extra]
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=str(MIG))
    return p.returncode, p.stdout, p.stderr

def headline(out):
    lines = [l for l in out.splitlines() if l.strip()]
    return lines[-1] if lines else ""

def json_tool(script, root):
    rc, out, err = run(script, root, ["--format", "json"])
    if rc != 0:
        return None, (err.strip().splitlines() or [""])[-1][:140]
    try:
        return json.loads(out or "[]"), None
    except json.JSONDecodeError as e:
        return None, f"bad json: {e}"

def scrape_tool(script, root, count_rx, extra=None):
    rc, out, err = run(script, root, extra or [])
    if rc != 0:
        return None, (err.strip().splitlines() or [""])[-1][:140], ""
    m = re.search(count_rx, out)
    return (int(m.group(1)) if m else None), None, headline(out)

def recon_volume(vol_dir: Path):
    row = {}
    detail = {}
    full = stubs = 0
    for p in sorted(vol_dir.iterdir()):
        if not p.is_dir():
            continue
        if not ((p / "chapter.yaml").exists() or (p / "index.tex").exists()):
            continue
        if (p / "notes").is_dir() and (p / "proofs").is_dir():
            full += 1
        else:
            stubs += 1
    row["full"] = full; row["stubs"] = stubs
    # --- missing proofs (json) ---
    data, err = json_tool("identify_missing_proofs.py", vol_dir)
    if err is None:
        c = Counter(o["status"] for o in data)
        row["missing"] = c.get("missing", 0); row["unindexed"] = c.get("unindexed", 0)
        detail["missing_proofs"] = dict(c)
    else:
        row["missing"] = row["unindexed"] = "ERR"; detail["missing_proofs"] = {"error": err}
    # --- misplaced proof files (json) ---
    data, err = json_tool("identify_misplaced_files.py", vol_dir)
    if err is None:
        c = Counter(i["kind"] for i in data)
        row["misplaced"] = sum(v for k,v in c.items() if k!="flat_notes"); detail["misplaced_files"] = dict(c)
    else:
        row["misplaced"] = "ERR"; detail["misplaced_files"] = {"error": err}
    # --- flat notes (json) ---
    data, err = json_tool("identify_misplaced_notes.py", vol_dir)
    if err is None:
        row["flat_notes"] = len(data)
        detail["flat_notes"] = dict(Counter(i["status"] for i in data))
    else:
        row["flat_notes"] = "ERR"; detail["flat_notes"] = {"error": err}
    # --- dry-run text tools (scrape count) ---
    for key, script, rx in [
        ("capstone_gaps", "ensure_capstones.py", r"DRY-RUN:\s*(\d+) chapter"),
        ("status_planned", "remove_status_planned.py", r"DRY-RUN:\s*(\d+) marker"),
        ("legacy_chrome", "remove_legacy_chrome.py", r"Dry-run:\s*(\d+) legacy block"),
        ("archives", "purge_archives.py", r"DRY-RUN:\s*(\d+) archive dir"),
    ]:
        n, err, head = scrape_tool(script, vol_dir, rx)
        row[key] = ("ERR" if err else (n if n is not None else "?"))
        detail[key] = {"headline": head} if not err else {"error": err}
    if row.get("archives") == "?":
        row["archives"] = 0   # purge_archives prints "No 'archive' directories" when none exist
    return row, detail

COLS = [("full","chap"),("stubs","stub"),("missing","miss"),("unindexed","unidx"),("misplaced","misp"),("flat_notes","flatN"),
        ("capstone_gaps","caps"),("status_planned","statP"),("legacy_chrome","chrome"),("archives","arch")]

def main():
    ap = argparse.ArgumentParser(description="Recon all volume content trees (read-only).")
    ap.add_argument("--repos-root", required=True, help=r"e.g. F:\repos")
    ap.add_argument("--out", help="Write full markdown report here.")
    ap.add_argument("--volumes", help="Comma list of romans to limit (default all i..viii).")
    a = ap.parse_args()
    repos = Path(a.repos_root).resolve()
    romans = [r.strip() for r in a.volumes.split(",")] if a.volumes else ROMANS

    rows = {}; details = {}; found = []
    for r in romans:
        vol = repos / f"lra-volume-{r}" / f"volume-{r}"
        if not vol.is_dir():
            continue
        found.append(r)
        rows[r], details[r] = recon_volume(vol)

    # ---- matrix ----
    hdr = "| volume | " + " | ".join(short for _, short in COLS) + " |"
    sep = "|" + "---|" * (len(COLS) + 1)
    body = []
    for r in found:
        cells = " | ".join(str(rows[r].get(k, "")) for k, _ in COLS)
        body.append(f"| volume-{r} | {cells} |")
    matrix = "\n".join([hdr, sep, *body])

    lines = ["# LRA volume recon (read-only)", "",
             f"repos-root: `{repos}`  |  volumes found: {', '.join('volume-'+r for r in found) or 'none'}",
             "", "## Divergence matrix", "", matrix, "",
             "Legend: chap=full chapters (notes+proofs), stub=stub/partial chapters, miss=missing proof stubs, unidx=unindexed proofs, misp=misplaced proof files, "
             "flatN=flat notes, caps=chapters needing capstone action, statP=Status:Planned marker lines, "
             "chrome=legacy chrome blocks, arch=archive dirs. ERR=tool failed (see detail).", ""]
    lines += ["## Per-volume detail", ""]
    for r in found:
        lines.append(f"### volume-{r}")
        for k, v in details[r].items():
            lines.append(f"- **{k}**: {json.dumps(v)}")
        lines.append("")
    report = "\n".join(lines)

    print(matrix)
    print(f"\n[{len(found)} volume(s) reconned]")
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(report + "\n", encoding="utf-8")
        print(f"full report -> {a.out}")

if __name__ == "__main__":
    raise SystemExit(main())
