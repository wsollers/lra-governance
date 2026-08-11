from __future__ import annotations

from pathlib import Path

import yaml

from tools.governance.update_internal_object_index import main
from tools.governance.internal_object_sqlite import metadata


def write_source(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def run_update(tmp_path: Path, tex_root: Path, *, full: bool = False) -> dict:
    output = tmp_path / "internal-index.yaml"
    state = tmp_path / "internal-index.state.yaml"
    argv = [
        "update_internal_object_index.py",
        "--tex-root",
        str(tex_root),
        "--output",
        str(output),
        "--state",
        str(state),
    ]
    if full:
        argv.append("--full")
    import sys

    previous = sys.argv
    try:
        sys.argv = argv
        assert main() == 0
    finally:
        sys.argv = previous
    return yaml.safe_load(output.read_text(encoding="utf-8"))


def test_delta_update_indexes_new_tex_object_and_removes_deleted_file(tmp_path: Path) -> None:
    tex_root = tmp_path / "lra-volume-iii"
    source = tex_root / "volume-iii" / "book-analysis-i" / "functions" / "notes" / "functions" / "defs" / "source.tex"
    write_source(
        source,
        r"""
\begin{definition}[Function]
\label{def:function}
A function is a single-valued relation.
\end{definition}
""",
    )

    first = run_update(tmp_path, tex_root, full=True)
    assert first["counts"] == {"objects": 1, "tex": 1, "lean": 0}
    assert first["delta"]["mode"] == "full"
    assert metadata(tmp_path / "sqlite" / "tex-search.sqlite")["object_count"] == "1"

    write_source(
        source,
        r"""
\begin{definition}[Function]
\label{def:function}
A function is a single-valued relation.
\end{definition}

\begin{definition}[Image of a Set]
\label{def:image-of-a-set}
The image collects all values attained on the set.
\end{definition}
""",
    )

    second = run_update(tmp_path, tex_root)
    assert second["counts"] == {"objects": 2, "tex": 2, "lean": 0}
    assert second["delta"]["mode"] == "delta"
    assert second["delta"]["files"]["changed"] == 1
    assert {item["object_id"] for item in second["objects"]} == {
        "tex:def:function",
        "tex:def:image-of-a-set",
    }

    source.unlink()
    third = run_update(tmp_path, tex_root)
    assert third["counts"] == {"objects": 0, "tex": 0, "lean": 0}
    assert third["delta"]["files"]["deleted"] == 1
    assert metadata(tmp_path / "sqlite" / "tex-search.sqlite")["object_count"] == "0"
