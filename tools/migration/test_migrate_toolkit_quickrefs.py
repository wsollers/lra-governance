from migrate_toolkit_quickrefs import migrate_text


def test_moves_detail_link_to_first_cell():
    source = r"""\begin{toolkitbox}{Ordered Sets --- Quick Reference}
\small
\begin{tabular}{l l l}
\toprule
\textbf{Concept} & \textbf{Meaning} & \textbf{Detail} \\
\midrule
Ordered set & $(A,\leq)$ & \hyperref[def:ordered-set]{$\downarrow$ Def} \\
\bottomrule
\end{tabular}
\end{toolkitbox}
"""
    migrated, count = migrate_text(source)
    assert count == 1
    assert r"\begin{tabular}{l l}" in migrated
    assert r"\textbf{Concept}" in migrated
    assert r"\textbf{Meaning}" in migrated
    assert r"\hyperref[def:ordered-set]{Ordered set}" in migrated
    assert r"& $(A,\leq)$ \\" in migrated
    assert r"\textbf{Detail}" not in migrated


def test_preserves_multiline_row_separator():
    source = r"""\begin{toolkitbox}{Bisection}
\begin{tabular}{l l l l}
\textbf{Label} & \textbf{Statement} & \textbf{Proof method} & \textbf{Detail} \\
NIP
  & statement
  & proof
  & \hyperref[thm:nip]{$\downarrow$} \\[4pt]
\end{tabular}
\end{toolkitbox}
"""
    migrated, count = migrate_text(source)
    assert count == 1
    assert r"\begin{tabular}{l l l}" in migrated
    assert "\\hyperref[thm:nip]{NIP}" in migrated
    assert r"& \hyperref[thm:nip]{$\downarrow$}" not in migrated
    assert r"\\[4pt]" in migrated


def test_keeps_midrule_outside_first_link():
    source = r"""\begin{toolkitbox}{Ordered Sets --- Quick Reference}
\begin{tabular}{l l l}
\textbf{Concept} & \textbf{Meaning} & \textbf{Detail} \\
\midrule
Ordered set & meaning & \hyperref[def:ordered-set]{$\downarrow$ Def} \\
\end{tabular}
\end{toolkitbox}
"""
    migrated, count = migrate_text(source)
    assert count == 1
    assert "\\midrule\n\\hyperref[def:ordered-set]{Ordered set}" in migrated
    assert r"\hyperref[def:ordered-set]{\midrule" not in migrated


def test_migrates_reference_link_column():
    source = r"""\begin{toolkitbox}{Rational Approximation --- Quick Reference}
\begin{tabular}{l l l}
\textbf{Concept} & \textbf{Idea} & \textbf{Reference} \\
\midrule
Mediant & refinement & \hyperref[def:mediant]{$\downarrow$} \\
\end{tabular}
\end{toolkitbox}
"""
    migrated, count = migrate_text(source)
    assert count == 1
    assert r"\textbf{Reference}" not in migrated
    assert r"\hyperref[def:mediant]{Mediant}" in migrated
    assert r"& refinement \\" in migrated


def test_places_link_inside_multicolumn_cell():
    source = r"""\begin{toolkitbox}{Induced Orders}
\begin{tabular}{l l l}
\textbf{Concept} & \textbf{Meaning} & \textbf{Detail} \\
\midrule
\multicolumn{2}{l}{$f$ embedding $\Rightarrow$ isomorphism onto image.} & \hyperref[prop:embedding-iso]{$\downarrow$} \\
\end{tabular}
\end{toolkitbox}
"""
    migrated, count = migrate_text(source)
    assert count == 1
    assert (
        r"\multicolumn{2}{l}{\hyperref[prop:embedding-iso]{$f$ embedding $\Rightarrow$ isomorphism onto image.}}"
        in migrated
    )
    assert r"\hyperref[prop:embedding-iso]{\multicolumn" not in migrated
