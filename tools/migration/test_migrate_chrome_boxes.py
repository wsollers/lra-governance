import unittest

import migrate_chrome_boxes as mcb


class MigrateChromeBoxesTests(unittest.TestCase):
    def test_toolkit_tcolorbox_becomes_toolkitbox(self):
        source = r"""\begin{tcolorbox}[colback=gray!6, colframe=gray!40, arc=2pt,
  left=6pt, right=6pt, top=4pt, bottom=4pt,
  title={\small\textbf{Equality Rules -- Quick Reference}},
  fonttitle=\small\bfseries]
\small
body
\end{tcolorbox}
"""
        report = []
        out = mcb.process(source, report, "x.tex")

        self.assertIn(r"\begin{toolkitbox}{Equality Rules -- Quick Reference}", out)
        self.assertNotIn(r"\begin{toolkitbox}{Equality Rules -- Quick Reference}}", out)
        self.assertIn(r"\end{toolkitbox}", out)
        self.assertNotIn(r"\begin{tcolorbox}", out)
        self.assertEqual(report, [("toolkit", "x.tex")])

    def test_title_cleanup_preserves_nested_math_braces(self):
        source = r"""\begin{tcolorbox}[colback=gray!6, colframe=gray!40, arc=2pt,
  left=6pt, right=6pt, top=4pt, bottom=4pt,
  title={\small\textbf{Toolkit: Problems in $\mathbb{Q}$}},
  fonttitle=\small\bfseries]
body
\end{tcolorbox}
"""
        report = []
        out = mcb.process(source, report, "x.tex")

        self.assertIn(r"\begin{toolkitbox}{Toolkit: Problems in $\mathbb{Q}$}", out)
        self.assertNotIn(r"\mathbb{Q$", out)

    def test_formal_tcolorbox_becomes_box_macro(self):
        source = r"""\begin{tcolorbox}[colback=propbox, colframe=propborder, arc=2pt,
  left=6pt, right=6pt, top=4pt, bottom=4pt,
  title={\small\textbf{Definition (Equality Introduction -- Reflexivity)}},
  fonttitle=\small\bfseries]
\label{def:eq-refl}
For any term $t$, one may infer $t = t$.
\end{tcolorbox}
"""
        report = []
        out = mcb.process(source, report, "x.tex")

        self.assertIn(
            r"\begin{propositionbox}{Definition (Equality Introduction -- Reflexivity)}",
            out,
        )
        self.assertNotIn(
            r"\begin{propositionbox}{Definition (Equality Introduction -- Reflexivity)}}",
            out,
        )
        self.assertIn(r"\end{propositionbox}", out)
        self.assertNotIn(r"\begin{tcolorbox}", out)
        self.assertEqual(report, [("propositionbox", "x.tex")])


if __name__ == "__main__":
    unittest.main()
