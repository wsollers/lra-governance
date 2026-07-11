from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .tex import read_stripped_text


FORMAL_BEGIN_RE = re.compile(
    r"\\begin\{(?P<env>definition|axiom|theorem|lemma|proposition|corollary)\}"
    r"(?:\[(?P<title>[^\]]*)\])?",
    re.IGNORECASE,
)
SECTION_RE = re.compile(r"\\(?:chapter|section|subsection|subsubsection)\*?\{")
LABEL_RE = re.compile(r"\\label\{(?P<label>[a-z]+:[^{}]+)\}")


@dataclass(frozen=True)
class FormalBlock:
    path: Path
    env: str
    title: str
    label: str
    begin: int
    end: int
    next_begin: int
    next_boundary: int
    line: int
    body: str
    decoration: str


def formal_blocks_for_file(path: Path) -> list[FormalBlock]:
    return _formal_blocks_for_file(path.resolve())


def clear_formal_block_cache() -> None:
    _formal_blocks_for_file.cache_clear()


@lru_cache(maxsize=512)
def _formal_blocks_for_file(path: Path) -> list[FormalBlock]:
    text = read_stripped_text(path)
    begins = list(FORMAL_BEGIN_RE.finditer(text))
    blocks: list[FormalBlock] = []
    for index, begin in enumerate(begins):
        env = begin.group("env").lower()
        end_match = re.search(rf"\\end\{{{re.escape(env)}\}}", text[begin.end():], re.IGNORECASE)
        if not end_match:
            continue
        end = begin.end() + end_match.end()
        next_begin = begins[index + 1].start() if index + 1 < len(begins) else len(text)
        next_boundary = _next_boundary(text, end, next_begin)
        body = text[begin.start():end]
        labels = LABEL_RE.findall(body)
        label = labels[0] if labels else ""
        blocks.append(
            FormalBlock(
                path=path,
                env=env,
                title=begin.group("title") or "",
                label=label,
                begin=begin.start(),
                end=end,
                next_begin=next_begin,
                next_boundary=next_boundary,
                line=text.count("\n", 0, begin.start()) + 1,
                body=body,
                decoration=text[end:next_begin],
            )
        )
    return blocks


def _next_boundary(text: str, start: int, default: int) -> int:
    formal = FORMAL_BEGIN_RE.search(text, start)
    section = SECTION_RE.search(text, start)
    candidates = [match.start() for match in (formal, section) if match]
    return min(candidates) if candidates else default
