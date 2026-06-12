from __future__ import annotations

from pathlib import Path
import re


INPUT_RE = re.compile(r"\\(?:input|include)\{([^}]+)\}")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def strip_latex_comment(line: str) -> str:
    escaped = False
    out: list[str] = []
    for ch in line:
        if ch == "\\":
            escaped = not escaped
            out.append(ch)
            continue
        if ch == "%" and not escaped:
            break
        escaped = False
        out.append(ch)
    return "".join(out)


def strip_latex_comments(text: str) -> str:
    return "\n".join(strip_latex_comment(line) for line in text.splitlines())


def line_at(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def input_targets(text: str) -> set[str]:
    targets: set[str] = set()
    for match in INPUT_RE.finditer(text):
        target = match.group(1).replace("\\", "/").removesuffix(".tex")
        targets.add(target)
        targets.add(target.removesuffix("/index"))
        targets.add(Path(target).name)
    return targets


def is_routed(index_path: Path, target: Path, chapter_root: Path) -> bool:
    if not index_path.exists():
        return False
    targets = input_targets(read_text(index_path))
    try:
        rel = target.relative_to(chapter_root).as_posix().removesuffix(".tex")
    except ValueError:
        rel = target.as_posix().removesuffix(".tex")
    variants = {
        rel,
        rel.removesuffix("/index"),
        target.name,
        target.stem,
        target.parent.name,
    }
    return bool(targets & variants)
