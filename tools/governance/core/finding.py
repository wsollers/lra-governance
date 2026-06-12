from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    path: str
    line: int = 0
    severity: str = "error"


def rel_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def finding(
    code: str,
    message: str,
    path: Path,
    root: Path,
    line: int = 0,
    severity: str = "error",
) -> Finding:
    return Finding(code=code, message=message, path=rel_path(path, root), line=line, severity=severity)
