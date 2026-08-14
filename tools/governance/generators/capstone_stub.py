from __future__ import annotations

import re
from collections.abc import Sequence


_SUBJECT_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_LABEL_RE = re.compile(r"[a-z][a-z0-9-]*:[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def render_capstone_stub(
    chapter_subject: str,
    chapter_display_title: str,
    dependencies: Sequence[tuple[str, str]] | None = None,
) -> str:
    """Render a theorem-shaped capstone placeholder without inventing content."""
    if not _SUBJECT_RE.fullmatch(chapter_subject or ""):
        raise ValueError("chapter_subject must be lowercase ASCII words separated by hyphens")
    chapter_display_title = (chapter_display_title or "").strip()
    if not chapter_display_title:
        raise ValueError("chapter_display_title is required")
    if dependencies:
        items: list[str] = []
        for label, display in dependencies:
            if not _LABEL_RE.fullmatch(label or ""):
                raise ValueError(f"invalid dependency label: {label}")
            if not (display or "").strip():
                raise ValueError("dependency display name is required")
            items.append(f"  \\item \\hyperref[{label}]{{{display.strip()}}}")
        dependency_items = "\n".join(items)
    else:
        dependency_items = "  \\item TODO: list the supplied dependency labels."
    return (
        "\\phantomsection\n"
        f"\\label{{cap:{chapter_subject}}}\n\n"
        "\\begin{tcolorbox}[\n"
        "  colback=gray!6,\n"
        "  colframe=gray!40,\n"
        "  arc=2pt,\n"
        "  left=8pt, right=8pt, top=6pt, bottom=6pt,\n"
        "  title={\\small\\textbf{Capstone Theorem}},\n"
        "  fonttitle=\\small\\bfseries\n"
        "]\n"
        "\\textbf{Theorem.}\n"
        f"TODO: state the theorem-shaped capstone target for {chapter_display_title}.\n"
        "\\end{tcolorbox}\n\n"
        "\\begin{remark*}[Dependencies to state]\n"
        "TODO: list only supplied labels needed to parse the statement.\n"
        "\\end{remark*}\n\n"
        "\\begin{remark*}[Dependencies to prove]\n"
        "TODO: list only supplied labels needed to prove the theorem.\n"
        "\\end{remark*}\n\n"
        "\\begin{remark*}[Dependency ceiling]\n"
        "The capstone may use only results routed at or before this chapter.\n"
        "\\end{remark*}\n\n"
        "\\begin{dependencies}\n"
        "\\begin{itemize}\n"
        f"{dependency_items}\n"
        "\\end{itemize}\n"
        "\\end{dependencies}\n\n"
        "\\clearpage\n"
    )
