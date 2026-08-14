from __future__ import annotations

import re
from collections.abc import Sequence


PREFIX = {
    "theorem": "thm",
    "lemma": "lem",
    "proposition": "prop",
    "corollary": "cor",
}
RESTATEMENT_ENV = {
    "theorem": "theorem*",
    "lemma": "lemma*",
    "proposition": "proposition*",
    "corollary": "corollary*",
}
_SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_LABEL_RE = re.compile(r"[a-z][a-z0-9-]*:[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def _require_text(name: str, value: str) -> str:
    value = (value or "").strip()
    if not value:
        raise ValueError(f"{name} is required")
    return value


def _validate_label(name: str, value: str) -> str:
    value = _require_text(name, value)
    if not _LABEL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a canonical label such as thm:cauchy-criterion")
    return value


def _dependency_block(dependencies: Sequence[tuple[str, str]]) -> str:
    if not dependencies:
        return r"\NoLocalDependencies"
    items: list[str] = []
    for target, display in dependencies:
        target = _validate_label("dependency label", target)
        display = _require_text("dependency display name", display)
        items.append(f"  \\item \\hyperref[{target}]{{{display}}}")
    return (
        "\\begin{dependencies}\n"
        "\\begin{itemize}\n"
        + "\n".join(items)
        + "\n\\end{itemize}\n"
        "\\end{dependencies}"
    )


def render_proof_stub(
    kind: str,
    slug: str,
    title: str,
    statement_body: str,
    deps: Sequence[tuple[str, str]] | None = None,
    *,
    statement_label: str | None = None,
    proof_label: str | None = None,
    dependency_block: str | None = None,
) -> str:
    """Render a proof stub from explicit inputs without model inference.

    ``statement_body`` is copied verbatim after surrounding whitespace is
    removed. Dependencies may be supplied either as label/display pairs or as
    an already validated LaTeX dependency block, but not both.
    """
    if kind not in PREFIX:
        raise ValueError(f"kind must be one of: {', '.join(PREFIX)}")
    if not _SLUG_RE.fullmatch(slug or ""):
        raise ValueError("slug must be lowercase ASCII words separated by hyphens")
    title = _require_text("title", title)
    statement_body = _require_text("statement_body", statement_body)
    statement_label = _validate_label(
        "statement_label", statement_label or f"{PREFIX[kind]}:{slug}"
    )
    expected_prefix = f"{PREFIX[kind]}:"
    if not statement_label.startswith(expected_prefix):
        raise ValueError(f"statement_label for {kind} must start with {expected_prefix}")
    proof_label = _validate_label("proof_label", proof_label or f"prf:{slug}")
    if not proof_label.startswith("prf:"):
        raise ValueError("proof_label must start with prf:")
    if dependency_block is not None and deps:
        raise ValueError("supply deps or dependency_block, not both")
    rendered_dependencies = (
        _require_text("dependency_block", dependency_block)
        if dependency_block is not None
        else _dependency_block(deps or ())
    )
    kindword = kind.capitalize()
    environment = RESTATEMENT_ENV[kind]
    return (
        "\\newpage\n"
        "\\phantomsection\n"
        f"\\label{{{proof_label}}}\n"
        f"\\LRAProofFor{{{statement_label}}}\n\n"
        "\\begin{remark*}[Return]\n"
        f"\\hyperref[{statement_label}]{{$\\leftarrow$ Back to {kindword} ({title}) in Notes}}\n"
        "\\end{remark*}\n\n"
        f"\\begin{{{environment}}}[{title}]\n"
        f"{statement_body}\n"
        f"\\end{{{environment}}}\n\n"
        "\\begin{proof}[Professional Standard Proof]\n"
        "\\LRAProofBodyStart\n"
        "TODO: supply the compact professional proof.\n"
        "\\end{proof}\n\n"
        "\\begin{proof}[Detailed Learning Proof]\n"
        "\\LRAProofBodyStart\n"
        "TODO: supply the expanded learning proof.\n"
        "\\end{proof}\n\n"
        "\\begin{remark*}[Proof structure]\n"
        "\\end{remark*}\n\n"
        f"{rendered_dependencies}\n\n"
        "\\clearpage\n"
    )


def proof_filename(slug: str) -> str:
    if not _SLUG_RE.fullmatch(slug or ""):
        raise ValueError("slug must be lowercase ASCII words separated by hyphens")
    return f"prf-{slug}.tex"
