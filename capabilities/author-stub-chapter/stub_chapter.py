r"""author-stub-chapter (pure Python, no LLM).

Scaffolds a layout-validator-compliant chapter and, when section titles are given,
invokes stub_section for each (in order) directly in Python. Emits \breadcrumb +
\stubstatus + \chapterroadmap as first content (no Structural Roadmap), no capstone.
Routes the chapter into both volume routers (index.tex monorepo, main.tex local).
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

_here = Path(__file__).resolve()
for _up in _here.parents:
    if (_up / "capabilities").is_dir():
        sys.path.insert(0, str(_up / "capabilities" / "author-stub-section"))
        break
from stub_section import stub_section, slugify, append_once, write_new

def _tex(value: str) -> str:
    return (value or "").replace("\\", r"\textbackslash{}").replace("{", r"\{").replace("}", r"\}")

def render_breadcrumb(subject: str, display_title: str, registry: list[dict], is_stub: bool = True) -> str:
    prior_t, _, next_t, _ = _neighbors(subject, registry)
    out = (f"\\breadcrumb{{{_tex(subject)}}}{{{_tex(prior_t)}}}"
           f"{{{_tex(display_title)}}}{{{_tex(next_t)}}}")
    if is_stub:
        out += "\n\\stubstatus"
    return out

def _neighbors(subject, registry):
    subs = [e["subject"] for e in registry]; titles = [e["display_title"] for e in registry]
    if subject in subs:
        i = subs.index(subject)
        return (titles[i-1] if i > 0 else "", subs[i-1] if i > 0 else "",
                titles[i+1] if i < len(titles)-1 else "", subs[i+1] if i < len(titles)-1 else "")
    return ("", "", "", "")

def stub_chapter(volume_root, subject, display_title, registry, section_titles):
    volume_root = Path(volume_root); chap = volume_root / subject
    if chap.exists() and any(chap.iterdir()):
        raise FileExistsError(f"refusing to overwrite existing chapter: {chap}")
    (chap / "notes").mkdir(parents=True, exist_ok=True)
    (chap / "proofs").mkdir(parents=True, exist_ok=True)
    (chap / "proofs" / "exercises").mkdir(parents=True, exist_ok=True)
    write_new(chap / "proofs" / "exercises" / ".gitkeep", "")

    prior_t, prior_s, next_t, next_s = _neighbors(subject, registry)
    bc = render_breadcrumb(subject, display_title, registry, is_stub=True)
    topics = ", ".join(section_titles) if section_titles else "topics to be studied"
    roadmap = (f"\\chapterroadmap{{{prior_t or 'the prior development'}}}"
               f"{{{next_t or 'the next chapter'}}}{{{topics}}}")
    write_new(chap / "index.tex",
        f"\\chapter{{{display_title}}}\n{bc}\n{roadmap}\n\\input{{notes/index}}\n\\input{{proofs/index}}\n",
    )

    if section_titles:
        secs = "sections:\n" + "".join(
            f"  - subject: {slugify(t)}\n    display_title: \"{t}\"\n" for t in section_titles)
    else:
        secs = "sections: []\n"
    write_new(chap / "chapter.yaml",
        f"subject: {subject}\ndisplay_title: \"{display_title}\"\nvolume: {volume_root.name}\n"
        f"status: planned\n{secs}dependencies:\n  prior: {prior_s}\n  next: {next_s}\n")

    write_new(chap / "notes" / "index.tex",
        f"% Notes index for chapter: {display_title}\n% Status: Planned\n"
        f"% Sections are \\section + \\input here in dependency order.\n")
    write_new(chap / "proofs" / "index.tex",
        f"% Proofs index for chapter: {display_title}\n"
        f"% Proof topics \\input here, matching notes sections in dependency order.\n")

    for router in ("index.tex", "main.tex"):
        rp = volume_root / router
        if rp.exists():
            append_once(rp, f"\\input{{{subject}/index}}")

    created = [stub_section(chap, t) for t in section_titles]   # the atom, in order
    return {"chapter": str(chap), "sections": created}

def main(argv=None):
    ap = argparse.ArgumentParser(description="Scaffold a stub chapter (pure Python).")
    ap.add_argument("--volume-root", required=True)
    ap.add_argument("--subject", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--sections", default="", help="section titles in order, ';'-separated")
    ap.add_argument("--registry", help="JSON list of {subject, display_title} in dependency order")
    a = ap.parse_args(argv)
    registry = json.loads(Path(a.registry).read_text()) if a.registry else []
    titles = [t.strip() for t in a.sections.split(";") if t.strip()]
    res = stub_chapter(a.volume_root, a.subject, a.title, registry, titles)
    print("created chapter:", res["chapter"])
    for s in res["sections"]: print("  section:", s["slug"])

if __name__ == "__main__":
    main()
