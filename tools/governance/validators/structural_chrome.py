from __future__ import annotations

import re
from pathlib import Path

from core.finding import Finding, finding
from core.tex import read_text
from core.file_inventory import validator_files


MACHINERY_RE = re.compile(
    r"\\(input|include|LRAExcludeFromPrintEditionBegin|LRAExcludeFromPrintEditionEnd|label|index|phantomsection|addcontentsline|clearpage|newpage|FloatBarrier|lrameta)\b"
)
HEADING_RE = re.compile(r"\\(chapter|section|subsection|subsubsection)\b")
ENV_BEGIN_RE = re.compile(r"\\begin\{(exposition|toolkitbox)\}")
ENV_END_RE = re.compile(r"\\end\{(exposition|toolkitbox)\}")
BREADCRUMB_RE = re.compile(r"\\(?:breadcrumb\{|LraBreadcrumb\b)")
TOOLKITBOX_RE = re.compile(r"\\begin\{toolkitbox\}.*?\\end\{toolkitbox\}", re.DOTALL)
LABEL_RE = re.compile(r"\\label\{([^}]+)\}")
HYPERREF_RE = re.compile(r"\\hyperref\[([^\]]+)\]")
TOOLKIT_DETAIL_HEADER_RE = re.compile(r"\\textbf\{Detail\}")
TOOLKIT_DETAIL_LINK_RE = re.compile(r"&\s*\\hyperref\[[^\]]+\]\{[^{}]*(?:Def|Thm|Prop|Lem|Cor|Ax|Rem|Ex|downarrow|Down)[^{}]*\}\s*\\\\")
FORMAL_OR_PROOF_RE = re.compile(r"\\begin\{(?:definition|theorem|lemma|proposition|corollary|axiom|proof)\}")
RAW_TOOLKIT_RE = re.compile(r"\\begin\{tcolorbox\}\[(.*?)\]", re.DOTALL)
RAW_BREADCRUMB_RE = re.compile(r"\\begin\{tcolorbox\}[\s\S]*?colback=breadcrumb", re.IGNORECASE)
ROADMAP_RE = re.compile(r"[Ss]tructural\s+[Rr]oadmap")
ROLE_RE = re.compile(r"[Ss]tructural\s+[Rr]ole")
ENV_NAME = {"exposition": "exposition", "toolkitbox": "toolkit"}


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    visible_labels = _collect_visible_labels(volume_root, files)
    for tex in validator_files(volume_root, files):
        _validate_file(volume_root, tex, findings, visible_labels)
    return findings


def _validate_file(volume_root: Path, path: Path, findings: list[Finding], visible_labels: set[str]) -> None:
    text = read_text(path)
    rel = path.resolve().relative_to(volume_root.resolve()).as_posix()
    _check_breadcrumb_format(volume_root, path, text, findings)
    _check_toolkit(volume_root, path, rel, text, findings, visible_labels)
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


def _check_toolkit(
    volume_root: Path,
    path: Path,
    rel: str,
    text: str,
    findings: list[Finding],
    visible_labels: set[str],
) -> None:
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
        body = match.group(0)
        line = text.count("\n", 0, match.start()) + 1
        tabulars = list(_tabulars(body))
        if not tabulars:
            findings.append(
                finding(
                    "toolkit_missing_table",
                    "Toolkit boxes must contain a two-column quick-reference table.",
                    path,
                    volume_root,
                    line,
                )
            )
        for tabular_start, spec, table_body in tabulars:
            table_line = text.count("\n", 0, match.start() + tabular_start) + 1
            column_count = _tabular_column_count(spec)
            if column_count != 2:
                findings.append(
                    finding(
                        "toolkit_table_not_two_columns",
                        "Toolkit quick-reference tables must have exactly two columns: linked name and Meaning.",
                        path,
                        volume_root,
                        table_line,
                    )
                )
            headers = _table_headers(table_body)
            if len(headers) < 2:
                findings.append(
                    finding(
                        "toolkit_table_header_missing",
                        "Toolkit quick-reference tables must start with headers for linked name and Meaning.",
                        path,
                        volume_root,
                        table_line,
                    )
                )
            else:
                if _normalize_header(headers[0]) != "name":
                    findings.append(
                        finding(
                            "toolkit_first_column_not_name",
                            "Toolkit quick-reference tables must use Name as the first column header.",
                            path,
                            volume_root,
                            table_line,
                        )
                    )
                if _normalize_header(headers[1]) != "meaning":
                    findings.append(
                        finding(
                            "toolkit_second_column_not_meaning",
                            "Toolkit quick-reference tables must use Meaning as the second column header.",
                            path,
                            volume_root,
                            table_line,
                        )
                    )
        if FORMAL_OR_PROOF_RE.search(body):
            findings.append(
                finding(
                    "toolkit_contains_formal",
                    "Toolkit box contains a formal environment or proof.",
                    path,
                    volume_root,
                    line,
                )
            )
        if TOOLKIT_DETAIL_HEADER_RE.search(body):
            findings.append(
                finding(
                    "toolkit_detail_column",
                    "Toolkit quick-reference tables must put the hyperref on the leading concept/row label and omit the Detail column.",
                    path,
                    volume_root,
                    line,
                )
            )
        elif TOOLKIT_DETAIL_LINK_RE.search(body):
            findings.append(
                finding(
                    "toolkit_detail_link_cell",
                    "Toolkit quick-reference links belong on the leading concept/row label, not in a trailing detail cell.",
                    path,
                    volume_root,
                    line,
                )
            )
        _check_toolkit_links(volume_root, path, text, match.start(), body, visible_labels, findings)
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


def _collect_visible_labels(volume_root: Path, files) -> set[str]:
    labels: set[str] = set()
    for tex in validator_files(volume_root, files):
        labels.update(LABEL_RE.findall(read_text(tex)))
    return labels


def _check_toolkit_links(
    volume_root: Path,
    path: Path,
    full_text: str,
    toolkit_start: int,
    body: str,
    visible_labels: set[str],
    findings: list[Finding],
) -> None:
    for match in HYPERREF_RE.finditer(body):
        target = match.group(1)
        line = full_text.count("\n", 0, toolkit_start + match.start()) + 1
        if target not in visible_labels:
            findings.append(
                finding(
                    "toolkit_link_unknown_target",
                    f"Toolkit link targets unknown label {target}.",
                    path,
                    volume_root,
                    line,
                )
            )

    for row_start, row in _toolkit_table_rows(body):
        first_amp = _first_unescaped_ampersand(row)
        first_link = HYPERREF_RE.search(row)
        if first_amp is None or first_link is None or first_link.start() < first_amp:
            continue
        line = full_text.count("\n", 0, toolkit_start + row_start + first_link.start()) + 1
        findings.append(
            finding(
                "toolkit_link_not_leading_cell",
                "Toolkit quick-reference links should be on the leading concept/row label cell.",
                path,
                volume_root,
                line,
                "warning",
            )
        )


def _toolkit_table_rows(body: str):
    for match in re.finditer(r"(?P<row>.*?)(?:\\\\|\\cr)(?:\s*(?:\n|$))", body, re.DOTALL):
        row = match.group("row")
        if "\\hyperref[" not in row:
            continue
        if "\\textbf{" in row:
            continue
        yield match.start("row"), row


def _tabulars(body: str):
    begin = r"\begin{tabular}"
    end = r"\end{tabular}"
    position = 0
    while True:
        start = body.find(begin, position)
        if start == -1:
            return
        spec_start = body.find("{", start + len(begin))
        if spec_start == -1:
            return
        spec_end = _balanced_group_end(body, spec_start)
        if spec_end is None:
            return
        end_start = body.find(end, spec_end)
        if end_start == -1:
            return
        yield start, body[spec_start + 1 : spec_end - 1], body[spec_end:end_start]
        position = end_start + len(end)


def _balanced_group_end(text: str, start: int) -> int | None:
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == "{" and (index == 0 or text[index - 1] != "\\"):
            depth += 1
        elif char == "}" and (index == 0 or text[index - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return index + 1
    return None


def _tabular_column_count(spec: str) -> int:
    count = 0
    index = 0
    while index < len(spec):
        char = spec[index]
        if char in "lcr":
            count += 1
            index += 1
        elif char in "pmb" and index + 1 < len(spec) and spec[index + 1] == "{":
            end = _balanced_group_end(spec, index + 1)
            count += 1
            index = end if end is not None else index + 1
        elif char in "| @!<>":
            index += 1
        else:
            index += 1
    return count


def _table_headers(table_body: str) -> list[str]:
    match = re.search(r"(?P<row>.*?)(?:\\\\|\\cr)", table_body, re.DOTALL)
    if not match:
        return []
    return re.findall(r"\\textbf\{([^}]+)\}", match.group("row"))


def _normalize_header(header: str) -> str:
    return re.sub(r"\s+", " ", header.strip()).lower()


def _first_unescaped_ampersand(text: str) -> int | None:
    for match in re.finditer("&", text):
        prefix = text[: match.start()]
        backslash_count = len(prefix) - len(prefix.rstrip("\\"))
        if backslash_count % 2 == 0:
            return match.start()
    return None


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
    rel_path = Path(rel)
    if rel_path.name.startswith("figure-") or "figures" in rel_path.parts:
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
