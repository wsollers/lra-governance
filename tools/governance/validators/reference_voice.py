from __future__ import annotations

import re
from pathlib import Path

from core.finding import Finding, finding
from core.tex import read_text, strip_latex_comments
from core.volume import iter_tex


VOICE_BLOCK_RE = re.compile(
    r"\\begin\{(?P<env>remark\*|example\*|exposition)\}(?:\[(?P<title>[^\]]+)\])?(?P<body>[\s\S]*?)\\end\{(?P=env)\}",
    re.IGNORECASE,
)
VOICE_BANNED_PATTERNS = {
    r"\bwe\b": "first-person plural",
    r"\bus\b": "first-person plural",
    r"\bour\b": "first-person plural",
    r"\bours\b": "first-person plural",
    r"\bourselves\b": "first-person plural",
    r"\byou\b": "direct reader address",
    r"\byour\b": "direct reader address",
    r"\byours\b": "direct reader address",
    r"\byourself\b": "direct reader address",
    r"\byourselves\b": "direct reader address",
    r"\bstudents?\b": "classroom voice",
    r"\breaders?\b": "reader-address voice",
    r"\blearners?\b": "classroom voice",
    r"\binstructors?\b": "classroom voice",
    r"\bteachers?\b": "classroom voice",
    r"\bclass(?:room)?\b": "classroom voice",
    r"\bcourse\b": "course-transcript voice",
    r"\blecture\b": "course-transcript voice",
    r"\blesson\b": "workbook voice",
    r"\bworkbook\b": "workbook voice",
    r"\bworksheet\b": "workbook voice",
    r"\bhomework\b": "workbook voice",
}


def validate(volume_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for tex in iter_tex(volume_root):
        if tex.name.startswith("figure-"):
            continue
        _validate_file(volume_root, tex, findings)
    return findings


def _validate_file(volume_root: Path, path: Path, findings: list[Finding]) -> None:
    text = strip_latex_comments(read_text(path))
    for block in VOICE_BLOCK_RE.finditer(text):
        body = _voice_text(block.group("body"))
        for pattern, reason in VOICE_BANNED_PATTERNS.items():
            match = re.search(pattern, body, re.IGNORECASE)
            if not match:
                continue
            title = (block.group("title") or block.group("env")).strip()
            findings.append(
                finding(
                    "non_reference_voice",
                    f"{title} block uses {reason}: '{match.group(0)}'. Use impersonal reference voice.",
                    path,
                    volume_root,
                    text.count("\n", 0, block.start("body")) + 1,
                    "warning",
                )
            )


def _voice_text(body: str) -> str:
    text = re.sub(r"\\(?:label|hyperref|ref|citep?|url|href)\b(?:\[[^\]]*\])?(?:\{[^{}]*\}){0,2}", " ", body)
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?", " ", text)
    text = re.sub(r"[{}$^_\\]", " ", text)
    return re.sub(r"\s+", " ", text)
