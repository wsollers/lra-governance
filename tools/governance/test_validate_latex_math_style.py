from __future__ import annotations

import json
import shutil
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path

from validate_latex_math_style import load_notation_roles, main, validate_target


ROOT = Path(__file__).resolve().parents[2]
TEMP_ROOT = ROOT / ".test-tmp" / "latex-math-style"


@contextmanager
def temporary_directory():
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    path = TEMP_ROOT / f"case-{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    try:
        yield str(path)
    finally:
        shutil.rmtree(path, ignore_errors=True)


class LatexMathStyleValidatorTests(unittest.TestCase):
    def test_loads_notation_roles_from_registry(self) -> None:
        roles = load_notation_roles()

        self.assertIn(r"\to", roles.function_type_arrow)
        self.assertIn(r"\mapsto", roles.function_rule_arrow)
        self.assertIn(r"\colon", roles.function_signature_colon)
        self.assertIn(r":", roles.set_builder_separator)
        self.assertIn(r"\Longrightarrow", roles.logical_implication)
        self.assertIn(r"\Longleftrightarrow", roles.logical_equivalence)
        self.assertIn(r"\neg", roles.logical_negation)
        self.assertIn(r"\land", roles.logical_conjunction)
        self.assertIn(r"\lor", roles.logical_disjunction)
        self.assertIn(r"\models", roles.semantic_satisfaction)
        self.assertIn(r"\vdash", roles.syntactic_derivability)
        self.assertIn(r"\equiv", roles.formula_object_equivalence)
        self.assertIn(r"\rightarrow", roles.logical_implication)
        self.assertIn(r"\leftrightarrow", roles.logical_equivalence)

    def test_notation_roles_keep_relation_equivalence_distinct_from_logical_iff(self) -> None:
        roles = load_notation_roles()

        self.assertNotIn(r"\equiv", roles.logical_equivalence)
        self.assertNotIn(r"\leftrightarrow", roles.formula_object_equivalence)
        self.assertNotIn(r"\to", roles.logical_implication)
        self.assertNotIn(r"\rightarrow", roles.function_type_arrow)

    def test_accepts_house_function_logic_and_set_builder_notation(self) -> None:
        with temporary_directory() as tmp:
            path = Path(tmp) / "good.tex"
            path.write_text(
                r"""
\[
f\colon A\to B,\qquad x\mapsto x^2.
\]
\[
P\Longrightarrow Q,\qquad P\Longleftrightarrow Q.
\]
\[
\Gamma\models\varphi,\qquad \Gamma\vdash\varphi,\qquad \varphi\equiv\psi.
\]
\[
\{x\in X: x>0\},\qquad \left\{y\in Y\mid y\geq 0\right\}.
\]
\begin{remark*}[Standard quantified statement]
\[
\forall x\in A,\ x\leq u.
\]
\end{remark*}
""",
                encoding="utf-8",
            )

            self.assertEqual(validate_target(path), [])

    def test_rejects_ambiguous_function_and_display_logic_notation(self) -> None:
        with temporary_directory() as tmp:
            path = Path(tmp) / "bad.tex"
            path.write_text(
                r"""
\[
f: A\to B.
\]
\[
f\colon A\rightarrow B.
\]
\[
x\to x^2.
\]
\[
P\Rightarrow Q,\qquad P\iff Q.
\]
""",
                encoding="utf-8",
            )

            codes = {finding.code for finding in validate_target(path)}
            self.assertIn("function_signature_uses_plain_colon", codes)
            self.assertIn("function_signature_uses_logical_arrow", codes)
            self.assertIn("function_rule_uses_type_arrow", codes)
            self.assertIn("display_implication_uses_compact_connective", codes)
            self.assertIn("display_equivalence_uses_inline_connective", codes)

    def test_rejects_malformed_tex_artifacts_and_prose_quantified_statement(self) -> None:
        with temporary_directory() as tmp:
            path = Path(tmp) / "bad.tex"
            path.write_text(
                r"""
\[
\left{x\in X: x>0\right}
\]
=======
\begin{remark*}[Standard quantified statement]
\[
\text{Let } A\subseteq\mathbb{R}.
\]
\end{remark*}
""",
                encoding="utf-8",
            )

            codes = {finding.code for finding in validate_target(path)}
            self.assertIn("malformed_set_brace_delimiter", codes)
            self.assertIn("markdown_artifact_in_tex", codes)
            self.assertIn("standard_quantified_statement_contains_prose", codes)

    def test_accepts_consistent_family_representations(self) -> None:
        with temporary_directory() as tmp:
            path = Path(tmp) / "good.tex"
            path.write_text(
                r"""
\[
\forall \mathcal U\,
\left(
\operatorname{OpenCover}(\mathcal U,K,\mathbb R)
\Longrightarrow
\exists \mathcal V\subseteq\mathcal U,\quad
K\subseteq\bigcup_{V\in\mathcal V}V
\right).
\]
\[
\forall \{U_i\}_{i\in I}\,
\left(
K\subseteq\bigcup_{i\in I}U_i
\Longrightarrow
\exists \text{finite }J\subseteq I,\quad
K\subseteq\bigcup_{i\in J}U_i
\right).
\]
""",
                encoding="utf-8",
            )

            self.assertEqual(validate_target(path), [])

    def test_accepts_theorem_body_display_with_prose_declared_indexed_family(self) -> None:
        with temporary_directory() as tmp:
            path = Path(tmp) / "good.tex"
            path.write_text(
                r"""
\begin{theorem}
If \(n\in\mathbb N\) and \(F_1,\ldots,F_n\subseteq\mathbb R\) are closed, then
\[
  \bigcup_{k=1}^{n}F_k
\]
is closed.
\end{theorem}
""",
                encoding="utf-8",
            )

            self.assertEqual(validate_target(path), [])

    def test_rejects_mixed_family_representation_with_free_indexed_symbols(self) -> None:
        with temporary_directory() as tmp:
            path = Path(tmp) / "bad.tex"
            path.write_text(
                r"""
\begin{remark*}[Predicate reading]
\[
K\subseteq\mathbb{R},\qquad
\operatorname{IsCompact}(K,\mathbb{R})
\Longleftrightarrow
\forall \mathcal{U}\;\bigl(\operatorname{OpenCover}(\mathcal{U},K,\mathbb{R})
\Longrightarrow \exists J\;(J\subseteq I\land \operatorname{FiniteSet}(J)
\land K\subseteq\textstyle\bigcup_{i\in J}U_i)\bigr).
\]
\end{remark*}
""",
                encoding="utf-8",
            )

            codes = {finding.code for finding in validate_target(path)}
            self.assertIn("undeclared_indexed_family_symbol", codes)
            self.assertIn("possibly_undeclared_family_index_set", codes)
            self.assertIn("mixed_set_and_indexed_family_representation", codes)

    def test_rejects_standard_quantified_block_not_visibly_closed(self) -> None:
        with temporary_directory() as tmp:
            path = Path(tmp) / "bad.tex"
            path.write_text(
                r"""
\begin{remark*}[Standard quantified statement]
\[
\{U_i\}_{i\in J} \text{ is a finite subcover of } E
\Longleftrightarrow
\bigl(J\subseteq I \land J \text{ is finite}
\land E\subseteq\textstyle\bigcup_{i\in J}U_i\bigr).
\]
\end{remark*}
""",
                encoding="utf-8",
            )

            codes = {finding.code for finding in validate_target(path)}
            self.assertIn("possibly_undeclared_family_index_set", codes)
            self.assertIn("support_block_not_visibly_closed", codes)

    def test_rejects_lost_family_delimiters(self) -> None:
        with temporary_directory() as tmp:
            path = Path(tmp) / "bad.tex"
            path.write_text(
                r"""
\[
\exists \{U_i\}_{i\in I}\Bigl(\bigl(\forall i\in IU_i \text{ open}\bigr)
\land \forall \text{finite }J\subseteq IK\not\subseteq\bigcup_{i\in J}U_i\Bigr).
\]
""",
                encoding="utf-8",
            )

            codes = {finding.code for finding in validate_target(path)}
            self.assertIn("suspect_lost_delimiter_after_membership_domain", codes)
            self.assertIn("suspect_lost_delimiter_after_subset_domain", codes)

    def test_rejects_common_malformed_control_sequence_typos(self) -> None:
        with temporary_directory() as tmp:
            path = Path(tmp) / "bad.tex"
            path.write_text(
                r"""
\[
\leqft[
A
\rigth]
\]
""",
                encoding="utf-8",
            )

            codes = {finding.code for finding in validate_target(path)}
            self.assertIn("malformed_common_control_sequence", codes)

    def test_reports_json_shape_from_cli(self) -> None:
        with temporary_directory() as tmp:
            path = Path(tmp) / "bad.tex"
            path.write_text(r"\[f: A\to B.\]", encoding="utf-8")
            output = _capture_stdout(lambda: main(["--target", str(path), "--format", "json"]))
            payload = json.loads(output)

            self.assertFalse(payload["clean"])
            self.assertEqual(payload["findings"][0]["code"], "function_signature_uses_plain_colon")


def _capture_stdout(callable_):
    import io
    import contextlib

    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        callable_()
    return stream.getvalue()


if __name__ == "__main__":
    unittest.main()
