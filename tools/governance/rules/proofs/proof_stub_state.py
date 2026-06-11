from __future__ import annotations

import re
from collections.abc import Iterable

from core.finding import Finding

PROOF_STRUCTURE_RE = re.compile(
    r"\\begin\{remark\*\}\[Proof structure\](.*?)\\end\{remark\*\}",
    re.DOTALL,
)
PROOF_BODY_RE = re.compile(r"\\begin\{proof\}(?:\[(?P<title>[^\]]*)\])?(?P<body>.*?)\\end\{proof\}", re.DOTALL)


def _strip_comments_ws(text: str) -> str:
    lines = [re.sub(r"(?<!\\)%.*$", "", line) for line in text.splitlines()]
    return "".join(lines).strip()


def check(text: str, info, ctx) -> Iterable[Finding]:
    name = info.path.replace("\\", "/").rsplit("/", 1)[-1]
    if not name.startswith("prf-"):
        return
    bodies = []
    for proof in PROOF_BODY_RE.finditer(text):
        title = proof.group("title") or ""
        body = proof.group("body") or ""
        if (
            "Professional Standard Proof" in title
            or "Detailed Learning Proof" in title
            or "Professional Standard Proof" in body
            or "Detailed Learning Proof" in body
        ):
            bodies.append(body)
    is_stub = bool(bodies) and all(re.search(r"\bTODO\b", body, re.IGNORECASE) for body in bodies)
    match = PROOF_STRUCTURE_RE.search(text)
    if not match:
        return
    if is_stub and _strip_comments_ws(match.group(1)):
        yield Finding(
            "proof_stub_structure_not_blank",
            "Proof structure block must be blank while the proof is a stub (bodies are TODO); "
            "found planned-proof prose. Leave it blank until the proof is authored.",
            "error",
            text.count("\n", 0, match.start()) + 1,
        )
