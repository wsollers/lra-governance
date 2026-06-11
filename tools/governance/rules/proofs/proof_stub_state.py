from __future__ import annotations

import re
from collections.abc import Iterable

from core.finding import Finding

PROOF_STRUCTURE_RE = re.compile(
    r"\\begin\{remark\*\}\[Proof structure\](.*?)\\end\{remark\*\}",
    re.DOTALL,
)
PROOF_BODY_RE = re.compile(r"\\begin\{proof\}(?:\[(?P<title>[^\]]*)\])?(?P<body>.*?)\\end\{proof\}", re.DOTALL)
TODO_RE = re.compile(
    r"\bTODO\b|MIGRATION TODO|professional standard proof for|detailed learning proof for|"
    r"supply the compact professional proof|supply the expanded learning proof|"
    r"Expand the proof into a detailed learning proof|"
    r"Expand the professional proof into a detailed learning proof",
    re.IGNORECASE,
)
CONTENT_RE = re.compile(r"[A-Za-z]{3,}")


def _strip_comments_ws(text: str) -> str:
    lines = [re.sub(r"(?<!\\)%.*$", "", line) for line in text.splitlines()]
    return "".join(lines).strip()


def _body_without_comments(text: str) -> str:
    lines = [re.sub(r"(?<!\\)%.*$", "", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line and line != r"\LRAProofBodyStart"]
    return "\n".join(lines).strip()


def _is_stub_body(text: str) -> bool:
    body = _body_without_comments(text)
    if not body:
        return True
    lines = [line for line in body.splitlines() if line]
    if lines and all(TODO_RE.search(line) for line in lines):
        return True
    non_todo = "\n".join(line for line in lines if not TODO_RE.search(line))
    return not CONTENT_RE.search(non_todo)


def check(text: str, info, ctx) -> Iterable[Finding]:
    name = info.path.replace("\\", "/").rsplit("/", 1)[-1]
    if not name.startswith("prf-"):
        return
    bodies = []
    professional_states = []
    detailed_states = []
    for proof in PROOF_BODY_RE.finditer(text):
        title = proof.group("title") or ""
        body = proof.group("body") or ""
        is_stub_body = _is_stub_body(body)
        line = text.count("\n", 0, proof.start()) + 1
        if "Professional Standard Proof" in title:
            professional_states.append((is_stub_body, line))
        if "Detailed Learning Proof" in title:
            detailed_states.append((is_stub_body, line))
        if (
            "Professional Standard Proof" in title
            or "Detailed Learning Proof" in title
            or "Professional Standard Proof" in body
            or "Detailed Learning Proof" in body
        ):
            bodies.append(body)
    if professional_states and detailed_states:
        professional_authored = any(not is_stub for is_stub, _line in professional_states)
        detailed_stub = all(is_stub for is_stub, _line in detailed_states)
        if professional_authored and detailed_stub:
            yield Finding(
                "mixed_authored_professional_detailed_stub",
                "Professional proof layer is authored but Detailed Learning Proof is still a stub. "
                "Either keep both layers as a generated stub or author the detailed layer.",
                "error",
                detailed_states[0][1],
            )
    is_stub = bool(bodies) and all(_is_stub_body(body) for body in bodies)
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
