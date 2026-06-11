#!/usr/bin/env python3
"""Identify theorem-like statements in notes that lack a proof file/stub.

Conventions MIRROR tools/governance/audit_proof_layout.py (keep in sync): a proof
for a notes/{topic} theorem labelled thm|prop|lem|cor:{root} must live at
proofs/{topic}/prf-{root}.tex, labelled prf:{root}, reachable from
proofs/{topic}/index.tex. Read-only: this tool never writes.

Library + CLI. create_missing_proofs.py imports find_missing() and the helpers.
"""
from __future__ import annotations
import argparse, json, re
from dataclasses import dataclass, asdict
from pathlib import Path

THEOREM_ENV_RE = re.compile(
    r"\\begin\{(theorem|proposition|lemma|corollary)\}(?:\[([^\]]*)\])?(.*?)\\end\{\1\}",
    re.DOTALL)
LABEL_IN_BODY_RE = re.compile(r"\\label\{((?:thm|prop|lem|cor):[a-z0-9-]+)\}")
PROOF_LINK_RE   = re.compile(r"\\hyperref\[prf:[a-z0-9-]+\]")
DEPENDENCIES_RE = re.compile(r"\\begin\{dependencies\}.*?\\end\{dependencies\}", re.DOTALL)
INPUT_RE        = re.compile(r"\\(?:input|include)\{([^}]+)\}")

def find_chapter_roots(root: Path):
    roots = []
    for proofs_dir in root.rglob("proofs"):
        if proofs_dir.is_dir() and (proofs_dir.parent / "notes").is_dir():
            roots.append(proofs_dir.parent.resolve())
    if (root / "proofs").is_dir() and (root / "notes").is_dir():
        roots.append(root.resolve())
    return sorted(set(roots))

def volume_rel(chapter_root: Path) -> str:
    parts = chapter_root.resolve().parts
    for i, p in enumerate(parts):
        if re.fullmatch(r"volume-[ivx]+", p):
            return "/".join(parts[i:])
    return chapter_root.name

def topic_after(anchor: str, path: Path, chapter_root: Path):
    try:
        parts = path.resolve().relative_to(chapter_root.resolve()).parts
    except ValueError:
        return None
    if anchor not in parts:
        return None
    i = parts.index(anchor)
    return parts[i + 1] if i + 2 < len(parts) else None

def normalized_input_targets(text: str):
    out = set()
    for m in INPUT_RE.finditer(text):
        t = m.group(1).replace("\\", "/").removesuffix(".tex")
        out.add(t); out.add(Path(t).name)
    return out

def index_inputs(index_path: Path, target_rel: str) -> bool:
    if not index_path.exists():
        return False
    targets = normalized_input_targets(index_path.read_text(encoding="utf-8", errors="ignore"))
    return target_rel in targets or Path(target_rel).name in targets

def clean_restatement(body: str) -> str:
    keep = [ln for ln in body.splitlines()
            if not LABEL_IN_BODY_RE.search(ln) and not PROOF_LINK_RE.search(ln)]
    return "\n".join(keep).strip("\n")

@dataclass
class Obligation:
    chapter: str
    chapter_root_abs: str
    topic: str | None
    env: str
    thm_label: str
    root: str
    title: str
    notes_file: str
    expected_proof: str
    proof_label: str
    status: str   # missing | unindexed | present | unlabeled | no-topic

def iter_theorems(chapter_root: Path):
    notes = chapter_root / "notes"
    if not notes.exists():
        return
    for path in sorted(notes.rglob("*.tex")):
        if path.name == "index.tex":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in THEOREM_ENV_RE.finditer(text):
            env, title, body = m.group(1), (m.group(2) or "").strip(), m.group(3)
            lab = LABEL_IN_BODY_RE.search(body)
            yield path, env, title, (lab.group(1) if lab else None), body

def find_missing(root: Path, require_link: bool = False, topic_filter: str | None = None,
                 include_present: bool = False):
    out = []
    for chap in find_chapter_roots(root):
        vrel = volume_rel(chap)
        for path, env, title, label, body in iter_theorems(chap):
            if require_link and not PROOF_LINK_RE.search(body):
                continue
            topic = topic_after("notes", path, chap)
            if topic_filter and topic != topic_filter:
                continue
            notes_rel = path.resolve().relative_to(chap.resolve()).as_posix()
            if label is None:
                out.append(Obligation(vrel, str(chap), topic, env, "", "", title, notes_rel,
                                      "", "", "unlabeled"))
                continue
            rid = label.split(":", 1)[1]
            if topic is None:
                out.append(Obligation(vrel, str(chap), None, env, label, rid, title, notes_rel,
                                      "", f"prf:{rid}", "no-topic"))
                continue
            exp_rel = f"proofs/{topic}/prf-{rid}.tex"
            tgt = f"{vrel}/proofs/{topic}/prf-{rid}"
            if not (chap / exp_rel).exists():
                status = "missing"
            elif not index_inputs(chap / "proofs" / topic / "index.tex", tgt):
                status = "unindexed"
            else:
                status = "present"
            if status == "present" and not include_present:
                continue
            out.append(Obligation(vrel, str(chap), topic, env, label, rid, title, notes_rel,
                                  exp_rel, f"prf:{rid}", status))
    return out

def main():
    ap = argparse.ArgumentParser(description="Identify theorem-like statements lacking a proof file/stub.")
    ap.add_argument("--root", required=True, help="Leaf repo, volume, or chapter root.")
    ap.add_argument("--topic", help="Restrict to one notes/{topic}.")
    ap.add_argument("--require-proof-link", action="store_true",
                    help="Only count theorems carrying a \\hyperref[prf:...] 'Go to proof' link.")
    ap.add_argument("--include-present", action="store_true", help="Also list satisfied obligations.")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    a = ap.parse_args()
    obs = find_missing(Path(a.root).resolve(), a.require_proof_link, a.topic, a.include_present)
    if a.format == "json":
        print(json.dumps([asdict(o) for o in obs], indent=2)); return
    by = {}
    for o in obs:
        by.setdefault(o.status, []).append(o)
    order = ["missing", "unindexed", "unlabeled", "no-topic", "present"]
    print(f"root: {a.root}")
    for st in order:
        if st not in by:
            continue
        print(f"\n{st.upper()} ({len(by[st])}):")
        for o in by[st]:
            loc = o.expected_proof or "(no expected path)"
            print(f"  [{o.chapter}/{o.topic}] {o.thm_label or '(unlabeled)'}  \"{o.title}\"")
            print(f"       notes:    {o.notes_file}")
            if o.expected_proof:
                print(f"       expected: {loc}")
    counts = {st: len(v) for st, v in by.items()}
    print(f"\nsummary: {counts}")

if __name__ == "__main__":
    raise SystemExit(main())
