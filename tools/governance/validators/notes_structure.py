from __future__ import annotations

import re
from pathlib import Path

from core.finding import Finding, finding
from core.file_inventory import validator_file_set
from core.tex import INPUT_RE, is_routed, read_text, strip_latex_comment
from core.volume import routed_chapter_roots, is_ignored


FORMAL_ENV_RE = re.compile(r"\\begin\{(?:definition|axiom|theorem|lemma|proposition|corollary)\}")
PROOF_ENV_RE = re.compile(r"\\begin\{proof\}")
_SECTION_TITLE = r"(?:[^{}]|\{[^{}]*\})+"
UNSTARRED_SUBSECTION_RE = re.compile(rf"\\sub(?:sub)?section(?:\[[^\]]*\])?\{{{_SECTION_TITLE}\}}")
TOOLKIT_BEGIN_RE = re.compile(r"\\begin\{toolkitbox\}(?:\{.*\})?")
TOOLKIT_END_RE = re.compile(r"\\end\{toolkitbox\}")


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    for chapter in routed_chapter_roots(volume_root):
        included = validator_file_set(chapter, files)
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
                if body.name.startswith("figure-") or body.stem.startswith("figure"):
                    continue
                if topic_index_included and not is_routed(topic_index, body, chapter):
                    findings.append(
                        finding(
                            "unrouted_notes_topic_body",
                            f"{body.relative_to(chapter).as_posix()} is not routed from notes/{topic_dir.name}/index.tex.",
                            body,
                            volume_root,
                            severity="warning",
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
    in_toolkit = False
    seen_section = False
    for line_no, raw in enumerate(read_text(index).splitlines(), 1):
        line = strip_latex_comment(raw).strip()
        if in_toolkit:
            if TOOLKIT_END_RE.search(line):
                in_toolkit = False
            continue
        if not line:
            continue
        if _is_topic_section_line(line):
            if seen_section:
                findings.append(
                    finding(
                        "notes_topic_index_duplicate_section",
                        "notes/{topic}/index.tex must contain exactly one non-starred \\section{...} heading.",
                        index,
                        volume_root,
                        line_no,
                    )
                )
            seen_section = True
            continue
        if _is_topic_subsection_line(line):
            if not seen_section:
                findings.append(
                    finding(
                        "notes_topic_index_missing_section",
                        "notes/{topic}/index.tex must begin rendered content with one non-starred \\section{...} before nested subsection headings.",
                        index,
                        volume_root,
                        line_no,
                    )
                )
            continue
        if INPUT_RE.fullmatch(line):
            if not seen_section:
                findings.append(
                    finding(
                        "notes_topic_index_missing_section",
                        "notes/{topic}/index.tex must begin rendered content with one non-starred \\section{...} before body inputs.",
                        index,
                        volume_root,
                        line_no,
                    )
                )
            continue
        if TOOLKIT_BEGIN_RE.fullmatch(line):
            if not seen_section:
                findings.append(
                    finding(
                        "notes_topic_index_missing_section",
                        "notes/{topic}/index.tex must begin rendered content with one non-starred \\section{...} before toolkit or body content.",
                        index,
                        volume_root,
                        line_no,
                    )
                )
            in_toolkit = True
            continue
        else:
            findings.append(
                finding(
                    "notes_topic_index_contains_rendered_content",
                    "notes/{topic}/index.tex may contain comments, exactly one non-starred \\section{...}, nested non-starred \\subsection{...} headings, an optional toolkit box, and input lines only.",
                    index,
                    volume_root,
                    line_no,
                )
            )
    if not seen_section:
        findings.append(
            finding(
                "notes_topic_index_missing_section",
                "notes/{topic}/index.tex must contain exactly one non-starred \\section{...} heading.",
                index,
                volume_root,
            )
        )


def _check_body_heading(volume_root: Path, body: Path, findings: list[Finding]) -> None:
    for line_no, raw in enumerate(read_text(body).splitlines(), 1):
        line = strip_latex_comment(raw).strip()
        if _starts_section_command(line):
            findings.append(
                finding(
                    "notes_topic_body_section_heading",
                    "Note body files must not introduce top-level \\section headings; the topic router owns \\section{...}. Use \\subsection{...} for nested note headings.",
                    body,
                    volume_root,
                    line_no,
                )
            )


def _is_topic_section_line(line: str) -> bool:
    return _is_heading_line(line, command="section", starred=False)


def _is_topic_subsection_line(line: str) -> bool:
    return _is_heading_line(line, command="subsection", starred=False)


def _is_heading_line(line: str, *, command: str, starred: bool) -> bool:
    prefix = f"\\{command}"
    if not line.startswith(prefix):
        return False
    pos = len(prefix)
    has_star = pos < len(line) and line[pos] == "*"
    if has_star != starred:
        return False
    if has_star:
        pos += 1
    if pos < len(line) and line[pos] == "[":
        pos = _consume_balanced_group(line, pos, "[", "]")
        if pos is None:
            return False
    if pos >= len(line) or line[pos] != "{":
        return False
    pos = _consume_balanced_group(line, pos, "{", "}")
    return pos == len(line)


def _starts_section_command(line: str) -> bool:
    prefix = r"\section"
    if not line.startswith(prefix):
        return False
    if line.startswith(r"\sectionmark"):
        return False
    pos = len(prefix)
    return pos < len(line) and line[pos] in "*[{"


def _consume_balanced_group(line: str, start: int, opener: str, closer: str) -> int | None:
    if start >= len(line) or line[start] != opener:
        return None
    depth = 0
    for pos in range(start, len(line)):
        char = line[pos]
        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return pos + 1
    return None
