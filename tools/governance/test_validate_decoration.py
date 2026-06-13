#!/usr/bin/env python3
"""Focused tests for the validate_decoration CLI harness."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import _targeting as tg
import validate_decoration as vd


HERE = Path(__file__).resolve().parent
TMP = HERE.parent.parent / ".test-tmp" / "validate-decoration"


def reset_tmp():
    if TMP.exists():
        shutil.rmtree(TMP)


def test_repo_root_walks_discovered_volume_only():
    reset_tmp()
    root = TMP / "lra-volume-i"
    try:
        (root / "volume-i").mkdir(parents=True)
        (root / "docs" / "workflows" / "fixtures").mkdir(parents=True)
        (root / "volume-i" / "index.tex").write_text("% volume entry\n", encoding="utf-8")
        (root / "docs" / "workflows" / "fixtures" / "fixture.tex").write_text("% fixture\n", encoding="utf-8")

        target = tg.resolve_target(root, None, None, None)
        roots = vd.walk_roots_for(target, root)
        files = sorted(path.relative_to(root).as_posix() for path in vd.iter_tex(roots))

        assert roots == [(root / "volume-i").resolve()]
        assert files == ["volume-i/index.tex"]
    finally:
        reset_tmp()


def test_cli_ignores_commented_formal_blocks():
    reset_tmp()
    chapter = TMP / "lra-volume-i" / "volume-i" / "sample-chapter"
    notes = chapter / "notes" / "sample-topic"
    proofs = chapter / "proofs" / "sample-topic"
    try:
        notes.mkdir(parents=True)
        proofs.mkdir(parents=True)
        (chapter / "index.tex").write_text("% chapter\n", encoding="utf-8")
        (notes / "index.tex").write_text(r"\section{Sample Topic}" + "\n", encoding="utf-8")
        (notes / "sample-topic.tex").write_text(
            "\n".join(
                [
                    r"\subsection*{Sample Topic}",
                    r"% \begin{tcolorbox}[colback=red]",
                    r"% \begin{definition}",
                    r"% \label{def:commented-out}",
                    r"% Commented definition.",
                    r"% \end{definition}",
                    r"% \end{tcolorbox}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        out = TMP / "report.json"
        cmd = [
            sys.executable,
            str(HERE / "validate_decoration.py"),
            "--root",
            str(TMP / "lra-volume-i"),
            "--json",
            str(out),
        ]
        proc = subprocess.run(cmd, cwd=HERE, text=True, capture_output=True)
        assert proc.returncode == 0, proc.stdout + proc.stderr
    finally:
        reset_tmp()


def test_iter_tex_excludes_print_technique_folders():
    reset_tmp()
    root_i = TMP / "lra-volume-i" / "volume-i"
    root_ii = TMP / "lra-volume-ii" / "volume-ii"
    root_iii = TMP / "lra-volume-iii" / "volume-iii"
    try:
        (root_i / "proof-techniques").mkdir(parents=True)
        (root_i / "sets").mkdir(parents=True)
        (root_ii / "lean").mkdir(parents=True)
        (root_ii / "natural-numbers").mkdir(parents=True)
        (root_iii / "analysis" / "real-analysis" / "notes" / "proof-techniques").mkdir(parents=True)
        (root_iii / "analysis" / "real-analysis" / "notes" / "standard-topic").mkdir(parents=True)
        (root_iii / "analysis" / "functions").mkdir(parents=True)
        (root_i / "proof-techniques" / "skip.tex").write_text("% skip\n", encoding="utf-8")
        (root_i / "sets" / "keep.tex").write_text("% keep\n", encoding="utf-8")
        (root_ii / "lean" / "skip.tex").write_text("% skip\n", encoding="utf-8")
        (root_ii / "natural-numbers" / "keep.tex").write_text("% keep\n", encoding="utf-8")
        (root_iii / "analysis" / "real-analysis" / "notes" / "proof-techniques" / "skip.tex").write_text("% skip\n", encoding="utf-8")
        (root_iii / "analysis" / "real-analysis" / "notes" / "standard-topic" / "keep.tex").write_text("% keep\n", encoding="utf-8")
        (root_iii / "analysis" / "functions" / "keep.tex").write_text("% keep\n", encoding="utf-8")

        files = {
            path.relative_to(TMP).as_posix()
            for path in vd.iter_tex([root_i, root_ii, root_iii])
        }

        assert "lra-volume-i/volume-i/proof-techniques/skip.tex" not in files
        assert "lra-volume-ii/volume-ii/lean/skip.tex" not in files
        assert "lra-volume-iii/volume-iii/analysis/real-analysis/notes/proof-techniques/skip.tex" not in files
        assert "lra-volume-iii/volume-iii/analysis/real-analysis/notes/standard-topic/keep.tex" not in files
        assert "lra-volume-i/volume-i/sets/keep.tex" in files
        assert "lra-volume-ii/volume-ii/natural-numbers/keep.tex" in files
        assert "lra-volume-iii/volume-iii/analysis/functions/keep.tex" in files
    finally:
        reset_tmp()


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {test.__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    raise SystemExit(1 if failed else 0)
