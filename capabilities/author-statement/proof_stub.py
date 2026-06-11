r"""Deterministic proof-stub generator (validator-compliant, no LLM).

Emits a proof stub matching audit_proof_layout's required layer order:
\newpage, \phantomsection, \label{prf:slug}, \LRAProofFor{prefix:slug},
remark*[Return] (with return hyperref), theorem* restatement, two \begin{proof}
bodies (Professional / Detailed, both TODO for a stub), remark*[Proof structure]
(BLANK body in a stub -- whitespace satisfies the validator's presence check while
rendering blank), dependencies, \clearpage. Filename must be prf-<slug>.tex.

Stub squareness: both proof bodies are TODO (compliant_stub) and the Proof structure
body is blank. When the proof is authored, the bodies and structure block are filled.
"""
from __future__ import annotations

PREFIX = {"theorem": "thm", "lemma": "lem", "proposition": "prop", "corollary": "cor"}

def render_proof_stub(kind: str, slug: str, title: str, statement_body: str,
                      deps: list[tuple[str, str]] | None = None) -> str:
    """Return the validator-compliant proof-stub LaTeX for a provable statement.

    kind: theorem|lemma|proposition|corollary. statement_body: the verbatim claim
    (no \\label). deps: list of (target_label, display) hyperref pairs; empty -> \\NoLocalDependencies.
    """
    prefix = PREFIX[kind]
    kindword = kind.capitalize()
    if deps:
        items = "\n".join(f"  \\item \\hyperref[{tgt}]{{{label}}}" for tgt, label in deps)
        depblock = ("\\begin{dependencies}\n\\begin{itemize}\n"
                    f"{items}\n\\end{{itemize}}\n\\end{{dependencies}}")
    else:
        depblock = "\\NoLocalDependencies"
    body = statement_body.strip()
    return (
        "\\newpage\n"
        "\\phantomsection\n"
        f"\\label{{prf:{slug}}}\n"
        f"\\LRAProofFor{{{prefix}:{slug}}}\n"
        "\\begin{remark*}[Return]\n"
        f"\\hyperref[{prefix}:{slug}]{{$\\leftarrow$ Back to {kindword} ({title}) in Notes}}\n"
        "\\end{remark*}\n"
        f"\\begin{{theorem*}}[{title}]\n{body}\n\\end{{theorem*}}\n"
        "\\begin{proof}[Professional Standard Proof]\n"
        "TODO: supply the compact professional proof.\n"
        "\\end{proof}\n"
        "\\begin{proof}[Detailed Learning Proof]\n"
        "TODO: supply the expanded learning proof.\n"
        "\\end{proof}\n"
        "\\begin{remark*}[Proof structure]\n\n\\end{remark*}\n"   # blank body: present + renders blank
        f"{depblock}\n"
        "\\clearpage\n"
    )

def proof_filename(slug: str) -> str:
    return f"prf-{slug}.tex"
