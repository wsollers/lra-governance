r"""author-stub-section (pure Python, no LLM).

Creates a section topic under a chapter: notes/<slug>/index.tex and the matching
proofs/<slug>/index.tex, and routes each from its router (notes/index.tex carries
the \section heading; proofs/index.tex wires the proof topic). Deterministic.
"""
from __future__ import annotations
import re
from pathlib import Path

def slugify(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return re.sub(r"-+", "-", s)

def append_once(path: Path, snippet: str) -> bool:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if snippet.strip() and snippet.strip() in text:
        return False
    with path.open("a", encoding="utf-8") as f:
        if text and not text.endswith("\n"): f.write("\n")
        f.write(snippet if snippet.endswith("\n") else snippet + "\n")
    return True

def write_new(path: Path, text: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite existing file: {path}")
    path.write_text(text, encoding="utf-8")

def stub_section(chapter_root: Path, title: str) -> dict:
    chapter_root = Path(chapter_root)
    slug = slugify(title)
    notes_dir = chapter_root / "notes" / slug
    proofs_dir = chapter_root / "proofs" / slug
    notes_dir.mkdir(parents=True, exist_ok=True)
    proofs_dir.mkdir(parents=True, exist_ok=True)
    write_new(notes_dir / "index.tex", f"% Section: {title}  (notes router; content authored later)\n")
    write_new(proofs_dir / "index.tex", f"% Section: {title}  (proofs router; proof files \\input here as authored)\n")
    append_once(chapter_root / "notes" / "index.tex", f"\\section{{{title}}}\n\\input{{{slug}/index}}")
    append_once(chapter_root / "proofs" / "index.tex", f"\\input{{{slug}/index}}")
    return {"slug": slug, "title": title, "notes": str(notes_dir), "proofs": str(proofs_dir)}
