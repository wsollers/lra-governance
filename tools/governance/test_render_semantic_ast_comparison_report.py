#!/usr/bin/env python3
"""Tests for semantic AST comparison report rendering."""

from __future__ import annotations

import sys
import unittest
import uuid
from contextlib import contextmanager
from argparse import Namespace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "governance"))

import render_semantic_ast_comparison_report as report  # noqa: E402

TEMP_ROOT = ROOT / ".test-tmp" / "semantic-ast-report"


@contextmanager
def temp_dir():
    path = TEMP_ROOT / str(uuid.uuid4())
    path.mkdir(parents=True, exist_ok=True)
    yield path


class RenderSemanticAstComparisonReportTests(unittest.TestCase):
    def test_pending_candidate_renders_parser_witnesses_without_artifact(self):
        with temp_dir() as repo:
            volume = repo / "volume-iii"
            notes = volume / "book-analysis-i" / "bounding" / "notes" / "bounds-extremals"
            notes.mkdir(parents=True)
            root = repo / "volume-iii-bounds-sequences-and-series.tex"
            source = notes / "notes-upper-lower-bounds.tex"
            root.write_text(
                "\\input{volume-iii/book-analysis-i/bounding/notes/bounds-extremals/notes-upper-lower-bounds}\n",
                encoding="utf-8",
            )
            source.write_text(
                r"""\begin{definition}[Upper Bound]
\label{def:real-upper-bound}
Let $A\subseteq\mathbb R$. A real number $b$ is an upper bound of $A$ when
\[
\forall a\in A\;(a\leq b).
\]
\end{definition}
""",
                encoding="utf-8",
            )
            args = Namespace(
                repos_root=repo.parent,
                volume_root=repo,
                volume="iii",
                book=None,
                chapter=None,
                section=None,
                target=notes,
                label=None,
            )
            repo_root, _volume_source, _roots, candidates = report.routed_formals(args)

            rendered = report.render_label(repo_root, candidates[0], {})

            self.assertIn("## def:real-upper-bound", rendered)
            self.assertIn("### Original Routed TeX", rendered)
            self.assertIn("### Routed Display Parser Witness", rendered)
            self.assertIn("Hand parser available: `True`", rendered)
            self.assertIn("Lark parser available: `True`", rendered)
            self.assertIn("kind: forall", rendered)
            self.assertIn("Artifact: `volume-iii/book-analysis-i/bounding/notes/bounds-extremals/def-real-upper-bound/artifact.yaml`", rendered)
            self.assertIn("_missing_", rendered)


if __name__ == "__main__":
    unittest.main()
