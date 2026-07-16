from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "governance" / "semantic_chapter_sweep.py"


DARBOUX_SOURCE = r"""
\begin{theorembox}{Theorem (Darboux's Theorem)}
\begin{theorem}[Darboux's Theorem]
\label{thm:darboux}
Let $I := [a,b] \subseteq \mathbb{R}$ and let $f : I \to \mathbb{R}$ be differentiable on $I$.
If $k$ is strictly between $f'(a)$ and $f'(b)$, then there exists $c \in (a,b)$ such that
\[
f'(c) = k.
\]
\end{theorem}
\end{theorembox}

\begin{remark*}[Standard quantified statement]
\[
\forall k\;(\min(f'(a),f'(b)) < k < \max(f'(a),f'(b)) \Rightarrow \exists c \in (a,b)\;(f'(c)=k)).
\]
\end{remark*}

\begin{remark*}[Predicate reading]
The displayed quantified statement is the predicate-level form of $label.
\[
  \operatorname{Derivative}(D,f,a,\mathbb{R},\mathbb{R}).
\]
\end{remark*}
"""


QUANTIFIER_SOURCE = r"""
\begin{definitionbox}{Class \(C^{1,1}\)}
\begin{definition}[Class \(C^{1,1}\)]
\label{def:class-c11}
The function \(f\) is in \(C^{1,1}\) if its derivative is Lipschitz.
\end{definition}
\end{definitionbox}

\begin{remark*}[Standard quantified statement]
\[
  \forall x,y\in I\; |f'(x)-f'(y)| \leq L|x-y|.
\]
\end{remark*}
"""


class SemanticChapterSweepTests(unittest.TestCase):
    def run_sweep(self, source: str) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            tex = repo / "chapter.tex"
            tex.write_text(source, encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(TOOL),
                    "--target",
                    str(tex),
                    "--repo-root",
                    str(repo),
                    "--no-discover-knowledge",
                    "--format",
                    "json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            return json.loads(completed.stdout)

    def run_sweep_with_knowledge(self, source: str, knowledge_ids: list[str]) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            tex = repo / "chapter.tex"
            tex.write_text(source, encoding="utf-8")
            knowledge = repo / "knowledge.json"
            knowledge.write_text(
                json.dumps({"nodes": [{"id": item} for item in knowledge_ids]}),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(TOOL),
                    "--target",
                    str(tex),
                    "--repo-root",
                    str(repo),
                    "--knowledge-json",
                    str(knowledge),
                    "--no-discover-knowledge",
                    "--format",
                    "json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            return json.loads(completed.stdout)

    def test_flags_known_darboux_endpoint_and_placeholder_traps(self) -> None:
        payload = self.run_sweep(DARBOUX_SOURCE)
        item = payload["items"][0]
        self.assertEqual(item["label"], "thm:darboux")
        codes = {finding["code"] for finding in item["findings"]}
        self.assertIn("DARBOUX_ENDPOINT_FORMULATION", codes)
        self.assertIn("PLACEHOLDER_PREDICATE_READING", codes)
        self.assertIn("BARE_DERIVATIVE_LOCUS", codes)

    def test_flags_quantifier_macro_variable_count_mismatch(self) -> None:
        payload = self.run_sweep(QUANTIFIER_SOURCE)
        item = payload["items"][0]
        codes = {finding["code"] for finding in item["findings"]}
        self.assertIn("QUANTIFIER_VARIABLE_COUNT_MISMATCH", codes)

    def test_uses_knowledge_explorer_ids_for_strict_dependency_resolution(self) -> None:
        source = r"""
\begin{theorembox}{Uses External Dependency}
\begin{theorem}[Uses External Dependency]
\label{thm:local}
If \(x=x\), then \(x=x\).
\end{theorem}
\end{theorembox}
\begin{dependencies}
\begin{itemize}
\item \hyperref[def:function]{Function}
\end{itemize}
\end{dependencies}
"""
        unresolved = self.run_sweep(source)
        unresolved_codes = {finding["code"] for item in unresolved["items"] for finding in item["findings"]}
        self.assertIn("UNRESOLVED_REFERENCE_LABEL", unresolved_codes)

        resolved = self.run_sweep_with_knowledge(source, ["def:function"])
        resolved_codes = {finding["code"] for item in resolved["items"] for finding in item["findings"]}
        self.assertNotIn("UNRESOLVED_REFERENCE_LABEL", resolved_codes)
        self.assertEqual(1, resolved["known_label_counts"]["knowledge_explorer"])


if __name__ == "__main__":
    unittest.main()
