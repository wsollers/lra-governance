#!/usr/bin/env python3
"""Move toolkit quick-reference links from a Detail column to row labels.

The migration targets tabular environments inside ``toolkitbox`` blocks whose
last header cell is ``\\textbf{Detail}``. For ordinary rows ending in a
``\\hyperref[...]`` cell, it removes that final cell and wraps the first cell in
the same link.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path


TOOLKIT_RE = re.compile(r"\\begin\{toolkitbox\}.*?\\end\{toolkitbox\}", re.DOTALL)
TABULAR_RE = re.compile(
    r"\\begin\{tabular\}\{(?P<spec>[^}]*)\}(?P<body>.*?)\\end\{tabular\}",
    re.DOTALL,
)
HYPERREF_CELL_RE = re.compile(
    r"^\s*\\hyperref\[(?P<label>[^\]]+)\]\{(?P<text>.*)\}\s*$",
    re.DOTALL,
)

def migrate_text(text: str) -> tuple[str, int]:
    changes = 0
    pieces: list[str] = []
    last = 0
    for toolkit in TOOLKIT_RE.finditer(text):
        migrated, repair_count = _repair_midrule_links(toolkit.group(0))
        migrated, count = _migrate_toolkit(migrated)
        pieces.append(text[last:toolkit.start()])
        pieces.append(migrated)
        last = toolkit.end()
        changes += count + repair_count
    pieces.append(text[last:])
    return "".join(pieces), changes


def _migrate_toolkit(block: str) -> tuple[str, int]:
    changes = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal changes
        body, count = _migrate_tabular_body(match.group("body"))
        if count == 0:
            return match.group(0)
        changes += count
        spec = _drop_last_tabular_column(match.group("spec"))
        return f"\\begin{{tabular}}{{{spec}}}{body}\\end{{tabular}}"

    return TABULAR_RE.sub(repl, block), changes


def _migrate_tabular_body(body: str) -> tuple[str, int]:
    rows = _split_rows(body)
    if not any(_has_navigation_header(row) for row, _ in rows):
        return body, 0

    out: list[str] = []
    changes = 0
    for row, ending in rows:
        migrated = row
        if _has_navigation_header(row):
            migrated = _drop_final_cell(row)
        elif ending:
            row_migrated, did_change = _migrate_data_row(row)
            if did_change:
                migrated = row_migrated
                changes += 1
        out.append(migrated + ending)
    return "".join(out), changes


def _split_rows(body: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    start = 0
    depth = 0
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == "\\":
            if i + 1 < len(body) and body[i + 1] == "\\" and depth == 0:
                end = i + 2
                if end < len(body) and body[end] == "[":
                    close = body.find("]", end + 1)
                    if close != -1:
                        end = close + 1
                rows.append((body[start:i], body[i:end]))
                start = end
                i = end
                continue
            i += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}" and depth:
            depth -= 1
        i += 1
    rows.append((body[start:], ""))
    return rows


def _split_cells(row: str) -> list[str]:
    cells: list[str] = []
    start = 0
    depth = 0
    i = 0
    while i < len(row):
        ch = row[i]
        if ch == "\\":
            i += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}" and depth:
            depth -= 1
        elif ch == "&" and depth == 0:
            cells.append(row[start:i])
            start = i + 1
        i += 1
    cells.append(row[start:])
    return cells


def _join_cells(cells: list[str]) -> str:
    return " &".join(cells)


def _has_navigation_header(row: str) -> bool:
    cells = _split_cells(row)
    return bool(cells) and cells[-1].strip() in {r"\textbf{Detail}", r"\textbf{Reference}"}


def _drop_final_cell(row: str) -> str:
    cells = _split_cells(row)
    return _join_cells(cells[:-1]) if len(cells) > 1 else row


def _migrate_data_row(row: str) -> tuple[str, bool]:
    prefix, row = _split_leading_rule_commands(row)
    cells = _split_cells(row)
    if len(cells) < 2:
        return prefix + row, False
    match = HYPERREF_CELL_RE.match(cells[-1])
    if not match:
        return prefix + row, False
    if r"\hyperref[" in cells[0]:
        return prefix + _join_cells(cells[:-1]), True
    cells[0] = _wrap_first_cell(cells[0], match.group("label"))
    return prefix + _join_cells(cells[:-1]), True


def _split_leading_rule_commands(row: str) -> tuple[str, str]:
    match = re.match(r"(?P<prefix>(?:\s*\\(?:toprule|midrule|bottomrule)\s*)+)(?P<body>.*)", row, re.DOTALL)
    if not match:
        return "", row
    return match.group("prefix"), match.group("body")


def _wrap_first_cell(cell: str, label: str) -> str:
    multicolumn = _parse_multicolumn(cell)
    if multicolumn is not None:
        indent, count, align, body, trailing = multicolumn
        linked = rf"\hyperref[{label}]{{{body.strip()}}}"
        return f"{indent}\\multicolumn{{{count}}}{{{align}}}{{{linked}}}{trailing}"
    indent_match = re.match(r"(?P<indent>\s*)(?P<body>.*?)(?P<trailing>\s*)$", cell, re.DOTALL)
    assert indent_match is not None
    indent = indent_match.group("indent")
    body = indent_match.group("body").strip()
    trailing = indent_match.group("trailing")
    return rf"{indent}\hyperref[{label}]{{{body}}}{trailing}"


def _parse_multicolumn(cell: str) -> tuple[str, str, str, str, str] | None:
    indent_match = re.match(r"(?P<indent>\s*)\\multicolumn", cell)
    if indent_match is None:
        return None
    i = indent_match.end()
    groups: list[str] = []
    for _ in range(3):
        while i < len(cell) and cell[i].isspace():
            i += 1
        if i >= len(cell) or cell[i] != "{":
            return None
        end = _find_matching_brace(cell, i)
        if end is None:
            return None
        groups.append(cell[i + 1:end])
        i = end + 1
    trailing = cell[i:]
    if trailing.strip():
        return None
    return indent_match.group("indent"), groups[0], groups[1], groups[2], trailing


def _drop_last_tabular_column(spec: str) -> str:
    stripped = spec.strip()
    parts = stripped.split()
    if len(parts) > 1:
        return " ".join(parts[:-1])
    compact = re.fullmatch(r"([lcrX]+)", stripped)
    if compact and len(stripped) > 1:
        return stripped[:-1]
    return spec


def _repair_midrule_links(text: str) -> tuple[str, int]:
    out: list[str] = []
    changes = 0
    cursor = 0
    pattern = re.compile(r"\\hyperref\[[^\]]+\]\{")
    for match in pattern.finditer(text):
        open_brace = match.end() - 1
        close_brace = _find_matching_brace(text, open_brace)
        if close_brace is None:
            continue
        body = text[open_brace + 1:close_brace]
        stripped = body.lstrip()
        if not stripped.startswith(r"\midrule"):
            continue
        after_midrule = stripped[len(r"\midrule"):].lstrip()
        leading = body[: len(body) - len(stripped)]
        replacement = f"{leading}\\midrule\n{match.group(0)}{after_midrule}}}"
        out.append(text[cursor:match.start()])
        out.append(replacement)
        cursor = close_brace + 1
        changes += 1
    if not changes:
        return text, 0
    out.append(text[cursor:])
    return "".join(out), changes


def _find_matching_brace(text: str, open_brace: int) -> int | None:
    depth = 0
    i = open_brace
    while i < len(text):
        ch = text[i]
        if ch == "\\":
            i += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def migrate_path(path: Path, *, write: bool) -> int:
    text = path.read_text(encoding="utf-8")
    migrated, changes = migrate_text(text)
    if write and changes and migrated != text:
        path.write_text(migrated, encoding="utf-8", newline="")
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    total = 0
    for root in args.paths:
        files = [root] if root.is_file() else sorted(root.rglob("*.tex"))
        for path in files:
            changes = migrate_path(path, write=args.write)
            if changes:
                print(f"{path}: {changes} row(s)")
                total += changes
    print(f"total: {total} row(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
