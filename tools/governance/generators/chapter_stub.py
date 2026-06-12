from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.volume import latex_input_path
from generators.section_stub import append_once, slugify, stub_section, write_new


def _tex(value: str) -> str:
    return (value or "").replace("\\", r"\textbackslash{}").replace("{", r"\{").replace("}", r"\}")


def _neighbors(subject: str, registry: list[dict]):
    subjects = [entry["subject"] for entry in registry]
    titles = [entry["display_title"] for entry in registry]
    if subject in subjects:
        index = subjects.index(subject)
        return (
            titles[index - 1] if index > 0 else "",
            subjects[index - 1] if index > 0 else "",
            titles[index + 1] if index < len(titles) - 1 else "",
            subjects[index + 1] if index < len(titles) - 1 else "",
        )
    return ("", "", "", "")


def render_breadcrumb(subject: str, display_title: str, registry: list[dict]) -> str:
    prior_title, _, next_title, _ = _neighbors(subject, registry)
    return (
        f"\\breadcrumb{{{_tex(subject)}}}{{{_tex(prior_title)}}}"
        f"{{{_tex(display_title)}}}{{{_tex(next_title)}}}"
    )


def _capstone_stub(subject: str, display_title: str) -> str:
    return (
        "\\newpage\n"
        "\\phantomsection\n"
        f"\\label{{cap:{subject}}}\n\n"
        "\\begin{tcolorbox}[\n"
        "  colback=gray!6,\n"
        "  colframe=gray!40,\n"
        "  arc=2pt,\n"
        "  left=8pt, right=8pt, top=6pt, bottom=6pt,\n"
        "  title={\\small\\textbf{Capstone Problem}},\n"
        "  fonttitle=\\small\\bfseries\n"
        "]\n"
        "\\textbf{Problem.}\n"
        f"TODO: state one synthesizing problem for {display_title}, using only concepts at or\n"
        "before this chapter in the registry.\n"
        "\\end{tcolorbox}\n\n"
        "\\begin{remark*}[Dependency ceiling]\n"
        "The capstone may use only results routed at or before this chapter.\n"
        "\\end{remark*}\n\n"
        "\\clearpage\n"
    )


def stub_chapter(volume_root, subject, display_title, registry, section_titles):
    volume_root = Path(volume_root)
    chapter = volume_root / subject
    if chapter.exists() and any(chapter.iterdir()):
        raise FileExistsError(f"refusing to overwrite existing chapter: {chapter}")

    (chapter / "notes").mkdir(parents=True, exist_ok=True)
    (chapter / "proofs").mkdir(parents=True, exist_ok=True)
    (chapter / "proofs" / "exercises").mkdir(parents=True, exist_ok=True)

    _prior_title, prior_subject, _next_title, next_subject = _neighbors(subject, registry)
    breadcrumb = render_breadcrumb(subject, display_title, registry)
    chapter_route = latex_input_path(chapter / "index.tex").removesuffix("/index")
    write_new(
        chapter / "index.tex",
        "% =========================================================\n"
        f"% Chapter: {display_title}\n"
        "% =========================================================\n"
        f"\\chapter{{{display_title}}}\n"
        f"\\label{{chap:{subject}}}\n\n"
        f"{breadcrumb}\n\n"
        f"\\input{{{chapter_route}/notes/index}}\n\n"
        "\\LRAExcludeFromPrintEditionBegin\n"
        "\\section*{Proofs}\n"
        f"\\input{{{chapter_route}/proofs/index}}\n\n"
        "\\section*{Capstone}\n"
        f"\\input{{{chapter_route}/proofs/exercises/index}}\n"
        "\\LRAExcludeFromPrintEditionEnd\n",
    )

    if section_titles:
        sections = "sections:\n" + "".join(
            f"  - subject: {slugify(title)}\n    display_title: \"{title}\"\n"
            for title in section_titles
        )
    else:
        sections = "sections: []\n"
    write_new(
        chapter / "chapter.yaml",
        f"subject: {subject}\ndisplay_title: \"{display_title}\"\nvolume: {volume_root.name}\n"
        f"status: planned\n{sections}dependencies:\n  prior: {prior_subject}\n  next: {next_subject}\n",
    )
    write_new(
        chapter / "notes" / "index.tex",
        f"% Notes index for chapter: {display_title}\n% Sections are \\section + \\input here in dependency order.\n",
    )
    write_new(
        chapter / "proofs" / "index.tex",
        f"% Proofs index for chapter: {display_title}\n% Proof topics \\input here, matching notes sections in dependency order.\n",
    )
    write_new(
        chapter / "proofs" / "exercises" / "index.tex",
        f"% Exercise proofs index for chapter: {display_title}\n"
        f"\\input{{{chapter_route}/proofs/exercises/capstone-{subject}}}\n",
    )
    write_new(
        chapter / "proofs" / "exercises" / f"capstone-{subject}.tex",
        _capstone_stub(subject, display_title),
    )

    for router in ("index.tex", "main.tex"):
        path = volume_root / router
        if path.exists():
            append_once(path, f"\\input{{{subject}/index}}")

    created = [stub_section(chapter, title) for title in section_titles]
    append_once(chapter / "proofs" / "index.tex", f"\\input{{{chapter_route}/proofs/exercises/index}}")
    return {"chapter": str(chapter), "sections": created}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Scaffold a canonical stub chapter.")
    parser.add_argument("--volume-root", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--sections", default="", help="section titles in order, ';'-separated")
    parser.add_argument("--registry", help="JSON list of {subject, display_title} in dependency order")
    args = parser.parse_args(argv)
    registry = json.loads(Path(args.registry).read_text()) if args.registry else []
    section_titles = [title.strip() for title in args.sections.split(";") if title.strip()]
    result = stub_chapter(args.volume_root, args.subject, args.title, registry, section_titles)
    print("created chapter:", result["chapter"])
    for section in result["sections"]:
        print("  section:", section["slug"])


if __name__ == "__main__":
    main()
