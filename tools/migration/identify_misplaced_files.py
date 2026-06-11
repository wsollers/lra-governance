#!/usr/bin/env python3
"""Identify .tex source files that violate the canonical chapter layout.

Required layout (constitution/schema/file-schema.yaml): a chapter is a set of
notes/{topic}/ <-> proofs/{topic}/ pairs, each with index.tex; proof files live
at proofs/{topic}/prf-{root}.tex. Legacy flat files under notes/ or proofs/notes/
are misplaced. A misplaced proof's correct topic is its theorem's notes topic.

Conventions mirror audit_volume_layout.py + audit_proof_layout.py (keep in sync).
Read-only: never writes. Library (find_misplaced) + CLI. archive/ is excluded.
"""
from __future__ import annotations
import argparse, json, re
from dataclasses import dataclass, asdict
from pathlib import Path

THEOREM_LABEL_RE = re.compile(r"\\label\{((?:thm|lem|prop|cor):[a-z0-9-]+)\}")
PROOF_LABEL_RE   = re.compile(r"\\label\{prf:([a-z0-9-]+)\}")
PROOF_FOR_RE     = re.compile(r"\\LRAProofFor\{((?:thm|lem|prop|cor):[a-z0-9-]+)\}")
RETURN_LABEL_RE  = re.compile(r"\\hyperref\[((?:thm|lem|prop|cor):[a-z0-9-]+)\]")
SOURCE_TOPIC_RE  = re.compile(r"%\s*Source:\s*\S*?/notes/([a-z0-9-]+)/", re.IGNORECASE)
INPUT_RE         = re.compile(r"\\(?:input|include)\{([^}]+)\}")
GOOD_PROOF_NAME  = re.compile(r"^prf-[a-z0-9-]+\.tex$")
EXCLUDE_DIRS     = {"archive"}

def _excluded(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)

def find_chapter_roots(root: Path):
    root = root.resolve()
    if (root / "notes").is_dir() and (root / "proofs").is_dir() and not _excluded(root):
        return [root]
    out = []
    for proofs_dir in root.rglob("proofs"):
        chap = proofs_dir.parent
        if proofs_dir.is_dir() and (chap / "notes").is_dir() and not _excluded(chap):
            out.append(chap.resolve())
    return sorted(set(out))

def volume_rel(chapter_root: Path) -> str:
    parts = chapter_root.resolve().parts
    for i, p in enumerate(parts):
        if re.fullmatch(r"volume-[ivx]+", p):
            return "/".join(parts[i:])
    return chapter_root.name

def topic_after(anchor: str, path: Path, chapter_root: Path):
    parts = path.resolve().relative_to(chapter_root.resolve()).parts
    if anchor not in parts:
        return None
    i = parts.index(anchor)
    return parts[i + 1] if i + 2 < len(parts) else None

def note_topics(chapter_root: Path):
    out = {}
    notes = chapter_root / "notes"
    if not notes.exists():
        return out
    for path in sorted(notes.rglob("*.tex")):
        if path.name == "index.tex":
            continue
        topic = topic_after("notes", path, chapter_root)
        if not topic:
            continue
        for lab in THEOREM_LABEL_RE.findall(path.read_text(encoding="utf-8", errors="ignore")):
            out[lab] = topic
    return out

def existing_topics(chapter_root: Path):
    notes = {p.name for p in (chapter_root / "notes").iterdir() if p.is_dir()} if (chapter_root/"notes").is_dir() else set()
    return notes

def resolve_topic(text: str, prf_root: str, notes_map: dict, valid_topics: set):
    """Return (topic, signal) or (None, None)."""
    m = SOURCE_TOPIC_RE.search(text)
    if m and m.group(1) in valid_topics:
        return m.group(1), "source-comment"
    for rx, sig in ((PROOF_FOR_RE, "LRAProofFor"), (RETURN_LABEL_RE, "return-link")):
        mm = rx.search(text)
        if mm and mm.group(1) in notes_map:
            return notes_map[mm.group(1)], sig
    for lab, topic in notes_map.items():        # match by shared root
        if lab.split(":", 1)[1] == prf_root:
            return topic, "root-match"
    return None, None

@dataclass
class Misplacement:
    chapter: str
    chapter_root_abs: str
    kind: str            # legacy_proofs_notes | proof_topic_mismatch | flat_notes |
                         # nonconforming_proof_name | vestigial_legacy_dir
    current: str         # chapter-relative posix
    target: str          # chapter-relative posix ("" if unresolved)
    topic: str | None
    signal: str | None
    status: str          # movable | needs-human | cleanup

def proof_files(chapter_root: Path):
    proofs = chapter_root / "proofs"
    if not proofs.exists():
        return
    for path in sorted(proofs.rglob("*.tex")):
        if path.name == "index.tex" or _excluded(path):
            continue
        if "exercises" in path.relative_to(proofs).parts:
            continue
        yield path

def find_misplaced(root: Path, topic_filter: str | None = None):
    out = []
    for chap in find_chapter_roots(root):
        notes_map = note_topics(chap)
        valid = existing_topics(chap)
        # ---- proof files ----
        for path in proof_files(chap):
            rel = path.relative_to(chap).as_posix()
            cur_topic = topic_after("proofs", path, chap)
            text = path.read_text(encoding="utf-8", errors="ignore")
            pm = PROOF_LABEL_RE.search(text)
            prf_root = pm.group(1) if pm else path.stem.removeprefix("prf-")
            legacy = (cur_topic == "notes") or (cur_topic is None)
            if legacy:
                tt, sig = resolve_topic(text, prf_root, notes_map, valid)
                if topic_filter and tt != topic_filter:
                    continue
                target = f"proofs/{tt}/prf-{prf_root}.tex" if tt else ""
                out.append(Misplacement(volume_rel(chap), str(chap), "legacy_proofs_notes",
                                        rel, target, tt, sig, "movable" if tt else "needs-human"))
                continue
            # in a topic already: check mismatch + name
            tt, sig = resolve_topic(text, prf_root, notes_map, valid)
            if tt and tt != cur_topic:
                if topic_filter and tt != topic_filter:
                    continue
                out.append(Misplacement(volume_rel(chap), str(chap), "proof_topic_mismatch",
                                        rel, f"proofs/{tt}/prf-{prf_root}.tex", tt, sig, "movable"))
            elif not GOOD_PROOF_NAME.match(path.name):
                out.append(Misplacement(volume_rel(chap), str(chap), "nonconforming_proof_name",
                                        rel, f"proofs/{cur_topic}/prf-{prf_root}.tex", cur_topic,
                                        "label-root", "movable"))
        # ---- flat notes files ----
        notes = chap / "notes"
        if notes.is_dir():
            for path in sorted(notes.glob("*.tex")):
                if path.name == "index.tex":
                    continue
                stem_topic = path.stem.removeprefix("notes-")
                tt = stem_topic if stem_topic in valid else None
                if topic_filter and tt != topic_filter:
                    continue
                out.append(Misplacement(volume_rel(chap), str(chap), "flat_notes",
                                        path.relative_to(chap).as_posix(),
                                        f"notes/{tt}/{path.name}" if tt else "",
                                        tt, "filename" if tt else None,
                                        "movable" if tt else "needs-human"))
        # ---- vestigial legacy proofs/notes dir (only index.tex) ----
        pn = chap / "proofs" / "notes"
        if pn.is_dir():
            movable_here = [p for p in pn.glob("*.tex") if p.name != "index.tex"]
            if not movable_here:
                out.append(Misplacement(volume_rel(chap), str(chap), "vestigial_legacy_dir",
                                        "proofs/notes", "", None, None, "cleanup"))
    return out

def main():
    ap = argparse.ArgumentParser(description="Identify misplaced .tex files vs the canonical layout.")
    ap.add_argument("--root", required=True, help="Leaf repo, volume, or chapter root.")
    ap.add_argument("--topic", help="Restrict to one target {topic}.")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    a = ap.parse_args()
    items = find_misplaced(Path(a.root).resolve(), a.topic)
    if a.format == "json":
        print(json.dumps([asdict(i) for i in items], indent=2)); return
    by = {}
    for i in items:
        by.setdefault(i.kind, []).append(i)
    print(f"root: {a.root}")
    for kind, lst in by.items():
        print(f"\n{kind.upper()} ({len(lst)}):")
        for i in lst:
            arrow = f"  ->  {i.target}" if i.target else "  ->  (unresolved; needs human)"
            print(f"  [{i.status}] {i.current}{arrow}"
                  + (f"   ({i.signal})" if i.signal else ""))
    print(f"\nsummary: { {k: len(v) for k, v in by.items()} }")

if __name__ == "__main__":
    raise SystemExit(main())
