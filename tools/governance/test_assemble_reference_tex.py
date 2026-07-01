from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assemble_reference_tex import generate_reference_roots


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


class AssembleReferenceTexTests(unittest.TestCase):
    def test_reference_root_keeps_only_definitions_and_theorem_like_blocks(self) -> None:
        repo = Path(__file__).resolve().parents[2] / "test-reference-fixture"
        if repo.exists():
            shutil.rmtree(repo)
        repo.mkdir(parents=True)
        self.addCleanup(lambda: shutil.rmtree(repo, ignore_errors=True))
        write(
            repo / "volume-i.tex",
            r"""\documentclass{report}
\input{common/volume-preamble}
\begin{document}
\input{volume-i/index}
\end{document}
""",
        )
        write(
            repo / "volume-i" / "index.tex",
            r"""\part{Logic}
\input{volume-i/chapter/index}
""",
        )
        write(
            repo / "volume-i" / "chapter" / "index.tex",
            r"""\chapter{Chapter}
\input{volume-i/chapter/notes/index}
\input{volume-i/chapter/proofs/index}
""",
        )
        write(
            repo / "volume-i" / "chapter" / "notes" / "index.tex",
            r"""\section{Topic}
\input{volume-i/chapter/notes/topic/notes-topic}
""",
        )
        write(
            repo / "volume-i" / "chapter" / "notes" / "topic" / "notes-topic.tex",
            r"""Introductory prose that should not render.
\begin{definition}[Kept Definition]\label{def:kept}
Definition body.
\end{definition}
\begin{example}
Example body.
\end{example}
\begin{lemma}[Kept Lemma]\label{lem:kept}
Lemma body.
\end{lemma}
""",
        )
        write(
            repo / "volume-i" / "chapter" / "proofs" / "index.tex",
            r"""\begin{theorem*}[Proof Restatement]
Proof restatement body.
\end{theorem*}
""",
        )

        generated = generate_reference_roots(
            repo,
            [repo / "volume-i.tex"],
            repo / "build" / "reference",
        )

        self.assertEqual(len(generated), 1)
        text = generated[0].read_text(encoding="utf-8")
        self.assertIn(r"\begin{definition}[Kept Definition]", text)
        self.assertIn(r"\begin{lemma}[Kept Lemma]", text)
        self.assertIn(r"\section{Topic}", text)
        self.assertNotIn("Introductory prose", text)
        self.assertNotIn(r"\begin{example}", text)
        self.assertNotIn("Proof Restatement", text)


if __name__ == "__main__":
    unittest.main()
