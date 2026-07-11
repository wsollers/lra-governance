from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re


INPUT_RE = re.compile(r"\\(?:input|include)\{([^}]+)\}")

_RAW_TEXT_CACHE: dict[Path, str] = {}
_STRIPPED_TEXT_CACHE: dict[Path, str] = {}


def clear_text_cache() -> None:
    _RAW_TEXT_CACHE.clear()
    _STRIPPED_TEXT_CACHE.clear()
    strip_latex_comments.cache_clear()


def register_text_cache(path: Path, raw: str, stripped: str | None = None) -> None:
    key = path.resolve()
    _RAW_TEXT_CACHE[key] = raw
    _STRIPPED_TEXT_CACHE[key] = stripped if stripped is not None else strip_latex_comments(raw)


def read_text(path: Path) -> str:
    key = path.resolve()
    if key not in _RAW_TEXT_CACHE:
        _RAW_TEXT_CACHE[key] = path.read_text(encoding="utf-8", errors="replace")
    return _RAW_TEXT_CACHE[key]


def read_stripped_text(path: Path) -> str:
    key = path.resolve()
    if key not in _STRIPPED_TEXT_CACHE:
        _STRIPPED_TEXT_CACHE[key] = strip_latex_comments(read_text(path))
    return _STRIPPED_TEXT_CACHE[key]


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


@lru_cache(maxsize=512)
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
        target.parent.name,
    }
    if target.stem != "index":
        variants.add(target.stem)
    if targets & variants:
        return True
    rel_base = rel.removesuffix("/index")
    return any(
        routed.endswith(f"/{rel}") or routed.endswith(f"/{rel_base}")
        for routed in targets
    )
