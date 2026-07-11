from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from .tex import clear_text_cache, register_text_cache, strip_latex_comments


@dataclass(frozen=True)
class PreprocessResult:
    file_count: int
    output_dir: Path
    manifest_path: Path
    elapsed_seconds: float


def preprocess_tex_files(files: list[Path], volume_root: Path, output_dir: Path) -> PreprocessResult:
    start = time.perf_counter()
    output_dir = output_dir.resolve()
    stripped_root = output_dir / "stripped"
    stripped_root.mkdir(parents=True, exist_ok=True)
    clear_text_cache()

    records: list[dict[str, object]] = []
    for path in sorted({item.resolve() for item in files}):
        raw = path.read_text(encoding="utf-8", errors="replace")
        stripped = strip_latex_comments(raw)
        register_text_cache(path, raw, stripped)
        try:
            rel = path.relative_to(volume_root).as_posix()
        except ValueError:
            rel = path.name
        out_path = stripped_root / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(stripped, encoding="utf-8")
        records.append(
            {
                "source": str(path),
                "relative": rel,
                "stripped": str(out_path),
                "raw_chars": len(raw),
                "stripped_chars": len(stripped),
            }
        )

    manifest_path = output_dir / "manifest.json"
    elapsed = time.perf_counter() - start
    manifest_path.write_text(
        json.dumps(
            {
                "volume_root": str(volume_root),
                "file_count": len(records),
                "elapsed_seconds": elapsed,
                "files": records,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return PreprocessResult(len(records), output_dir, manifest_path, elapsed)
