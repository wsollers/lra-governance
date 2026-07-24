#!/usr/bin/env python3
"""Tests for routed semantic artifact inventory."""

from __future__ import annotations

import sys
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "governance"))

from semantic_artifact_inventory import formal_blocks_in_file  # noqa: E402

TEMP_ROOT = ROOT / ".test-tmp" / "semantic-artifact-inventory"


@contextmanager
def temp_dir():
    path = TEMP_ROOT / str(uuid.uuid4())
    path.mkdir(parents=True, exist_ok=True)
    yield path


class SemanticArtifactInventoryTests(unittest.TestCase):
    def test_formal_block_excludes_owning_box_and_support_remarks(self):
        with temp_dir() as root:
            volume = root / "volume-i"
            source = volume / "book-order" / "bounds" / "notes.tex"
            source.parent.mkdir(parents=True)
            book_root = root / "volume-i-book-order.tex"
            book_root.write_text(r"\input{volume-i/book-order/bounds/notes}" + "\n", encoding="utf-8")
            source.write_text(
                r"""\begin{definitionbox}{Bound}
\begin{definition}[Bound]
\label{def:bound}
Formal definition only.
\end{definition}
\end{definitionbox}

\begin{remark*}[Standard quantified statement]
\[
  \forall a\in A\;(a\leq b).
\]
\end{remark*}

\begin{definitionbox}{Upper Bound}
\begin{definition}[Upper Bound]
\label{def:upper-bound}
Next definition.
\end{definition}
\end{definitionbox}
""",
                encoding="utf-8",
            )

            blocks = formal_blocks_in_file(source, book_root, volume)

        self.assertEqual([block.label for block in blocks], ["def:bound", "def:upper-bound"])
        self.assertIn(r"\begin{definition}[Bound]", blocks[0].text)
        self.assertIn(r"\end{definition}", blocks[0].text)
        self.assertNotIn(r"\end{definitionbox}", blocks[0].text)
        self.assertNotIn("Standard quantified statement", blocks[0].text)
        self.assertNotIn("def:upper-bound", blocks[0].text)


if __name__ == "__main__":
    unittest.main()
