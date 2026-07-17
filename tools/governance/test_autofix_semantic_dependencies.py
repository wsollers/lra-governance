from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "governance"))
import autofix_semantic_dependencies as fixer  # noqa: E402


def report_for(label: str, source_file: str, additions: list[str]) -> dict:
    return {
        "schema_version": "lra.semantic-ast-ensemble/1.0",
        "reports": [
            {
                "label": label,
                "source_file": source_file,
                "dependency_verification": {
                    "status": "fail" if additions else "pass",
                    "suggested_dependency_additions": additions,
                },
            }
        ],
    }


class AutofixSemanticDependenciesTests(unittest.TestCase):
    def run_fix(self, tex: str, report: dict, *, dry_run: bool = False) -> tuple[dict, str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "fixture.tex"
            source.write_text(tex, encoding="utf-8")
            report_path = root / "report.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            summary = fixer.autofix(root, [report_path], dry_run=dry_run)
            return summary, source.read_text(encoding="utf-8")

    def test_adds_missing_dependency_to_existing_itemize_block(self):
        tex = r"""
\begin{definitionbox}{Supremum}
\begin{definition}[Supremum]
\label{def:supremum}
Definition text.
\end{definition}
\end{definitionbox}
\begin{remark*}[Predicate reading]
\[
P=\mathsf{OrderedSet}(S,\leq),\quad \operatorname{UpperBound}(s,A,P).
\]
\end{remark*}
\begin{dependencies}
\begin{itemize}
  \item \hyperref[def:real-upper-bound]{Upper Bound}
\end{itemize}
\end{dependencies}
"""
        report = report_for("def:supremum", "fixture.tex", ["def:ordered-set", "def:real-upper-bound"])
        summary, patched = self.run_fix(tex, report)
        self.assertEqual(1, summary["patched_count"])
        self.assertIn(r"\item \hyperref[def:ordered-set]{Ordered Set}", patched)
        self.assertEqual(1, patched.count("def:real-upper-bound"))
        record = summary["records"][0]
        self.assertEqual(["def:ordered-set"], record["additions"])
        self.assertEqual(["def:real-upper-bound"], record["skipped_existing"])

    def test_creates_dependency_block_when_missing(self):
        tex = r"""
\begin{theorembox}{Fixture}
\begin{theorem}[Fixture]
\label{thm:fixture}
Theorem text.
\end{theorem}
\end{theorembox}
\begin{remark*}[Predicate reading]
\[
\operatorname{Positive}(x)\Rightarrow\operatorname{Nonzero}(x).
\]
\end{remark*}
"""
        report = report_for("thm:fixture", "fixture.tex", ["def:positive", "def:nonzero"])
        summary, patched = self.run_fix(tex, report)
        self.assertEqual(1, summary["patched_count"])
        self.assertIn(r"\begin{dependencies}", patched)
        self.assertIn(r"\item \hyperref[def:positive]{Positive}", patched)
        self.assertIn(r"\item \hyperref[def:nonzero]{Nonzero}", patched)

    def test_dry_run_reports_without_writing(self):
        tex = r"""
\begin{theorembox}{Fixture}
\begin{theorem}[Fixture]
\label{thm:fixture}
Theorem text.
\end{theorem}
\end{theorembox}
"""
        report = report_for("thm:fixture", "fixture.tex", ["def:positive"])
        summary, patched = self.run_fix(tex, report, dry_run=True)
        self.assertEqual(1, summary["would_patch_count"])
        self.assertEqual(tex, patched)

    def test_skips_when_all_dependencies_already_present(self):
        tex = r"""
\begin{theorembox}{Fixture}
\begin{theorem}[Fixture]
\label{thm:fixture}
Theorem text.
\end{theorem}
\end{theorembox}
\begin{dependencies}
\begin{itemize}
  \item \hyperref[def:positive]{Positive}
\end{itemize}
\end{dependencies}
"""
        report = report_for("thm:fixture", "fixture.tex", ["def:positive"])
        summary, patched = self.run_fix(tex, report)
        self.assertEqual(1, summary["unchanged_count"])
        self.assertEqual(tex, patched)


if __name__ == "__main__":
    unittest.main()
