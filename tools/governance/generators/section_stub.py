from __future__ import annotations

import argparse
import re
from pathlib import Path

from core.volume import latex_input_path


def slugify(title: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return re.sub(r"-+", "-", text)


def append_once(path: Path, snippet: str) -> bool:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if snippet.strip() and snippet.strip() in text:
        return False
    with path.open("a", encoding="utf-8") as f:
        if text and not text.endswith("\n"):
            f.write("\n")
        f.write(snippet if snippet.endswith("\n") else snippet + "\n")
    return True


def insert_once_before(path: Path, snippet: str, before: str) -> bool:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if snippet.strip() and snippet.strip() in text:
        return False
    if before.strip() not in text:
        return append_once(path, snippet)
    insert = snippet if snippet.endswith("\n") else snippet + "\n"
    path.write_text(text.replace(before, insert + before, 1), encoding="utf-8")
    return True


def write_new(path: Path, text: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def stub_section(chapter_root: Path, title: str) -> dict:
    chapter_root = Path(chapter_root)
    slug = slugify(title)
    notes_dir = chapter_root / "notes" / slug
    proofs_dir = chapter_root / "proofs" / slug
    chapter_route = latex_input_path(chapter_root / "index.tex").removesuffix("/index")
    notes_dir.mkdir(parents=True, exist_ok=True)
    proofs_dir.mkdir(parents=True, exist_ok=True)
    write_new(
        notes_dir / "index.tex",
        f"% Section: {title}  (notes router; content authored later)\n\\section{{{title}}}\n",
    )
    write_new(proofs_dir / "index.tex", f"% Section: {title}  (proofs router; proof files \\input here as authored)\n")
    append_once(
        chapter_root / "notes" / "index.tex",
        f"\\input{{{latex_input_path(notes_dir / 'index.tex')}}}",
    )
    insert_once_before(
        chapter_root / "proofs" / "index.tex",
        f"\\input{{{latex_input_path(proofs_dir / 'index.tex')}}}",
        f"\\input{{{chapter_route}/proofs/exercises/index}}",
    )
    return {"slug": slug, "title": title, "notes": str(notes_dir), "proofs": str(proofs_dir)}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Scaffold a canonical stub section.")
    parser.add_argument("--chapter-root", required=True)
    parser.add_argument("--title", required=True)
    args = parser.parse_args(argv)
    result = stub_section(Path(args.chapter_root), args.title)
    print("created section:", result["slug"])


if __name__ == "__main__":
    main()
