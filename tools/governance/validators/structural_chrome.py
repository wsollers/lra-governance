from __future__ import annotations

import re
from pathlib import Path

from core.finding import Finding, finding
from core.tex import read_text
from core.file_inventory import files_to_validate


MACHINERY_RE = re.compile(
    r"\\(input|include|LRAExcludeFromPrintEditionBegin|LRAExcludeFromPrintEditionEnd|label|index|phantomsection|addcontentsline|clearpage|newpage|FloatBarrier|lrameta)\b"
)
HEADING_RE = re.compile(r"\\(chapter|section|subsection|subsubsection)\b")
ENV_BEGIN_RE = re.compile(r"\\begin\{(exposition|toolkitbox)\}")
ENV_END_RE = re.compile(r"\\end\{(exposition|toolkitbox)\}")
BREADCRUMB_RE = re.compile(r"\\(?:breadcrumb\{|LraBreadcrumb\b)")
TOOLKITBOX_RE = re.compile(r"\\begin\{toolkitbox\}.*?\\end\{toolkitbox\}", re.DOTALL)
FORMAL_OR_PROOF_RE = re.compile(r"\\begin\{(?:definition|theorem|lemma|proposition|corollary|axiom|proof)\}")
RAW_TOOLKIT_RE = re.compile(r"\\begin\{tcolorbox\}\[(.*?)\]", re.DOTALL)
RAW_BREADCRUMB_RE = re.compile(r"\\begin\{tcolorbox\}[\s\S]*?colback=breadcrumb", re.IGNORECASE)
ROADMAP_RE = re.compile(r"[Ss]tructural\s+[Rr]oadmap")
ROLE_RE = re.compile(r"[Ss]tructural\s+[Rr]ole")
ENV_NAME = {"exposition": "exposition", "toolkitbox": "toolkit"}


def validate(volume_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for tex in files_to_validate([volume_root]):
        _validate_file(volume_root, tex, findings)
    return findings


def _validate_file(volume_root: Path, path: Path, findings: list[Finding]) -> None:
    text = read_text(path)
    rel = path.resolve().relative_to(volume_root.resolve()).as_posix()
    _check_breadcrumb_format(volume_root, path, text, findings)
    _check_toolkit(volume_root, path, rel, text, findings)
    _check_retired_structural_text(volume_root, path, text, findings)
    _check_inline_tikz(volume_root, path, rel, text, findings)


def _check_breadcrumb_format(volume_root: Path, path: Path, text: str, findings: list[Finding]) -> None:
    match = RAW_BREADCRUMB_RE.search(text)
    if match and "\\breadcrumb{" not in text and "\\LraBreadcrumb" not in text:
        findings.append(
            finding(
                "breadcrumb_hand_rolled",
                "Breadcrumb is a hand-rolled tcolorbox instead of the \\breadcrumb{...} macro.",
                path,
                volume_root,
                text.count("\n", 0, match.start()) + 1,
                "warning",
            )
        )


def _check_toolkit(volume_root: Path, path: Path, rel: str, text: str, findings: list[Finding]) -> None:
    role = _notes_role(rel)
    events = _events(text)
    for index, (kind, line, level) in enumerate(events):
        if kind != "toolkit":
            continue
        if role not in {"notes_index", "topic_index"}:
            findings.append(
                finding(
                    "toolkit_not_in_notes_router",
                    "Toolkit boxes belong in notes routers, not note body files or chapter routers.",
                path,
                volume_root,
                line,
                "warning",
            )
        )
            continue
        prior = index - 1
        exposition_count = 0
        while prior >= 0 and events[prior][0] in {"exposition", "toolkit"}:
            if events[prior][0] == "exposition":
                exposition_count += 1
            prior -= 1
        previous = events[prior] if prior >= 0 else None
        if exposition_count > 1:
            findings.append(
                finding(
                    "toolkit_leading_exposition",
                    f"{exposition_count} exposition block(s) between heading and toolkit; max allowed is 1.",
                    path,
                    volume_root,
                    line,
                )
            )
        if previous is None or not (previous[0] == "heading" and previous[2] in {"section", "subsection"}):
            findings.append(
                finding(
                    "toolkit_misplaced",
                    "Toolkit must sit at the top of a section or subsection.",
                    path,
                    volume_root,
                    line,
                )
            )

    for match in TOOLKITBOX_RE.finditer(text):
        if FORMAL_OR_PROOF_RE.search(match.group(0)):
            findings.append(
                finding(
                    "toolkit_contains_formal",
                    "Toolkit box contains a formal environment or proof.",
                    path,
                    volume_root,
                    text.count("\n", 0, match.start()) + 1,
                )
            )
    for match in RAW_TOOLKIT_RE.finditer(text):
        if "oolkit" in match.group(1):
            findings.append(
                finding(
                    "toolkit_hand_rolled",
                    "Toolkit rendered as a raw tcolorbox; use \\begin{toolkitbox}{...}.",
                    path,
                    volume_root,
                    text.count("\n", 0, match.start()) + 1,
                )
            )


def _check_retired_structural_text(volume_root: Path, path: Path, text: str, findings: list[Finding]) -> None:
    for line_no, line in enumerate(text.splitlines(), 1):
        if ROADMAP_RE.search(line):
            findings.append(
                finding(
                    "structural_roadmap_present",
                    "Retired roadmap text is present; remove the block or wording.",
                    path,
                    volume_root,
                    line_no,
                )
            )
        if ROLE_RE.search(line):
            findings.append(
                finding(
                    "structural_role_present",
                    "Retired role text is present; remove the block or wording.",
                    path,
                    volume_root,
                    line_no,
                )
            )


def _check_inline_tikz(volume_root: Path, path: Path, rel: str, text: str, findings: list[Finding]) -> None:
    if Path(rel).name.startswith("figure-"):
        return
    match = re.search(r"\\begin\{tikzpicture\}", text)
    if match:
        findings.append(
            finding(
                "inline_tikzpicture",
                "Nontrivial TikZ must live in a dedicated figure source file.",
                path,
                volume_root,
                text.count("\n", 0, match.start()) + 1,
                "warning",
            )
        )


def _events(text: str):
    events = []
    current_env = None
    env_line = 0
    for line_no, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if current_env:
            match = ENV_END_RE.search(line)
            if match and match.group(1) == current_env:
                events.append((ENV_NAME[current_env], env_line, ""))
                current_env = None
            continue
        if not stripped or stripped.startswith("%"):
            continue
        begin = ENV_BEGIN_RE.search(line)
        if begin:
            current_env = begin.group(1)
            env_line = line_no
            continue
        if MACHINERY_RE.search(line) and not BREADCRUMB_RE.search(line):
            continue
        heading = HEADING_RE.search(line)
        if heading:
            events.append(("heading", line_no, heading.group(1)))
            continue
        if BREADCRUMB_RE.search(line):
            events.append(("breadcrumb", line_no, ""))
            continue
        events.append(("content", line_no, ""))
    return events


def _notes_role(rel: str) -> str | None:
    parts = rel.split("/")
    if "notes" not in parts:
        return None
    index = parts.index("notes")
    tail = parts[index + 1:]
    if tail == ["index.tex"]:
        return "notes_index"
    if len(tail) != 2:
        return None
    topic, filename = tail
    if filename == "index.tex":
        return "topic_index"
    if filename.startswith("figure-") or not filename.endswith(".tex"):
        return "ignore"
    return "body"
