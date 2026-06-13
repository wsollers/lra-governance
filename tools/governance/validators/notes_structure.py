from __future__ import annotations

import re
from pathlib import Path

from core.finding import Finding, finding
from core.file_inventory import reachable_files
from core.tex import INPUT_RE, is_routed, read_text, strip_latex_comment
from core.volume import chapter_roots, is_ignored


FORMAL_ENV_RE = re.compile(r"\\begin\{(?:definition|axiom|theorem|lemma|proposition|corollary)\}")
PROOF_ENV_RE = re.compile(r"\\begin\{proof\}")
UNSTARRED_SUBSECTION_RE = re.compile(r"\\sub(?:sub)?section(?:\[[^\]]*\])?\{[^{}]+\}")
TOPIC_SECTION_RE = re.compile(r"\\section(?:\[[^\]]*\])?\{[^{}]+\}")
TOPIC_SUBSECTION_RE = re.compile(r"\\subsection\*(?:\[[^\]]*\])?\{[^{}]+\}")
TOOLKIT_BEGIN_RE = re.compile(r"\\begin\{toolkitbox\}(?:\{.*\})?")
TOOLKIT_END_RE = re.compile(r"\\end\{toolkitbox\}")


def validate(volume_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for chapter in chapter_roots(volume_root):
        included = reachable_files(chapter)
        notes_root = chapter / "notes"
        notes_index = notes_root / "index.tex"
        if notes_index.exists() and notes_index.resolve() in included:
            _check_router_content(volume_root, notes_index, findings)
        if not notes_root.exists():
            continue
        for topic_dir in sorted(
            path for path in notes_root.iterdir() if path.is_dir() and not is_ignored(path, notes_root)
        ):
            topic_index = topic_dir / "index.tex"
            topic_index_included = topic_index.exists() and topic_index.resolve() in included
            if topic_index_included:
                _check_router_content(volume_root, topic_index, findings)
                _check_topic_router_only(volume_root, topic_index, included, findings)
                if not is_routed(notes_index, topic_index, chapter):
                    findings.append(
                        finding(
                            "unrouted_notes_topic",
                            f"notes/{topic_dir.name}/index.tex is not routed from notes/index.tex.",
                            topic_index,
                            volume_root,
                        )
                    )
            for body in sorted(topic_dir.glob("*.tex")):
                if body.name == "index.tex":
                    continue
                if body.resolve() not in included:
                    continue
                if body.name.startswith("figure-"):
                    continue
                if topic_index_included and not is_routed(topic_index, body, chapter):
                    findings.append(
                        finding(
                            "unrouted_notes_topic_body",
                            f"{body.relative_to(chapter).as_posix()} is not routed from notes/{topic_dir.name}/index.tex.",
                            body,
                            volume_root,
                        )
                    )
                _check_body_heading(volume_root, body, findings)
    return findings


def _check_router_content(volume_root: Path, index: Path, findings: list[Finding]) -> None:
    text = read_text(index)
    if FORMAL_ENV_RE.search(text) or PROOF_ENV_RE.search(text):
        findings.append(
            finding(
                "notes_index_contains_formal_content",
                "Notes index files must route note files, not contain formal artifacts or proofs.",
                index,
                volume_root,
            )
        )


def _check_topic_router_only(volume_root: Path, index: Path, included: set[Path], findings: list[Finding]) -> None:
    topic_body_count = sum(
        1
        for body in index.parent.glob("*.tex")
        if body.name != "index.tex" and not body.name.startswith("figure-")
        and body.resolve() in included
    )
    in_toolkit = False
    for line_no, raw in enumerate(read_text(index).splitlines(), 1):
        line = strip_latex_comment(raw).strip()
        if in_toolkit:
            if TOOLKIT_END_RE.search(line):
                in_toolkit = False
            continue
        if not line:
            continue
        if INPUT_RE.fullmatch(line) or TOPIC_SECTION_RE.fullmatch(line):
            continue
        if TOOLKIT_BEGIN_RE.fullmatch(line):
            in_toolkit = True
            continue
        if TOPIC_SUBSECTION_RE.fullmatch(line) and topic_body_count > 1:
            continue
        else:
            findings.append(
                finding(
                    "notes_topic_index_contains_rendered_content",
                    "notes/{topic}/index.tex must be a router containing only \\section lines, eligible \\subsection* lines, and input lines.",
                    index,
                    volume_root,
                    line_no,
                )
            )


def _check_body_heading(volume_root: Path, body: Path, findings: list[Finding]) -> None:
    text = read_text(body)
    match = UNSTARRED_SUBSECTION_RE.search(text)
    if match:
        line = text.count("\n", 0, match.start()) + 1
        findings.append(
            finding(
                "unstarred_subsection_body_heading",
                "Topic body files must use starred subsection headings so the table of contents remains a chapter-section spine.",
                body,
                volume_root,
                line,
            )
        )
