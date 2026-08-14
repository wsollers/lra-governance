"""Deterministically audit chapter symbol usage against canonical registries."""

import sys
from pathlib import Path

from auditor import config
from auditor.report import save_symbol_audit_report


TOOLS_ROOT = Path(__file__).resolve().parents[3] / "tools" / "governance"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from audit_chapter_symbols import (  # noqa: E402
    audit_chapter_symbols,
    collect_chapter_tex,
    format_symbol_audit_markdown,
)


def _collect_chapter_tex(chapter_path: Path) -> str:
    """Compatibility wrapper for callers that need the concatenated view."""
    return collect_chapter_tex(chapter_path)


def audit_symbols(
    chapter_path: Path,
) -> str:
    """
    Audits a chapter's use of predicates, structures, notation, and relations.

    Returns:
        A markdown string containing the audit report.
        The report is also written to disk and printed to terminal.
    """
    chapter_path = Path(chapter_path).resolve()
    chapter = chapter_path.name
    result = audit_chapter_symbols(
        chapter_path,
        governance_root=config.REPO_ROOT,
    )
    markdown = format_symbol_audit_markdown(result)

    save_symbol_audit_report(markdown, chapter)

    return markdown
