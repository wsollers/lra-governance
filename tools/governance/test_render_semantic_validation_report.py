from __future__ import annotations

import json
import subprocess
import sys
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REPORTER = ROOT / "tools" / "governance" / "render_semantic_validation_report.py"
TEMP_ROOT = ROOT / ".test-tmp" / "semantic-report"

if str(ROOT / "tools" / "governance") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools" / "governance"))

from test_validate_semantic_logic import CORRECTED_TEX, real_upper_bound_artifact  # noqa: E402


@contextmanager
def temp_dir():
    path = TEMP_ROOT / str(uuid.uuid4())
    path.mkdir(parents=True, exist_ok=True)
    yield path


def write_fake_volume(root: Path) -> Path:
    volume = root / "lra-volume-i"
    target = volume / "volume-i" / "book-order" / "bounds"
    target.mkdir(parents=True)
    (volume / "volume-i-book-order.tex").write_text(
        r"\input{volume-i/book-order/bounds/index}" + "\n",
        encoding="utf-8",
    )
    (target / "index.tex").write_text(
        r"\chapter{Bounds}" + "\n" + r"\input{volume-i/book-order/bounds/routed}" + "\n",
        encoding="utf-8",
    )
    routed_tex = "\n".join(
        [
            r"\begin{definitionbox}{Upper Bound}",
            CORRECTED_TEX.replace(
                r"\begin{definition}",
                r"\begin{definition}[Upper Bound in the Real Line]",
            ).replace(
                r"\end{definition}",
                r"\label{def:real-upper-bound}\end{definition}",
            ).strip(),
            r"\end{definitionbox}",
            r"\begin{remark*}[Standard quantified statement]",
            r"\[",
            r"  \operatorname{UpperBound}(u,A,P_{\mathbb{R}})\iff(\forall x\in A)(x\leq u).",
            r"\]",
            r"\end{remark*}",
            r"\begin{remark*}[Predicate reading]",
            r"\[",
            r"  \operatorname{UpperBound}(u,A,P_{\mathbb{R}}).",
            r"\]",
            r"\end{remark*}",
            r"\begin{remark*}[Negated quantified statement]",
            r"\[",
            r"  (\exists x\in A)(u<x).",
            r"\]",
            r"\end{remark*}",
            r"\begin{remark*}[Failure modes]",
            r"A witness above the candidate upper bound.",
            r"\end{remark*}",
            r"\begin{remark*}[Interpretation]",
            r"Every element of A lies below u.",
            r"\end{remark*}",
            r"\begin{dependencies}",
            r"\begin{itemize}",
            r"  \item \hyperref[def:ordered-set]{Ordered Set}",
            r"\end{itemize}",
            r"\end{dependencies}",
        ]
    )
    (target / "routed.tex").write_text(routed_tex, encoding="utf-8")
    (target / "unrouted.tex").write_text(
        r"\begin{definition}\label{def:unrouted}Not routed.\end{definition}",
        encoding="utf-8",
    )
    return volume


class RenderSemanticValidationReportTests(unittest.TestCase):
    def test_renders_positive_report_with_llm_payload_comparison(self):
        with temp_dir() as root:
            write_fake_volume(root)
            llm_dir = root / "llm"
            llm_dir.mkdir()
            payload = {"artifact": real_upper_bound_artifact(), "corrected_tex": CORRECTED_TEX}
            (llm_dir / "def-real-upper-bound.json").write_text(json.dumps(payload), encoding="utf-8")
            scope = root / "scope.json"
            scope.write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "label": "def:real-upper-bound",
                                "status": "validated_llm_payload",
                                "result": {"result": "pass"},
                                "materialized": True,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            index = root / "build" / "bounding-rpt.md"
            reports = root / "build" / "bounding-rpt"
            summary = root / "summary.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPORTER),
                    "--repos-root",
                    str(root),
                    "--volume",
                    "i",
                    "--chapter",
                    "bounds",
                    "--scope-validation",
                    str(scope),
                    "--llm-data-dir",
                    str(llm_dir),
                    "--output-index",
                    str(index),
                    "--output-dir",
                    str(reports),
                    "--summary-output",
                    str(summary),
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
            )
            report_text = (reports / "def-real-upper-bound.md").read_text(encoding="utf-8")
            index_text = index.read_text(encoding="utf-8")
            data = json.loads(summary.read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(data["formal_candidates"], 1)
        self.assertIn("# def:real-upper-bound", report_text)
        self.assertIn("## Original Environment", report_text)
        self.assertIn("Standard quantified statement", report_text)
        self.assertIn("Artifact Comparison", report_text)
        self.assertIn("def:ordered-set (Ordered Set)", report_text)
        self.assertIn("def-real-upper-bound.md", index_text)

    def test_missing_payload_is_pending_not_failure(self):
        with temp_dir() as root:
            write_fake_volume(root)
            index = root / "build" / "bounding-rpt.md"
            reports = root / "build" / "bounding-rpt"
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPORTER),
                    "--repos-root",
                    str(root),
                    "--volume",
                    "i",
                    "--chapter",
                    "bounds",
                    "--output-index",
                    str(index),
                    "--output-dir",
                    str(reports),
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
            )
            report_text = (reports / "def-real-upper-bound.md").read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("LLM payload: `missing`", report_text)
        self.assertIn("_missing_", report_text)

    def test_malformed_payload_is_reported(self):
        with temp_dir() as root:
            write_fake_volume(root)
            llm_dir = root / "llm"
            llm_dir.mkdir()
            (llm_dir / "def-real-upper-bound.json").write_text(json.dumps({"not_artifact": {}}), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPORTER),
                    "--repos-root",
                    str(root),
                    "--volume",
                    "i",
                    "--chapter",
                    "bounds",
                    "--llm-data-dir",
                    str(llm_dir),
                    "--output-index",
                    str(root / "build" / "bounding-rpt.md"),
                    "--output-dir",
                    str(root / "build" / "bounding-rpt"),
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
            )
            report_text = (root / "build" / "bounding-rpt" / "def-real-upper-bound.md").read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("LLM payload could not be read", report_text)

    def test_unrouted_tex_is_excluded(self):
        with temp_dir() as root:
            write_fake_volume(root)
            summary = root / "summary.yaml"
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPORTER),
                    "--repos-root",
                    str(root),
                    "--volume",
                    "i",
                    "--chapter",
                    "bounds",
                    "--output-index",
                    str(root / "build" / "bounding-rpt.md"),
                    "--output-dir",
                    str(root / "build" / "bounding-rpt"),
                    "--summary-output",
                    str(summary),
                ],
                capture_output=True,
                text=True,
            )
            data = yaml.safe_load(summary.read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(data["formal_candidates"], 1)
        self.assertFalse((root / "build" / "bounding-rpt" / "def-unrouted.md").exists())


if __name__ == "__main__":
    unittest.main()
