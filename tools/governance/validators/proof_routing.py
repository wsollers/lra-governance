from __future__ import annotations

from pathlib import Path

from core.finding import Finding, finding
from core.tex import INPUT_RE, is_routed, read_text, strip_latex_comment
from core.volume import chapter_roots


def validate(volume_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for chapter in chapter_roots(volume_root):
        proofs_root = chapter / "proofs"
        proofs_index = proofs_root / "index.tex"
        exercises_index = proofs_root / "exercises" / "index.tex"
        if exercises_index.exists() and not is_routed(proofs_index, exercises_index, chapter):
            findings.append(
                finding(
                    "unrouted_proof_exercises_index",
                    "proofs/exercises/index.tex is not routed from proofs/index.tex.",
                    proofs_index,
                    volume_root,
                )
            )

        if proofs_index.exists():
            text = read_text(proofs_index)
            if "\\begin{proof}" in text or "\\LRAProofFor{" in text:
                findings.append(
                    finding(
                        "proofs_index_contains_proof_content",
                        "proofs/index.tex must be a router, not a proof-content file.",
                        proofs_index,
                        volume_root,
                    )
                )
            _check_router_only(volume_root, proofs_index, findings, "proofs_index_contains_rendered_content", "proofs/index.tex")

        if not proofs_root.exists():
            continue
        for topic_dir in sorted(path for path in proofs_root.iterdir() if path.is_dir() and path.name != "exercises"):
            index = topic_dir / "index.tex"
            if index.exists():
                text = read_text(index)
                if "\\begin{proof}" in text or "\\LRAProofFor{" in text:
                    findings.append(
                        finding(
                            "proofs_topic_index_contains_proof_content",
                            f"proofs/{topic_dir.name}/index.tex must route proof files, not contain proof content.",
                            index,
                            volume_root,
                        )
                    )
                _check_router_only(
                    volume_root,
                    index,
                    findings,
                    "proofs_topic_index_contains_rendered_content",
                    f"proofs/{topic_dir.name}/index.tex",
                )
                if not is_routed(proofs_index, index, chapter):
                    findings.append(
                        finding(
                            "unrouted_proofs_topic",
                            f"proofs/{topic_dir.name}/index.tex is not routed from proofs/index.tex.",
                            index,
                            volume_root,
                        )
                    )
            for proof_file in sorted(topic_dir.glob("*.tex")):
                if proof_file.name == "index.tex":
                    continue
                if not is_routed(index, proof_file, chapter):
                    findings.append(
                        finding(
                            "unrouted_proof_topic_file",
                            f"{proof_file.relative_to(chapter).as_posix()} is not routed from proofs/{topic_dir.name}/index.tex.",
                            proof_file,
                            volume_root,
                        )
                    )
    return findings


def _check_router_only(volume_root: Path, index: Path, findings: list[Finding], code: str, label: str) -> None:
    for line_no, raw in enumerate(read_text(index).splitlines(), 1):
        line = strip_latex_comment(raw).strip()
        if line and not INPUT_RE.fullmatch(line):
            findings.append(
                finding(
                    code,
                    f"{label} must be a router containing only input lines.",
                    index,
                    volume_root,
                    line_no,
                )
            )
