from __future__ import annotations

import re
from pathlib import Path

from core.finding import Finding, finding
from core.tex import read_text, strip_latex_comments
from core.volume import iter_tex


BEGIN_END_RE = re.compile(r"\\(begin|end)\{([^{}]+)\}")


def validate(volume_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for tex in iter_tex(volume_root):
        _validate_file(volume_root, tex, findings)
    return findings


def _validate_file(volume_root: Path, path: Path, findings: list[Finding]) -> None:
    text = strip_latex_comments(read_text(path))
    stack: list[tuple[str, int]] = []
    for match in BEGIN_END_RE.finditer(text):
        kind, env = match.group(1), match.group(2)
        line = text.count("\n", 0, match.start()) + 1
        if kind == "begin":
            stack.append((env, line))
        elif not stack:
            findings.append(finding("unmatched_environment_end", f"Unmatched \\end{{{env}}}.", path, volume_root, line))
        else:
            open_env, open_line = stack.pop()
            if open_env != env:
                findings.append(
                    finding(
                        "mismatched_environment",
                        f"Opened {open_env} at line {open_line} but closed {env}.",
                        path,
                        volume_root,
                        line,
                    )
                )
    for env, line in stack:
        findings.append(finding("unclosed_environment", f"Unclosed environment {env}.", path, volume_root, line))

    if len(re.findall(r"(?<!\\)\\\[", text)) != len(re.findall(r"(?<!\\)\\\]", text)):
        findings.append(finding("unbalanced_display_math", "Display math delimiters \\[ and \\] are not balanced.", path, volume_root))

    if len(re.findall(r"\\begin\{tcolorbox\}", text)) != len(re.findall(r"\\end\{tcolorbox\}", text)):
        findings.append(finding("unbalanced_tcolorbox", "tcolorbox begin/end count is not balanced.", path, volume_root))
