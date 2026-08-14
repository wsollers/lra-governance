from __future__ import annotations


def _tex(value: str) -> str:
    return (
        value.replace("\\", r"\textbackslash{}")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("#", r"\#")
        .replace("_", r"\_")
    )


def render_breadcrumb(
    subject: str,
    current_title: str,
    registry: list[dict],
    is_stub: bool = False,
) -> str:
    """Render prior/current/next breadcrumb values from registry order."""
    subjects = [entry["subject"] for entry in registry]
    titles = [entry["display_title"] for entry in registry]
    if subject in subjects:
        index = subjects.index(subject)
        current = titles[index]
        prior = titles[index - 1] if index else ""
        following = titles[index + 1] if index < len(titles) - 1 else ""
    else:
        current, prior, following = current_title, "", ""
    output = (
        f"\\breadcrumb{{{_tex(subject)}}}{{{_tex(prior)}}}"
        f"{{{_tex(current)}}}{{{_tex(following)}}}"
    )
    return output + ("\n\\stubstatus" if is_stub else "")
